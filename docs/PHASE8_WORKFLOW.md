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

Evidence-Constrained Replay requires an explicit aware fixed cutoff and always declares
`parametric_lookahead_risk=true`. The worker reads a
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
The combined offline Gate E acceptance record is in `docs/GATE_E_QUALIFICATION.md`.

## 3. Forward forecast statistics — implemented offline

The evaluation module joins frozen ForecastRecords to matured OutcomeRecords by ID,
rejects duplicate or unmatched outcomes, and requires a single horizon cohort. A
configurable policy sets the minimum early sample, mature sample, outcome coverage,
and usable bucket size. The report always exposes `EvaluationMaturity`, sample count,
coverage, directional accuracy, Brier score, log loss, and all ten probability buckets.
Every bucket includes `sample_count`, predicted probability, observed frequency,
Wilson confidence interval, mean MFE, MAE, excess return, and statistical status.
Empty or small buckets are explicitly `INSUFFICIENT_SAMPLE`; reports below `MATURE`
are marked exploratory. Tests cover cold start, accumulation, mature cohorts, the
70–80% bucket, and duplicate or unmatched outcomes. Brier is reported beside the
bucket reliability data and is not labeled a calibration score.

This is an offline evaluation calculation. No live forward performance is claimed.

## 4. Frozen OutcomeRecord persistence — implemented offline

Migration `0012` adds one append-only OutcomeRecord per frozen ForecastRecord, with
its observation payload, evaluated time, and configured horizon end. PostgreSQL
rejects direct UPDATE and DELETE. The repository requires an existing forecast,
explicit horizon-to-days policy, an observation at or after maturity whose availability
precedes evaluation, finite returns and excursions, and a source name/version.
Direction correctness and excess return are derived rather than accepted from a
caller. Repeating the exact observation is idempotent; changed observations are
rejected. SQLite tests cover early rejection, successful linking, derivation,
idempotence, and immutability.

This storage path does not yet schedule outcome acquisition from a qualified provider.
PostgreSQL migration qualification and live forward observations remain pending.

The bounded `ForwardEvaluationRunner` scans forecasts without Outcomes, checks their
configured due time, asks an injected observation source for available data, and
records exactly one Outcome per matured forecast. A repeated run skips recorded
forecasts. The test verifies due selection and idempotent repeat execution. No
production observation adapter or periodic schedule is configured yet.

## 5. Agent and integrity evaluation — implemented offline

The Agent evaluation layer accepts labeled cases and aggregates tool-selection,
evidence-selection, citation, unsupported-claim, structured-output, replanning,
iteration, latency, token, cost, fallback, timeout, and provider-error metrics.
Rates with no denominator are `null`, so an empty evaluation cannot appear perfect.
The integrity layer counts future evidence, visible PIT and budget violations, and
blocked security states across persisted research states. Its pass flag covers only
these observable invariants; corporate-action, privilege, credential, and broker
invariants require their separate structural or adversarial probes. Offline tests
cover repeated unnecessary tools, label denominators, and simultaneous integrity
violations.
