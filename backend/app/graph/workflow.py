"""Bounded Phase 5 research workflow composed over qualified application seams."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from hashlib import sha256
from time import perf_counter
from typing import Any, Protocol, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from backend.app.ai.gateway import ModelGateway
from backend.app.contracts.base import utc_now
from backend.app.contracts.evaluation import (
    QualityAssessment,
    QualityGateDecision,
    ResearchCompletion,
    SystemConfidence,
)
from backend.app.contracts.evidence import Evidence, TrustLevel
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketSnapshot, TechnicalSnapshot
from backend.app.contracts.model import ModelRequest, ProviderName, TaskKind
from backend.app.contracts.research import ResearchPlan, ResearchState, ResearchStatus
from backend.app.graph.budget_guard import BudgetGuard
from backend.app.market_data.normalization import PriceNormalizationError
from backend.app.market_data.quality import ProviderQualityError
from backend.app.market_data.service import MarketDataRequest, MarketDataService
from backend.app.quant.indicators import IndicatorError, calculate_technical_snapshot

StateSaver = Callable[[ResearchState], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class EvidenceCollection:
    market_snapshot: MarketSnapshot | None = None
    technical_snapshot: TechnicalSnapshot | None = None
    evidence: tuple[Evidence, ...] = ()
    gaps: tuple[str, ...] = ()


class ResearchNode(StrEnum):
    START = "start"
    PLAN = "plan"
    PLAN_STARTED = "plan_started"
    COLLECT_EVIDENCE = "collect_evidence"
    EVIDENCE_STARTED = "evidence_started"
    FINISH = "finish"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FAILED = "failed"


class BudgetDimension(StrEnum):
    ITERATIONS = "iterations"
    TOOL_CALLS = "tool_calls"
    LLM_CALLS = "llm_calls"
    WALL_TIME_SECONDS = "wall_time_seconds"
    CONTEXT_TOKENS = "context_tokens"
    ESTIMATED_COST_USD = "estimated_cost_usd"


class ResearchEvidence(Protocol):
    """Provider-neutral evidence boundary consumed by the graph."""

    async def collect(
        self, state: ResearchState
    ) -> EvidenceCollection: ...


class MarketResearchEvidence:
    """Adapt qualified market data and deterministic indicators into graph evidence."""

    def __init__(
        self,
        service: MarketDataService,
        *,
        currency: str,
        lookback_days: int = 60,
    ) -> None:
        self._service = service
        self._currency = currency
        self._lookback_days = lookback_days

    async def collect(
        self, state: ResearchState
    ) -> EvidenceCollection:
        try:
            bars = await self._service.load_bars(
                MarketDataRequest(
                    instrument_id=state.instrument_id,
                    start=state.analysis_timestamp - timedelta(days=self._lookback_days),
                    end=state.analysis_timestamp,
                    analysis_timestamp=state.analysis_timestamp,
                    adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
                )
            )
            technical = calculate_technical_snapshot(
                bars, analysis_timestamp=state.analysis_timestamp
            )
        except (IndicatorError, PriceNormalizationError, ProviderQualityError) as exc:
            return EvidenceCollection(gaps=(str(exc),))
        latest = max(bars, key=lambda bar: bar.timestamp)
        market = MarketSnapshot(
            instrument_id=state.instrument_id,
            analysis_timestamp=state.analysis_timestamp,
            latest_bar=latest,
            currency=self._currency,
        )
        content = (
            f"Point-in-time market snapshot for instrument {state.instrument_id}: "
            f"close={latest.close}; indicators={technical.indicators}"
        )
        evidence = Evidence(
            instrument_id=state.instrument_id,
            evidence_type="market_technical_snapshot",
            source_name=latest.source,
            observed_at=latest.observed_at,
            retrieved_at=utc_now(),
            available_at=latest.available_at,
            content=content,
            structured_data={
                "market_snapshot": market.model_dump(mode="json"),
                "technical_snapshot": technical.model_dump(mode="json"),
            },
            confidence=1.0,
            freshness=1.0,
            trust_level=TrustLevel.TRUSTED_PROVIDER,
            source_type="market_data_provider",
            content_hash=sha256(content.encode()).hexdigest(),
            sanitization_status="deterministic_structured_data",
            injection_risk=0.0,
        )
        return EvidenceCollection(
            market_snapshot=market,
            technical_snapshot=technical,
            evidence=(evidence,),
        )


class _GraphState(TypedDict):
    research: ResearchState


class ResearchWorkflow:
    """A small resumable graph that persists each externally visible transition."""

    def __init__(
        self,
        *,
        model_gateway: ModelGateway,
        save: StateSaver,
        evidence_provider: ResearchEvidence | None = None,
        provider_order: tuple[ProviderName, ...] | None = None,
    ) -> None:
        self._gateway = model_gateway
        self._save = save
        self._evidence_provider = evidence_provider
        self._provider_order = provider_order
        self._run_started = 0.0
        self._initial_wall_time = 0.0
        graph = StateGraph(_GraphState)
        graph.add_node(ResearchNode.START, cast(Any, self._start))
        graph.add_node(ResearchNode.PLAN, cast(Any, self._plan))
        graph.add_node(ResearchNode.COLLECT_EVIDENCE, cast(Any, self._collect_evidence))
        graph.add_node(ResearchNode.FINISH, cast(Any, self._finish))
        graph.add_edge(START, ResearchNode.START)
        graph.add_edge(ResearchNode.START, ResearchNode.PLAN)
        graph.add_edge(ResearchNode.PLAN, ResearchNode.COLLECT_EVIDENCE)
        graph.add_edge(ResearchNode.COLLECT_EVIDENCE, ResearchNode.FINISH)
        graph.add_edge(ResearchNode.FINISH, END)
        self._graph = graph.compile()

    async def run(self, state: ResearchState) -> ResearchState:
        if state.status in {
            ResearchStatus.COMPLETE,
            ResearchStatus.INSUFFICIENT_EVIDENCE,
            ResearchStatus.FAILED,
        }:
            return state
        self._run_started = perf_counter()
        self._initial_wall_time = state.budget_usage.wall_time_seconds
        result = cast(_GraphState, await self._graph.ainvoke({"research": state}))
        return result["research"]

    async def _start(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["research"]
        if state.status is ResearchStatus.PENDING:
            state = self._with_elapsed_time(state)
            decision = _relevant_budget_decision(
                state,
                {BudgetDimension.ITERATIONS, BudgetDimension.WALL_TIME_SECONDS},
            )
            if decision:
                state = _budget_exhausted(
                    state, f"budget exhausted before start: {', '.join(decision)}"
                )
            else:
                usage = state.budget_usage.model_copy(
                    update={"iterations": state.budget_usage.iterations + 1}
                )
                state = _transition(
                    state,
                    status=ResearchStatus.RUNNING,
                    budget_usage=usage,
                    node=ResearchNode.START,
                )
            await self._save(state)
        return {"research": state}

    async def _plan(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["research"]
        state = self._with_elapsed_time(state)
        if state.status is not ResearchStatus.RUNNING or state.research_plan is not None:
            return {"research": state}
        if _attempt_started(state, ResearchNode.PLAN):
            state = failed_research_state(
                state,
                RuntimeError("model-call outcome is unknown after worker interruption"),
            )
            await self._save(state)
            return {"research": state}
        exhausted_fields = _relevant_budget_decision(
            state,
            {
                BudgetDimension.LLM_CALLS,
                BudgetDimension.CONTEXT_TOKENS,
                BudgetDimension.ESTIMATED_COST_USD,
                BudgetDimension.WALL_TIME_SECONDS,
            },
        )
        if exhausted_fields:
            exhausted = ", ".join(exhausted_fields)
            state = _budget_exhausted(state, f"budget exhausted before planning: {exhausted}")
            await self._save(state)
            return {"research": state}

        request = ModelRequest[ResearchPlan](
            task="Create a bounded equity-research plan. Do not provide investment advice.",
            task_kind=TaskKind.RESEARCH_PLANNING,
            context={
                "instrument_id": str(state.instrument_id),
                "query": state.query,
                "horizon": state.horizon,
                "analysis_timestamp": state.analysis_timestamp.isoformat(),
            },
            output_schema=ResearchPlan,
        )
        state = _mark_attempt_started(
            state, ResearchNode.PLAN, request_id=str(request.request_id)
        )
        await self._save(state)
        response = await self._gateway.execute(
            cast(ModelRequest[Any], request), provider_order=self._provider_order
        )
        state = self._with_elapsed_time(state)
        plan = ResearchPlan.model_validate(response.output)
        metadata = response.metadata
        usage = state.budget_usage.model_copy(
            update={
                "llm_calls": state.budget_usage.llm_calls + 1,
                "context_tokens": state.budget_usage.context_tokens
                + (metadata.input_tokens or 0)
                + (metadata.output_tokens or 0),
                "estimated_cost_usd": state.budget_usage.estimated_cost_usd
                + (metadata.estimated_cost_usd or 0),
            }
        )
        history = (*state.model_history, metadata.model_dump(mode="json"))
        state = _transition(
            _mark_attempt_completed(state, ResearchNode.PLAN),
            node=ResearchNode.PLAN,
            research_plan=plan,
            budget_usage=usage,
            model_history=history,
        )
        await self._save(state)
        return {"research": state}

    async def _collect_evidence(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["research"]
        state = self._with_elapsed_time(state)
        if (
            state.status is not ResearchStatus.RUNNING
            or state.evidence
            or self._evidence_provider is None
        ):
            return {"research": state}
        if _attempt_started(state, ResearchNode.COLLECT_EVIDENCE):
            state = failed_research_state(
                state,
                RuntimeError("evidence-call outcome is unknown after worker interruption"),
            )
            await self._save(state)
            return {"research": state}
        exhausted_fields = _relevant_budget_decision(
            state, {BudgetDimension.TOOL_CALLS, BudgetDimension.WALL_TIME_SECONDS}
        )
        if exhausted_fields:
            state = _budget_exhausted(
                state,
                f"budget exhausted before evidence collection: "
                f"{', '.join(exhausted_fields)}",
            )
            await self._save(state)
            return {"research": state}
        state = _mark_attempt_started(state, ResearchNode.COLLECT_EVIDENCE)
        await self._save(state)
        collection = await self._evidence_provider.collect(state)
        state = self._with_elapsed_time(state)
        state = _transition(
            _mark_attempt_completed(state, ResearchNode.COLLECT_EVIDENCE),
            node=ResearchNode.COLLECT_EVIDENCE,
            market_snapshot=collection.market_snapshot,
            technical_snapshot=collection.technical_snapshot,
            evidence=collection.evidence,
            evidence_gaps=(*state.evidence_gaps, *collection.gaps),
            data_quality_status=(
                collection.market_snapshot.latest_bar.data_quality_status
                if collection.market_snapshot is not None
                else state.data_quality_status
            ),
            budget_usage=state.budget_usage.model_copy(
                update={"tool_calls": state.budget_usage.tool_calls + 1}
            ),
        )
        await self._save(state)
        return {"research": state}

    async def _finish(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["research"]
        state = self._with_elapsed_time(state)
        if state.status is not ResearchStatus.RUNNING:
            return {"research": state}
        has_required_output = state.research_plan is not None and bool(state.evidence)
        completion = (
            ResearchCompletion.COMPLETE
            if has_required_output
            else ResearchCompletion.INSUFFICIENT_EVIDENCE
        )
        status = (
            ResearchStatus.COMPLETE
            if has_required_output
            else ResearchStatus.INSUFFICIENT_EVIDENCE
        )
        decision = (
            QualityGateDecision.DEGRADED
            if has_required_output
            else QualityGateDecision.INSUFFICIENT
        )
        reasons = (
            ()
            if has_required_output
            else ("Qualified point-in-time evidence is unavailable.",)
        )
        limitations = (
            ()
            if has_required_output
            else ("No qualified evidence provider was available for this run.",)
        )
        gaps = state.evidence_gaps
        if not state.evidence:
            gaps += ("qualified point-in-time evidence",)
        state = _terminal_research_state(
            state,
            node=ResearchNode.FINISH,
            status=status,
            completion=completion,
            decision=decision,
            confidence_score=0.5 if has_required_output else 0.0,
            confidence_factors={"evidence_available": 1.0 if state.evidence else 0.0},
            limitations=limitations,
            evidence_coverage=1.0 if state.evidence else 0.0,
            reasons=reasons,
            evidence_gaps=gaps,
        )
        await self._save(state)
        return {"research": state}

    def _with_elapsed_time(self, state: ResearchState) -> ResearchState:
        elapsed = self._initial_wall_time + max(0.0, perf_counter() - self._run_started)
        usage = state.budget_usage.model_copy(update={"wall_time_seconds": elapsed})
        return state.model_copy(update={"budget_usage": usage})


def _transition(
    state: ResearchState, *, node: str | ResearchNode, **updates: object
) -> ResearchState:
    transitions = (*tuple(state.runtime_metadata.get("transitions", ())), str(node))
    runtime_metadata = {**state.runtime_metadata, "transitions": transitions}
    return state.model_copy(update={**updates, "runtime_metadata": runtime_metadata})


def _mark_attempt_started(
    state: ResearchState,
    node: ResearchNode,
    *,
    request_id: str | None = None,
) -> ResearchState:
    attempts = dict(state.runtime_metadata.get("external_attempts", {}))
    attempts[node.value] = {"status": "started", "request_id": request_id}
    marked = state.model_copy(
        update={
            "runtime_metadata": {**state.runtime_metadata, "external_attempts": attempts}
        }
    )
    transition = (
        ResearchNode.PLAN_STARTED
        if node is ResearchNode.PLAN
        else ResearchNode.EVIDENCE_STARTED
    )
    return _transition(marked, node=transition)


def _mark_attempt_completed(state: ResearchState, node: ResearchNode) -> ResearchState:
    attempts = dict(state.runtime_metadata.get("external_attempts", {}))
    attempt = dict(attempts.get(node.value, {}))
    attempt["status"] = "completed"
    attempts[node.value] = attempt
    return state.model_copy(
        update={
            "runtime_metadata": {**state.runtime_metadata, "external_attempts": attempts}
        }
    )


def _attempt_started(state: ResearchState, node: ResearchNode) -> bool:
    attempts = state.runtime_metadata.get("external_attempts", {})
    attempt = attempts.get(node.value, {}) if isinstance(attempts, dict) else {}
    return isinstance(attempt, dict) and attempt.get("status") == "started"


def failed_research_state(state: ResearchState, exc: Exception) -> ResearchState:
    reason = f"{type(exc).__name__}: {exc}"
    return _terminal_research_state(
        state,
        node=ResearchNode.FAILED,
        status=ResearchStatus.FAILED,
        completion=ResearchCompletion.FAILED,
        decision=QualityGateDecision.BLOCKED,
        confidence_score=0,
        limitations=(reason,),
        evidence_coverage=0,
        reasons=(reason,),
        evidence_gaps=state.evidence_gaps,
    )


def _budget_exhausted(state: ResearchState, reason: str) -> ResearchState:
    return _terminal_research_state(
        state,
        node=ResearchNode.BUDGET_EXHAUSTED,
        status=ResearchStatus.INSUFFICIENT_EVIDENCE,
        completion=ResearchCompletion.BUDGET_EXHAUSTED,
        decision=QualityGateDecision.INSUFFICIENT,
        confidence_score=0,
        limitations=(reason,),
        evidence_coverage=0,
        reasons=(reason,),
        evidence_gaps=(reason,),
    )


def _terminal_research_state(
    state: ResearchState,
    *,
    node: ResearchNode,
    status: ResearchStatus,
    completion: ResearchCompletion,
    decision: QualityGateDecision,
    confidence_score: float,
    limitations: tuple[str, ...],
    evidence_coverage: float,
    reasons: tuple[str, ...],
    evidence_gaps: tuple[str, ...],
    confidence_factors: dict[str, float] | None = None,
) -> ResearchState:
    confidence = SystemConfidence(
        score=confidence_score,
        factors=confidence_factors or {},
        limitations=limitations,
    )
    assessment = QualityAssessment(
        data_quality=state.data_quality_status,
        evaluation_maturity=state.evaluation_maturity,
        replay_integrity=state.replay_integrity_level,
        security_status=state.security_status,
        evidence_coverage=evidence_coverage,
        research_completion=completion,
        system_confidence=confidence,
        decision=decision,
        reasons=reasons,
    )
    return _transition(
        state,
        node=node,
        status=status,
        research_completion=completion,
        quality_gate_decision=decision,
        system_confidence=confidence,
        quality_assessment=assessment,
        evidence_gaps=evidence_gaps,
    )


def _relevant_budget_decision(
    state: ResearchState, relevant_fields: set[BudgetDimension]
) -> tuple[str, ...]:
    decision = BudgetGuard.evaluate(state.research_budget, state.budget_usage)
    relevant_values = {field.value for field in relevant_fields}
    return tuple(field for field in decision.exhausted_fields if field in relevant_values)
