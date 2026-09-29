# Gate F — Strict Backtest (offline qualification)

Date: 2026-09-29. Scope: deterministic single-instrument long-or-cash fixtures.

| Gate F condition | Evidence | Result |
| --- | --- | --- |
| No current-LLM historical signal regeneration | The strict backtester accepts only timestamped market bars, corporate actions, historical universe membership, and qualified provider reports. `StrategySignal` is produced by a deterministic moving-average rule. Research Replay and other integrity levels are rejected. | Pass in code and fixtures |
| Point-in-time bars and features | Every feature is calculated at a bar's availability cutoff from only then-visible bars and corporate actions. Signals execute no earlier than the following raw open. | Pass |
| Point-in-time universe | Instrument membership must be present in a snapshot timestamped no later than the test start. | Pass |
| Corporate-action and price awareness | Raw prices are used for execution; feature prices are explicitly point-in-time adjusted. Held shares and cash account for qualified splits and dividends. Unsupported lifecycle changes fail closed. | Pass in restricted fixture universe |
| Quality and risk gates | Market and action qualification must pass. The pre-trade boundary blocks unsuitable QualityGate states, stale signals, loss/drawdown breaches, duplicate intents, low liquidity, price deviation, closed hours, and kill switch. | Pass |

These fixtures do not establish provider completeness for a live universe, actual
historical LLM performance, execution quality, or broker integration. No current
LLM is invoked in the strict path.
