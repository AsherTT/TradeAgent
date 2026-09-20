"""Pure deterministic corporate-action price normalization."""

from __future__ import annotations

from datetime import datetime

from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar


class PriceNormalizationError(ValueError):
    """Raised when prices cannot be normalized without ambiguity."""


_SPLIT_TYPES = {CorporateActionType.SPLIT, CorporateActionType.REVERSE_SPLIT}
_UNSUPPORTED_TYPES = {
    CorporateActionType.STOCK_DIVIDEND,
    CorporateActionType.MERGER,
    CorporateActionType.SPINOFF,
}


def normalize_prices(
    bars: tuple[MarketBar, ...],
    actions: tuple[CorporateAction, ...],
    *,
    mode: PriceAdjustmentMode,
    analysis_timestamp: datetime,
) -> tuple[MarketBar, ...]:
    """Normalize raw bars with only corporate actions knowable at analysis time."""

    visible_bars = tuple(
        sorted(
            (
                bar
                for bar in bars
                if bar.timestamp <= analysis_timestamp and bar.available_at <= analysis_timestamp
            ),
            key=lambda bar: bar.timestamp,
        )
    )
    if not visible_bars:
        return ()
    if any(bar.adjustment_mode is not PriceAdjustmentMode.RAW for bar in visible_bars):
        raise PriceNormalizationError("normalization requires unambiguous RAW provider bars")
    instrument_id = visible_bars[0].instrument_id
    if any(bar.instrument_id != instrument_id for bar in visible_bars):
        raise PriceNormalizationError("all bars must belong to one instrument")
    if len({bar.timestamp for bar in visible_bars}) != len(visible_bars):
        raise PriceNormalizationError("duplicate market-bar timestamps are not allowed")

    visible_actions = _deduplicate_actions(
        tuple(
            action
            for action in actions
            if action.instrument_id == instrument_id
            and action.available_at <= analysis_timestamp
            and action.effective_at <= analysis_timestamp
        )
    )
    _validate_supported_actions(visible_actions, mode)
    _validate_delisting(visible_bars, visible_actions)

    if mode is PriceAdjustmentMode.RAW:
        return visible_bars

    result: list[MarketBar] = []
    for bar in visible_bars:
        price_factor = 1.0
        volume_factor = 1.0
        for action in visible_actions:
            if bar.timestamp >= action.effective_at:
                continue
            if action.action_type in _SPLIT_TYPES:
                ratio = _split_ratio(action)
                price_factor /= ratio
                volume_factor *= ratio
            elif action.action_type is CorporateActionType.CASH_DIVIDEND and mode in {
                PriceAdjustmentMode.TOTAL_RETURN,
                PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            }:
                price_factor *= _dividend_factor(visible_bars, visible_actions, action)

        result.append(
            bar.model_copy(
                update={
                    "open": bar.open * price_factor,
                    "high": bar.high * price_factor,
                    "low": bar.low * price_factor,
                    "close": bar.close * price_factor,
                    "volume": bar.volume * volume_factor,
                    "adjustment_mode": mode,
                    "adjustment_factor": price_factor,
                }
            )
        )
    return tuple(result)


def _deduplicate_actions(actions: tuple[CorporateAction, ...]) -> tuple[CorporateAction, ...]:
    by_id: dict[object, CorporateAction] = {}
    for action in actions:
        previous = by_id.get(action.action_id)
        if previous is not None and previous != action:
            raise PriceNormalizationError(f"conflicting duplicate action {action.action_id}")
        by_id[action.action_id] = action
    by_event: dict[tuple[object, ...], CorporateAction] = {}
    for action in by_id.values():
        event_key = (
            action.instrument_id,
            action.action_type,
            action.effective_at,
            action.ex_date,
            action.ratio,
            action.cash_amount,
            action.currency,
        )
        current = by_event.get(event_key)
        if current is None or (action.available_at, str(action.action_id)) < (
            current.available_at,
            str(current.action_id),
        ):
            by_event[event_key] = action
    return tuple(
        sorted(by_event.values(), key=lambda item: (item.effective_at, str(item.action_id)))
    )


def _validate_supported_actions(
    actions: tuple[CorporateAction, ...], mode: PriceAdjustmentMode
) -> None:
    if mode not in {
        PriceAdjustmentMode.TOTAL_RETURN,
        PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
    }:
        return
    unsupported = [action for action in actions if action.action_type in _UNSUPPORTED_TYPES]
    if unsupported:
        names = ", ".join(action.action_type.value for action in unsupported)
        raise PriceNormalizationError(
            f"unsupported corporate actions for price adjustment: {names}"
        )


def _validate_delisting(
    bars: tuple[MarketBar, ...], actions: tuple[CorporateAction, ...]
) -> None:
    delistings = [
        action.effective_at
        for action in actions
        if action.action_type is CorporateActionType.DELISTING
    ]
    if delistings and any(bar.timestamp > min(delistings) for bar in bars):
        raise PriceNormalizationError("market data contains a bar after delisting")


def _dividend_factor(
    bars: tuple[MarketBar, ...],
    actions: tuple[CorporateAction, ...],
    action: CorporateAction,
) -> float:
    prior = [bar for bar in bars if bar.timestamp < action.effective_at]
    if not prior or action.cash_amount is None:
        raise PriceNormalizationError(
            f"cash dividend {action.action_id} has no prior close for adjustment"
        )
    reference_close = prior[-1].close
    same_time_split_ratio = 1.0
    for peer in actions:
        if peer.effective_at == action.effective_at and peer.action_type in _SPLIT_TYPES:
            same_time_split_ratio *= _split_ratio(peer)
    reference_close /= same_time_split_ratio
    if action.cash_amount >= reference_close:
        raise PriceNormalizationError(
            f"cash dividend {action.action_id} is not smaller than its prior close"
        )
    return (reference_close - action.cash_amount) / reference_close


def _split_ratio(action: CorporateAction) -> float:
    if action.ratio is None:
        raise PriceNormalizationError(f"action {action.action_id} has no split ratio")
    return action.ratio
