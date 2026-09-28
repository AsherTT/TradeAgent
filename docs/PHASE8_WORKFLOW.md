# Phase 8 — Replay / Evaluation

Phase 8 implements the architecture's replay and evaluation layers in independently
verifiable slices. Gate E is the replay-integrity gate; Gate G separately covers forward
evaluation and statistical reliability.

## 1. Explicit research replay submission — implemented offline

`POST /research` requires `replay_integrity_level`. It accepts only
`research_replay` or `evidence_constrained_replay`; strict quant backtesting belongs
to Phase 9, and forward evaluation must use frozen ForecastRecords and later Outcomes.
The selected mode is persisted with the research state. Historical fixed cutoffs
automatically carry `parametric_lookahead_risk=true`, based on the persisted request
time rather than the wall clock at read time. The ResearchState contract also rejects
strict and forward modes if another caller bypasses the HTTP transport.

Offline contract and persistence tests cover explicit selection, mode rejection, and
the existing point-in-time research path. This slice does not claim Gate E completion:
the separate replay execution paths and their full temporal qualification follow.
