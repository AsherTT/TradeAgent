"""Independent formula goldens and PIT/integrity boundaries for V1 indicators."""

from datetime import timedelta
from math import sqrt

import pytest

from backend.app.contracts.market import MarketBar
from backend.app.quant.indicators import IndicatorError, calculate_technical_snapshot
from backend.tests.test_quant import _bars


def series(closes: list[float], volumes: list[float] | None = None) -> tuple[MarketBar, ...]:
    base = _bars()[0]
    return tuple(base.model_copy(update={
        "timestamp": base.timestamp+timedelta(days=index),
        "available_at": base.available_at+timedelta(days=index),
        "observed_at": base.observed_at+timedelta(days=index),
        "open": close, "high": close+1, "low": close-1, "close": close,
        "volume": volumes[index] if volumes else 1000.0,
    }) for index, close in enumerate(closes))


def test_ma_volume_distance_and_prior_range_goldens() -> None:
    bars = series([float(x) for x in range(100, 150)], [float(x) for x in range(1, 51)])
    result = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at)
    actual = result.indicators
    assert [actual[f"sma_{n}"] for n in (5, 10, 20, 50)] == [147, 144.5, 139.5, 124.5]
    assert actual["ema_20"] == pytest.approx(149-9.5*(1-(19/21)**49))
    assert actual["mavol_5"] == 48 and actual["mavol_10"] == 45.5
    assert actual["volume_ratio_5"] == pytest.approx(50/47)
    assert actual["distance_to_sma_20"] == pytest.approx(149/139.5-1)
    assert actual["support_20"] == 128 and actual["resistance_20"] == 149
    assert actual["trend_regime"] == "uptrend"


def test_macd_matches_closed_form_linear_series() -> None:
    bars = series([float(x) for x in range(100, 150)])
    def difference(index: int) -> float:
        return 12.5*(1-(25/27)**index)-5.5*(1-(11/13)**index)
    # Closed-form exponential weights, independently of pandas' recursive EWM.
    signal = (0.8**24)*difference(25)+sum(
        0.2*(0.8**(49-index))*difference(index) for index in range(26, 50)
    )
    actual = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at).indicators
    assert actual["macd"] == pytest.approx(difference(49))
    assert actual["macd_signal"] == pytest.approx(signal)
    assert actual["macd_histogram"] == pytest.approx(difference(49)-signal)


def test_rsi_wilder_initialization_and_following_step() -> None:
    prices = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
              45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00]
    bars = series(prices)
    initial = calculate_technical_snapshot(bars[:-1], analysis_timestamp=bars[-2].available_at)
    following = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at)
    assert initial.indicators["rsi_14"] == pytest.approx(70.464135021097, abs=1e-10)
    assert following.indicators["rsi_14"] == pytest.approx(66.249618553556, abs=1e-10)


def test_atr_accounts_for_gap_and_wilder_smoothing() -> None:
    bars = series([100.0]*14+[110.0])
    initial = calculate_technical_snapshot(bars[:-1], analysis_timestamp=bars[-2].available_at)
    following = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at)
    assert initial.indicators["atr_14"] == 2
    assert following.indicators["atr_14"] == pytest.approx(37/14)


@pytest.mark.parametrize("closes,regime,rsi", [
    ([100.0]*50, "range", 50), ([float(x) for x in range(150, 100, -1)], "downtrend", 0),
])
def test_flat_and_declining_regimes(closes: list[float], regime: str, rsi: int) -> None:
    bars = series(closes)
    actual = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at).indicators
    assert actual["trend_regime"] == regime and actual["rsi_14"] == rsi


def test_short_window_zero_volume_and_explicit_annualization() -> None:
    bars = series([float(x) for x in range(100, 125)], [0.0]*25)
    actual = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at)
    annual = calculate_technical_snapshot(bars, analysis_timestamp=bars[-1].available_at,
                                          periods_per_year=12)
    assert actual.indicators["sma_50"] is None
    assert actual.indicators["macd"] is None and actual.indicators["trend_regime"] is None
    assert actual.indicators["volume_ratio_5"] is None
    assert actual.indicators["realized_volatility_20"] is None
    assert annual.indicators["realized_volatility_20"] == pytest.approx(
        actual.indicators["historical_volatility_20"]*sqrt(12)
    )
    short = calculate_technical_snapshot(bars[:5], analysis_timestamp=bars[4].available_at)
    for key in ("rsi_14", "atr_14", "ema_20", "volume_ratio_5", "support_20", "macd_signal"):
        assert short.indicators[key] is None


def test_future_observation_is_excluded_even_if_available_time_is_forged() -> None:
    bars = series([100.0]*25)
    changed = bars[-1].model_copy(update={"observed_at": bars[-1].available_at+timedelta(days=1)})
    actual = calculate_technical_snapshot((*bars[:-1], changed),
                                          analysis_timestamp=bars[-1].available_at)
    assert actual.metadata["bar_count"] == 24


@pytest.mark.parametrize("update", [{"high": float("inf")}, {"volume": float("nan")},
                                    {"close": 0.0}, {"high": 1.0}])
def test_invalid_numeric_values_fail_closed(update: dict[str, float]) -> None:
    bars = series([100.0]*25)
    with pytest.raises(IndicatorError, match="OHLCV"):
        calculate_technical_snapshot((bars[0].model_copy(update=update),),
                                     analysis_timestamp=bars[-1].available_at)
