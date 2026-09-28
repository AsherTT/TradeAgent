"""Labeled agent metrics and observable research integrity counts."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.contracts.evaluation import SecurityStatus
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.research import BudgetUsage, ResearchState
from backend.app.evaluation import AgentEvaluationCase, evaluate_agent_cases, evaluate_integrity


def test_agent_metrics_use_labels_and_leave_empty_denominators_undefined() -> None:
    evidence_id = uuid4()
    wrong_id = uuid4()
    case = AgentEvaluationCase(
        expected_tools=("market", "news"),
        called_tools=("market", "market", "rag"),
        relevant_evidence_ids=(evidence_id,),
        selected_evidence_ids=(evidence_id, wrong_id),
        cited_evidence_ids=(evidence_id,),
        supported_claim_count=3,
        unsupported_claim_count=1,
        structured_output_valid=True,
        replan_count=1,
        iteration_count=2,
        latency_ms=100,
        token_usage=120,
        estimated_cost_usd=0.01,
        fallback_count=1,
        timeout_count=0,
        provider_error_count=0,
    )
    result = evaluate_agent_cases((case,))
    assert result.case_count == 1
    assert result.tool_selection_precision == pytest.approx(2 / 3)
    assert result.tool_selection_recall == 0.5
    assert result.unnecessary_tool_call_rate == pytest.approx(1 / 3)
    assert result.evidence_precision == 0.5
    assert result.citation_precision == 1
    assert result.unsupported_claim_rate == 0.25
    assert result.fallback_rate == 1
    assert evaluate_agent_cases(()).tool_selection_precision is None


def test_integrity_counts_future_evidence_budget_and_security_block() -> None:
    cutoff = datetime(2020, 1, 1, tzinfo=UTC)
    instrument_id = uuid4()
    evidence = Evidence(
        instrument_id=instrument_id,
        evidence_type="news_document",
        source_name="fixture",
        observed_at=cutoff,
        retrieved_at=cutoff,
        available_at=cutoff + timedelta(seconds=1),
        content="future",
        confidence=1,
        freshness=1,
        source_type="news",
        content_hash="fixture",
        sanitization_status="html_cleaned_and_scanned",
        injection_risk=0,
    )
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="historical setup",
        requested_at=cutoff + timedelta(days=1),
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        parametric_lookahead_risk=True,
        evidence=(evidence,),
        budget_usage=BudgetUsage(tool_calls=13),
        security_status=SecurityStatus.BLOCKED,
    )
    report = evaluate_integrity((state,))
    assert report.point_in_time_violation_count == 1
    assert report.future_evidence_leakage_count == 1
    assert report.budget_guard_violation_count == 1
    assert report.security_blocked_count == 1
    assert report.observable_invariants_pass is False
