"""Deterministic technical indicators over normalized point-in-time bars."""

from __future__ import annotations

from datetime import datetime
from math import sqrt

import numpy as np
import pandas as pd
from scipy.stats import linregress

from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar, TechnicalSnapshot


class IndicatorError(ValueError):
    """Raised when an indicator input violates quant-integrity requirements."""


def calculate_technical_snapshot(
    bars: tuple[MarketBar, ...],
    *,
    analysis_timestamp: datetime,
    feature_version: str = "phase4-v1",
) -> TechnicalSnapshot:
    visible = tuple(
        sorted(
            (
                bar
                for bar in bars
                if bar.timestamp <= analysis_timestamp
                and bar.available_at <= analysis_timestamp
            ),
            key=lambda bar: bar.timestamp,
        )
    )
    if not visible:
        raise IndicatorError("at least one point-in-time-visible market bar is required")
    instrument_id = visible[0].instrument_id
    modes = {bar.adjustment_mode for bar in visible}
    if len(modes) != 1 or PriceAdjustmentMode.RAW in modes:
        raise IndicatorError("indicators require one explicit normalized price mode")
    if any(bar.instrument_id != instrument_id for bar in visible):
        raise IndicatorError("all bars must belong to one instrument")
    eligible = {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
    if any(bar.data_quality_status not in eligible for bar in visible):
        raise IndicatorError("bar quality is below ACCEPTABLE")
    if len({bar.timestamp for bar in visible}) != len(visible):
        raise IndicatorError("duplicate market-bar timestamps are not allowed")

    closes = pd.Series(np.asarray([bar.close for bar in visible], dtype=np.float64))
    returns = closes.pct_change()
    indicators: dict[str, float | int | str | None] = {
        "close": float(closes.iloc[-1]),
        "return_1": _last_or_none(returns),
        "sma_20": _last_or_none(closes.rolling(20).mean()),
        "ema_20": _last_or_none(closes.ewm(span=20, adjust=False).mean()),
        "rsi_14": _rsi(closes, 14),
        "realized_volatility_20": _last_or_none(returns.rolling(20).std(ddof=1) * sqrt(252)),
        "trend_slope_20": _trend_slope(closes, 20),
    }
    return TechnicalSnapshot(
        instrument_id=instrument_id,
        analysis_timestamp=analysis_timestamp,
        price_adjustment_mode=next(iter(modes)),
        feature_version=feature_version,
        indicators=indicators,
        metadata={
            "bar_count": len(visible),
            "first_timestamp": visible[0].timestamp.isoformat(),
            "last_timestamp": visible[-1].timestamp.isoformat(),
        },
    )


def _last_or_none(series: pd.Series[float]) -> float | None:
    value = series.iloc[-1]
    return None if pd.isna(value) else float(value)


def _rsi(closes: pd.Series[float], period: int) -> float | None:
    if len(closes) <= period:
        return None
    changes = closes.diff().iloc[-period:]
    average_gain = float(changes.clip(lower=0).mean())
    average_loss = float((-changes.clip(upper=0)).mean())
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def _trend_slope(closes: pd.Series[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    window = closes.iloc[-period:].to_numpy(dtype=np.float64)
    return float(linregress(np.arange(period, dtype=np.float64), window).slope)
