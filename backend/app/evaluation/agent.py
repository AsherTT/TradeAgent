"""Agent engineering metrics over labeled offline or forward evaluation cases."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel


class AgentEvaluationCase(ContractModel):
    expected_tools: tuple[str, ...] = ()
    called_tools: tuple[str, ...] = ()
    relevant_evidence_ids: tuple[UUID, ...] = ()
    selected_evidence_ids: tuple[UUID, ...] = ()
    cited_evidence_ids: tuple[UUID, ...] = ()
    supported_claim_count: int = Field(ge=0)
    unsupported_claim_count: int = Field(ge=0)
    structured_output_valid: bool
    replan_count: int = Field(ge=0)
    iteration_count: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    token_usage: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    fallback_count: int = Field(ge=0)
    timeout_count: int = Field(ge=0)
    provider_error_count: int = Field(ge=0)


class AgentEvaluationReport(ContractModel):
    case_count: int = Field(ge=0)
    tool_selection_precision: float | None
    tool_selection_recall: float | None
    unnecessary_tool_call_rate: float | None
    evidence_precision: float | None
    evidence_recall: float | None
    citation_precision: float | None
    citation_coverage: float | None
    unsupported_claim_rate: float | None
    structured_output_valid_rate: float | None
    replan_count: int = Field(ge=0)
    iteration_count: int = Field(ge=0)
    latency_ms_mean: float | None
    token_usage: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    fallback_rate: float | None
    timeout_rate: float | None
    provider_error_rate: float | None


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate_agent_cases(cases: tuple[AgentEvaluationCase, ...]) -> AgentEvaluationReport:
    """Aggregate labeled cases; undefined rates stay null instead of implying success."""

    expected_tool_count = called_tool_count = correct_tool_count = recovered_tool_count = 0
    relevant_count = selected_count = correct_selected_count = 0
    cited_count = correct_cited_count = 0
    supported_claims = unsupported_claims = 0
    for case in cases:
        expected = set(case.expected_tools)
        called = set(case.called_tools)
        relevant = set(case.relevant_evidence_ids)
        selected = set(case.selected_evidence_ids)
        cited = set(case.cited_evidence_ids)
        expected_tool_count += len(expected)
        called_tool_count += len(case.called_tools)
        correct_tool_count += sum(tool in expected for tool in case.called_tools)
        recovered_tool_count += len(expected & called)
        relevant_count += len(relevant)
        selected_count += len(selected)
        correct_selected_count += len(relevant & selected)
        cited_count += len(cited)
        correct_cited_count += len(relevant & cited)
        supported_claims += case.supported_claim_count
        unsupported_claims += case.unsupported_claim_count
    count = len(cases)
    return AgentEvaluationReport(
        case_count=count,
        tool_selection_precision=_rate(correct_tool_count, called_tool_count),
        tool_selection_recall=_rate(recovered_tool_count, expected_tool_count),
        unnecessary_tool_call_rate=_rate(
            called_tool_count - correct_tool_count, called_tool_count
        ),
        evidence_precision=_rate(correct_selected_count, selected_count),
        evidence_recall=_rate(correct_selected_count, relevant_count),
        citation_precision=_rate(correct_cited_count, cited_count),
        citation_coverage=_rate(correct_cited_count, relevant_count),
        unsupported_claim_rate=_rate(
            unsupported_claims, supported_claims + unsupported_claims
        ),
        structured_output_valid_rate=_rate(
            sum(case.structured_output_valid for case in cases), count
        ),
        replan_count=sum(case.replan_count for case in cases),
        iteration_count=sum(case.iteration_count for case in cases),
        latency_ms_mean=(sum(case.latency_ms for case in cases) / count if count else None),
        token_usage=sum(case.token_usage for case in cases),
        estimated_cost_usd=sum(case.estimated_cost_usd for case in cases),
        fallback_rate=_rate(sum(case.fallback_count > 0 for case in cases), count),
        timeout_rate=_rate(sum(case.timeout_count > 0 for case in cases), count),
        provider_error_rate=_rate(sum(case.provider_error_count > 0 for case in cases), count),
    )
