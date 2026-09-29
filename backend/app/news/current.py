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

    async def collect(self, state: ResearchState) -> EvidenceCollection:
        if (
            state.timestamp_mode is ResearchTimestampMode.CURRENT_RESEARCH
            and state.analysis_timestamp is None
            and state.research_budget.max_news_documents > 0
        ):
            try:
                self._documents = await self._loader.load_current_news(
                    state.instrument_id, limit=state.research_budget.max_news_documents
                )
            except FinnhubNewsError as exc:
                self._gap = str(exc)
        collection = await self._market.collect(state)
        cutoff = collection.analysis_timestamp
        if cutoff is None:
            return collection
        news = (
            await NewsResearchEvidence(self).collect(
                NewsSearchRequest(
                    instrument_id=state.instrument_id,
                    analysis_timestamp=cutoff,
                    query=state.query,
                    limit=state.research_budget.max_news_documents,
                )
            )
            if self._documents and state.research_budget.max_news_documents > 0
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
        )

    async def load_news(self, request: NewsSearchRequest) -> tuple[NewsDocument, ...]:
        return tuple(
            doc
            for doc in self._documents
            if doc.instrument_id == request.instrument_id
            and doc.observed_at <= request.analysis_timestamp
            and doc.published_at <= request.analysis_timestamp
        )[: request.limit]
