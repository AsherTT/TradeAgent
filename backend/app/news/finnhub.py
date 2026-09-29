"""Bounded Finnhub company-news adapter for current research."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from backend.app.contracts.base import utc_now
from backend.app.market_data.instrument import InstrumentMetadataResolver
from backend.app.news.research import NewsDocument, NewsSearchRequest

FINNHUB_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"


class FinnhubNewsError(Exception):
    """A Finnhub request or response cannot support trustworthy news evidence."""


@dataclass(frozen=True, slots=True)
class FinnhubNewsBatch:
    documents: tuple[NewsDocument, ...]
    documents_scanned: int


class FinnhubNewsLoader:
    def __init__(
        self,
        *,
        api_key: str,
        instrument_resolver: InstrumentMetadataResolver,
        base_url: str = FINNHUB_COMPANY_NEWS_URL,
        client: httpx.AsyncClient | None = None,
        observed_at: Callable[[], datetime] = utc_now,
        lookback_days: int = 7,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "finnhub.io"
            or parsed.path != "/api/v1/company-news"
            or parsed.port is not None
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Finnhub news URL must be the official HTTPS company-news endpoint")
        if not api_key.strip():
            raise ValueError("Finnhub news requires an API key")
        if not 1 <= lookback_days <= 365:
            raise ValueError("Finnhub news lookback must be between 1 and 365 days")
        self._api_key = api_key
        self._resolver = instrument_resolver
        self._base_url = base_url
        self._client = client
        self._observed_at = observed_at
        self._lookback_days = lookback_days

    async def load_news(self, request: NewsSearchRequest) -> tuple[NewsDocument, ...]:
        # A new live retrieval cannot establish what was known at an earlier cutoff.
        if self._observed_at() > request.analysis_timestamp:
            return ()
        instrument = await self._resolver.resolve_instrument(
            request.instrument_id, at=request.analysis_timestamp
        )
        batch = await self._fetch(request, instrument.symbol.upper(), request.analysis_timestamp)
        return batch.documents

    async def load_current_news(
        self, instrument_id: UUID, *, limit: int
    ) -> FinnhubNewsBatch:
        """Acquire before current research freezes its evidence cutoff."""
        now = self._observed_at()
        instrument = await self._resolver.resolve_instrument(instrument_id, at=now)
        request = NewsSearchRequest(
            instrument_id=instrument_id,
            analysis_timestamp=datetime.max.replace(tzinfo=UTC),
            query=instrument.symbol,
            limit=limit,
        )
        return await self._fetch(request, instrument.symbol.upper(), now)

    async def _fetch(
        self, request: NewsSearchRequest, symbol: str, query_end: datetime
    ) -> FinnhubNewsBatch:
        start = (query_end - timedelta(days=self._lookback_days)).date()
        end = query_end.date()
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15, follow_redirects=False)
        try:
            response = await client.get(
                self._base_url,
                params={"symbol": symbol, "from": start.isoformat(), "to": end.isoformat()},
                headers={"X-Finnhub-Token": self._api_key},
            )
            response.raise_for_status()
            if len(response.content) > 2_000_000:
                raise FinnhubNewsError("Finnhub news response exceeds size limit")
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise FinnhubNewsError(
                f"Finnhub company news returned HTTP {exc.response.status_code}"
            ) from None
        except httpx.RequestError:
            raise FinnhubNewsError("Finnhub company news network request failed") from None
        except ValueError as exc:
            raise FinnhubNewsError("Finnhub company news returned invalid JSON") from exc
        finally:
            if owns_client:
                await client.aclose()
        observed = self._observed_at()
        if observed > request.analysis_timestamp:
            return FinnhubNewsBatch((), 0)
        if not isinstance(payload, list):
            raise FinnhubNewsError("Finnhub company news response must be a list")
        documents: list[NewsDocument] = []
        seen_urls: set[str] = set()
        candidates = sorted(payload, key=_published_epoch, reverse=True)[: request.limit]
        for item in candidates:
            if not isinstance(item, Mapping):
                continue
            document = _document(item, request, symbol, observed)
            if document is None or document.source_uri in seen_urls:
                continue
            seen_urls.add(document.source_uri)
            documents.append(document)
        return FinnhubNewsBatch(tuple(documents), len(candidates))


def _published_epoch(item: object) -> int:
    if isinstance(item, Mapping):
        timestamp = item.get("datetime")
        if isinstance(timestamp, int) and not isinstance(timestamp, bool):
            return timestamp
    return -1


def _document(
    item: Mapping[str, Any],
    request: NewsSearchRequest,
    symbol: str,
    observed: datetime,
) -> NewsDocument | None:
    timestamp = item.get("datetime")
    headline = item.get("headline")
    summary = item.get("summary")
    uri = item.get("url")
    related = item.get("related")
    if (
        not isinstance(timestamp, int)
        or isinstance(timestamp, bool)
        or not isinstance(headline, str)
        or not headline.strip()
        or not isinstance(uri, str)
        or not uri.strip()
    ):
        return None
    if isinstance(related, str) and related.strip():
        tickers = {part.strip().upper() for part in related.split(",")}
        if symbol not in tickers:
            return None
    try:
        published = datetime.fromtimestamp(timestamp, UTC)
    except (OverflowError, OSError, ValueError):
        return None
    if published > request.analysis_timestamp or published > observed:
        return None
    body = summary.strip() if isinstance(summary, str) else ""
    content = (
        f"{headline.strip()}\n{body}"
        if body and body != headline.strip()
        else headline.strip()
    )
    try:
        return NewsDocument(
            instrument_id=request.instrument_id,
            source_name="finnhub.company_news",
            source_uri=uri,
            published_at=published,
            observed_at=observed,
            available_at=observed,
            content=content[:20_000],
        )
    except ValueError:
        return None
