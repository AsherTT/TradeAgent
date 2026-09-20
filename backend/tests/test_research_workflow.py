import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

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
)
from backend.app.graph import MarketResearchEvidence, ResearchWorkflow
from backend.app.market_data.providers import (
    InMemoryCorporateActionProvider,
    InMemoryMarketDataProvider,
)
from backend.app.market_data.service import MarketDataService

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


def _market_evidence(
    instrument_id: UUID, *, include_bars: bool = True
) -> MarketResearchEvidence:
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
            observed_at=NOW - timedelta(days=day),
            available_at=NOW - timedelta(days=day),
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
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=bars, quality_report=report),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=report
        ),
    )
    return MarketResearchEvidence(service, currency="USD")


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

        async def save(_: ResearchState) -> None:
            return None

        result = await ResearchWorkflow(
            model_gateway=ModelGateway([executor]),
            provider_order=(ProviderName.MOCK,),
            save=save,
        ).run(_state(uuid4()))
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_completion is ResearchCompletion.INSUFFICIENT_EVIDENCE
        assert result.quality_assessment is not None
        assert result.quality_assessment.evidence_coverage == 0

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
        assert any("visible market bar" in gap for gap in result.evidence_gaps)

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

    asyncio.run(scenario())
