# Gate E — Replay Integrity (offline qualification)

Date: 2026-09-28. Scope: local contract, SQLite, worker-composition, and fixture tests.
No real model, live market data, or live document service was used.

| Gate E condition | Evidence | Result |
| --- | --- | --- |
| Replay mode explicit | `ResearchSubmission` requires `replay_integrity_level`; research accepts only Research Replay or Evidence-Constrained Replay; `ResearchState` also rejects strict and forward modes | Pass |
| Parametric risk metadata present | Submission derives `parametric_lookahead_risk=true` for historical Research Replay cutoffs relative to `requested_at` and for every Evidence-Constrained Replay; state validation requires it and persistence retains the value | Pass |
| Evidence time filters correct | Persisted replay queries observed, available, and published times at or before cutoff; adapter rechecks them and rejects later or foreign evidence and market snapshots | Pass |
| Research Replay differs from Strict Quant Backtest | Strict mode cannot enter the LLM research workflow; Research Replay may use the current LLM and carries historical risk. Phase 9 owns strict quant backtesting. | Pass |

The constrained worker path reads only immutable persisted evidence and does not build
live market or RAG adapters. Missing exact-cutoff market evidence yields an evidence
gap, not a fabricated snapshot. Tests use saved fixtures; the result is an offline
Gate E qualification and does not establish strict historical LLM Alpha performance.
