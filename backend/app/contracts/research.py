"""Research orchestration contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.evaluation import (
    DataQualityStatus,
    EvaluationMaturity,
    QualityAssessment,
    QualityGateDecision,
    ReplayIntegrityLevel,
    ResearchCompletion,
    SecurityStatus,
    SystemConfidence,
)
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.market import MarketSnapshot, TechnicalSnapshot
from backend.app.contracts.thesis import Thesis


class ResearchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTimestampMode(StrEnum):
    FIXED_CUTOFF = "fixed_cutoff"
    CURRENT_RESEARCH = "current_research"


class ResearchStep(ContractModel):
    step_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    objective: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    required: bool = True


class ResearchIntent(ContractModel):
    research_goal: str = Field(min_length=1, max_length=500)
    focus_areas: tuple[Annotated[str, Field(min_length=1, max_length=100)], ...] = Field(
        min_length=1, max_length=5
    )


class ResearchPlan(ContractModel):
    question: str = Field(min_length=1)
    instrument_symbol: str = Field(min_length=1, max_length=32)
    horizon: str = Field(min_length=1)
    steps: tuple[ResearchStep, ...] = Field(min_length=1)
    stop_conditions: tuple[str, ...] = Field(min_length=1)
    evidence_requirements: tuple[str, ...] = Field(min_length=1)


class ResearchBudget(ContractModel):
    max_iterations: int = Field(default=4, ge=1)
    max_replans: int = Field(default=2, ge=0)
    max_tool_calls: int = Field(default=12, ge=0)
    max_llm_calls: int = Field(default=10, ge=0)
    max_wall_time_seconds: int = Field(default=120, ge=1)
    max_context_tokens: int = Field(default=100_000, ge=1)
    max_estimated_cost_usd: float = Field(default=10.0, ge=0)
    max_news_documents: int = Field(default=30, ge=0)
    max_rag_chunks: int = Field(default=12, ge=0)


class BudgetUsage(ContractModel):
    iterations: int = Field(default=0, ge=0)
    replans: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    llm_calls: int = Field(default=0, ge=0)
    wall_time_seconds: float = Field(default=0, ge=0)
    context_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)
    news_documents: int = Field(default=0, ge=0)
    rag_chunks: int = Field(default=0, ge=0)

    def exceeded_fields(self, budget: ResearchBudget) -> tuple[str, ...]:
        mapping = {
            "iterations": "max_iterations",
            "replans": "max_replans",
            "tool_calls": "max_tool_calls",
            "llm_calls": "max_llm_calls",
            "wall_time_seconds": "max_wall_time_seconds",
            "context_tokens": "max_context_tokens",
            "estimated_cost_usd": "max_estimated_cost_usd",
            "news_documents": "max_news_documents",
            "rag_chunks": "max_rag_chunks",
        }
        return tuple(
            usage_name
            for usage_name, budget_name in mapping.items()
            if getattr(self, usage_name) >= getattr(budget, budget_name)
        )


class ResearchState(ContractModel):
    research_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    ticker: str
    query: str
    requested_at: datetime = Field(default_factory=utc_now)
    timestamp_mode: ResearchTimestampMode = ResearchTimestampMode.FIXED_CUTOFF
    analysis_timestamp: datetime | None
    horizon: str
    research_intent: ResearchIntent | None = None
    research_plan: ResearchPlan | None = None
    research_budget: ResearchBudget = Field(default_factory=ResearchBudget)
    budget_usage: BudgetUsage = Field(default_factory=BudgetUsage)
    market_snapshot: MarketSnapshot | None = None
    technical_snapshot: TechnicalSnapshot | None = None
    news_events: tuple[dict[str, Any], ...] = ()
    filings: tuple[dict[str, Any], ...] = ()
    sector_context: dict[str, Any] | None = None
    macro_context: dict[str, Any] | None = None
    evidence: tuple[Evidence, ...] = ()
    previous_thesis: Thesis | None = None
    current_thesis: Thesis | None = None
    bull_case: dict[str, Any] | None = None
    bear_case: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None
    evidence_gaps: tuple[str, ...] = ()
    tool_history: tuple[dict[str, Any], ...] = ()
    model_history: tuple[dict[str, Any], ...] = ()
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)
    replay_integrity_level: ReplayIntegrityLevel = ReplayIntegrityLevel.RESEARCH_REPLAY
    parametric_lookahead_risk: bool = False
    data_quality_status: DataQualityStatus = DataQualityStatus.UNVERIFIED
    evaluation_maturity: EvaluationMaturity = EvaluationMaturity.COLD_START
    security_status: SecurityStatus = SecurityStatus.PASS
    research_completion: ResearchCompletion | None = None
    quality_gate_decision: QualityGateDecision | None = None
    system_confidence: SystemConfidence | None = None
    quality_assessment: QualityAssessment | None = None
    status: ResearchStatus = ResearchStatus.PENDING

    @model_validator(mode="after")
    def historical_replay_discloses_parametric_risk(self) -> ResearchState:
        if (
            self.timestamp_mode is ResearchTimestampMode.FIXED_CUTOFF
            and self.analysis_timestamp is None
        ):
            raise ValueError("fixed-cutoff research requires analysis_timestamp")
        if self.status is ResearchStatus.COMPLETE and self.analysis_timestamp is None:
            raise ValueError("complete research requires a frozen analysis_timestamp")
        if self.analysis_timestamp is None:
            return self
        historical_modes = {
            ReplayIntegrityLevel.RESEARCH_REPLAY,
            ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        }
        historical_cutoff = self.requested_at - timedelta(minutes=5)
        if (
            self.replay_integrity_level in historical_modes
            and self.analysis_timestamp < historical_cutoff
        ):
            if not self.parametric_lookahead_risk:
                raise ValueError("historical LLM replay must declare parametric_lookahead_risk")
        return self
