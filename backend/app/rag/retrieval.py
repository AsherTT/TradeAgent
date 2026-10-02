"""Point-in-time hybrid retrieval with PostgreSQL FTS, pgvector, and bounded RRF."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from math import isfinite
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.evidence import TrustLevel
from backend.app.contracts.rag import DocumentSourceType, RagHit, RagSearchRequest
from backend.app.persistence.models import RagChunkRow, RagDocumentRow
from backend.app.rag.embedding import EMBEDDING_DIMENSIONS, EmbeddingProvider
from backend.app.rag.ingestion import SCANNER_VERSION


class RagRetrievalError(ValueError):
    """The query cannot be safely executed against the configured RAG index."""


def reciprocal_rank_fusion(
    lexical: tuple[UUID, ...], vector: tuple[UUID, ...], *, rank_constant: int = 60
) -> tuple[tuple[UUID, float], ...]:
    """Fuse two already-filtered rankings; ties are stable by UUID."""
    if rank_constant < 1:
        raise ValueError("rank constant must be positive")
    scores: dict[UUID, float] = {}
    for ranking in (lexical, vector):
        for rank, chunk_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (rank_constant + rank)
    return tuple(sorted(scores.items(), key=lambda item: (-item[1], str(item[0]))))


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class RagRetriever:
    def __init__(self, session: AsyncSession, *, embeddings: EmbeddingProvider | None) -> None:
        self._session = session
        self._embeddings = embeddings

    @property
    def mode(self) -> Literal["hybrid", "lexical_only"]:
        return "lexical_only" if self._embeddings is None else "hybrid"

    async def search(self, request: RagSearchRequest) -> tuple[RagHit, ...]:
        cutoff = request.analysis_timestamp
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            raise RagRetrievalError("analysis timestamp must be timezone-aware")
        if self._session.bind is None or self._session.bind.dialect.name != "postgresql":
            raise RagRetrievalError("hybrid retrieval requires PostgreSQL")
        vector = None
        if self._embeddings is not None:
            vectors = await self._embeddings.embed((request.query,))
            if len(vectors) != 1 or not self._embeddings.model_id:
                raise RagRetrievalError("query embedding is unavailable")
            vector = vectors[0]
            if (
                len(vector) != EMBEDDING_DIMENSIONS
                or any(not isfinite(value) for value in vector)
                or not any(value != 0 for value in vector)
            ):
                raise RagRetrievalError("query embedding is invalid")
        cutoff = cutoff.astimezone(UTC)
        predicates: list[Any] = [
            RagDocumentRow.instrument_id == request.instrument_id,
            RagDocumentRow.status == "accepted",
            RagDocumentRow.injection_risk < 0.7,
            RagDocumentRow.scanner_version == SCANNER_VERSION,
            RagDocumentRow.sanitization_status == "parsed_normalized_scanned",
            RagDocumentRow.trust_level.in_(
                [
                    TrustLevel.OFFICIAL_PRIMARY.value,
                    TrustLevel.TRUSTED_PROVIDER.value,
                    TrustLevel.PUBLIC_SOURCE.value,
                    TrustLevel.USER_CONTENT.value,
                ]
            ),
            RagDocumentRow.observed_at <= cutoff,
            RagDocumentRow.available_at <= cutoff,
            (RagDocumentRow.published_at.is_(None) | (RagDocumentRow.published_at <= cutoff)),
        ]
        if self._embeddings is not None:
            predicates.extend([
                RagChunkRow.embedding_model == self._embeddings.model_id,
                RagChunkRow.embedding.is_not(None),
            ])
        if request.source_types:
            predicates.append(
                RagDocumentRow.source_type.in_([source.value for source in request.source_types])
            )
        candidate_limit = min(50, max(12, request.top_k * 4))
        query = func.plainto_tsquery("english", request.query)
        if self._embeddings is None:
            terms = tuple(dict.fromkeys(re.findall(r"[A-Za-z0-9]{2,40}", request.query)))[:12]
            query = func.websearch_to_tsquery("english", " OR ".join(terms))
        search_vector = func.to_tsvector("english", RagChunkRow.content)
        common = (
            select(RagChunkRow.chunk_id)
            .join(RagDocumentRow, RagDocumentRow.document_id == RagChunkRow.document_id)
            .where(*predicates)
        )
        lexical = tuple(
            (
                await self._session.scalars(
                    common.where(search_vector.op("@@")(query))
                    .order_by(func.ts_rank(search_vector, query).desc(), RagChunkRow.chunk_id)
                    .limit(candidate_limit)
                )
            ).all()
        )
        semantic: tuple[UUID, ...] = ()
        if vector is not None:
            distance = cast(Any, RagChunkRow.embedding).cosine_distance(list(vector))
            semantic = tuple(
            (
                await self._session.scalars(
                    common.order_by(distance, RagChunkRow.chunk_id).limit(candidate_limit)
                )
            ).all()
            )
        ranking = reciprocal_rank_fusion(lexical, semantic)[: request.top_k]
        if not ranking:
            return ()
        scores = dict(ranking)
        rows = (
            await self._session.execute(
                select(RagChunkRow, RagDocumentRow)
                .join(RagDocumentRow, RagDocumentRow.document_id == RagChunkRow.document_id)
                .where(RagChunkRow.chunk_id.in_(scores), *predicates)
            )
        ).all()
        hits = {
            chunk.chunk_id: RagHit(
                chunk_id=chunk.chunk_id,
                document_id=document.document_id,
                instrument_id=document.instrument_id,
                source_type=DocumentSourceType(document.source_type),
                source_name=document.source_name,
                source_uri=document.source_uri,
                observed_at=_as_utc(document.observed_at),
                available_at=_as_utc(document.available_at),
                published_at=(
                    _as_utc(document.published_at) if document.published_at is not None else None
                ),
                heading=chunk.heading,
                content=chunk.content,
                content_hash=chunk.content_hash,
                trust_level=TrustLevel(document.trust_level),
                sanitization_status=document.sanitization_status,
                injection_risk=document.injection_risk,
                scanner_version=document.scanner_version,
                score=scores[chunk.chunk_id],
            )
            for chunk, document in rows
        }
        return tuple(hits[chunk_id] for chunk_id, _ in ranking if chunk_id in hits)
