"""Deterministic technical indicators over normalized point-in-time bars."""

from __future__ import annotations

from datetime import datetime
from itertools import pairwise
from math import isfinite, sqrt

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
    feature_version: str = "v1-technical-v2",
    periods_per_year: int | None = None,
) -> TechnicalSnapshot:
    if analysis_timestamp.tzinfo is None or analysis_timestamp.utcoffset() is None:
        raise IndicatorError("analysis_timestamp must be timezone-aware")
    if periods_per_year is not None and (
        type(periods_per_year) is not int or periods_per_year <= 0
    ):
        raise IndicatorError("periods_per_year must be a positive integer")
    if any(time.tzinfo is None or time.utcoffset() is None for bar in bars for time in (
        bar.timestamp, bar.available_at, bar.observed_at,
    )):
        raise IndicatorError("market-bar timestamps must be timezone-aware")
    visible = tuple(
        sorted(
            (
                bar
                for bar in bars
                if bar.timestamp <= analysis_timestamp
                and bar.available_at <= analysis_timestamp
                and bar.observed_at <= analysis_timestamp
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
    for bar in visible:
        prices = (bar.open, bar.high, bar.low, bar.close)
        if (
            not all(isfinite(value) and value > 0 for value in prices)
            or not isfinite(bar.volume) or bar.volume < 0
            or bar.high < max(prices) or bar.low > min(prices)
        ):
            raise IndicatorError("finite valid OHLCV values are required")

    closes = pd.Series(np.asarray([bar.close for bar in visible], dtype=np.float64))
    returns = closes.pct_change()
    volumes = pd.Series([bar.volume for bar in visible], dtype=np.float64)
    means = {period: _last_or_none(closes.rolling(period).mean()) for period in (5, 10, 20, 50)}
    volatility = _last_or_none(returns.rolling(20).std(ddof=1))
    macd = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
    valid_macd = macd.iloc[25:]
    macd_line = _last_or_none(valid_macd) if len(valid_macd) else None
    signal = _last_or_none(valid_macd.ewm(span=9, adjust=False, min_periods=9).mean()) \
        if len(valid_macd) else None
    previous_volume = _last_or_none(volumes.shift(1).rolling(5).mean())
    indicators: dict[str, float | int | str | None] = {
        "close": float(closes.iloc[-1]),
        "return_1": _last_or_none(returns),
        **{f"sma_{period}": value for period, value in means.items()},
        "ema_20": _last_or_none(closes.ewm(span=20, adjust=False, min_periods=20).mean()),
        "rsi_14": _rsi(closes, 14),
        "historical_volatility_20": volatility,
        "realized_volatility_20": volatility * sqrt(periods_per_year)
        if volatility is not None and periods_per_year is not None else None,
        "trend_slope_20": _trend_slope(closes, 20),
        "macd": macd_line,
        "macd_signal": signal,
        "macd_histogram": macd_line-signal
        if macd_line is not None and signal is not None else None,
        "atr_14": _atr(visible, 14),
        "mavol_5": _last_or_none(volumes.rolling(5).mean()),
        "mavol_10": _last_or_none(volumes.rolling(10).mean()),
        "volume_ratio_5": float(volumes.iloc[-1]) / previous_volume
        if previous_volume is not None and previous_volume > 0 else None,
        "distance_to_sma_20": float(closes.iloc[-1])/means[20]-1
        if means[20] is not None else None,
        "trend_regime": _trend_regime(float(closes.iloc[-1]), means[20], means[50]),
        "support_20": min(bar.low for bar in visible[-21:-1]) if len(visible) >= 21 else None,
        "resistance_20": max(bar.high for bar in visible[-21:-1]) if len(visible) >= 21 else None,
    }
    indicators = {name: None if isinstance(value, float) and not isfinite(value) else value
                  for name, value in indicators.items()}
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
            "periods_per_year": periods_per_year,
            "support_resistance_definition": "prior_20_bar_range_proxy",
        },
    )


def _last_or_none(series: pd.Series[float]) -> float | None:
    value = series.iloc[-1]
    return None if not isfinite(value) else float(value)


def _rsi(closes: pd.Series[float], period: int) -> float | None:
    if len(closes) <= period:
        return None
    changes = closes.diff().iloc[1:]
    average_gain = _wilder(changes.clip(lower=0).tolist(), period)
    average_loss = _wilder((-changes.clip(upper=0)).tolist(), period)
    assert average_gain is not None and average_loss is not None
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def _wilder(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    average = sum(values[:period])/period
    for value in values[period:]:
        average = (average*(period-1)+value)/period
    return average


def _atr(bars: tuple[MarketBar, ...], period: int) -> float | None:
    ranges = [bars[0].high-bars[0].low]
    ranges.extend(max(bar.high-bar.low, abs(bar.high-previous.close), abs(bar.low-previous.close))
                  for previous, bar in pairwise(bars))
    return _wilder(ranges, period)


def _trend_regime(close: float, sma20: float | None, sma50: float | None) -> str | None:
    if sma20 is None or sma50 is None:
        return None
    if close > sma20 > sma50:
        return "uptrend"
    if close < sma20 < sma50:
        return "downtrend"
    return "range"


def _trend_slope(closes: pd.Series[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    window = closes.iloc[-period:].to_numpy(dtype=np.float64)
    return float(linregress(np.arange(period, dtype=np.float64), window).slope)
