"""Budgeted current financial acquisition before the market freezes the cutoff."""

import asyncio
from collections.abc import Callable
from datetime import datetime
from time import perf_counter
from typing import Protocol

from backend.app.contracts.base import utc_now
from backend.app.contracts.evaluation import ReplayIntegrityLevel
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.research import ResearchState, ResearchTimestampMode
from backend.app.financials.admission import admitted_financial_fact
from backend.app.financials.sec import SecFinancialError, SecFinancialSnapshot
from backend.app.graph.workflow import EvidenceCollection, ResearchEvidence
from backend.app.market_data.instrument import InstrumentMetadataResolver


class CurrentFinancialLoader(Protocol):
    requests_made: int

    async def load_current(self, ticker: str) -> SecFinancialSnapshot: ...


class CurrentFinancialSnapshot:
    def __init__(
        self,
        loader: CurrentFinancialLoader,
        downstream: ResearchEvidence,
        *,
        resolver: InstrumentMetadataResolver,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._loader = loader
        self._downstream = downstream
        self._resolver = resolver
        self._clock = clock

    async def collect(self, state: ResearchState) -> EvidenceCollection:
        if (
            state.timestamp_mode is not ResearchTimestampMode.CURRENT_RESEARCH
            or state.analysis_timestamp is not None
            or state.replay_integrity_level is ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY
        ):
            return await self._downstream.collect(state)
        remaining = state.research_budget.max_tool_calls - state.budget_usage.tool_calls
        if remaining < 3:
            collection = await self._downstream.collect(state)
            return _with_financials(collection, (), ("financials skipped: reserve market call",), 0)
        remaining_time = (
            state.research_budget.max_wall_time_seconds - state.budget_usage.wall_time_seconds
        )
        if remaining_time <= 0:
            return EvidenceCollection(
                tool_calls=0, gaps=("financials skipped: wall time exhausted",)
            )
        start = perf_counter()
        snapshot = None
        gaps: tuple[str, ...] = ()
        self._loader.requests_made = 0
        try:
            async with asyncio.timeout(remaining_time):
                instrument = await self._resolver.resolve_instrument(
                    state.instrument_id, at=self._clock()
                )
                if instrument.currency != "USD":
                    raise SecFinancialError("SEC financial slice requires USD instrument")
                snapshot = await self._loader.load_current(instrument.symbol)
                if snapshot.ticker != instrument.symbol.strip().upper():
                    raise ValueError("financial snapshot does not match resolved instrument")
        except SecFinancialError:
            gaps = ("current SEC financial acquisition unavailable",)
        except TimeoutError:
            gaps = ("current SEC financial acquisition reached wall-time budget",)
        calls = self._loader.requests_made
        if not 0 <= calls <= 2:
            raise ValueError("financial loader exceeded reserved request budget")
        elapsed = perf_counter() - start
        downstream_state = state.model_copy(
            update={
                "budget_usage": state.budget_usage.model_copy(
                    update={
                        "tool_calls": state.budget_usage.tool_calls + calls,
                        "wall_time_seconds": state.budget_usage.wall_time_seconds + elapsed,
                    }
                )
            }
        )
        collection = (
            await self._downstream.collect(downstream_state)
            if elapsed < remaining_time
            else EvidenceCollection(
                analysis_timestamp=self._clock(),
                tool_calls=0,
                gaps=("market skipped: financial acquisition exhausted wall time",),
            )
        )
        cutoff = collection.analysis_timestamp
        evidence: tuple[Evidence, ...] = ()
        if snapshot is not None and cutoff is not None:
            candidates = tuple(
                fact.to_evidence(state.instrument_id, cutoff=cutoff) for fact in snapshot.facts
            )
            evidence = tuple(
                item
                for item in candidates
                if admitted_financial_fact(item, cutoff=cutoff) is not None
            )
            gaps = (*gaps, *snapshot.gaps)
            if len(evidence) != len(candidates):
                gaps = (*gaps, "financial observations outside freshness or provenance policy")
        elif snapshot is not None:
            gaps = (*gaps, "financial observations withheld: current cutoff unavailable")
        return _with_financials(collection, evidence, gaps, calls)


def _with_financials(
    collection: EvidenceCollection,
    evidence: tuple[Evidence, ...],
    gaps: tuple[str, ...],
    calls: int,
) -> EvidenceCollection:
    return EvidenceCollection(
        analysis_timestamp=collection.analysis_timestamp,
        market_snapshot=collection.market_snapshot,
        market_acquisition=collection.market_acquisition,
        technical_snapshot=collection.technical_snapshot,
        evidence=(*collection.evidence, *evidence),
        gaps=(*collection.gaps, *gaps),
        tool_calls=collection.tool_calls + calls,
        news_documents_scanned=collection.news_documents_scanned,
    )
