"""Orchestration behind the provider-neutral market-data seam."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar
from backend.app.market_data.normalization import normalize_prices
from backend.app.market_data.providers import CorporateActionProvider, MarketDataProvider
from backend.app.market_data.quality import (
    require_report_matches_actions,
    require_report_matches_bars,
    require_strict_backtest_eligible,
    require_strict_bars_eligible,
    worse_quality,
)


class MarketDataRequest(ContractModel):
    instrument_id: UUID
    start: datetime
    end: datetime
    analysis_timestamp: datetime
    adjustment_mode: PriceAdjustmentMode
    strict_backtest: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> MarketDataRequest:
        if self.end < self.start:
            raise ValueError("end must not be earlier than start")
        if self.end > self.analysis_timestamp:
            raise ValueError("end must not be later than analysis_timestamp")
        return self


class MarketDataService:
    def __init__(
        self,
        *,
        market_data_provider: MarketDataProvider,
        corporate_action_provider: CorporateActionProvider,
    ) -> None:
        self._market_data_provider = market_data_provider
        self._corporate_action_provider = corporate_action_provider

    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        quality_report = await self._market_data_provider.get_quality_report()
        action_quality_report = await self._corporate_action_provider.get_quality_report()
        if request.strict_backtest:
            require_strict_backtest_eligible(quality_report)
            require_strict_backtest_eligible(action_quality_report)
        bars = await self._market_data_provider.get_bars(
            request.instrument_id,
            start=request.start,
            end=request.analysis_timestamp,
            analysis_timestamp=request.analysis_timestamp,
        )
        require_report_matches_bars(quality_report, bars)
        actions = await self._corporate_action_provider.get_actions(
            request.instrument_id,
            start=request.start,
            end=request.analysis_timestamp,
            analysis_timestamp=request.analysis_timestamp,
        )
        require_report_matches_actions(action_quality_report, actions)
        qualified_bars = tuple(
            bar.model_copy(
                update={
                    "data_quality_status": worse_quality(
                        bar.data_quality_status, quality_report.quality_status
                    ),
                }
            )
            for bar in bars
        )
        if request.strict_backtest:
            require_strict_bars_eligible(qualified_bars)
        normalized = normalize_prices(
            qualified_bars,
            actions,
            mode=request.adjustment_mode,
            analysis_timestamp=request.analysis_timestamp,
        )
        return tuple(bar for bar in normalized if bar.timestamp <= request.end)
