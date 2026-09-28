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
the existing point-in-time research path. The separate evidence path follows below.

## 2. Evidence-constrained replay — implemented offline

Evidence-Constrained Replay requires an explicit aware fixed cutoff. The worker reads a
bounded set of immutable evidence rows through the point-in-time repository instead
of contacting a market-data or RAG provider. Repository reads require observation,
availability, and publication times at or before the cutoff; the replay adapter
checks those fields again before passing evidence to the graph. Persisted market and
technical snapshots are validated against the requested instrument and exact cutoff.
If no matching market snapshot exists, the graph receives an explicit evidence gap
and cannot produce a fully qualified forecast. The current LLM remains subject to
`parametric_lookahead_risk`; this path is not a strict historical Alpha test.

Offline SQLite tests exercise PIT selection and exclusion of a future record, and an
adapter test rejects future evidence even if its repository violates the query rule.
The full Gate E acceptance record remains open until both replay paths and metadata
are qualified together.
