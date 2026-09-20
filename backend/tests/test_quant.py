from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar
from backend.app.quant.indicators import IndicatorError, calculate_technical_snapshot


def _bars() -> tuple[MarketBar, ...]:
    instrument_id = uuid4()
    start = datetime(2024, 1, 1, 21, tzinfo=UTC)
    return tuple(
        MarketBar(
            instrument_id=instrument_id,
            symbol="ACME",
            timestamp=start + timedelta(days=index),
            open=float(close),
            high=float(close),
            low=float(close),
            close=float(close),
            volume=1000,
            adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            adjustment_factor=1,
            source="fixture",
            observed_at=start + timedelta(days=index),
            available_at=start + timedelta(days=index),
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="fixture-v1",
        )
        for index, close in enumerate(range(100, 125))
    )


def test_deterministic_indicators_match_golden_values() -> None:
    bars = _bars()
    snapshot = calculate_technical_snapshot(
        bars, analysis_timestamp=bars[-1].available_at
    )

    assert snapshot.instrument_id == bars[0].instrument_id
    assert snapshot.price_adjustment_mode is PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED
    assert snapshot.feature_version == "phase4-v1"
    assert snapshot.indicators["close"] == 124
    assert snapshot.indicators["return_1"] == pytest.approx(124 / 123 - 1)
    assert snapshot.indicators["sma_20"] == pytest.approx(114.5)
    assert snapshot.indicators["rsi_14"] == 100
    assert snapshot.indicators["trend_slope_20"] == pytest.approx(1)


def test_indicators_exclude_bars_unavailable_at_analysis_time() -> None:
    bars = _bars()
    snapshot = calculate_technical_snapshot(
        bars, analysis_timestamp=bars[-2].available_at
    )
    assert snapshot.indicators["close"] == 123
    assert snapshot.metadata["bar_count"] == 24


def test_indicators_reject_raw_or_degraded_input() -> None:
    bars = _bars()
    with pytest.raises(IndicatorError, match="normalized"):
        calculate_technical_snapshot(
            (bars[0].model_copy(update={"adjustment_mode": PriceAdjustmentMode.RAW}),),
            analysis_timestamp=bars[-1].available_at,
        )
    with pytest.raises(IndicatorError, match="quality"):
        calculate_technical_snapshot(
            (bars[0].model_copy(update={"data_quality_status": DataQualityStatus.DEGRADED}),),
            analysis_timestamp=bars[-1].available_at,
        )


def test_indicators_reject_empty_mixed_or_duplicate_series() -> None:
    bars = _bars()
    with pytest.raises(IndicatorError, match="at least one"):
        calculate_technical_snapshot((), analysis_timestamp=bars[-1].available_at)
    with pytest.raises(IndicatorError, match="one instrument"):
        calculate_technical_snapshot(
            (bars[0], bars[1].model_copy(update={"instrument_id": uuid4()})),
            analysis_timestamp=bars[-1].available_at,
        )
    with pytest.raises(IndicatorError, match="duplicate"):
        calculate_technical_snapshot(
            (bars[0], bars[0]), analysis_timestamp=bars[-1].available_at
        )


def test_short_and_declining_series_have_explicit_indicator_results() -> None:
    short = _bars()[:10]
    short_snapshot = calculate_technical_snapshot(
        short, analysis_timestamp=short[-1].available_at
    )
    assert short_snapshot.indicators["rsi_14"] is None

    bars = tuple(reversed(_bars()[:15]))
    declining = tuple(
        bar.model_copy(update={"close": float(200 - index)})
        for index, bar in enumerate(reversed(bars))
    )
    snapshot = calculate_technical_snapshot(
        declining,
        analysis_timestamp=max(bar.available_at for bar in declining),
    )
    assert snapshot.indicators["sma_20"] is None
    assert snapshot.indicators["realized_volatility_20"] is None
    assert snapshot.indicators["trend_slope_20"] is None
    assert snapshot.indicators["rsi_14"] == 0


def test_flat_short_series_has_neutral_rsi() -> None:
    bars = tuple(bar.model_copy(update={"close": 100.0}) for bar in _bars()[:15])
    snapshot = calculate_technical_snapshot(
        bars, analysis_timestamp=bars[-1].available_at
    )
    assert snapshot.indicators["rsi_14"] == 50
