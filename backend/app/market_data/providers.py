"""Interfaces and deterministic adapters for external market-data seams."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from backend.app.contracts.evaluation import ProviderQualityReport
from backend.app.contracts.instrument import CorporateAction
from backend.app.contracts.market import MarketBar


@runtime_checkable
class MarketDataProvider(Protocol):
    async def get_bars(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[MarketBar, ...]: ...

    async def get_quality_report(self) -> ProviderQualityReport: ...


@runtime_checkable
class CorporateActionProvider(Protocol):
    async def get_actions(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[CorporateAction, ...]: ...

    async def get_quality_report(self) -> ProviderQualityReport: ...


class InMemoryMarketDataProvider:
    """Deterministic adapter used by tests and offline qualification fixtures."""

    def __init__(
        self, *, bars: tuple[MarketBar, ...], quality_report: ProviderQualityReport
    ) -> None:
        self._bars = bars
        self._quality_report = quality_report

    async def get_bars(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[MarketBar, ...]:
        return tuple(
            bar
            for bar in self._bars
            if bar.instrument_id == instrument_id
            and start <= bar.timestamp <= end
            and bar.timestamp <= analysis_timestamp
            and bar.available_at <= analysis_timestamp
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report


class InMemoryCorporateActionProvider:
    """Point-in-time-safe deterministic corporate-action adapter."""

    def __init__(
        self, *, actions: tuple[CorporateAction, ...], quality_report: ProviderQualityReport
    ) -> None:
        self._actions = actions
        self._quality_report = quality_report

    async def get_actions(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[CorporateAction, ...]:
        return tuple(
            action
            for action in self._actions
            if action.instrument_id == instrument_id
            and start <= action.effective_at <= end
            and action.available_at <= analysis_timestamp
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report
