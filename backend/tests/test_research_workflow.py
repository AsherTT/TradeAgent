import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.contracts.evaluation import (
    DataQualityStatus,
    ProviderQualityReport,
    ResearchCompletion,
)
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar
from backend.app.contracts.model import ProviderName
from backend.app.contracts.research import (
    BudgetUsage,
    ResearchBudget,
    ResearchPlan,
    ResearchState,
    ResearchStatus,
    ResearchTimestampMode,
)
from backend.app.graph import (
    MarketResearchEvidence,
    ResearchWorkflow,
    failed_research_state,
)
from backend.app.graph.workflow import EvidenceCollection
from backend.app.market_data.errors import (
    MarketDataIntegrityError,
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.providers import (
    InMemoryCorporateActionProvider,
    InMemoryMarketDataProvider,
)
from backend.app.market_data.quality import ProviderQualityError
from backend.app.market_data.service import (
    CurrentMarketDataRequest,
    CurrentMarketDataResult,
    MarketDataRequest,
    MarketDataService,
    ProviderAttempt,
    ProviderAttemptOutcome,
)

NOW = datetime(2026, 9, 18, 8, tzinfo=UTC)


def _plan_payload() -> dict[str, Any]:
    return {
        "question": "Assess the setup",
        "instrument_symbol": "ACME",
        "horizon": "3-5 days",
        "steps": (
            {
                "step_id": "market_snapshot",
                "objective": "Use qualified point-in-time market evidence",
                "capability": "market",
            },
        ),
        "stop_conditions": ("required evidence collected",),
        "evidence_requirements": ("point-in-time market data",),
    }


def _state(instrument_id: UUID, *, budget: ResearchBudget | None = None) -> ResearchState:
    return ResearchState(
        instrument_id=instrument_id,
        ticker="ACME",
        query="Assess the setup",
        horizon="3-5 days",
        analysis_timestamp=NOW,
        parametric_lookahead_risk=True,
        research_budget=budget or ResearchBudget(),
    )


def _market_service(
    instrument_id: UUID,
    *,
    include_bars: bool = True,
    observation_delay: timedelta = timedelta(),
) -> MarketDataService:
    bars = tuple(
        MarketBar(
            instrument_id=instrument_id,
            symbol="ACME",
            timestamp=NOW - timedelta(days=day),
            open=100 + day,
            high=100 + day,
            low=100 + day,
            close=100 + day,
            volume=1000,
            adjustment_mode=PriceAdjustmentMode.RAW,
            adjustment_factor=1,
            source="fixture",
            observed_at=(
                NOW + observation_delay
                if observation_delay
                else NOW - timedelta(days=day)
            ),
            available_at=(
                NOW + observation_delay
                if observation_delay
                else NOW - timedelta(days=day)
            ),
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="fixture-v1",
        )
        for day in range(20, 0, -1)
    ) if include_bars else ()
    report = ProviderQualityReport(
        provider="fixture",
        provider_version="fixture-v1",
        evaluated_at=NOW,
        golden_case_count=1,
        passed_case_count=1,
        coverage=1,
        quality_status=DataQualityStatus.VERIFIED,
    )
    return MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=bars, quality_report=report),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=report
        ),
    )


def _market_evidence(
    instrument_id: UUID, *, include_bars: bool = True
) -> MarketResearchEvidence:
    return MarketResearchEvidence(
        _market_service(instrument_id, include_bars=include_bars), currency="USD"
    )


def test_offline_graph_persists_each_transition_and_completes() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        saved: list[ResearchState] = []
        executor = MockExecutor(lambda _: _plan_payload())

        async def save(state: ResearchState) -> None:
            saved.append(state)

        workflow = ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            evidence_provider=_market_evidence(instrument_id),
            provider_order=(ProviderName.MOCK,),
            save=save,
        )
        result = await workflow.run(_state(instrument_id))

        assert result.status is ResearchStatus.COMPLETE
        assert result.research_completion is ResearchCompletion.COMPLETE
        assert result.research_plan is not None
        assert result.market_snapshot is not None
        assert result.technical_snapshot is not None
        assert len(result.evidence) == 1
        assert result.budget_usage.iterations == 1
        assert result.budget_usage.llm_calls == 1
        assert result.budget_usage.tool_calls == 1
        assert [item.status for item in saved] == [
            ResearchStatus.RUNNING,
            ResearchStatus.RUNNING,
            ResearchStatus.RUNNING,
            ResearchStatus.RUNNING,
            ResearchStatus.RUNNING,
            ResearchStatus.COMPLETE,
        ]
        assert result.runtime_metadata["transitions"] == (
            "start",
            "plan_started",
            "plan",
            "evidence_started",
            "collect_evidence",
            "finish",
        )

    asyncio.run(scenario())


def test_graph_without_qualified_evidence_finishes_insufficient() -> None:
    async def scenario() -> None:
        executor = MockExecutor(lambda _: _plan_payload())

        saved: list[ResearchState] = []

        async def save(state: ResearchState) -> None:
            saved.append(state)

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(_state(uuid4()))
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_completion is ResearchCompletion.INSUFFICIENT_EVIDENCE
        assert result.quality_assessment is not None
        assert result.quality_assessment.evidence_coverage == 0
        attempt = result.runtime_metadata["external_attempts"]["plan"]
        assert attempt["status"] == "completed"
        assert attempt["outcome_known"] is True
        assert attempt["retry_eligible"] is False
        assert attempt["started_at"] and attempt["finished_at"]

    asyncio.run(scenario())


def test_queue_delayed_observation_after_analysis_cutoff_finishes_insufficient() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        executor = MockExecutor(lambda _: _plan_payload())

        async def save(_: ResearchState) -> None:
            return None

        evidence_provider = MarketResearchEvidence(
            _market_service(
                instrument_id,
                observation_delay=timedelta(minutes=2),
            ),
            currency="USD",
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            evidence_provider=evidence_provider,
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(_state(instrument_id))

        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_completion is ResearchCompletion.INSUFFICIENT_EVIDENCE
        assert result.market_snapshot is None
        assert result.evidence == ()
        assert result.quality_assessment is not None
        assert result.quality_assessment.evidence_coverage == 0
        assert "qualified point-in-time evidence" in result.evidence_gaps

    asyncio.run(scenario())


def test_current_research_freezes_cutoff_after_queue_delayed_acquisition() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        observed_at = NOW + timedelta(minutes=2)
        frozen_cutoff = observed_at + timedelta(seconds=1)
        bars = tuple(
            MarketBar(
                instrument_id=instrument_id,
                symbol="ACME",
                timestamp=NOW - timedelta(days=day),
                open=100 + day,
                high=100 + day,
                low=100 + day,
                close=100 + day,
                volume=1000,
                adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
                adjustment_factor=1,
                source="current-fixture",
                observed_at=observed_at,
                available_at=observed_at,
                data_quality_status=DataQualityStatus.VERIFIED,
                provider_quality_version="current-fixture-v1",
            )
            for day in range(20, 0, -1)
        )

        class CurrentLoader:
            async def load_current_bars(
                self, request: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                assert request.requested_at == NOW
                return CurrentMarketDataResult(bars=bars)

        saved: list[ResearchState] = []

        async def save(state: ResearchState) -> None:
            saved.append(state)

        planning_context: dict[str, Any] = {}

        def plan(request: Any) -> dict[str, Any]:
            planning_context.update(request.context)
            return _plan_payload()

        state = ResearchState(
            instrument_id=instrument_id,
            ticker="ACME",
            query="Assess the setup",
            horizon="3-5 days",
            requested_at=NOW,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            parametric_lookahead_risk=True,
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(plan)]),
            evidence_provider=MarketResearchEvidence(
                CurrentLoader(), currency="USD", clock=lambda: frozen_cutoff
            ),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(state)

        assert result.status is ResearchStatus.COMPLETE
        assert result.analysis_timestamp == frozen_cutoff
        assert result.market_snapshot is not None
        assert result.market_snapshot.analysis_timestamp == frozen_cutoff
        assert result.evidence[0].available_at == observed_at
        assert planning_context["timestamp_mode"] == "current_research"
        assert planning_context["analysis_timestamp"] == "pending_evidence_acquisition"

        persisted_after_acquisition = next(
            item for item in saved if item.evidence and item.status is ResearchStatus.RUNNING
        )

        class MustNotRepeatEvidence:
            async def collect(self, _: ResearchState) -> EvidenceCollection:
                raise AssertionError("persisted current evidence must not be reacquired")

        resumed = await ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=MustNotRepeatEvidence(),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(persisted_after_acquisition)
        assert resumed.status is ResearchStatus.COMPLETE
        assert resumed.analysis_timestamp == frozen_cutoff

    asyncio.run(scenario())


def test_fixed_cutoff_cannot_be_replaced_by_an_evidence_adapter() -> None:
    async def scenario() -> None:
        class InvalidEvidenceProvider:
            async def collect(self, _: ResearchState) -> EvidenceCollection:
                return EvidenceCollection(analysis_timestamp=NOW + timedelta(minutes=1))

        async def save(_: ResearchState) -> None:
            return None

        workflow = ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=InvalidEvidenceProvider(),
            provider_order=(ProviderName.MOCK,),
            save=save,
        )
        with pytest.raises(ValueError, match="fixed analysis_timestamp is immutable"):
            await workflow.run(_state(uuid4()))

    asyncio.run(scenario())


def test_workflow_rejects_evidence_available_after_the_frozen_cutoff() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        valid = await _market_evidence(instrument_id).collect(_state(instrument_id))
        late = valid.evidence[0].model_copy(
            update={
                "observed_at": NOW + timedelta(seconds=1),
                "available_at": NOW + timedelta(seconds=1),
            }
        )

        class InvalidEvidenceProvider:
            async def collect(self, _: ResearchState) -> EvidenceCollection:
                return EvidenceCollection(
                    analysis_timestamp=NOW,
                    market_snapshot=valid.market_snapshot,
                    technical_snapshot=valid.technical_snapshot,
                    evidence=(late,),
                )

        async def save(_: ResearchState) -> None:
            return None

        workflow = ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=InvalidEvidenceProvider(),
            provider_order=(ProviderName.MOCK,),
            save=save,
        )
        with pytest.raises(ValueError, match="evidence exceeds analysis_timestamp"):
            await workflow.run(_state(instrument_id))

    asyncio.run(scenario())


def test_current_research_rejects_a_cutoff_before_the_request() -> None:
    async def scenario() -> None:
        class InvalidCurrentLoader:
            async def load_current_bars(
                self, _: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                return CurrentMarketDataResult(bars=())

        state = ResearchState(
            instrument_id=uuid4(),
            ticker="ACME",
            query="Assess the setup",
            horizon="3-5 days",
            requested_at=NOW,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            parametric_lookahead_risk=True,
        )
        with pytest.raises(ValueError, match="earlier than requested_at"):
            await MarketResearchEvidence(
                InvalidCurrentLoader(),
                currency="USD",
                clock=lambda: NOW - timedelta(seconds=1),
            ).collect(state)

    asyncio.run(scenario())


def test_current_research_rejects_an_observation_after_acquisition_completion() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        bar = MarketBar(
            instrument_id=instrument_id,
            symbol="ACME",
            timestamp=NOW - timedelta(days=1),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1000,
            adjustment_mode=PriceAdjustmentMode.RAW,
            adjustment_factor=1,
            source="invalid-current-fixture",
            observed_at=NOW + timedelta(seconds=1),
            available_at=NOW - timedelta(days=1),
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="invalid-current-fixture-v1",
        )

        class InvalidCurrentLoader:
            async def load_current_bars(
                self, _: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                return CurrentMarketDataResult(bars=(bar,))

        state = ResearchState(
            instrument_id=instrument_id,
            ticker="ACME",
            query="Assess the setup",
            horizon="3-5 days",
            requested_at=NOW,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            parametric_lookahead_risk=True,
        )
        with pytest.raises(ValueError, match="eligible at the frozen cutoff"):
            await MarketResearchEvidence(
                InvalidCurrentLoader(), currency="USD", clock=lambda: NOW
            ).collect(state)

    asyncio.run(scenario())


def test_current_research_cannot_complete_with_evidence_but_no_cutoff() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()

        class InvalidEvidenceProvider:
            async def collect(self, state: ResearchState) -> EvidenceCollection:
                fixed_state = state.model_copy(
                    update={
                        "timestamp_mode": ResearchTimestampMode.FIXED_CUTOFF,
                        "analysis_timestamp": NOW,
                    }
                )
                collection = await _market_evidence(instrument_id).collect(fixed_state)
                return EvidenceCollection(
                    market_snapshot=collection.market_snapshot,
                    technical_snapshot=collection.technical_snapshot,
                    evidence=collection.evidence,
                )

        async def save(_: ResearchState) -> None:
            return None

        state = ResearchState(
            instrument_id=instrument_id,
            ticker="ACME",
            query="Assess the setup",
            horizon="3-5 days",
            requested_at=NOW,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            parametric_lookahead_risk=True,
        )
        workflow = ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=InvalidEvidenceProvider(),
            provider_order=(ProviderName.MOCK,),
            save=save,
        )
        with pytest.raises(
            ValueError, match="current-research evidence requires a frozen"
        ):
            await workflow.run(state)

    asyncio.run(scenario())


def test_interrupted_current_acquisition_is_not_repeated() -> None:
    async def scenario() -> None:
        calls = 0

        class CurrentLoader:
            async def load_current_bars(
                self, _: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                nonlocal calls
                calls += 1
                return CurrentMarketDataResult(bars=())

        async def save(_: ResearchState) -> None:
            return None

        interrupted = ResearchState(
            instrument_id=uuid4(),
            ticker="ACME",
            query="Assess the setup",
            horizon="3-5 days",
            requested_at=NOW,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            research_plan=ResearchPlan.model_validate(_plan_payload()),
            runtime_metadata={
                "external_attempts": {
                    "collect_evidence": {"status": "started", "request_id": None}
                }
            },
            status=ResearchStatus.RUNNING,
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=MarketResearchEvidence(CurrentLoader(), currency="USD"),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(interrupted)

        assert result.status is ResearchStatus.FAILED
        assert result.analysis_timestamp is None
        assert calls == 0

    asyncio.run(scenario())


def test_market_evidence_persists_the_ordered_provider_attempt_record() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        service = _market_service(instrument_id)

        class TracedLoader:
            @property
            def last_attempts(self) -> tuple[ProviderAttempt, ...]:
                return (
                    ProviderAttempt(
                        provider="alpha_vantage",
                        outcome=ProviderAttemptOutcome.OPERATIONAL_FAILURE,
                        reason="quota_exhausted",
                    ),
                    ProviderAttempt(
                        provider="yfinance",
                        outcome=ProviderAttemptOutcome.SELECTED,
                    ),
                )

            async def load_bars(
                self, request: MarketDataRequest
            ) -> tuple[MarketBar, ...]:
                return await service.load_bars(request)

        collection = await MarketResearchEvidence(
            TracedLoader(), currency="USD"
        ).collect(_state(instrument_id))

        attempts = collection.evidence[0].structured_data["provider_attempts"]
        assert attempts == [
            {
                "provider": "alpha_vantage",
                "outcome": "operational_failure",
                "reason": "quota_exhausted",
            },
            {"provider": "yfinance", "outcome": "selected", "reason": None},
        ]
        assert "alpha_vantage:operational_failure" in collection.evidence[0].content
        assert "yfinance:selected" in collection.evidence[0].content

    asyncio.run(scenario())


def test_graph_stops_before_model_when_llm_budget_is_zero() -> None:
    async def scenario() -> None:
        executor = MockExecutor(lambda _: _plan_payload())

        async def save(_: ResearchState) -> None:
            return None

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(_state(uuid4(), budget=ResearchBudget(max_llm_calls=0)))
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_completion is ResearchCompletion.BUDGET_EXHAUSTED
        assert executor.call_count == 0

    asyncio.run(scenario())


def test_terminal_run_is_idempotent() -> None:
    async def scenario() -> None:
        terminal = _state(uuid4()).model_copy(update={"status": ResearchStatus.FAILED})
        executor = MockExecutor(lambda _: _plan_payload())
        saves = 0

        async def save(_: ResearchState) -> None:
            nonlocal saves
            saves += 1

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(terminal)
        assert result is terminal
        assert saves == 0
        assert executor.call_count == 0

    asyncio.run(scenario())


def test_graph_honors_iteration_and_tool_limits_and_resumes_planned_run() -> None:
    async def scenario() -> None:
        executor = MockExecutor(lambda _: _plan_payload())

        async def save(_: ResearchState) -> None:
            return None

        iteration_limited = _state(uuid4()).model_copy(
            update={"budget_usage": BudgetUsage(iterations=4)}
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(iteration_limited)
        assert result.research_completion is ResearchCompletion.BUDGET_EXHAUSTED

        instrument_id = uuid4()
        planned = _state(
            instrument_id, budget=ResearchBudget(max_tool_calls=0)
        ).model_copy(
            update={
                "status": ResearchStatus.RUNNING,
                "research_plan": ResearchPlan.model_validate(_plan_payload()),
            }
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            evidence_provider=_market_evidence(instrument_id),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(planned)
        assert result.research_completion is ResearchCompletion.BUDGET_EXHAUSTED
        assert executor.call_count == 0

    asyncio.run(scenario())


def test_unavailable_market_evidence_is_insufficient_not_failed() -> None:
    async def scenario() -> None:
        executor = MockExecutor(lambda _: _plan_payload())

        async def save(_: ResearchState) -> None:
            return None

        instrument_id = uuid4()
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            evidence_provider=_market_evidence(instrument_id, include_bars=False),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(_state(instrument_id))
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_completion is ResearchCompletion.INSUFFICIENT_EVIDENCE
        assert any("IndicatorError" in gap for gap in result.evidence_gaps)

    asyncio.run(scenario())


def test_current_provider_failure_persists_attempt_in_terminal_gap() -> None:
    async def scenario() -> None:
        class UnavailableCurrentLoader:
            @property
            def last_attempts(self) -> tuple[ProviderAttempt, ...]:
                return (
                    ProviderAttempt(
                        provider="yfinance",
                        outcome=ProviderAttemptOutcome.TERMINAL_OPERATIONAL_FAILURE,
                        reason=OperationalFailureReason.RATE_LIMITED.value,
                    ),
                )

            async def load_current_bars(
                self, request: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                raise MarketDataOperationalError(
                    "rate limited",
                    reason=OperationalFailureReason.RATE_LIMITED,
                )

        async def save(_: ResearchState) -> None:
            return None

        instrument_id = uuid4()
        state = ResearchState(
            instrument_id=instrument_id,
            ticker="ACME",
            query="Assess the current setup",
            requested_at=NOW - timedelta(hours=1),
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            horizon="3-5 days",
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=MarketResearchEvidence(
                UnavailableCurrentLoader(), currency="USD", clock=lambda: NOW
            ),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(state)

        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert any(
            "yfinance:terminal_operational_failure(rate_limited)" in gap
            for gap in result.evidence_gaps
        )

    asyncio.run(scenario())


def test_current_integrity_failure_persists_attempt_in_failed_state() -> None:
    async def scenario() -> None:
        class InvalidCurrentLoader:
            @property
            def last_attempts(self) -> tuple[ProviderAttempt, ...]:
                return (
                    ProviderAttempt(
                        provider="yfinance",
                        outcome=ProviderAttemptOutcome.INTEGRITY_FAILURE,
                        reason="YFinanceProviderError",
                    ),
                )

            async def load_current_bars(
                self, request: CurrentMarketDataRequest
            ) -> CurrentMarketDataResult:
                raise MarketDataIntegrityError("history response is malformed")

        saved: list[ResearchState] = []

        async def save(state: ResearchState) -> None:
            saved.append(state)

        instrument_id = uuid4()
        state = ResearchState(
            instrument_id=instrument_id,
            ticker="ACME",
            query="Assess the current setup",
            requested_at=NOW - timedelta(hours=1),
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            horizon="3-5 days",
        )
        workflow = ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=MarketResearchEvidence(
                InvalidCurrentLoader(), currency="USD", clock=lambda: NOW
            ),
            provider_order=(ProviderName.MOCK,),
            save=save,
        )

        with pytest.raises(MarketDataIntegrityError) as exc_info:
            await workflow.run(state)
        terminal = failed_research_state(saved[-1], exc_info.value)

        assert terminal.status is ResearchStatus.FAILED
        assert any(
            "yfinance:integrity_failure(YFinanceProviderError)" in gap
            for gap in terminal.evidence_gaps
        )

    asyncio.run(scenario())


def test_interrupted_external_attempt_is_not_repeated() -> None:
    async def scenario() -> None:
        executor = MockExecutor(lambda _: _plan_payload())
        interrupted = _state(uuid4()).model_copy(
            update={
                "status": ResearchStatus.RUNNING,
                "runtime_metadata": {
                    "external_attempts": {
                        "plan": {"status": "started", "request_id": str(uuid4())}
                    }
                },
            }
        )

        async def save(_: ResearchState) -> None:
            return None

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(interrupted)
        assert result.status is ResearchStatus.FAILED
        assert executor.call_count == 0
        assert result.quality_assessment is not None
        assert "outcome is unknown" in result.quality_assessment.reasons[0]
        attempt = result.runtime_metadata["external_attempts"]["plan"]
        assert attempt["status"] == "unknown_outcome"
        assert attempt["outcome_known"] is False
        assert attempt["retry_eligible"] is False

    asyncio.run(scenario())


def test_interrupted_evidence_attempt_is_not_repeated() -> None:
    async def scenario() -> None:
        instrument_id = uuid4()
        executor = MockExecutor(lambda _: _plan_payload())
        interrupted = _state(instrument_id).model_copy(
            update={
                "status": ResearchStatus.RUNNING,
                "research_plan": ResearchPlan.model_validate(_plan_payload()),
                "runtime_metadata": {
                    "external_attempts": {
                        "collect_evidence": {"status": "started", "request_id": None}
                    }
                },
            }
        )

        async def save(_: ResearchState) -> None:
            return None

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            evidence_provider=_market_evidence(instrument_id),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(interrupted)
        assert result.status is ResearchStatus.FAILED
        assert result.market_snapshot is None
        assert executor.call_count == 0
        assert (
            result.runtime_metadata["external_attempts"]["collect_evidence"]["status"]
            == "unknown_outcome"
        )

    asyncio.run(scenario())


def test_known_external_failure_records_only_bounded_safe_metadata() -> None:
    started = _state(uuid4()).model_copy(
        update={
            "status": ResearchStatus.RUNNING,
            "runtime_metadata": {
                "external_attempts": {
                    "plan": {"status": "started", "request_id": str(uuid4())}
                }
            },
        }
    )
    secret = "https://provider.invalid/path?api_key=do-not-store"
    failed = failed_research_state(started, RuntimeError(secret))
    attempt = failed.runtime_metadata["external_attempts"]["plan"]
    assert attempt["status"] == "known_failure"
    assert attempt["outcome_known"] is True
    assert attempt["retry_eligible"] is False
    assert attempt["failure_type"] == "RuntimeError"
    assert secret not in failed.model_dump_json()
    forged = failed_research_state(
        started, MarketDataIntegrityError(f"provider_attempts={secret}")
    )
    assert secret not in forged.model_dump_json()


def test_market_evidence_gap_excludes_credential_bearing_provider_identifier() -> None:
    async def scenario() -> None:
        secret = "https://user:password@provider.invalid/history?api_key=do-not-store"

        class LeakingLoader:
            async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
                raise ProviderQualityError(f"provider {secret} is not qualified")

        async def save(_: ResearchState) -> None:
            return None

        instrument_id = uuid4()
        state = _state(instrument_id).model_copy(
            update={"research_plan": ResearchPlan.model_validate(_plan_payload())}
        )
        result = await ResearchWorkflow(
            model_gateway=ModelGateway([MockExecutor(lambda _: _plan_payload())]),
            evidence_provider=MarketResearchEvidence(LeakingLoader(), currency="USD"),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(state)
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert "ProviderQualityError" in result.evidence_gaps[0]
        assert secret not in result.model_dump_json()

    asyncio.run(scenario())


def test_successful_evidence_redacts_provider_attempt_identifiers() -> None:
    async def scenario() -> None:
        secret = "https://user:password@provider.invalid/history?api_key=do-not-store"
        instrument_id = uuid4()
        underlying = _market_service(instrument_id)

        class LeakingAttempts:
            @property
            def last_attempts(self) -> tuple[ProviderAttempt, ...]:
                return (
                    ProviderAttempt(
                        provider=secret,
                        outcome=ProviderAttemptOutcome.INTEGRITY_FAILURE,
                        reason=secret,
                    ),
                )

            async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
                return await underlying.load_bars(request)

        collection = await MarketResearchEvidence(
            LeakingAttempts(), currency="USD"
        ).collect(_state(instrument_id))
        assert collection.evidence
        assert secret not in collection.evidence[0].model_dump_json()
        assert collection.evidence[0].structured_data["provider_attempts"] == [
            {
                "provider": "redacted",
                "outcome": "integrity_failure",
                "reason": "redacted",
            }
        ]

    asyncio.run(scenario())


def test_credential_bearing_market_source_is_rejected_before_persistence() -> None:
    async def scenario() -> None:
        secret = "https://provider.invalid/history?api_key=do-not-store"
        instrument_id = uuid4()
        underlying = _market_service(instrument_id)

        class LeakingSource:
            async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
                bars = await underlying.load_bars(request)
                return tuple(bar.model_copy(update={"source": secret}) for bar in bars)

        with pytest.raises(MarketDataIntegrityError) as caught:
            await MarketResearchEvidence(
                LeakingSource(), currency="USD"
            ).collect(_state(instrument_id))
        assert secret not in str(caught.value)

    asyncio.run(scenario())
