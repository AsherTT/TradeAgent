"""Evaluate observable temporal, budget and security-state invariants."""

from __future__ import annotations

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import SecurityStatus
from backend.app.contracts.research import ResearchState


class IntegrityEvaluationReport(ContractModel):
    run_count: int = Field(ge=0)
    point_in_time_violation_count: int = Field(ge=0)
    future_evidence_leakage_count: int = Field(ge=0)
    budget_guard_violation_count: int = Field(ge=0)
    security_blocked_count: int = Field(ge=0)
    observable_invariants_pass: bool


def evaluate_integrity(states: tuple[ResearchState, ...]) -> IntegrityEvaluationReport:
    """Count violations visible in persisted state; external invariants need their own probes."""

    pit = leakage = budget = blocked = 0
    for state in states:
        cutoff = state.analysis_timestamp
        if cutoff is not None:
            for evidence in state.evidence:
                if (
                    evidence.observed_at > cutoff
                    or evidence.available_at > cutoff
                    or (evidence.published_at is not None and evidence.published_at > cutoff)
                ):
                    leakage += 1
                    pit += 1
        snapshot = state.market_snapshot
        if cutoff is not None and snapshot is not None and (
            snapshot.analysis_timestamp != cutoff
            or snapshot.latest_bar.timestamp > cutoff
            or snapshot.latest_bar.observed_at > cutoff
            or snapshot.latest_bar.available_at > cutoff
        ):
            pit += 1
        usage = state.budget_usage
        limits = state.research_budget
        if any((
            usage.iterations > limits.max_iterations,
            usage.replans > limits.max_replans,
            usage.tool_calls > limits.max_tool_calls,
            usage.llm_calls > limits.max_llm_calls,
            usage.wall_time_seconds > limits.max_wall_time_seconds,
            usage.context_tokens > limits.max_context_tokens,
            usage.estimated_cost_usd > limits.max_estimated_cost_usd,
            usage.news_documents > limits.max_news_documents,
            usage.rag_chunks > limits.max_rag_chunks,
        )):
            budget += 1
        if state.security_status is SecurityStatus.BLOCKED:
            blocked += 1
    return IntegrityEvaluationReport(
        run_count=len(states),
        point_in_time_violation_count=pit,
        future_evidence_leakage_count=leakage,
        budget_guard_violation_count=budget,
        security_blocked_count=blocked,
        observable_invariants_pass=pit == leakage == budget == blocked == 0,
    )
