"""Evidence and trust-boundary contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import Field

from backend.app.contracts.base import ContractModel


class TrustLevel(StrEnum):
    OFFICIAL_PRIMARY = "official_primary"
    TRUSTED_PROVIDER = "trusted_provider"
    PUBLIC_SOURCE = "public_source"
    USER_CONTENT = "user_content"
    UNKNOWN = "unknown"


class Evidence(ContractModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    evidence_type: str
    source_name: str
    source_uri: str | None = None
    published_at: datetime | None = None
    effective_at: datetime | None = None
    observed_at: datetime
    retrieved_at: datetime
    available_at: datetime
    content: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    trust_level: TrustLevel = TrustLevel.UNKNOWN
    source_type: str
    content_hash: str
    sanitization_status: str
    injection_risk: float = Field(ge=0, le=1)
    scanner_version: str | None = None


class EvidenceBundle(ContractModel):
    evidence: tuple[Evidence, ...] = ()
    coverage: float = Field(ge=0, le=1)
    gaps: tuple[str, ...] = ()


class EvidenceGapResult(ContractModel):
    """Deterministic coverage of the capabilities required by a research plan."""

    required_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    coverage: float = Field(ge=0, le=1)
    sufficient: bool


class ResearchSynthesis(ContractModel):
    """Evidence-cited research summary, separate from the Phase 6 thesis lifecycle."""

    summary: str = Field(min_length=1, max_length=2000)
    bull_case: str = Field(min_length=1, max_length=1000)
    bear_case: str = Field(min_length=1, max_length=1000)
    limitations: tuple[Annotated[str, Field(min_length=1, max_length=500)], ...] = Field(
        max_length=5
    )
    evidence_ids: tuple[UUID, ...] = Field(min_length=1, max_length=8)
    confidence: float = Field(ge=0, le=1)
