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

## Remaining slices

- Deterministic StrategySignal and next-bar strict PIT backtester with costs,
  corporate-action accounting, and reproducible metrics.
- Deterministic risk policy and non-executable TradeIntent boundary.
- Gate F adversarial tests, PostgreSQL integration where relevant, one whole-phase
  code review, and then a single Phase 9 push.
