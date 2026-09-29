"""Deterministic pre-trade policy that emits intent, never broker orders."""

from __future__ import annotations

from datetime import UTC, datetime, time
from enum import StrEnum
from math import isfinite
from uuid import UUID

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import QualityGateDecision
from backend.app.strategy.backtest import SignalSide, StrategySignal


class RiskDisposition(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NO_ACTION = "no_action"


class PortfolioSnapshot(ContractModel):
    as_of: datetime
    cash: float = Field(ge=0)
    net_asset_value: float = Field(gt=0)
    current_position_value: float = Field(ge=0)
    total_exposure_value: float = Field(ge=0)
    daily_pnl: float
    drawdown_fraction: float = Field(ge=0, le=1)
    open_intent_exists: bool = False


class TradeRiskPolicy(ContractModel):
    max_position_fraction: float = Field(default=0.25, gt=0, le=1)
    max_portfolio_exposure_fraction: float = Field(default=0.8, gt=0, le=1)
    max_trade_fraction: float = Field(default=0.1, gt=0, le=1)
    max_daily_loss_fraction: float = Field(default=0.05, gt=0, le=1)
    max_drawdown_fraction: float = Field(default=0.3, gt=0, le=1)
    min_quote_volume: float = Field(default=1000, ge=0)
    max_price_deviation_fraction: float = Field(default=0.05, ge=0, lt=1)
    max_signal_age_seconds: int = Field(default=86_400, ge=1)
    trading_start_utc: time = time(14, 30)
    trading_end_utc: time = time(21, 0)
    kill_switch: bool = False

    @model_validator(mode="after")
    def validate_session(self) -> TradeRiskPolicy:
        if self.trading_start_utc.tzinfo is not None or self.trading_end_utc.tzinfo is not None:
            raise ValueError("trading session boundaries must be plain UTC times")
        if self.trading_start_utc >= self.trading_end_utc:
            raise ValueError("trading session must have a positive UTC interval")
        return self


class TradeIntent(ContractModel):
    instrument_id: UUID
    created_at: datetime
    side: SignalSide
    target_notional: float = Field(gt=0)
    reference_price: float = Field(gt=0)
    signal_generated_at: datetime
    requires_external_authorization: bool = True


class TradeRiskAssessment(ContractModel):
    disposition: RiskDisposition
    reasons: tuple[str, ...]
    intent: TradeIntent | None = None


def assess_trade_intent(
    *,
    instrument_id: UUID,
    signal: StrategySignal,
    portfolio: PortfolioSnapshot,
    quality_gate: QualityGateDecision,
    quote_price: float,
    quote_reference_price: float,
    quote_volume: float,
    now: datetime,
    policy: TradeRiskPolicy,
) -> TradeRiskAssessment:
    """Apply structural checks and return a non-executable, bounded intent."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("risk clock must be timezone-aware")
    if portfolio.as_of.tzinfo is None or portfolio.as_of.utcoffset() is None:
        raise ValueError("portfolio timestamp must be timezone-aware")
    if signal.generated_at.tzinfo is None or signal.generated_at.utcoffset() is None:
        raise ValueError("signal timestamp must be timezone-aware")
    if (
        not all(isfinite(value) for value in (quote_price, quote_reference_price, quote_volume))
        or quote_price <= 0 or quote_reference_price <= 0 or quote_volume < 0
    ):
        raise ValueError("quote price and volume must be valid")
    if signal.generated_at > portfolio.as_of or portfolio.as_of > now:
        return TradeRiskAssessment(
            disposition=RiskDisposition.BLOCKED, reasons=("future-dated signal or portfolio",)
        )
    now_utc = now.astimezone(UTC)
    reasons: list[str] = []
    if not signal.deterministic:
        reasons.append("unqualified nondeterministic signal")
    if (now - signal.generated_at).total_seconds() > policy.max_signal_age_seconds:
        reasons.append("signal is stale")
    if policy.kill_switch:
        reasons.append("kill switch active")
    if quality_gate is not QualityGateDecision.PUBLISHABLE:
        reasons.append("quality gate does not permit strategy input")
    if portfolio.open_intent_exists:
        reasons.append("duplicate open intent")
    if portfolio.daily_pnl < -portfolio.net_asset_value * policy.max_daily_loss_fraction:
        reasons.append("daily loss limit exceeded")
    if portfolio.drawdown_fraction > policy.max_drawdown_fraction:
        reasons.append("drawdown limit exceeded")
    if not policy.trading_start_utc <= now_utc.time() < policy.trading_end_utc:
        reasons.append("outside configured UTC trading session")
    if quote_volume < policy.min_quote_volume:
        reasons.append("quote liquidity below minimum")
    if abs(quote_price / quote_reference_price - 1) > policy.max_price_deviation_fraction:
        reasons.append("quote price deviation exceeded")
    if reasons:
        return TradeRiskAssessment(disposition=RiskDisposition.BLOCKED, reasons=tuple(reasons))
    if signal.side is SignalSide.WATCH:
        return TradeRiskAssessment(
            disposition=RiskDisposition.NO_ACTION, reasons=("watch signal",)
        )
    if signal.side is SignalSide.SELL:
        amount = portfolio.current_position_value
    else:
        amount = min(
            portfolio.cash,
            portfolio.net_asset_value * policy.max_trade_fraction,
            portfolio.net_asset_value * policy.max_position_fraction
            - portfolio.current_position_value,
            portfolio.net_asset_value * policy.max_portfolio_exposure_fraction
            - portfolio.total_exposure_value,
        )
    if amount <= 0:
        return TradeRiskAssessment(
            disposition=RiskDisposition.NO_ACTION,
            reasons=("no permitted position change",),
        )
    return TradeRiskAssessment(
        disposition=RiskDisposition.ALLOWED,
        reasons=(),
        intent=TradeIntent(
            instrument_id=instrument_id,
            created_at=now,
            side=signal.side,
            target_notional=amount,
            reference_price=quote_price,
            signal_generated_at=signal.generated_at,
        ),
    )
