"""Integrity, maturity, quality, and statistical reliability contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from backend.app.contracts.base import ContractModel


class ReplayIntegrityLevel(StrEnum):
    RESEARCH_REPLAY = "research_replay"
    EVIDENCE_CONSTRAINED_REPLAY = "evidence_constrained_replay"
    STRICT_QUANT_BACKTEST = "strict_quant_backtest"
    FORWARD_EVALUATION = "forward_evaluation"


class EvaluationMaturity(StrEnum):
    COLD_START = "cold_start"
    ACCUMULATING = "accumulating"
    EARLY_SAMPLE = "early_sample"
    MATURE = "mature"


class DataQualityStatus(StrEnum):
    VERIFIED = "verified"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


class SecurityStatus(StrEnum):
    PASS = "pass"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ResearchCompletion(StrEnum):
    COMPLETE = "complete"
    BUDGET_EXHAUSTED = "budget_exhausted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityGateDecision(StrEnum):
    PUBLISHABLE = "publishable"
    DEGRADED = "degraded"
    INSUFFICIENT = "insufficient"
    BLOCKED = "blocked"


class StatisticalStatus(StrEnum):
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    EARLY_ESTIMATE = "early_estimate"
    USABLE = "usable"


class ProviderQualityReport(ContractModel):
    provider: str
    provider_version: str
    evaluated_at: datetime
    golden_case_count: int = Field(ge=0)
    passed_case_count: int = Field(ge=0)
    failed_cases: tuple[str, ...] = ()
    coverage: float = Field(ge=0, le=1)
    quality_status: DataQualityStatus
    notes: str | None = None


class SystemConfidence(ContractModel):
    """System-level confidence, deliberately separate from model probability."""

    score: float = Field(ge=0, le=1)
    factors: dict[str, float] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()


class QualityAssessment(ContractModel):
    data_quality: DataQualityStatus
    evaluation_maturity: EvaluationMaturity
    replay_integrity: ReplayIntegrityLevel
    security_status: SecurityStatus
    evidence_coverage: float = Field(ge=0, le=1)
    research_completion: ResearchCompletion
    system_confidence: SystemConfidence
    decision: QualityGateDecision
    reasons: tuple[str, ...] = ()
