"""Append-only RAG document/chunk persistence with checked embedding provenance."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from math import isfinite
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.rag import DocumentStatus, RagChunk, RagDocument, RagIngestResult
from backend.app.persistence.models import RagChunkRow, RagDocumentRow
from backend.app.rag.embedding import EMBEDDING_DIMENSIONS, EmbeddingProvider
from backend.app.rag.ingestion import SCANNER_VERSION, _chunks


class RagStorageError(ValueError):
    """A document, chunk, or embedding violates the indexed-content invariant."""


class RagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(
        self, result: RagIngestResult, *, embeddings: EmbeddingProvider
    ) -> RagIngestResult:
        document = result.document
        chunks = result.chunks
        if (
            document.scanner_version != SCANNER_VERSION
            or document.sanitization_status != "parsed_normalized_scanned"
            or document.content_hash != sha256(document.content.encode()).hexdigest()
            or (document.status is DocumentStatus.QUARANTINED) != (not chunks)
            or (document.status is DocumentStatus.QUARANTINED and document.injection_risk < 0.7)
            or (document.status is DocumentStatus.ACCEPTED and document.injection_risk >= 0.7)
        ):
            raise RagStorageError("document did not pass the current RAG scanner")
        if len(chunks) > 64 or any(
            chunk.document_id != document.document_id
            or chunk.ordinal != index
            or chunk.content_hash != sha256(chunk.content.encode()).hexdigest()
            for index, chunk in enumerate(chunks)
        ):
            raise RagStorageError("chunk sequence or content hash is invalid")
        if chunks:
            expected_chunks = _chunks(document)
            if len(chunks) != len(expected_chunks) or any(
                (actual.ordinal, actual.heading, actual.content, actual.content_hash)
                != (expected.ordinal, expected.heading, expected.content, expected.content_hash)
                for actual, expected in zip(chunks, expected_chunks, strict=True)
            ):
                raise RagStorageError("chunks do not match sanitized document")
        prior = await self._session.get(RagDocumentRow, document.document_id)
        if prior is not None:
            if (
                await self.get_document(document.document_id) != document
                or await self.list_chunks(document.document_id) != chunks
            ):
                raise RagStorageError("document identifier cannot be rewritten")
            return result
        vectors = await embeddings.embed(tuple(chunk.content for chunk in chunks)) if chunks else ()
        if len(vectors) != len(chunks) or not embeddings.model_id:
            raise RagStorageError("embedding provider returned an invalid batch")
        for vector in vectors:
            if (
                len(vector) != EMBEDDING_DIMENSIONS
                or any(not isfinite(value) for value in vector)
                or not any(value != 0 for value in vector)
            ):
                raise RagStorageError("embedding dimensions or values are invalid")
        self._session.add(
            RagDocumentRow(
                document_id=document.document_id,
                instrument_id=document.instrument_id,
                source_type=document.source_type.value,
                source_name=document.source_name,
                source_uri=document.source_uri,
                document_format=document.document_format.value,
                observed_at=document.observed_at,
                available_at=document.available_at,
                published_at=document.published_at,
                content=document.content,
                content_hash=document.content_hash,
                trust_level=document.trust_level.value,
                sanitization_status=document.sanitization_status,
                injection_risk=document.injection_risk,
                scanner_version=document.scanner_version,
                status=document.status.value,
                risk_reasons=list(document.risk_reasons),
            )
        )
        await self._session.flush()
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._session.add(
                RagChunkRow(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    ordinal=chunk.ordinal,
                    heading=chunk.heading,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                    embedding=list(vector),
                    embedding_model=embeddings.model_id,
                )
            )
        await self._session.flush()
        return result

    async def get_document(self, document_id: UUID) -> RagDocument | None:
        row = await self._session.get(RagDocumentRow, document_id)
        if row is None:
            return None
        from backend.app.contracts.evidence import TrustLevel
        from backend.app.contracts.rag import DocumentFormat, DocumentSourceType

        def aware(value: datetime) -> datetime:
            return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

        return RagDocument(
            document_id=row.document_id,
            instrument_id=row.instrument_id,
            source_type=DocumentSourceType(row.source_type),
            source_name=row.source_name,
            source_uri=row.source_uri,
            document_format=DocumentFormat(row.document_format),
            observed_at=aware(row.observed_at),
            available_at=aware(row.available_at),
            published_at=aware(row.published_at) if row.published_at is not None else None,
            content=row.content,
            content_hash=row.content_hash,
            trust_level=TrustLevel(row.trust_level),
            sanitization_status=row.sanitization_status,
            injection_risk=row.injection_risk,
            scanner_version=row.scanner_version,
            status=DocumentStatus(row.status),
            risk_reasons=tuple(row.risk_reasons),
        )

    async def list_chunks(self, document_id: UUID) -> tuple[RagChunk, ...]:
        rows = await self._session.scalars(
            select(RagChunkRow)
            .where(RagChunkRow.document_id == document_id)
            .order_by(RagChunkRow.ordinal)
        )
        return tuple(
            RagChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                ordinal=row.ordinal,
                heading=row.heading,
                content=row.content,
                content_hash=row.content_hash,
            )
            for row in rows
        )
