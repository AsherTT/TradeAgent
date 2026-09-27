"""Bounded document and chunk contracts for the untrusted RAG boundary."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evidence import TrustLevel


class DocumentFormat(StrEnum):
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


class DocumentSourceType(StrEnum):
    SEC_FILING = "sec_filing"
    WEB_ARTICLE = "web_article"
    EXTERNAL_RESEARCH = "external_research"
    USER_NOTE = "user_note"


class DocumentStatus(StrEnum):
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"


class RagSource(ContractModel):
    instrument_id: UUID
    source_type: DocumentSourceType
    source_name: str = Field(min_length=1, max_length=128)
    source_uri: str | None = Field(default=None, max_length=2048)
    document_format: DocumentFormat
    raw_content: bytes = Field(min_length=1, max_length=2_000_000)
    observed_at: datetime
    available_at: datetime
    published_at: datetime | None = None


class RagDocument(ContractModel):
    document_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    source_type: DocumentSourceType
    source_name: str
    source_uri: str | None
    document_format: DocumentFormat
    observed_at: datetime
    available_at: datetime
    published_at: datetime | None
    content: str
    content_hash: str
    trust_level: TrustLevel
    sanitization_status: str
    injection_risk: float = Field(ge=0, le=1)
    scanner_version: str
    status: DocumentStatus
    risk_reasons: tuple[str, ...] = ()


class RagChunk(ContractModel):
    chunk_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    ordinal: int = Field(ge=0)
    heading: str | None = None
    content: str = Field(min_length=1, max_length=1200)
    content_hash: str


class RagIngestResult(ContractModel):
    document: RagDocument
    chunks: tuple[RagChunk, ...]
