"""Single-instrument, long-or-cash, deterministic strict PIT backtest."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from math import sqrt

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import ReplayIntegrityLevel
from backend.app.contracts.instrument import CorporateActionType
from backend.app.strategy.features import StrictBacktestInput, StrictFeature, build_strict_features


class SignalSide(StrEnum):
    BUY = "buy"
    SELL = "sell"
    WATCH = "watch"


class StrategySignal(ContractModel):
    bar_timestamp: datetime
    generated_at: datetime
    side: SignalSide
    target_fraction: float = Field(ge=0, le=1)
    feature_version: str
    deterministic: bool = True


class BacktestRiskPolicy(ContractModel):
    initial_cash: float = Field(default=100_000, gt=0)
    max_position_fraction: float = Field(default=0.25, gt=0, le=1)
    max_drawdown_fraction: float = Field(default=0.3, gt=0, le=1)
    commission_fraction: float = Field(default=0.001, ge=0, lt=1)
    slippage_bps: float = Field(default=5, ge=0, lt=10_000)
    minimum_bar_volume: float = Field(default=1, ge=0)
    kill_switch: bool = False


class BacktestTrade(ContractModel):
    executed_at: datetime
    side: SignalSide
    shares: float = Field(gt=0)
    raw_price: float = Field(gt=0)
    execution_price: float = Field(gt=0)
    commission: float = Field(ge=0)
    signal_generated_at: datetime


class NavPoint(ContractModel):
    timestamp: datetime
    cash: float
    shares: float = Field(ge=0)
    nav: float = Field(ge=0)


class BacktestMetrics(ContractModel):
    total_return: float
    max_drawdown: float = Field(ge=0, le=1)
    volatility_per_bar: float | None = None
    trade_count: int = Field(ge=0)
    commission_paid: float = Field(ge=0)


class StrictBacktestResult(ContractModel):
    replay_integrity_level: ReplayIntegrityLevel
    signals: tuple[StrategySignal, ...]
    trades: tuple[BacktestTrade, ...]
    nav: tuple[NavPoint, ...]
    metrics: BacktestMetrics
    risk_blocked: bool


def make_strategy_signals(features: tuple[StrictFeature, ...]) -> tuple[StrategySignal, ...]:
    """A deterministic trend rule; no model call or historical regeneration."""

    return tuple(
        StrategySignal(
            bar_timestamp=feature.bar_timestamp,
            generated_at=feature.as_of,
            side=SignalSide.BUY if feature.fast_mean > feature.slow_mean else SignalSide.SELL,
            target_fraction=1 if feature.fast_mean > feature.slow_mean else 0,
            feature_version=feature.feature_version,
        )
        for feature in features
    )


def run_strict_backtest(
    data: StrictBacktestInput,
    *,
    risk: BacktestRiskPolicy,
    fast_window: int = 2,
    slow_window: int = 3,
) -> StrictBacktestResult:
    """Trade at the following raw open, after the prior feature became available."""

    signals = make_strategy_signals(
        build_strict_features(data, fast_window=fast_window, slow_window=slow_window)
    )
    by_bar = {signal.bar_timestamp: signal for signal in signals}
    cash = risk.initial_cash
    shares = 0.0
    commission_paid = 0.0
    peak = cash
    blocked = risk.kill_switch
    risk_trigger_at: datetime | None = None
    trades: list[BacktestTrade] = []
    nav: list[NavPoint] = []
    prior_bar_at: datetime | None = None
    pending: StrategySignal | None = None
    ordered_actions = sorted(
        data.corporate_actions,
        key=lambda item: (
            item.effective_at,
            0 if item.action_type in {
                CorporateActionType.SPLIT, CorporateActionType.REVERSE_SPLIT
            } else 1,
        ),
    )
    for bar in data.bars:
        for action in ordered_actions:
            if (
                (prior_bar_at is None or prior_bar_at < action.effective_at)
                and action.effective_at <= bar.timestamp
            ):
                if action.action_type in {
                    CorporateActionType.SPLIT, CorporateActionType.REVERSE_SPLIT
                }:
                    if action.ratio is None:
                        raise ValueError("split ratio is missing")
                    shares *= action.ratio
                elif action.action_type is CorporateActionType.CASH_DIVIDEND:
                    if action.cash_amount is None:
                        raise ValueError("cash dividend amount is missing")
                    cash += shares * action.cash_amount
        signal_ready = pending is not None and pending.generated_at < bar.timestamp
        risk_exit_ready = (
            blocked and shares > 0 and risk_trigger_at is not None
            and risk_trigger_at < bar.timestamp
        )
        if signal_ready or risk_exit_ready:
            if bar.volume < risk.minimum_bar_volume:
                blocked = True
            elif (
                signal_ready and pending is not None
                and pending.side is SignalSide.BUY and not blocked and shares == 0
            ):
                execution_price = bar.open * (1 + risk.slippage_bps / 10_000)
                allocation = min(cash, (cash + shares * bar.open) * risk.max_position_fraction)
                bought = allocation / (execution_price * (1 + risk.commission_fraction))
                if bought > 0:
                    fee = bought * execution_price * risk.commission_fraction
                    cash -= bought * execution_price + fee
                    shares += bought
                    commission_paid += fee
                    trades.append(BacktestTrade(
                        executed_at=bar.timestamp, side=SignalSide.BUY, shares=bought,
                        raw_price=bar.open, execution_price=execution_price,
                        commission=fee, signal_generated_at=pending.generated_at,
                    ))
            elif (
                (signal_ready and pending is not None and pending.side is SignalSide.SELL)
                or risk_exit_ready
            ) and shares > 0:
                execution_price = bar.open * (1 - risk.slippage_bps / 10_000)
                sold = shares
                fee = sold * execution_price * risk.commission_fraction
                cash += sold * execution_price - fee
                shares = 0
                commission_paid += fee
                trades.append(BacktestTrade(
                    executed_at=bar.timestamp, side=SignalSide.SELL, shares=sold,
                    raw_price=bar.open, execution_price=execution_price,
                    commission=fee,
                    signal_generated_at=(
                        risk_trigger_at if risk_exit_ready and risk_trigger_at is not None
                        else pending.generated_at  # type: ignore[union-attr]
                    ),
                ))
        value = cash + shares * bar.close
        peak = max(peak, value)
        if 1 - value / peak > risk.max_drawdown_fraction:
            blocked = True
            risk_trigger_at = bar.available_at
        nav.append(NavPoint(timestamp=bar.timestamp, cash=cash, shares=shares, nav=value))
        pending = by_bar.get(bar.timestamp)
        prior_bar_at = bar.timestamp
    values = [point.nav for point in nav]
    returns = [values[index] / values[index - 1] - 1 for index in range(1, len(values))]
    mean = sum(returns) / len(returns) if returns else 0
    volatility = (
        sqrt(sum((item - mean) ** 2 for item in returns) / (len(returns) - 1))
        if len(returns) > 1 else None
    )
    running_peak = values[0]
    max_drawdown = 0.0
    for value in values:
        running_peak = max(running_peak, value)
        max_drawdown = max(max_drawdown, 1 - value / running_peak)
    return StrictBacktestResult(
        replay_integrity_level=ReplayIntegrityLevel.STRICT_QUANT_BACKTEST,
        signals=signals,
        trades=tuple(trades),
        nav=tuple(nav),
        metrics=BacktestMetrics(
            total_return=values[-1] / risk.initial_cash - 1,
            max_drawdown=max_drawdown,
            volatility_per_bar=volatility,
            trade_count=len(trades),
            commission_paid=commission_paid,
        ),
        risk_blocked=blocked,
    )
