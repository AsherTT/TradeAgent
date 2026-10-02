"""Default-off, token-guarded secure RAG intake and retrieval endpoints."""

from __future__ import annotations

from base64 import b64decode
from binascii import Error as Base64Error
from datetime import datetime
from secrets import compare_digest
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.rag import (
    DocumentFormat,
    DocumentSourceType,
    DocumentStatus,
    RagContext,
    RagHit,
    RagSearchRequest,
    RagSource,
)
from backend.app.persistence.rag import RagRepository, RagStorageError
from backend.app.persistence.session import get_session
from backend.app.rag.context import build_rag_context
from backend.app.rag.embedding import (
    EmbeddingProvider,
    RagEmbeddingError,
    build_rag_embedding_provider,
)
from backend.app.rag.ingestion import RagIngestionError, ingest_document
from backend.app.rag.retrieval import RagRetrievalError, RagRetriever

router = APIRouter(prefix="/rag", tags=["rag"])


class RagDocumentSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_id: UUID
    source_type: DocumentSourceType
    source_name: str = Field(min_length=1, max_length=128)
    source_uri: str | None = Field(default=None, max_length=2048)
    document_format: DocumentFormat
    content_base64: str = Field(min_length=1, max_length=2_700_000)
    available_at: datetime
    published_at: datetime | None = None


class RagDocumentRecorded(ContractModel):
    document_id: UUID
    status: DocumentStatus
    chunk_count: int
    injection_risk: float
    risk_reasons: tuple[str, ...]


class RagSearchSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_id: UUID
    query: str = Field(min_length=1, max_length=500)
    analysis_timestamp: datetime
    top_k: int = Field(default=8, ge=1, le=12)
    source_types: tuple[DocumentSourceType, ...] = ()
    max_context_chars: int = Field(default=6000, ge=256, le=12_000)


class RagSearchRecorded(ContractModel):
    hits: tuple[RagHit, ...]
    context: RagContext
    retrieval_mode: Literal["hybrid", "lexical_only"] = "hybrid"


def get_rag_embedder() -> EmbeddingProvider | None:
    provider = build_rag_embedding_provider(get_settings())
    if provider is None and get_settings().rag_retrieval_mode != "lexical_only":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG embedding provider is not configured",
        )
    return provider


def _require_access(token: str | None) -> None:
    settings = get_settings()
    if not settings.rag_enabled or not settings.rag_write_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG is disabled",
        )
    if token is None or not compare_digest(token, settings.rag_write_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid RAG token")


@router.post("/documents", response_model=RagDocumentRecorded)
async def record_document(
    submission: RagDocumentSubmission,
    session: Annotated[AsyncSession, Depends(get_session)],
    embeddings: Annotated[EmbeddingProvider | None, Depends(get_rag_embedder)],
    token: Annotated[str | None, Header(alias="X-RAG-Token")] = None,
) -> RagDocumentRecorded:
    _require_access(token)
    try:
        content = b64decode(submission.content_base64, validate=True)
        if (
            submission.available_at.tzinfo is None
            or submission.available_at.utcoffset() is None
        ):
            raise RagIngestionError("document timestamps must be timezone-aware")
        ingested_at = utc_now()
        source = RagSource(
            instrument_id=submission.instrument_id,
            source_type=submission.source_type,
            source_name=submission.source_name,
            source_uri=submission.source_uri,
            document_format=submission.document_format,
            raw_content=content,
            observed_at=ingested_at,
            available_at=max(submission.available_at, ingested_at),
            published_at=submission.published_at,
        )
        result = ingest_document(source)
        await RagRepository(session).store(result, embeddings=embeddings)
        await session.commit()
    except (Base64Error, RagIngestionError, RagStorageError, ValueError) as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RagEmbeddingError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RagDocumentRecorded(
        document_id=result.document.document_id,
        status=result.document.status,
        chunk_count=len(result.chunks),
        injection_risk=result.document.injection_risk,
        risk_reasons=result.document.risk_reasons,
    )


@router.post("/search", response_model=RagSearchRecorded)
async def search_documents(
    submission: RagSearchSubmission,
    session: Annotated[AsyncSession, Depends(get_session)],
    embeddings: Annotated[EmbeddingProvider | None, Depends(get_rag_embedder)],
    token: Annotated[str | None, Header(alias="X-RAG-Token")] = None,
) -> RagSearchRecorded:
    _require_access(token)
    request = RagSearchRequest(
        instrument_id=submission.instrument_id,
        query=submission.query,
        analysis_timestamp=submission.analysis_timestamp,
        top_k=submission.top_k,
        source_types=submission.source_types,
    )
    try:
        retriever = RagRetriever(session, embeddings=embeddings)
        hits = await retriever.search(request)
        context = build_rag_context(
            hits,
            instrument_id=request.instrument_id,
            analysis_timestamp=request.analysis_timestamp,
            max_chars=submission.max_context_chars,
            max_chunks=request.top_k,
        )
    except (RagRetrievalError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RagEmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RagSearchRecorded(hits=hits, context=context, retrieval_mode=retriever.mode)
