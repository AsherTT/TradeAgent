"""Source-bounded arithmetic, catalyst model budgets and durable recovery."""

from datetime import timedelta
from decimal import Decimal, localcontext
from hashlib import sha256
from time import perf_counter
from uuid import uuid4

import pytest

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.contracts.evidence import CatalystAssessment, Evidence, SynthesisClaim, TrustLevel
from backend.app.contracts.model import ProviderName
from backend.app.contracts.research import (
    BudgetUsage,
    ResearchBudget,
    ResearchState,
    ResearchStatus,
)
from backend.app.financials.analysis import derive_financial_metrics
from backend.app.graph.workflow import ResearchWorkflow
from backend.app.news.catalysts import catalyst_sources, validate_catalysts
from backend.app.reports.research import build_research_report
from backend.tests.test_financial_integration import ID, NOW, financial_evidence, snapshot, state


def news() -> Evidence:
    text = "KLA announced its quarterly earnings release. More details remain unverified."
    return Evidence(
        instrument_id=ID, evidence_type="news_document", source_name="fixture",
        source_uri="https://example.org/fixture", observed_at=NOW, retrieved_at=NOW,
        available_at=NOW, published_at=NOW, content=text,
        content_hash=sha256(text.encode()).hexdigest(), confidence=0.5, freshness=1,
        trust_level=TrustLevel.PUBLIC_SOURCE, source_type="company_news",
        sanitization_status="html_cleaned_and_scanned", injection_risk=0,
        scanner_version="news-guard-v1",
    )


def incoming() -> ResearchState:
    return state(
        analysis_timestamp=NOW, evidence=(news(),), status=ResearchStatus.RUNNING,
        research_budget=ResearchBudget(max_llm_calls=3), budget_usage=BudgetUsage(llm_calls=2),
    )


def assessment(item: Evidence) -> CatalystAssessment:
    return CatalystAssessment(claims=(SynthesisClaim(
        section="catalyst", text="A source reports an earnings announcement.",
        evidence_id=item.evidence_id, supporting_quote="announced its quarterly earnings release",
    ),), limitations=("Event timing and price impact are not verified.",))


def test_financial_metrics_retain_source_formula_and_context_independent_precision() -> None:
    items = financial_evidence()
    metrics = derive_financial_metrics(items, cutoff=NOW)
    assert len(metrics) == 2
    assert all(metric.value == 1 and len(metric.evidence_ids) == 2 for metric in metrics)
    numerator = snapshot().facts[2].model_copy(update={"value": Decimal(1)}).to_evidence(
        ID, cutoff=NOW,
    )
    denominator = snapshot().facts[3].model_copy(update={"value": Decimal(3)}).to_evidence(
        ID, cutoff=NOW,
    )
    with localcontext() as context:
        context.prec = 2
        actual = derive_financial_metrics((*items[:2], numerator, denominator), cutoff=NOW)
    assert actual[0].value == Decimal("0.3333333333333333333333333333")
    assert actual[0].evidence_ids == (numerator.evidence_id, denominator.evidence_id)
    report = build_research_report(state(analysis_timestamp=NOW, evidence=items))
    assert report.financial_metrics == metrics and not report.complete_analysis


@pytest.mark.parametrize("concept,value,expected", [
    ("Assets", "0", ("annual_net_margin",)),
    ("RevenueFromContractWithCustomerExcludingAssessedTax", "-1", ("cash_to_assets",)),
    ("CashAndCashEquivalentsAtCarryingValue", "-1", ("annual_net_margin",)),
    ("NetIncomeLoss", "-50", ("annual_net_margin", "cash_to_assets")),
])
def test_invalid_denominators_and_cash_suppress_only_affected_metric(
    concept: str, value: str, expected: tuple[str, ...],
) -> None:
    items = tuple(fact.model_copy(update={"value": Decimal(value)}).to_evidence(ID, cutoff=NOW)
                  if fact.concept == concept else fact.to_evidence(ID, cutoff=NOW)
                  for fact in snapshot().facts)
    metrics = derive_financial_metrics(items, cutoff=NOW)
    assert tuple(metric.name for metric in metrics) == expected
    if concept == "NetIncomeLoss":
        assert metrics[0].value < 0


def test_stale_or_missing_financial_group_has_no_derived_metrics() -> None:
    items = financial_evidence()
    assert derive_financial_metrics(items[:-1], cutoff=NOW) == ()
    assert derive_financial_metrics(items, cutoff=NOW+timedelta(days=600)) == ()


@pytest.mark.parametrize("change", [
    {"available_at": NOW+timedelta(seconds=1)}, {"trust_level": TrustLevel.USER_CONTENT},
    {"content_hash": "forged"}, {"scanner_version": "old"}, {"injection_risk": 0.1},
])
def test_unqualified_catalyst_sources_are_excluded(change: dict[str, object]) -> None:
    current = incoming()
    altered = current.evidence[0].model_copy(update=change)
    assert catalyst_sources(current.model_copy(update={"evidence": (altered,)})) == ()


def test_quote_rejection_and_report_time_suppression() -> None:
    current = incoming()
    output = assessment(current.evidence[0])
    validate_catalysts(output, catalyst_sources(current))
    report = build_research_report(current.model_copy(update={"catalyst_assessment": output}))
    assert report.catalyst_interpretations == output.claims
    assert any(c.evidence_id == output.claims[0].evidence_id for c in report.citations)
    invalid = output.model_copy(update={"claims": (
        output.claims[0].model_copy(update={"supporting_quote": "invented event quotation"}),
    )})
    with pytest.raises(ValueError):
        validate_catalysts(invalid, catalyst_sources(current))
    report = build_research_report(current.model_copy(update={"catalyst_assessment": invalid}))
    assert not report.catalyst_interpretations
    assert "catalyst interpretation attribution is invalid" in report.gaps


@pytest.mark.asyncio
async def test_catalyst_call_is_checkpointed_once_and_completed_output_not_repeated() -> None:
    current = incoming()
    executor = MockExecutor(lambda _: assessment(current.evidence[0]).model_dump())
    saved = []
    async def save(updated: ResearchState) -> None:
        saved.append(updated)
    workflow = ResearchWorkflow(model_gateway=ModelGateway([executor]), save=save,
                                catalysts_enabled=True, provider_order=(ProviderName.MOCK,))
    workflow._run_started = perf_counter()
    result = (await workflow._catalysts({"research": current}))["research"]
    assert result.budget_usage.llm_calls == 3 and executor.call_count == 1
    assert saved[0].runtime_metadata["external_attempts"]["catalysts"]["status"] == "started"
    assert saved[-1].runtime_metadata["external_attempts"]["catalysts"]["status"] == "completed"
    assert result.model_history[-1]["task_kind"] == "news_extraction"
    assert result.catalyst_assessment is not None
    reloaded = ResearchState.model_validate_json(result.model_dump_json())
    assert reloaded.catalyst_assessment == result.catalyst_assessment
    assert reloaded.model_history == result.model_history
    assert (
        reloaded.runtime_metadata["external_attempts"]
        == result.runtime_metadata["external_attempts"]
    )
    await workflow._catalysts({"research": result})
    assert executor.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("disabled,no_budget,no_sources", [(True, False, False),
                                                         (False, True, False),
                                                         (False, False, True)])
async def test_disabled_exhausted_or_empty_extraction_never_calls_model(
    disabled: bool, no_budget: bool, no_sources: bool,
) -> None:
    current = incoming().model_copy(update={
        "evidence": () if no_sources else incoming().evidence,
        "budget_usage": BudgetUsage(llm_calls=3 if no_budget else 2),
    })
    def forbidden(request: object) -> object:
        raise AssertionError("unexpected model call")
    executor = MockExecutor(forbidden)
    async def save(updated: ResearchState) -> None:
        pass
    workflow = ResearchWorkflow(model_gateway=ModelGateway([executor]), save=save,
                                catalysts_enabled=not disabled)
    workflow._run_started = perf_counter()
    result = (await workflow._catalysts({"research": current}))["research"]
    assert executor.call_count == 0 and result.catalyst_assessment is None


@pytest.mark.asyncio
async def test_interrupted_catalyst_call_is_unknown_and_never_reissued() -> None:
    current = incoming().model_copy(update={"runtime_metadata": {"external_attempts": {
        "catalysts": {"status": "started", "request_id": str(uuid4())},
    }}})
    executor = MockExecutor(lambda _: {})
    async def save(updated: ResearchState) -> None:
        pass
    workflow = ResearchWorkflow(model_gateway=ModelGateway([executor]), save=save,
                                catalysts_enabled=True)
    result = await workflow.run(current)
    assert result.status is ResearchStatus.FAILED and executor.call_count == 0
    assert any("unknown" in gap for gap in result.evidence_gaps)


def test_empty_assessment_exposes_limitations_without_fabricating_events() -> None:
    report = build_research_report(incoming().model_copy(update={
        "catalyst_assessment": CatalystAssessment(
            claims=(), limitations=("No useful event was supported by the excerpts.",),
        ),
    }))
    assert report.catalyst_interpretations == ()
    assert report.catalyst_limitations == ("No useful event was supported by the excerpts.",)
    assert not report.complete_analysis


@pytest.mark.asyncio
async def test_optional_extraction_reserves_last_call_for_sufficient_synthesis() -> None:
    from backend.app.contracts.research import ResearchPlan
    from backend.app.graph.evidence_gap import judge_evidence_gaps
    from backend.tests.test_research_workflow import _market_evidence, _plan_payload
    current = incoming()
    collection = await _market_evidence(ID).collect(current)
    current = current.model_copy(update={
        "evidence": (*current.evidence, *collection.evidence),
        "market_snapshot": collection.market_snapshot,
        "technical_snapshot": collection.technical_snapshot,
        "research_plan": ResearchPlan.model_validate(_plan_payload()),
    })
    assert judge_evidence_gaps(current).sufficient
    executor = MockExecutor(lambda _: {})
    async def save(updated: ResearchState) -> None:
        pass
    workflow = ResearchWorkflow(model_gateway=ModelGateway([executor]), save=save,
                                catalysts_enabled=True)
    workflow._run_started = perf_counter()
    result = (await workflow._catalysts({"research": current}))["research"]
    assert executor.call_count == 0
    assert result.catalyst_assessment is None
