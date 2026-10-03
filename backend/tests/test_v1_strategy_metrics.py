"""Strategy statistic goldens, action accounting and benchmark admission."""

from datetime import timedelta
from math import sqrt

import pytest

from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.instrument import CorporateAction, CorporateActionType
from backend.app.market_data.quality import ProviderQualityError
from backend.app.strategy.backtest import (
    BacktestBenchmark,
    BacktestMetricPolicy,
    BacktestRiskPolicy,
    BacktestTrade,
    BenchmarkPoint,
    NavPoint,
    SignalSide,
    StrictBacktestResult,
    _calculate_metrics,
    run_strict_backtest,
)
from backend.tests.test_phase9_features import START, _input, _quality


def test_metric_formulas_against_hand_calculated_values() -> None:
    values = [1000.0, 1100.0, 990.0, 1188.0]
    nav = [NavPoint(timestamp=START+timedelta(days=index*365.25/3),
                    cash=value, shares=0, nav=value) for index, value in enumerate(values)]
    trades = [BacktestTrade(executed_at=nav[index+1].timestamp, side=side, shares=1,
                           raw_price=raw, execution_price=execution, commission=10,
                           signal_generated_at=START)
              for index, (side, raw, execution) in enumerate([
                  (SignalSide.BUY, 100.0, 101.0), (SignalSide.SELL, 110.0, 109.0),
              ])]
    result = _calculate_metrics(nav, trades, 1000, 20, [100, -50, 0],
                                BacktestMetricPolicy(periods_per_year=4,
                                                     risk_free_annual_return=0), None)
    assert result.total_return == pytest.approx(0.188)
    assert result.cagr == pytest.approx(0.188)
    assert result.max_drawdown == pytest.approx(0.1)
    assert result.volatility_per_bar == pytest.approx(sqrt(7/300))
    assert result.sharpe == pytest.approx((1/15)/sqrt(7/300)*2)
    assert result.sortino == pytest.approx((1/15)/sqrt(1/300)*2)
    assert result.closed_trade_count == 3 and result.hit_rate == pytest.approx(1/3)
    assert result.profit_factor == 2 and result.average_win == 100 and result.average_loss == -50
    assert result.turnover == pytest.approx(210/(sum(values)/4))
    assert result.slippage == 2 and result.transaction_cost == 22


def benchmark() -> BacktestBenchmark:
    data = _input()
    return BacktestBenchmark(
        benchmark_id="fixture-total-return-index", source="fixture-benchmark",
        source_version="fixture-v1", quality=_quality("fixture-benchmark"),
        points=tuple(BenchmarkPoint(timestamp=bar.timestamp, available_at=bar.available_at,
                                    total_return_value=100.0+index)
                     for index, bar in enumerate(data.bars)),
    )


def test_public_backtest_exposes_configured_benchmark_and_open_position_limits() -> None:
    result = run_strict_backtest(_input(), risk=BacktestRiskPolicy(
        initial_cash=1000, commission_fraction=0.01, slippage_bps=100,
    ), metric_policy=BacktestMetricPolicy(periods_per_year=252, risk_free_annual_return=0),
        benchmark=benchmark())
    assert result.metric_policy.periods_per_year == 252
    assert result.benchmark_id == "fixture-total-return-index"
    assert result.metrics.benchmark_total_return == pytest.approx(0.04)
    assert result.metrics.benchmark_excess_return == pytest.approx(result.metrics.total_return-0.04)
    assert result.metrics.closed_trade_count == 0 and result.metrics.hit_rate is None
    assert result.metrics.profit_factor is None and result.closed_trade_pnl == ()
    assert result.metrics.slippage > 0
    assert result.metrics.transaction_cost == pytest.approx(
        result.metrics.commission_paid+result.metrics.slippage
    )
    assert result.metrics.time_in_market == pytest.approx(2/5)
    expected_exposure = sum((point.nav-point.cash)/point.nav for point in result.nav)/5
    assert result.metrics.exposure == pytest.approx(expected_exposure)
    assert StrictBacktestResult.model_validate_json(result.model_dump_json()) == result


def test_closed_trade_profit_includes_split_dividend_and_all_costs() -> None:
    data = _input()
    second_split = CorporateAction(
        instrument_id=data.instrument_id, action_type=CorporateActionType.SPLIT,
        effective_at=START+timedelta(days=4), available_at=START+timedelta(days=3), ratio=2,
        source="fixture-actions", provider_quality_version="fixture-v1",
    )
    dividend = CorporateAction(
        instrument_id=data.instrument_id, action_type=CorporateActionType.CASH_DIVIDEND,
        effective_at=START+timedelta(days=4), available_at=START+timedelta(days=3),
        cash_amount=1, currency="USD", source="fixture-actions",
        provider_quality_version="fixture-v1",
    )
    final = data.bars[-1].model_copy(update=dict.fromkeys(("open", "high", "low", "close"), 27.5))
    extra = tuple(final.model_copy(update={
        "timestamp": START+timedelta(days=index), "observed_at": START+timedelta(days=index),
        "available_at": START+timedelta(days=index, hours=1),
        **dict.fromkeys(("open", "high", "low", "close"), 20.0),
    }) for index in (5, 6))
    data = data.model_copy(update={
        "bars": (*data.bars[:-1], final, *extra),
        "corporate_actions": (*data.corporate_actions, second_split, dividend),
    })
    result = run_strict_backtest(data, risk=BacktestRiskPolicy(
        initial_cash=1000, max_drawdown_fraction=1, commission_fraction=0.01, slippage_bps=100,
    ))
    assert len(result.trades) == 2 and result.metrics.closed_trade_count == 1
    bought, sold = result.trades
    assert sold.shares == pytest.approx(2*bought.shares)
    expected_pnl = (sold.shares*(sold.execution_price+1)-sold.commission
                    -bought.shares*bought.execution_price-bought.commission)
    assert result.closed_trade_pnl[0] == pytest.approx(expected_pnl)
    assert result.nav[-1].cash == pytest.approx(1000+expected_pnl)
    assert result.metrics.average_loss == pytest.approx(expected_pnl)
    assert result.metrics.hit_rate == 0 and result.metrics.profit_factor == 0


def test_cash_strategy_has_explicit_undefined_statistics() -> None:
    result = run_strict_backtest(_input(), risk=BacktestRiskPolicy(kill_switch=True))
    assert result.metrics.total_return == 0 and result.metrics.cagr == 0
    assert result.metrics.sharpe is None and result.metrics.sortino is None
    assert result.metrics.exposure == 0 and result.metrics.time_in_market == 0
    assert result.metrics.benchmark_excess_return is None
    assert "annualization_frequency_not_configured" in result.metrics.unavailable_reasons
    configured = run_strict_backtest(_input(), risk=BacktestRiskPolicy(kill_switch=True),
                                     metric_policy=BacktestMetricPolicy(
                                         periods_per_year=252, risk_free_annual_return=0,
                                     ))
    assert "sharpe_zero_volatility" in configured.metrics.unavailable_reasons
    assert "sortino_zero_downside" in configured.metrics.unavailable_reasons


def test_annualization_frequency_alone_does_not_assume_zero_risk_free_rate() -> None:
    result = run_strict_backtest(_input(), risk=BacktestRiskPolicy(),
                                metric_policy=BacktestMetricPolicy(periods_per_year=252))
    assert result.metrics.sharpe is None and result.metrics.sortino is None
    assert result.metric_policy.risk_free_annual_return is None
    assert "risk_free_rate_not_configured" in result.metrics.unavailable_reasons


@pytest.mark.parametrize("change,match", [
    ({"source": "unmatched"}, "provenance"),
    ({"points": benchmark().points[:-1]}, "align"),
    ({"points": (benchmark().points[0].model_copy(update={
        "available_at": START+timedelta(days=1),
    }), *benchmark().points[1:])}, "unavailable"),
])
def test_invalid_benchmark_fails_closed(change: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        run_strict_backtest(_input(), risk=BacktestRiskPolicy(),
                            benchmark=benchmark().model_copy(update=change))


def test_unqualified_benchmark_cannot_produce_excess_return() -> None:
    with pytest.raises(ProviderQualityError):
        run_strict_backtest(_input(), risk=BacktestRiskPolicy(), benchmark=benchmark().model_copy(
            update={"quality": _quality("fixture-benchmark", DataQualityStatus.UNVERIFIED)},
        ))
