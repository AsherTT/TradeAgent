"""Build historical features from data actually available at each decision time."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import ProviderQualityReport, ReplayIntegrityLevel
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.normalization import PriceNormalizationError, normalize_prices
from backend.app.market_data.quality import (
    require_report_matches_actions,
    require_report_matches_bars,
    require_strict_backtest_eligible,
    require_strict_bars_eligible,
)


class StrictInputError(ValueError):
    """The input cannot support an honest point-in-time historical test."""


class StrictBacktestInput(ContractModel):
    instrument_id: UUID
    universe_as_of: datetime
    universe_instrument_ids: tuple[UUID, ...] = Field(min_length=1)
    bars: tuple[MarketBar, ...] = Field(min_length=2)
    corporate_actions: tuple[CorporateAction, ...] = ()
    market_quality: ProviderQualityReport
    corporate_action_quality: ProviderQualityReport
    replay_integrity_level: ReplayIntegrityLevel = ReplayIntegrityLevel.STRICT_QUANT_BACKTEST

    @model_validator(mode="after")
    def validate_input(self) -> StrictBacktestInput:
        if self.replay_integrity_level is not ReplayIntegrityLevel.STRICT_QUANT_BACKTEST:
            raise ValueError("strategy input requires strict quant backtest integrity")
        if self.universe_as_of.tzinfo is None or self.universe_as_of.utcoffset() is None:
            raise ValueError("universe timestamp must be timezone-aware")
        if self.instrument_id not in self.universe_instrument_ids:
            raise ValueError("instrument is absent from the historical universe")
        if len(set(self.universe_instrument_ids)) != len(self.universe_instrument_ids):
            raise ValueError("historical universe has duplicate instruments")
        return self


class StrictFeature(ContractModel):
    instrument_id: UUID
    bar_timestamp: datetime
    as_of: datetime
    price_adjustment_mode: PriceAdjustmentMode
    feature_version: str
    close: float = Field(gt=0)
    fast_mean: float = Field(gt=0)
    slow_mean: float = Field(gt=0)
    source_bar_count: int = Field(ge=1)


def build_strict_features(
    data: StrictBacktestInput, *, fast_window: int = 2, slow_window: int = 3
) -> tuple[StrictFeature, ...]:
    """Use raw execution bars, then normalize independently at each visible cutoff."""

    if not 1 <= fast_window < slow_window:
        raise ValueError("feature windows require 1 <= fast < slow")
    bars = data.bars
    if any(bar.instrument_id != data.instrument_id for bar in bars):
        raise StrictInputError("market bars must belong to the selected instrument")
    if len({bar.symbol for bar in bars}) != 1:
        raise StrictInputError("symbol changes require separately qualified history")
    if any(bar.adjustment_mode is not PriceAdjustmentMode.RAW for bar in bars):
        raise StrictInputError("execution prices require RAW market bars")
    if any(
        timestamp.tzinfo is None or timestamp.utcoffset() is None
        for bar in bars
        for timestamp in (bar.timestamp, bar.observed_at, bar.available_at)
    ):
        raise StrictInputError("market-bar timestamps must be timezone-aware")
    if any(
        bar.observed_at > bar.available_at or bar.timestamp > bar.observed_at
        for bar in bars
    ):
        raise StrictInputError("market-bar chronology is invalid")
    if tuple(sorted(bars, key=lambda bar: bar.timestamp)) != bars:
        raise StrictInputError("market bars must be ordered by timestamp")
    if len({bar.timestamp for bar in bars}) != len(bars):
        raise StrictInputError("duplicate market-bar timestamps")
    if data.universe_as_of > bars[0].timestamp:
        raise StrictInputError("historical universe was selected after the test began")
    require_strict_backtest_eligible(data.market_quality)
    require_strict_backtest_eligible(data.corporate_action_quality)
    require_strict_bars_eligible(bars)
    require_report_matches_bars(data.market_quality, bars)
    require_report_matches_actions(data.corporate_action_quality, data.corporate_actions)
    if any(action.instrument_id != data.instrument_id for action in data.corporate_actions):
        raise StrictInputError("corporate actions must belong to the selected instrument")
    if any(
        timestamp.tzinfo is None or timestamp.utcoffset() is None
        for action in data.corporate_actions
        for timestamp in (action.effective_at, action.available_at)
    ):
        raise StrictInputError("corporate-action timestamps must be timezone-aware")
    action_keys = tuple(
        (
            action.action_type, action.effective_at, action.ratio,
            action.cash_amount, action.currency,
        )
        for action in data.corporate_actions
    )
    if (
        len({action.action_id for action in data.corporate_actions}) != len(action_keys)
        or len(set(action_keys)) != len(action_keys)
    ):
        raise StrictInputError("duplicate corporate actions would distort position accounting")
    unsupported = {
        CorporateActionType.MERGER,
        CorporateActionType.SPINOFF,
        CorporateActionType.STOCK_DIVIDEND,
        CorporateActionType.SYMBOL_CHANGE,
        CorporateActionType.DELISTING,
    }
    if any(
        action.action_type in unsupported
        and bars[0].timestamp <= action.effective_at <= bars[-1].timestamp
        for action in data.corporate_actions
    ):
        raise StrictInputError("unsupported corporate action inside backtest window")
    if any(
        action.available_at > action.effective_at
        for action in data.corporate_actions
        if action.action_type in {
            CorporateActionType.SPLIT,
            CorporateActionType.REVERSE_SPLIT,
            CorporateActionType.CASH_DIVIDEND,
            CorporateActionType.DELISTING,
        }
    ):
        raise StrictInputError("corporate action became available after its effective time")
    features: list[StrictFeature] = []
    for index, bar in enumerate(bars):
        if index + 1 < slow_window:
            continue
        if index + 1 < len(bars) and bar.available_at >= bars[index + 1].timestamp:
            continue
        visible = tuple(item for item in bars[: index + 1] if item.available_at <= bar.available_at)
        try:
            adjusted = normalize_prices(
                visible,
                data.corporate_actions,
                mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
                analysis_timestamp=bar.available_at,
            )
        except PriceNormalizationError as exc:
            raise StrictInputError(str(exc)) from exc
        if len(adjusted) < slow_window or adjusted[-1].timestamp != bar.timestamp:
            raise StrictInputError("current bar is not point-in-time visible")
        closes = [item.close for item in adjusted]
        features.append(StrictFeature(
            instrument_id=data.instrument_id,
            bar_timestamp=bar.timestamp,
            as_of=bar.available_at,
            price_adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            feature_version="strict-sma-v1",
            close=closes[-1],
            fast_mean=sum(closes[-fast_window:]) / fast_window,
            slow_mean=sum(closes[-slow_window:]) / slow_window,
            source_bar_count=len(adjusted),
        ))
    return tuple(features)
