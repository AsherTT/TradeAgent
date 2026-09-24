"""Qualified in-memory cache for complete market-data loads."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar
from backend.app.market_data.errors import MarketDataIntegrityError
from backend.app.market_data.service import (
    MarketDataAttemptSource,
    MarketDataLoader,
    MarketDataRequest,
    ProviderAttempt,
    ProviderAttemptOutcome,
)


@dataclass(frozen=True)
class QualifiedCacheKey:
    instrument_id: UUID
    start: datetime
    end: datetime
    analysis_timestamp: datetime
    adjustment_mode: PriceAdjustmentMode
    strict_backtest: bool
    source: str
    bar_quality_version: str
    action_quality_version: str


@dataclass(frozen=True)
class ProviderQualificationVersions:
    bar_version: str
    action_version: str


class InMemoryQualifiedMarketDataCache:
    def __init__(self, *, max_entries: int = 256) -> None:
        if max_entries < 1:
            raise ValueError("market-data cache max_entries must be positive")
        self._max_entries = max_entries
        self._entries: OrderedDict[QualifiedCacheKey, tuple[MarketBar, ...]] = (
            OrderedDict()
        )

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def get(self, key: QualifiedCacheKey) -> tuple[MarketBar, ...] | None:
        cached = self._entries.get(key)
        if cached is not None:
            self._entries.move_to_end(key)
        return cached

    def put(self, key: QualifiedCacheKey, bars: tuple[MarketBar, ...]) -> None:
        self._entries[key] = bars
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)


class CachedMarketDataLoader:
    """Check qualified provider/version entries before invoking the wrapped loader."""

    def __init__(
        self,
        *,
        loader: MarketDataLoader,
        cache: InMemoryQualifiedMarketDataCache,
        provider_order: tuple[str, ...],
        qualified_versions: Mapping[str, ProviderQualificationVersions],
    ) -> None:
        self._loader = loader
        self._cache = cache
        self._provider_order = provider_order
        self._qualified_versions = dict(qualified_versions)
        self._attempts: ContextVar[tuple[ProviderAttempt, ...]] = ContextVar(
            f"cached_market_data_attempts_{id(self)}", default=()
        )

    @property
    def last_attempts(self) -> tuple[ProviderAttempt, ...]:
        return self._attempts.get()

    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        self._attempts.set(())
        for source in self._provider_order:
            qualification = self._qualified_versions.get(source)
            if qualification is None:
                continue
            cached = self._cache.get(
                _key(request, source=source, qualification=qualification)
            )
            if cached is not None:
                self._attempts.set(
                    (
                        ProviderAttempt(
                            provider=source,
                            outcome=ProviderAttemptOutcome.CACHE_HIT,
                        ),
                    )
                )
                return cached

        try:
            bars = await self._loader.load_bars(request)
        finally:
            if isinstance(self._loader, MarketDataAttemptSource):
                self._attempts.set(self._loader.last_attempts)
        if not bars:
            return bars
        sources = {bar.source for bar in bars}
        versions = {bar.provider_quality_version for bar in bars}
        if len(sources) != 1 or len(versions) != 1:
            raise MarketDataIntegrityError(
                "a cached market-data result must use one provider and quality version"
            )
        source = next(iter(sources))
        version = next(iter(versions))
        qualification = self._qualified_versions.get(source)
        if qualification is None or qualification.bar_version != version:
            raise MarketDataIntegrityError(
                "market-data result does not match the current provider qualification version"
            )
        self._cache.put(
            _key(request, source=source, qualification=qualification), bars
        )
        return bars


def _key(
    request: MarketDataRequest,
    *,
    source: str,
    qualification: ProviderQualificationVersions,
) -> QualifiedCacheKey:
    return QualifiedCacheKey(
        instrument_id=request.instrument_id,
        start=request.start,
        end=request.end,
        analysis_timestamp=request.analysis_timestamp,
        adjustment_mode=request.adjustment_mode,
        strict_backtest=request.strict_backtest,
        source=source,
        bar_quality_version=qualification.bar_version,
        action_quality_version=qualification.action_version,
    )
