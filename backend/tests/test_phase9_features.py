"""Strict features require historical membership and point-in-time price inputs."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.contracts.evaluation import (
    DataQualityStatus,
    ProviderQualityReport,
    ReplayIntegrityLevel,
)
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.quality import ProviderQualityError
from backend.app.strategy import (
    BacktestRiskPolicy,
    SignalSide,
    StrictBacktestInput,
    StrictInputError,
    build_strict_features,
    run_strict_backtest,
)

START = datetime(2020, 1, 1, tzinfo=UTC)


def _quality(name: str, status: DataQualityStatus = DataQualityStatus.VERIFIED
             ) -> ProviderQualityReport:
    return ProviderQualityReport(
        provider=name, provider_version="fixture-v1", evaluated_at=START,
        golden_case_count=1, passed_case_count=1, coverage=1, quality_status=status,
    )


def _input() -> StrictBacktestInput:
    instrument_id = uuid4()
    closes = (100.0, 102.0, 104.0, 53.0, 55.0)
    bars = tuple(
        MarketBar(
            instrument_id=instrument_id, symbol="TEST",
            timestamp=START + timedelta(days=index),
            open=close, high=close, low=close, close=close, volume=1000,
            adjustment_mode=PriceAdjustmentMode.RAW, adjustment_factor=1,
            source="fixture-market", observed_at=START + timedelta(days=index),
            available_at=START + timedelta(days=index, hours=1),
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="fixture-v1",
        )
        for index, close in enumerate(closes)
    )
    split = CorporateAction(
        instrument_id=instrument_id, action_type=CorporateActionType.SPLIT,
        effective_at=START + timedelta(days=3),
        available_at=START + timedelta(days=2), ratio=2,
        source="fixture-actions", provider_quality_version="fixture-v1",
    )
    return StrictBacktestInput(
        instrument_id=instrument_id, universe_as_of=START,
        universe_instrument_ids=(instrument_id,), bars=bars,
        corporate_actions=(split,), market_quality=_quality("fixture-market"),
        corporate_action_quality=_quality("fixture-actions"),
    )


def test_features_use_only_actions_visible_at_each_bar() -> None:
    data = _input()
    features = build_strict_features(data)
    assert len(features) == 3
    assert features[0].bar_timestamp == data.bars[2].timestamp
    assert features[0].close == 104
    assert features[0].price_adjustment_mode is PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED
    assert features[1].close == 53
    assert features[1].slow_mean == pytest.approx((51 + 52 + 53) / 3)


def test_strict_input_rejects_unqualified_and_late_information() -> None:
    data = _input()
    with pytest.raises(ProviderQualityError):
        build_strict_features(data.model_copy(update={
            "market_quality": _quality("fixture-market", DataQualityStatus.DEGRADED),
        }))
    with pytest.raises(ValueError, match="historical universe"):
        StrictBacktestInput.model_validate(data.model_dump() | {
            "universe_as_of": START + timedelta(days=1),
            "universe_instrument_ids": (uuid4(),),
        })
    with pytest.raises(StrictInputError, match="historical universe"):
        build_strict_features(data.model_copy(update={
            "universe_as_of": START + timedelta(days=1),
        }))
    with pytest.raises(StrictInputError, match="effective time"):
        build_strict_features(data.model_copy(update={
            "corporate_actions": (
                data.corporate_actions[0].model_copy(update={
                    "available_at": START + timedelta(days=4),
                }),
            ),
        }))
    with pytest.raises(StrictInputError, match="duplicate corporate actions"):
        build_strict_features(data.model_copy(update={
            "corporate_actions": (*data.corporate_actions, data.corporate_actions[0]),
        }))
    with pytest.raises(ValueError, match="strict quant"):
        StrictBacktestInput.model_validate(data.model_dump() | {
            "replay_integrity_level": ReplayIntegrityLevel.RESEARCH_REPLAY,
        })


def test_strict_backtest_trades_next_raw_open_with_costs_and_position_limit() -> None:
    data = _input()
    result = run_strict_backtest(data, risk=BacktestRiskPolicy(
        initial_cash=1000, max_position_fraction=0.25,
        commission_fraction=0.01, slippage_bps=100,
    ))
    assert result.replay_integrity_level is ReplayIntegrityLevel.STRICT_QUANT_BACKTEST
    assert result.signals[0].generated_at == data.bars[2].available_at
    assert result.trades[0].executed_at == data.bars[3].timestamp
    assert result.trades[0].signal_generated_at < result.trades[0].executed_at
    assert result.trades[0].side is SignalSide.BUY
    assert result.trades[0].raw_price == 53
    assert result.trades[0].execution_price == pytest.approx(53.53)
    assert result.nav[3].shares * result.trades[0].execution_price <= 250
    assert result.metrics.commission_paid > 0
    assert result.metrics.trade_count == len(result.trades)
    assert result.metrics.max_drawdown >= 0


def test_risk_kill_switch_blocks_new_positions() -> None:
    result = run_strict_backtest(
        _input(), risk=BacktestRiskPolicy(kill_switch=True)
    )
    assert result.trades == ()
    assert result.risk_blocked


def test_position_accounting_applies_split_and_cash_dividend() -> None:
    data = _input()
    split = CorporateAction(
        instrument_id=data.instrument_id, action_type=CorporateActionType.SPLIT,
        effective_at=START + timedelta(days=4),
        available_at=START + timedelta(days=3), ratio=2,
        source="fixture-actions", provider_quality_version="fixture-v1",
    )
    dividend = CorporateAction(
        instrument_id=data.instrument_id, action_type=CorporateActionType.CASH_DIVIDEND,
        effective_at=START + timedelta(days=4),
        available_at=START + timedelta(days=3), cash_amount=1, currency="USD",
        source="fixture-actions", provider_quality_version="fixture-v1",
    )
    final_bar = data.bars[-1].model_copy(update={
        "open": 27.5, "high": 27.5, "low": 27.5, "close": 27.5,
    })
    data = data.model_copy(update={
        "bars": (*data.bars[:-1], final_bar),
        "corporate_actions": (*data.corporate_actions, dividend, split),
    })
    result = run_strict_backtest(data, risk=BacktestRiskPolicy())
    assert result.nav[3].shares > 0
    assert result.nav[4].shares == pytest.approx(result.nav[3].shares * 2)
    assert result.nav[4].cash == pytest.approx(
        result.nav[3].cash + result.nav[4].shares
    )
