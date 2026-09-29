"""Capture live news before the current market snapshot freezes its cutoff."""

from __future__ import annotations

from backend.app.contracts.research import ResearchState, ResearchTimestampMode
from backend.app.graph.workflow import EvidenceCollection, ResearchEvidence
from backend.app.news.finnhub import FinnhubNewsError, FinnhubNewsLoader
from backend.app.news.research import NewsDocument, NewsResearchEvidence, NewsSearchRequest


class CurrentNewsSnapshot:
    def __init__(self, loader: FinnhubNewsLoader, market: ResearchEvidence) -> None:
        self._loader = loader
        self._market = market
        self._documents: tuple[NewsDocument, ...] = ()
        self._gap: str | None = None
        self._documents_scanned = 0

    async def collect(self, state: ResearchState) -> EvidenceCollection:
        self._documents = ()
        self._gap = None
        self._documents_scanned = 0
        remaining_documents = max(
            0, state.research_budget.max_news_documents - state.budget_usage.news_documents
        )
        should_fetch = (
            state.timestamp_mode is ResearchTimestampMode.CURRENT_RESEARCH
            and state.analysis_timestamp is None
            and remaining_documents > 0
        )
        has_call_budget = (
            state.budget_usage.tool_calls + 1 < state.research_budget.max_tool_calls
        )
        attempted_news = should_fetch and has_call_budget
        if should_fetch and not has_call_budget:
            self._gap = "news skipped: tool call budget reserved for market acquisition"
        if attempted_news:
            try:
                batch = await self._loader.load_current_news(
                    state.instrument_id, limit=remaining_documents
                )
                self._documents = batch.documents
                self._documents_scanned = batch.documents_scanned
            except FinnhubNewsError as exc:
                self._gap = str(exc)
        collection = await self._market.collect(state)
        cutoff = collection.analysis_timestamp
        if cutoff is None:
            return EvidenceCollection(
                gaps=(*collection.gaps, *((self._gap,) if self._gap else ())),
                tool_calls=collection.tool_calls + int(attempted_news),
                news_documents_scanned=self._documents_scanned,
            )
        news = (
            await NewsResearchEvidence(self).collect(
                NewsSearchRequest(
                    instrument_id=state.instrument_id,
                    analysis_timestamp=cutoff,
                    query=state.query,
                    limit=remaining_documents,
                )
            )
            if self._documents
            else None
        )
        return EvidenceCollection(
            analysis_timestamp=cutoff,
            market_snapshot=collection.market_snapshot,
            technical_snapshot=collection.technical_snapshot,
            evidence=(*collection.evidence, *(news.evidence if news else ())),
            gaps=(
                *collection.gaps,
                *(news.gaps if news else ()),
                *((self._gap,) if self._gap else ()),
            ),
            tool_calls=collection.tool_calls + int(attempted_news),
            news_documents_scanned=self._documents_scanned,
        )

    async def load_news(self, request: NewsSearchRequest) -> tuple[NewsDocument, ...]:
        return tuple(
            doc
            for doc in self._documents
            if doc.instrument_id == request.instrument_id
            and doc.observed_at <= request.analysis_timestamp
            and doc.published_at <= request.analysis_timestamp
        )[: request.limit]
