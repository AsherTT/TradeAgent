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
configurable policy sets the horizon length, minimum early sample, mature sample,
outcome coverage, and usable bucket size. Coverage uses only forecasts past their
configured horizon. The report exposes `EvaluationMaturity`, eligible sample count,
coverage, directional accuracy, Brier score, log loss, calibration error and curve,
invalidation precision/recall when alert labels exist, and all ten probability buckets.
Every bucket includes `sample_count`, predicted probability, observed frequency,
Wilson confidence interval, mean MFE, MAE, excess return, and statistical status.
Empty or small buckets are explicitly `INSUFFICIENT_SAMPLE`; reports below `MATURE`
are marked exploratory. Tests cover cold start, accumulation, mature cohorts, the
70–80% bucket, and duplicate or unmatched outcomes. Calibration error is the
sample-weighted absolute difference between mean predicted and observed frequency
across nonempty buckets. Brier remains a separate proper score.

This is an offline evaluation calculation. No live forward performance is claimed.

## 4. Frozen OutcomeRecord persistence — implemented offline

Migration `0012` adds one append-only OutcomeRecord per frozen ForecastRecord, with
its observation payload, evaluated time, and configured horizon end. PostgreSQL
rejects direct UPDATE and DELETE. The repository requires an existing forecast,
explicit horizon-to-days policy, a bounded return window starting at the forecast
analysis time and closing after maturity, matching benchmark identity, an observation
whose availability precedes evaluation, finite returns and excursions, and a source
name/version. A cash benchmark requires explicit deployment policy and zero benchmark
return. Invalidation alerts carry an in-window timestamp when present.
Direction correctness and excess return are derived rather than accepted from a
caller. Repeating the exact observation is idempotent; changed observations are
rejected. SQLite tests cover early rejection, successful linking, derivation,
idempotence, and immutability.

This storage path does not yet schedule outcome acquisition from a qualified provider.
PostgreSQL migration, foreign-key, and mutation-trigger qualification is recorded in
`docs/PHASE8_POSTGRES_QUALIFICATION.md`. Live forward observations remain pending.

The bounded `ForwardEvaluationRunner` scans forecasts without Outcomes, checks their
configured due time, asks an injected observation source for available data, and
records exactly one Outcome per matured forecast. A repeated run skips recorded
forecasts. Migration `0013` adds an append-only source observation store; its
repository checks a frozen forecast, configured horizon, observation time, and
availability before accepting an observation. `PersistedOutcomeSource` supplies
these stored observations to the runner. SQLite and PostgreSQL fixtures verify
observation-to-Outcome execution, exact retries, mutation rejection, and rollback.
The Celery Beat due task is default-off. With an explicit positive horizon mapping,
it scans only available stored observations without Outcomes, locks selected Forecasts,
and freezes new Outcomes in one transaction. Tests cover schedule absence by default,
configuration rejection, one due write, and a repeated zero-write run. No live
market/benchmark observation adapter is configured or qualified.

## 5. Agent and integrity evaluation — implemented offline

The Agent evaluation layer accepts labeled cases and aggregates tool-selection,
evidence-selection, citation, unsupported-claim, structured-output, replanning,
iteration, latency, token, cost, fallback, timeout, and provider-error metrics.
Rates with no denominator are `null`, so an empty evaluation cannot appear perfect.
The integrity layer counts future evidence, visible PIT and budget violations, and
blocked security states across persisted research states. A correctly blocked unsafe
run is counted but is not itself an integrity violation. The pass flag covers only
these observable invariants; corporate-action, privilege, credential, and broker
invariants require their separate structural or adversarial probes. Offline tests
cover repeated unnecessary tools, label denominators, and simultaneous integrity
violations.

## 6. Configured cohort read path — implemented offline

`GET /evaluation/forecasts` reads a server-configured cohort keyed by universe ID,
horizon, and `directional_return` outcome definition. `EVALUATION_COHORTS` supplies
the cohort's instrument IDs and its maturity and bucket thresholds; no client can
set those thresholds in the request. The response includes the policy, full
`EvaluationMaturity`, sample count, outcome coverage, scores, and every bucket.
The read is capped at 1,000 ForecastRecords; oversized cohorts fail explicitly.
An offline HTTP test verifies the linked result and low-sample state. Current research
submissions also read the matching configured cohort maturity into ResearchState;
the workflow copies it into QualityAssessment. Historical fixed-cutoff replay stays
cold start to avoid using
future Outcomes. No frontend display or live forecast performance is claimed.

## Phase 8 review and qualification

The single whole-phase `skills/code-review` covered the diff since Phase 7. Its
Standards axis found no hard violations; duplicated horizon calculation and silent
unknown-horizon handling were corrected. Its Spec axis found four gaps: calibration
and invalidation metrics, outcome window/benchmark validation, blocked-state integrity
classification, and cohort maturity linkage. Those gaps are fixed and covered by the
ordinary suite. Docker PostgreSQL migration, immutability, due write/retry, and cohort
reads passed with rolled-back fixtures, including a repeat after the review fixes.
Gate E and the offline portion of Gate G are qualified. A live market/benchmark
observation adapter, real forward performance, and containerized HTTP integration
remain separately pending before production forward evaluation can be enabled.
