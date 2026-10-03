"""Report-boundary regressions for source-linked partial financial explanations."""

from datetime import date, timedelta
from decimal import Decimal, localcontext
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.financials.analysis import FinancialMetricAssessment
from backend.app.reports.research import ResearchReport, build_research_report
from backend.tests.test_financial_integration import ID, NOW, financial_evidence, snapshot, state


@pytest.mark.parametrize("net_income,expected", [
    ("200", "annual profit"), ("-200", "annual loss"), ("0", "break-even net income"),
])
def test_report_explains_reported_annual_sign_with_exact_sources(
    net_income: str, expected: str,
) -> None:
    items = tuple(fact.model_copy(update={"value": Decimal(net_income)}).to_evidence(ID, cutoff=NOW)
                  if fact.concept == "NetIncomeLoss" else fact.to_evidence(ID, cutoff=NOW)
                  for fact in snapshot().facts)
    incoming = state(analysis_timestamp=NOW, evidence=items)
    report = build_research_report(incoming)
    result = report.financial_metric_assessments[0]
    assert result.metric == report.financial_metrics[0]
    assert result.interpretation is not None and expected in result.interpretation
    assert "2025-07-01 to 2026-06-30" in result.interpretation
    assert result.metric.evidence_ids == (items[2].evidence_id, items[3].evidence_id)
    assert set(result.metric.evidence_ids) <= {c.evidence_id for c in report.citations}
    section = next(s for s in report.sections if s.title.endswith("annual_net_margin")
                   and s.title.startswith("Partial"))
    assert section.evidence_ids == result.metric.evidence_ids
    assert "does not establish growth" in section.text
    assert not report.complete_analysis
    assert report == ResearchReport.model_validate_json(report.model_dump_json())
    assert incoming.budget_usage == state().budget_usage


@pytest.mark.parametrize("concept,value,reason,index", [
    ("Assets", "0", "nonpositive_denominator", 1),
    ("RevenueFromContractWithCustomerExcludingAssessedTax", "-1", "nonpositive_denominator", 0),
    ("CashAndCashEquivalentsAtCarryingValue", "-1", "negative_cash", 1),
])
def test_metric_failure_exposes_reason_without_suppressing_other_metric(
    concept: str, value: str, reason: str, index: int,
) -> None:
    items = tuple(fact.model_copy(update={"value": Decimal(value)}).to_evidence(ID, cutoff=NOW)
                  if fact.concept == concept else fact.to_evidence(ID, cutoff=NOW)
                  for fact in snapshot().facts)
    report = build_research_report(state(analysis_timestamp=NOW, evidence=items))
    result = report.financial_metric_assessments[index]
    assert result.unavailable_reason == reason
    assert result.metric is None and result.interpretation is None
    assert report.financial_metric_assessments[1-index].metric is not None
    assert len(report.financial_metrics) == 1
    section = next(s for s in report.sections if s.title ==
                   f"Partial financial interpretation: {result.name}")
    assert reason in section.text and section.evidence_ids == ()


@pytest.mark.parametrize("case", ["missing", "stale", "future", "tampered", "instrument",
                                  "conflict", "period"])
def test_report_rechecks_group_qualification_before_explaining(case: str) -> None:
    items = financial_evidence()
    cutoff = NOW
    if case == "missing":
        items = items[:-1]
    elif case == "stale":
        cutoff += timedelta(days=600)
    elif case == "future":
        cutoff -= timedelta(seconds=1)
    elif case == "tampered":
        items = (items[0].model_copy(update={"content_hash": "forged"}), *items[1:])
    elif case == "instrument":
        items = (items[0].model_copy(update={"instrument_id": uuid4()}), *items[1:])
    elif case == "conflict":
        conflicting = snapshot().facts[0].model_copy(update={"value": Decimal(42)})
        items = (*items, conflicting.to_evidence(ID, cutoff=NOW))
    else:
        changed = snapshot().facts[-1].model_copy(update={"period_start": date(2025, 6, 30)})
        items = (*items[:-1], changed.to_evidence(ID, cutoff=NOW))
    report = build_research_report(state(analysis_timestamp=cutoff, evidence=items))
    assert report.financial_metrics == ()
    assert all(a.metric is None and a.interpretation is None and a.unavailable_reason ==
               "qualified_financial_group_unavailable" for a in report.financial_metric_assessments)


def test_missing_cutoff_and_legacy_report_are_explicit_and_readable() -> None:
    report = build_research_report(state(evidence=financial_evidence()))
    assert all(a.unavailable_reason == "analysis_cutoff_unavailable"
               for a in report.financial_metric_assessments)
    data = report.model_dump()
    del data["financial_metric_assessments"]
    assert ResearchReport.model_validate(data).financial_metric_assessments == ()


def test_extreme_reported_ratio_retains_precision_and_reconciliation_limit() -> None:
    items = tuple(fact.model_copy(update={"value": Decimal(3)}).to_evidence(ID, cutoff=NOW)
                  if fact.concept == "Assets" else fact.to_evidence(ID, cutoff=NOW)
                  for fact in snapshot().facts)
    with localcontext() as context:
        context.prec = 2
        report = build_research_report(state(analysis_timestamp=NOW, evidence=items))
    result = report.financial_metric_assessments[1]
    assert result.metric is not None
    assert result.metric.value == Decimal("333.3333333333333333333333333")
    assert any("Ratio exceeds one" in limit for limit in result.limitations)
    assert any("liquidity sufficiency" in limit for limit in result.limitations)


def test_assessment_rejects_contradictory_available_and_unavailable_states() -> None:
    metric = build_research_report(state(analysis_timestamp=NOW, evidence=financial_evidence()))
    with pytest.raises(ValidationError):
        FinancialMetricAssessment(name="annual_net_margin", interpretation="invented profit")
    with pytest.raises(ValidationError):
        FinancialMetricAssessment(name="cash_to_assets", metric=metric.financial_metrics[0],
                                  interpretation="wrong metric")
    with pytest.raises(ValidationError):
        FinancialMetricAssessment(name="annual_net_margin", metric=metric.financial_metrics[0],
                                  interpretation="profit", unavailable_reason="negative_cash")
