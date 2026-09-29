"""Trade intent stays outside broker execution and respects hard risk gates."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.app.contracts.evaluation import QualityGateDecision
from backend.app.strategy import (
    PortfolioSnapshot,
    RiskDisposition,
    SignalSide,
    StrategySignal,
    TradeRiskPolicy,
    assess_trade_intent,
)

NOW = datetime(2020, 1, 2, 15, 0, tzinfo=UTC)


def _assessment(**changes: object):
    values = {
        "instrument_id": uuid4(),
        "signal": StrategySignal(
            bar_timestamp=NOW - timedelta(days=1),
            generated_at=NOW - timedelta(hours=1),
            side=SignalSide.BUY, target_fraction=1, feature_version="strict-sma-v1",
        ),
        "portfolio": PortfolioSnapshot(
            as_of=NOW - timedelta(minutes=1), cash=1000,
            net_asset_value=1000, current_position_value=0,
            total_exposure_value=0, daily_pnl=0, drawdown_fraction=0,
        ),
        "quality_gate": QualityGateDecision.PUBLISHABLE,
        "quote_price": 100.0,
        "quote_reference_price": 100.0,
        "quote_volume": 10_000.0,
        "now": NOW,
        "policy": TradeRiskPolicy(),
    }
    values.update(changes)
    return assess_trade_intent(**values)  # type: ignore[arg-type]


def test_trade_intent_is_bounded_and_requires_external_authorization() -> None:
    assessment = _assessment()
    assert assessment.disposition is RiskDisposition.ALLOWED
    assert assessment.intent is not None
    assert assessment.intent.target_notional == 100
    assert assessment.intent.requires_external_authorization
    assert not hasattr(assessment.intent, "broker_order_id")


def test_risk_hard_gates_block_strategy_input() -> None:
    assert _assessment(quality_gate=QualityGateDecision.INSUFFICIENT).disposition is (
        RiskDisposition.BLOCKED
    )
    assert _assessment(policy=TradeRiskPolicy(kill_switch=True)).disposition is (
        RiskDisposition.BLOCKED
    )
    assert _assessment(portfolio=PortfolioSnapshot(
        as_of=NOW - timedelta(minutes=1), cash=1000, net_asset_value=1000,
        current_position_value=0, total_exposure_value=0, daily_pnl=-100,
        drawdown_fraction=0, open_intent_exists=True,
    )).disposition is RiskDisposition.BLOCKED
    assert _assessment(quote_price=110).disposition is RiskDisposition.BLOCKED
    assert _assessment(now=NOW + timedelta(hours=8)).disposition is RiskDisposition.BLOCKED
    assert _assessment(now=NOW + timedelta(days=2)).disposition is RiskDisposition.BLOCKED


def test_no_action_on_watch_or_full_position() -> None:
    signal = StrategySignal(
        bar_timestamp=NOW - timedelta(days=1),
        generated_at=NOW - timedelta(hours=1),
        side=SignalSide.WATCH, target_fraction=0, feature_version="strict-sma-v1",
    )
    assert _assessment(signal=signal).disposition is RiskDisposition.NO_ACTION
    assert _assessment(portfolio=PortfolioSnapshot(
        as_of=NOW - timedelta(minutes=1), cash=0, net_asset_value=1000,
        current_position_value=250, total_exposure_value=250,
        daily_pnl=0, drawdown_fraction=0,
    )).disposition is RiskDisposition.NO_ACTION
