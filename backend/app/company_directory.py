"""Bounded SEC identity discovery; deliberately separate from research security master."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from time import monotonic

import httpx

from backend.app.financials.sec import SecFinancialError

SEC_DIRECTORY_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
MAX_BYTES = 10 * 1024 * 1024
TTL_SECONDS = 24 * 60 * 60
MAX_STALE_SECONDS = 7 * TTL_SECONDS
RETRY_SECONDS = 5 * 60


class DirectoryUnavailable(Exception):
    """Safe error code without upstream bodies or contact configuration."""


@dataclass(frozen=True)
class DirectoryIdentity:
    cik: str
    symbol: str
    name: str
    exchange: str | None


@dataclass(frozen=True)
class DirectorySnapshot:
    items: tuple[DirectoryIdentity, ...]
    fetched_at: datetime
    stale: bool = False


def parse_directory(payload: object) -> tuple[DirectoryIdentity, ...]:
    if not isinstance(payload, dict) or payload.get("fields") != [
        "cik", "name", "ticker", "exchange",
    ]:
        raise DirectoryUnavailable("directory_unavailable")
    rows = payload.get("data")
    if not isinstance(rows, list) or not 0 < len(rows) <= 100_000:
        raise DirectoryUnavailable("directory_unavailable")
    identities: dict[tuple[str, str, str | None], DirectoryIdentity] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise DirectoryUnavailable("directory_unavailable")
        cik, name, symbol, exchange = row
        if (type(cik) is not int or not 0 < cik < 10**10
                or not isinstance(name, str) or not 0 < len(name.strip()) <= 256
                or not isinstance(symbol, str) or not 0 < len(symbol.strip()) <= 32
                or (exchange is not None and (
                    not isinstance(exchange, str) or not 0 < len(exchange.strip()) <= 32))):
            raise DirectoryUnavailable("directory_unavailable")
        identity = DirectoryIdentity(
            str(cik).zfill(10), symbol.strip().upper(), name.strip(),
            exchange.strip().upper() if exchange else None,
        )
        key = (identity.cik, identity.symbol, identity.exchange)
        if key in identities and identities[key] != identity:
            raise DirectoryUnavailable("directory_unavailable")
        identities[key] = identity
    return tuple(identities.values())


class SecCompanyDirectory:
    def __init__(
        self, user_agent: str | None, *, transport: httpx.AsyncBaseTransport | None = None,
        admission: Callable[[], Awaitable[None]] | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._user_agent = user_agent
        self._transport = transport
        self._admission = admission
        self._clock = clock
        self._snapshot: DirectorySnapshot | None = None
        self._loaded_at = 0.0
        self._retry_at = 0.0
        self._lock = asyncio.Lock()

    async def snapshot(self) -> DirectorySnapshot:
        if not self._user_agent:
            raise DirectoryUnavailable("directory_not_configured")
        async with self._lock:
            now = self._clock()
            age = now - self._loaded_at
            if self._snapshot and age < TTL_SECONDS:
                return self._snapshot
            if now >= self._retry_at:
                try:
                    async with asyncio.timeout(8):
                        items = await self._fetch()
                    self._snapshot = DirectorySnapshot(items, datetime.now(UTC))
                    self._loaded_at = self._clock()
                    self._retry_at = 0.0
                    return self._snapshot
                except (httpx.HTTPError, TimeoutError, ValueError,
                        DirectoryUnavailable, SecFinancialError):
                    self._retry_at = self._clock() + RETRY_SECONDS
            if self._snapshot and self._clock() - self._loaded_at < MAX_STALE_SECONDS:
                return replace(self._snapshot, stale=True)
            raise DirectoryUnavailable("directory_unavailable")

    async def _fetch(self) -> tuple[DirectoryIdentity, ...]:
        if self._admission:
            await self._admission()
        async with httpx.AsyncClient(
            transport=self._transport, timeout=4, follow_redirects=False,
            headers={"User-Agent": self._user_agent or "", "Accept": "application/json"},
        ) as client, client.stream("GET", SEC_DIRECTORY_URL) as response:
            response.raise_for_status()
            content = bytearray()
            async for chunk in response.aiter_bytes():
                if len(content) + len(chunk) > MAX_BYTES:
                    raise DirectoryUnavailable("directory_unavailable")
                content.extend(chunk)
        return parse_directory(json.loads(content))
