"""Offline qualification of free company-news ingestion and current cutoff ordering."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest

from backend.app.contracts.research import ResearchState, ResearchTimestampMode
from backend.app.graph.workflow import EvidenceCollection
from backend.app.market_data.instrument import ProviderInstrument
from backend.app.news import FinnhubNewsLoader, NewsResearchEvidence, NewsSearchRequest
from backend.app.news.current import CurrentNewsSnapshot
from backend.app.news.finnhub import FinnhubNewsError

INSTRUMENT_ID = uuid4()
NOW = datetime(2026, 9, 29, 10, tzinfo=UTC)


class _Resolver:
    async def resolve_instrument(
        self, instrument_id: UUID, *, at: datetime
    ) -> ProviderInstrument:
        assert instrument_id == INSTRUMENT_ID
        return ProviderInstrument("KLAC", "USD", datetime(1980, 1, 1, tzinfo=UTC))


def _payload() -> list[dict[str, object]]:
    return [
        {
            "datetime": int((NOW - timedelta(hours=1)).timestamp()),
            "headline": "KLA announces results",
            "summary": "Revenue rose.",
            "url": "https://example.org/story?tracking=1",
            "related": "KLAC,SOXX",
        },
        {
            "datetime": int((NOW + timedelta(days=1)).timestamp()),
            "headline": "Future story",
            "url": "https://example.org/future",
        },
        {
            "datetime": int((NOW - timedelta(hours=2)).timestamp()),
            "headline": "Another company",
            "url": "https://example.org/other",
            "related": "AAPL",
        },
    ]


@pytest.mark.asyncio
async def test_current_news_is_captured_before_cutoff_and_becomes_cited_evidence() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/api/v1/company-news"
        assert request.url.params["symbol"] == "KLAC"
        assert request.url.params["from"] == "2026-09-22"
        assert request.url.params["to"] == "2026-09-29"
        assert request.headers["X-Finnhub-Token"] == "offline-key"
        assert "offline-key" not in str(request.url)
        return httpx.Response(200, json=_payload())

    class Market:
        async def collect(self, state: ResearchState) -> EvidenceCollection:
            assert calls == 1  # News acquisition precedes the market cutoff.
            return EvidenceCollection(analysis_timestamp=NOW + timedelta(minutes=2))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        loader = FinnhubNewsLoader(
            api_key="offline-key",
            instrument_resolver=_Resolver(),
            client=client,
            observed_at=lambda: NOW,
        )
        snapshot = CurrentNewsSnapshot(loader, Market())
        state = ResearchState(
            instrument_id=INSTRUMENT_ID,
            ticker="KLAC",
            query="Assess KLA catalysts",
            horizon="3-5 days",
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            requested_at=NOW - timedelta(minutes=1),
        )
        collection = await snapshot.collect(state)
        assert collection.analysis_timestamp == NOW + timedelta(minutes=2)
        assert len(collection.evidence) == 1
        news = await NewsResearchEvidence(snapshot).collect(
            NewsSearchRequest(
                instrument_id=INSTRUMENT_ID,
                analysis_timestamp=collection.analysis_timestamp,
                query="KLA news",
                limit=2,
            )
        )
    assert calls == 1
    assert news.documents_scanned == 1
    assert news.evidence[0].source_name == "finnhub.company_news"
    assert news.evidence[0].source_uri == "https://example.org/story"
    assert "Revenue rose" in news.evidence[0].content
    assert news.evidence[0].observed_at == NOW


@pytest.mark.asyncio
async def test_fixed_cutoff_rejects_newly_observed_news_without_network_request() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("historical retrieval must not occur")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        loader = FinnhubNewsLoader(
            api_key="offline-key",
            instrument_resolver=_Resolver(),
            client=client,
            observed_at=lambda: NOW,
        )
        documents = await loader.load_news(
            NewsSearchRequest(
                instrument_id=INSTRUMENT_ID,
                analysis_timestamp=NOW - timedelta(days=1),
                query="KLA news",
                limit=5,
            )
        )
    assert documents == ()


@pytest.mark.asyncio
async def test_finnhub_errors_are_bounded_and_do_not_expose_key() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate limited"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        loader = FinnhubNewsLoader(
            api_key="offline-key",
            instrument_resolver=_Resolver(),
            client=client,
            observed_at=lambda: NOW,
        )
        with pytest.raises(FinnhubNewsError, match="HTTP 429") as caught:
            await loader.load_current_news(INSTRUMENT_ID, limit=3)
    assert "offline-key" not in str(caught.value)
