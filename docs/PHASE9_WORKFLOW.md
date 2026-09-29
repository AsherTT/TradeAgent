# Phase 9 — Strategy and Strict Backtest

Phase 9 implements deterministic strategy history separately from Research Replay.
Gate F forbids generating historical LLM signals with a current model. A strict
historical LLM evaluation must use signals or ForecastRecords persisted at the time;
this phase begins with deterministic quant inputs instead.

## 1. Strict point-in-time feature input — implemented offline

`StrictBacktestInput` requires an instrument in a historical universe snapshot,
ordered raw execution bars, and complete provider-quality reports for market and
corporate-action data. The builder rejects unqualified providers, low-quality bars,
provenance mismatch, ambiguous prices, late corporate actions, and unsupported
symbol or lifecycle changes. At each decision cutoff it recomputes normalized
features using only bars and actions then visible. A fixture split confirms earlier
features do not use future adjustments. This is a deliberately restricted validated
universe, not a claim that a live provider has passed corporate-action qualification.

## 2. Deterministic signal and strict backtest — implemented offline

The first V1 rule emits a BUY signal when a short point-in-time moving average
exceeds a longer one, otherwise SELL. Signals are generated only after the input
bar becomes available; execution uses the following raw bar's open. The bounded
long-or-cash simulator records raw and executed prices, commissions, slippage,
cash, shares, NAV, total return, per-bar volatility, trade count, and maximum
drawdown. It adjusts held shares for splits and cash for dividends. A kill switch,
position fraction, volume floor, and drawdown cap form the backtest risk skeleton.
Offline fixtures verify the next-bar boundary, costs, position limit, split,
dividend, and default kill-switch behavior. This does not use a current LLM to
generate any historical signal.

## 3. Deterministic trade risk and intent — implemented offline

The pre-trade policy checks QualityGate, signal age and provenance, portfolio
timestamps, kill switch, duplicate intent, daily loss, drawdown, liquidity,
price deviation, and configured UTC trading hours. It caps notional by cash,
single-position, total-exposure, and per-trade limits. Its only positive output
is an immutable `TradeIntent` requiring external authorization; there is no
broker order, credential, or execution call. Offline tests cover allowed,
blocked, and no-action outcomes. See `docs/GATE_F_QUALIFICATION.md`.

## Remaining qualification

Run the single whole-phase code review, resolve findings, and then make one
Phase 9 push. All current tests are fixtures. A live provider and historical
LLM Alpha performance are not qualified by this phase.
