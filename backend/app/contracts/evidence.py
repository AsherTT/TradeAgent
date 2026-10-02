"""Evidence and trust-boundary contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.thesis import Direction


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


class SynthesisClaim(ContractModel):
    section: Literal[
        "summary", "bull_case", "bear_case", "business", "financial", "catalyst", "price"
    ]
    text: str = Field(min_length=1, max_length=500)
    evidence_id: UUID
    supporting_quote: str = Field(min_length=10, max_length=300)

    @model_validator(mode="after")
    def meaningful_text(self) -> SynthesisClaim:
        if not self.text.strip() or len(self.supporting_quote.strip()) < 10:
            raise ValueError("claim text and quote must contain meaningful text")
        return self


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
    forecast_direction: Direction | None = None
    forecast_probability: float | None = Field(default=None, ge=0, le=1)
    claims: tuple[SynthesisClaim, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def complete_forecast_pair(self) -> ResearchSynthesis:
        if (self.forecast_direction is None) != (self.forecast_probability is None):
            raise ValueError("forecast direction and probability must be supplied together")
        return self


class CatalystAssessment(ContractModel):
    claims: tuple[SynthesisClaim, ...] = Field(default=(), max_length=5)
    limitations: tuple[Annotated[str, Field(min_length=1, max_length=300)], ...] = Field(
        max_length=3
    )

    @model_validator(mode="after")
    def catalyst_sections(self) -> CatalystAssessment:
        if any(claim.section != "catalyst" for claim in self.claims):
            raise ValueError("catalyst assessment permits only catalyst interpretations")
        return self
