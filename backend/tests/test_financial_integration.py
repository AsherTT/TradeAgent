"""Financial acquisition, typed admission, reporting and research safety golden cases."""

import asyncio
import importlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.config import Settings
from backend.app.contracts.evaluation import ReplayIntegrityLevel
from backend.app.contracts.evidence import Evidence, ResearchSynthesis
from backend.app.contracts.instrument import Instrument, SymbolHistory
from backend.app.contracts.research import (
    BudgetUsage,
    ResearchBudget,
    ResearchPlan,
    ResearchState,
    ResearchStatus,
    ResearchTimestampMode,
)
from backend.app.financials.admission import admitted_financial_fact, financial_coverage
from backend.app.financials.current import CurrentFinancialSnapshot
from backend.app.financials.sec import (
    CONCEPTS,
    SecFinancialClient,
    SecFinancialError,
    SecFinancialFact,
    SecFinancialSnapshot,
)
from backend.app.graph.evidence_gap import judge_evidence_gaps, qualified_evidence
from backend.app.graph.synthesis import select_synthesis_evidence, validate_synthesis
from backend.app.graph.workflow import EvidenceCollection, ResearchWorkflow
from backend.app.market_data.instrument import ProviderInstrument
from backend.app.persistence.base import Base
from backend.app.persistence.evidence import EvidenceRepository
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database
from backend.app.reports.research import build_research_report

NOW = datetime(2026, 10, 1, tzinfo=UTC)
ID = uuid4()


def snapshot() -> SecFinancialSnapshot:
    return SecFinancialSnapshot(
        ticker="KLAC",
        cik=319201,
        observed_at=NOW,
        gaps=(),
        facts=tuple(
            SecFinancialFact(
                cik=319201,
                concept=concept,
                value=Decimal(1000),
                period_start=None if concept in CONCEPTS[:2] else date(2025, 7, 1),
                period_end=date(2026, 6, 30),
                filed_on=date(2026, 8, 6),
                form="10-K",
                accession="0000319201-26-000027",
                observed_at=NOW,
            )
            for concept in CONCEPTS
        ),
    )


def financial_evidence() -> tuple[Evidence, ...]:
    return tuple(fact.to_evidence(ID, cutoff=NOW) for fact in snapshot().facts)


def state(**updates: Any) -> ResearchState:
    return ResearchState(
        instrument_id=ID,
        ticker="UNTRUSTED_SUBMITTED_SYMBOL",
        query="Assess KLAC",
        horizon="3 months",
        requested_at=NOW,
        timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
        analysis_timestamp=None,
    ).model_copy(update=updates)


class Resolver:
    async def resolve_instrument(self, instrument_id: UUID, *, at: datetime) -> ProviderInstrument:
        assert instrument_id == ID
        return ProviderInstrument("KLAC", "USD", NOW - timedelta(days=1000))


class Loader:
    requests_made = 0

    async def load_current(self, ticker: str) -> SecFinancialSnapshot:
        assert ticker == "KLAC"
        self.requests_made = 2
        return snapshot()


class Downstream:
    def __init__(self) -> None:
        self.calls = 0
        self.received: ResearchState | None = None

    async def collect(self, incoming: ResearchState) -> EvidenceCollection:
        self.calls += 1
        self.received = incoming
        return EvidenceCollection(
            analysis_timestamp=NOW + timedelta(seconds=1),
            tool_calls=1,
            gaps=("market unqualified",),
        )


@pytest.mark.asyncio
async def test_financials_precede_cutoff_and_use_permanent_resolved_identity() -> None:
    downstream = Downstream()
    result = await CurrentFinancialSnapshot(
        Loader(), downstream, resolver=Resolver(), clock=lambda: NOW
    ).collect(state())
    assert result.tool_calls == 3
    assert len(result.evidence) == 4
    assert downstream.received is not None
    assert downstream.received.budget_usage.tool_calls == 2
    assert result.analysis_timestamp == NOW + timedelta(seconds=1)
    assert all(item.available_at <= result.analysis_timestamp for item in result.evidence)
    assert result.gaps == ("market unqualified",)


@pytest.mark.asyncio
async def test_two_remaining_calls_are_reserved_for_downstream_without_sec() -> None:
    loader = Loader()
    downstream = Downstream()
    result = await CurrentFinancialSnapshot(loader, downstream, resolver=Resolver()).collect(
        state(research_budget=ResearchBudget(max_tool_calls=2))
    )
    assert loader.requests_made == 0
    assert result.tool_calls == 1
    assert result.evidence == ()
    assert "financials skipped: reserve market call" in result.gaps


@pytest.mark.asyncio
async def test_known_sec_failure_charges_only_the_initiated_request() -> None:
    class Failing(Loader):
        async def load_current(self, ticker: str) -> SecFinancialSnapshot:
            self.requests_made = 1
            raise SecFinancialError("controlled failure")

    downstream = Downstream()
    result = await CurrentFinancialSnapshot(Failing(), downstream, resolver=Resolver()).collect(
        state()
    )
    assert result.tool_calls == 2
    assert downstream.received.budget_usage.tool_calls == 1
    assert "current SEC financial acquisition unavailable" in result.gaps


@pytest.mark.asyncio
async def test_exhausted_financial_wall_budget_never_starts_market() -> None:
    class Slow(Loader):
        async def load_current(self, ticker: str) -> SecFinancialSnapshot:
            self.requests_made = 1
            await asyncio.sleep(0.1)
            return snapshot()

    downstream = Downstream()
    result = await CurrentFinancialSnapshot(
        Slow(), downstream, resolver=Resolver(), clock=lambda: NOW
    ).collect(
        state(
            research_budget=ResearchBudget(max_wall_time_seconds=1),
            budget_usage=BudgetUsage(wall_time_seconds=0.99),
        )
    )
    assert downstream.calls == 0
    assert result.tool_calls == 1
    assert result.analysis_timestamp == NOW
    assert "market skipped: financial acquisition exhausted wall time" in result.gaps


@pytest.mark.asyncio
async def test_fixed_cutoff_never_calls_current_financial_loader() -> None:
    class FailIfCalled(Loader):
        async def load_current(self, ticker: str) -> SecFinancialSnapshot:
            raise AssertionError("fixed cutoff cannot fetch current financials")

    result = await CurrentFinancialSnapshot(
        FailIfCalled(), Downstream(), resolver=Resolver()
    ).collect(state(timestamp_mode=ResearchTimestampMode.FIXED_CUTOFF, analysis_timestamp=NOW))
    assert result.tool_calls == 1
    assert result.evidence == ()


@pytest.mark.parametrize(
    "change",
    [
        {"source_uri": "https://evil.invalid/filing"},
        {"content_hash": "forged"},
        {"available_at": NOW - timedelta(days=1)},
        {"content": "forged financial conclusion"},
        {"injection_risk": 0.1},
        {"published_at": NOW - timedelta(days=1)},
        {"observed_at": NOW.replace(tzinfo=None)},
        {"available_at": NOW.replace(tzinfo=None)},
        {"retrieved_at": NOW.replace(tzinfo=None)},
    ],
)
def test_forged_financial_provenance_is_not_admitted(change: dict[str, Any]) -> None:
    item = financial_evidence()[0].model_copy(update=change)
    assert admitted_financial_fact(item, cutoff=NOW) is None
    assert qualified_evidence(state(analysis_timestamp=NOW, evidence=(item,))) == ()
    incoming = state(analysis_timestamp=NOW, evidence=(item,))
    assert not judge_evidence_gaps(incoming).sufficient
    assert build_research_report(incoming).financial_observations == ()


def test_freshness_and_future_cutoff_are_rechecked_at_report_time() -> None:
    item = financial_evidence()[0]
    assert admitted_financial_fact(item, cutoff=NOW) is not None
    assert admitted_financial_fact(item, cutoff=NOW - timedelta(seconds=1)) is None
    assert admitted_financial_fact(item, cutoff=NOW + timedelta(days=600)) is None
    report = build_research_report(
        state(analysis_timestamp=NOW + timedelta(days=600), evidence=(item,))
    )
    assert report.financial_observations == ()
    assert report.citations == ()


def test_all_four_concepts_need_one_period_and_cik_without_satisfying_market() -> None:
    items = financial_evidence()
    assert financial_coverage(items, cutoff=NOW)
    assert not financial_coverage(items[:-1], cutoff=NOW)
    other = snapshot().facts[-1].model_copy(update={"cik": 42}).to_evidence(ID, cutoff=NOW)
    assert not financial_coverage((*items[:-1], other), cutoff=NOW)
    different_period = (
        snapshot()
        .facts[-1]
        .model_copy(update={"period_start": date(2025, 6, 26)})
        .to_evidence(ID, cutoff=NOW)
    )
    assert not financial_coverage((*items[:-1], different_period), cutoff=NOW)
    inconsistent = state(analysis_timestamp=NOW, evidence=(*items[:-1], different_period))
    assert build_research_report(inconsistent).financial_observations == ()
    assert build_research_report(inconsistent).citations == ()
    plan = ResearchPlan(
        question="Assess KLAC",
        instrument_symbol="KLAC",
        horizon="3 months",
        steps=(
            {
                "step_id": "annual",
                "objective": "Annual facts",
                "capability": "financials",
                "required": True,
            },
        ),
        evidence_requirements=("annual financial facts",),
        stop_conditions=("done",),
    )
    incoming = state(analysis_timestamp=NOW, evidence=items, research_plan=plan)
    gap = judge_evidence_gaps(incoming)
    assert gap.missing_capabilities == ("market",)
    assert not gap.sufficient
    assert "financials" in gap.required_capabilities


def test_naive_cutoff_is_rejected_by_admission_gap_and_report() -> None:
    items = financial_evidence()
    cutoff = NOW.replace(tzinfo=None)
    assert admitted_financial_fact(items[0], cutoff=cutoff) is None
    incoming = state(analysis_timestamp=cutoff, evidence=items)
    assert qualified_evidence(incoming) == ()
    assert not judge_evidence_gaps(incoming).sufficient
    assert build_research_report(incoming).financial_observations == ()


@pytest.mark.parametrize("conflict", ["older_same_date", "same_accession", "annual_start"])
def test_conflicts_in_any_revision_suppress_coverage_and_report(conflict: str) -> None:
    items = financial_evidence()
    original = snapshot().facts[-1]
    if conflict == "older_same_date":
        changes = (
            {"filed_on": date(2026, 8, 1), "value": Decimal(50),
             "accession": "0000319201-26-000020"},
            {"filed_on": date(2026, 8, 1), "value": Decimal(60),
             "accession": "0000319201-26-000021"},
        )
    elif conflict == "same_accession":
        changes = ({"filed_on": date(2026, 8, 7), "value": Decimal(60)},)
    else:
        changes = ({"period_start": date(2025, 6, 26)},)
    contradictions = tuple(original.model_copy(update=change).to_evidence(ID, cutoff=NOW)
                           for change in changes)
    for evidence in ((*items, *contradictions), (*contradictions, *items)):
        assert not financial_coverage(evidence, cutoff=NOW)
        report = build_research_report(state(analysis_timestamp=NOW, evidence=evidence))
        assert report.financial_observations == ()
        assert report.citations == ()


def test_synthesis_selects_and_requires_each_financial_concept_citation() -> None:
    items = financial_evidence()
    incoming = state(analysis_timestamp=NOW, evidence=items)
    from backend.app.contracts.evidence import EvidenceGapResult

    incoming = incoming.model_copy(
        update={
            "evidence_gap_result": EvidenceGapResult(
                required_capabilities=("financials",),
                missing_capabilities=(),
                coverage=1,
                sufficient=True,
            )
        }
    )
    selected = select_synthesis_evidence(incoming)
    assert len(selected) == 4
    synthesis = ResearchSynthesis(
        summary="Reported observations",
        bull_case="Limited",
        bear_case="Limited",
        limitations=(),
        confidence=0.4,
        evidence_ids=tuple(item.evidence_id for item in selected),
    )
    validate_synthesis(synthesis, selected, ("financials",))
    with pytest.raises(ValueError, match="annual financial concepts"):
        validate_synthesis(
            synthesis.model_copy(update={"evidence_ids": synthesis.evidence_ids[:1]}),
            selected,
            ("financials",),
        )


def test_report_has_one_numeric_observation_and_citation_per_fact() -> None:
    report = build_research_report(
        state(
            analysis_timestamp=NOW,
            evidence=financial_evidence(),
            status=ResearchStatus.INSUFFICIENT_EVIDENCE,
        )
    )
    assert len(report.financial_observations) == 4
    assert len(report.citations) == 4
    assert report.complete_analysis is False
    sections = [
        section
        for section in report.sections
        if section.title.startswith("Annual financial observation:")
    ]
    assert len(sections) == 4
    assert all(len(section.evidence_ids) == 1 for section in sections)
    assert all("1000 USD" in section.text and "2026-08-06" in section.text for section in sections)


@pytest.mark.asyncio
async def test_completed_empty_acquisition_checkpoint_cannot_reacquire() -> None:
    class Forbidden:
        async def collect(self, incoming: ResearchState) -> EvidenceCollection:
            raise AssertionError("completed acquisition must not be repeated")

    incoming = state(
        analysis_timestamp=NOW,
        status=ResearchStatus.RUNNING,
        runtime_metadata={"external_attempts": {"collect_evidence": {"status": "completed"}}},
    )
    saved = []

    async def save(updated: ResearchState) -> None:
        saved.append(updated)

    workflow = ResearchWorkflow(
        model_gateway=ModelGateway([MockExecutor(lambda _: {})]),
        save=save,
        evidence_provider=Forbidden(),
    )
    result = await workflow._collect_evidence({"research": incoming})
    assert result["research"].evidence == ()
    assert saved == []


def test_financial_worker_configuration_is_default_off_and_requires_contact_and_market() -> None:
    assert Settings(_env_file=None).financials_enabled is False
    with pytest.raises(ValueError, match="SEC User-Agent"):
        Settings(_env_file=None, financials_enabled=True)
    Settings(
        _env_file=None,
        financials_enabled=True,
        market_data_enabled=True,
        sec_user_agent="TradeAgent offline@example.org",
    )


@pytest.mark.asyncio
async def test_failed_shared_limiter_prevents_any_sec_http_request() -> None:
    async def limiter() -> None:
        raise SecFinancialError("SEC shared request limiter unavailable")

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("limiter failure must prevent network requests")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        loader = SecFinancialClient(
            user_agent="TradeAgent offline@example.org", client=client, before_request=limiter
        )
        with pytest.raises(SecFinancialError, match="limiter"):
            await loader.load_current("KLAC")
        assert loader.requests_made == 0


@pytest.mark.asyncio
async def test_financial_checkpoint_persists_reloads_and_never_repeats_on_redelivery(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'financial-checkpoint.db'}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    instrument = Instrument(
        instrument_id=ID,
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA",
    )
    plan = ResearchPlan(
        question="Assess KLAC",
        instrument_symbol="KLAC",
        horizon="3 months",
        steps=(
            {
                "step_id": "annual",
                "objective": "Annual facts",
                "capability": "financials",
                "required": True,
            },
        ),
        evidence_requirements=("annual financial facts",),
        stop_conditions=("done",),
    )
    incoming = state(
        ticker="KLAC", research_plan=plan, research_budget=ResearchBudget(max_llm_calls=0)
    )
    downstream = Downstream()
    try:
        async with database.sessions() as session:
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            await repository.create(incoming)
            await session.commit()

            async def save(updated: ResearchState) -> None:
                await repository.save(updated)
                await session.commit()

            workflow = ResearchWorkflow(
                model_gateway=ModelGateway([MockExecutor(lambda _: {})]),
                save=save,
                evidence_provider=CurrentFinancialSnapshot(
                    Loader(), downstream, resolver=Resolver(), clock=lambda: NOW
                ),
            )
            result = await workflow.run(incoming)
            assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
            assert result.budget_usage.tool_calls == 3
            assert result.budget_usage.llm_calls == 0
        async with database.sessions() as session:
            persisted = await ResearchRunRepository(session).get(incoming.research_id)
            assert persisted is not None
            assert len(persisted.evidence) == 4
            assert len(build_research_report(persisted).financial_observations) == 4
            evidence = await EvidenceRepository(session).list_for_instrument(
                ID, analysis_timestamp=NOW + timedelta(seconds=1)
            )
            assert len(evidence) == 4
            assert (
                await EvidenceRepository(session).list_for_instrument(
                    ID, analysis_timestamp=NOW - timedelta(seconds=1)
                )
                == ()
            )
            await workflow.run(persisted)
            assert downstream.calls == 1
    finally:
        await database.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,enabled,replay,expected_calls",
    [
        (ResearchTimestampMode.CURRENT_RESEARCH, True, False, 2),
        (ResearchTimestampMode.CURRENT_RESEARCH, False, False, 0),
        (ResearchTimestampMode.FIXED_CUTOFF, True, False, 0),
        (ResearchTimestampMode.FIXED_CUTOFF, True, True, 0),
    ],
)
async def test_worker_financial_wiring_is_current_only_and_default_off(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: ResearchTimestampMode,
    enabled: bool,
    replay: bool,
    expected_calls: int,
) -> None:
    worker = importlib.import_module("backend.app.jobs.celery_app")
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'financial-worker.db'}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    instrument = Instrument(
        instrument_id=ID,
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA",
    )
    plan = ResearchPlan(
        question="Assess KLAC",
        instrument_symbol="KLAC",
        horizon="3 months",
        steps=(
            {
                "step_id": "annual",
                "objective": "Annual facts",
                "capability": "financials",
                "required": True,
            },
        ),
        evidence_requirements=("annual financial facts",),
        stop_conditions=("done",),
    )
    incoming = state(
        ticker="KLAC",
        research_plan=plan,
        timestamp_mode=mode,
        analysis_timestamp=NOW if mode is ResearchTimestampMode.FIXED_CUTOFF else None,
        replay_integrity_level=(
            ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY
            if replay
            else ReplayIntegrityLevel.RESEARCH_REPLAY
        ),
        parametric_lookahead_risk=replay,
        research_budget=ResearchBudget(max_llm_calls=0),
    )

    class FinancialLoader(Loader):
        def __init__(self, **kwargs: Any) -> None:
            assert kwargs["user_agent"] == "TradeAgent offline@example.org"
            assert callable(kwargs["before_request"])
            captures.append(self)

    class Market:
        async def collect(self, item: ResearchState) -> EvidenceCollection:
            return EvidenceCollection(
                analysis_timestamp=item.analysis_timestamp or NOW + timedelta(seconds=1),
                tool_calls=1,
            )

    captures: list[FinancialLoader] = []
    settings = Settings(
        _env_file=None,
        financials_enabled=enabled,
        market_data_enabled=True,
        sec_user_agent="TradeAgent offline@example.org",
    )
    monkeypatch.setattr(worker, "get_database", lambda: database)
    monkeypatch.setattr(worker, "get_settings", lambda: settings)
    monkeypatch.setattr(worker, "build_market_data_loader", lambda *args, **kwargs: object())
    monkeypatch.setattr(worker, "MarketResearchEvidence", lambda *args, **kwargs: Market())
    monkeypatch.setattr(worker, "SecFinancialClient", FinancialLoader)
    monkeypatch.setattr(
        worker, "build_model_gateway", lambda *args: ModelGateway([MockExecutor(lambda _: {})])
    )
    try:
        async with database.sessions() as session, session.begin():
            master = SecurityMasterRepository(session)
            await master.add_instrument(instrument)
            await master.add_symbol_history(
                SymbolHistory(
                    instrument_id=ID,
                    symbol="KLAC",
                    exchange="NASDAQ",
                    valid_from=datetime(2020, 1, 1, tzinfo=UTC),
                    available_at=datetime(2020, 1, 1, tzinfo=UTC),
                )
            )
            await ResearchRunRepository(session).create(incoming)
        result = await worker.execute_research_run(incoming.research_id)
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert sum(loader.requests_made for loader in captures) == expected_calls
        assert len(result.evidence) == (4 if expected_calls else 0)
        assert result.budget_usage.llm_calls == 0
    finally:
        await database.dispose()
