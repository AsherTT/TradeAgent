# Phase 5 Research Workflow

The first Phase 5 slice turns a persisted research request into a bounded durable LangGraph run.
It is deliberately provider-neutral and does not claim investment advice or live-data support.

## Graph

1. `start` changes a pending run to running and consumes one iteration.
2. `intent` checks the model budget and saves a bounded `ResearchIntent` through `ModelGateway`.
   The submitted instrument, question, horizon, and cutoff remain authoritative. A pre-Intent
   persisted plan is treated as a legacy checkpoint and resumes without another model call.
3. `plan` checks the remaining budget and uses the persisted intent through `ModelGateway`.
4. `collect_evidence` optionally loads point-in-time bars through `MarketDataLoader`, then calls
   the deterministic indicator implementation.
5. `news` optionally requests bounded documents through a provider-neutral loader after the cutoff
   is frozen. It admits only documents published, observed, and available by that cutoff, strips
   HTML/script and invisible text, rejects instruction-like content and unsafe source URLs, and
   records public-source trust metadata on accepted evidence. The provider must respect the
   remaining document limit; over-returning fails the run. Each acquisition has a durable pre-call
   marker and consumes one tool call plus the number of inspected documents. An exhausted news
   budget skips this optional step and preserves a complete qualified market result.
6. `gap_judge` checks the plan's required capabilities against point-in-time eligible evidence.
   Market and technical evidence remain the baseline requirement; a required News step needs an
   accepted, scanned News document. Unknown required capabilities fail closed. Its typed result
   records missing capabilities and coverage before the terminal decision. The plan's text
   `evidence_requirements` are also checked against the supported values `market data`,
   `point-in-time market data`, `technical indicators`, and `news documents`; unrecognized
   requirements remain unsatisfied and are identified by their plan position. Market/technical
   snapshots must match the instrument and
   frozen cutoff, and the latest market bar must be eligible at that cutoff.
7. `replan` can retry a missing required News capability when market evidence is already
   sufficient, a News loader exists, and iteration, replan, model, tool, document, and time budgets
   allow it. A revised plan must retain the question, instrument, horizon, required capabilities,
   and all prior evidence requirements. The model call has a durable pre-call marker; a completed
   replan must also change the bounded News search objective passed to the loader. It may then
   loop to News, while an interrupted call is never repeated automatically. Previous
   completed News attempt metadata is retained in bounded history. No market retry or alternative
   news-provider selection is implemented in this slice. If the replan call consumes the remaining
   time or tool budget, News retry terminates as budget exhausted without another provider call.
8. `finish` records a complete or insufficient-evidence quality assessment from that result.
   News evidence alone cannot satisfy the market and technical evidence requirement.

Each externally visible transition is saved by `ResearchRunRepository`. The API commits the run
before publishing its task and persists queue-dispatch failures. A database execution lease admits
only one worker at a time; busy or not-yet-visible deliveries retry without a fixed retry limit.
The Celery composition commits after every transition so a later delivery can resume from the
persisted plan or evidence. Already-terminal runs return unchanged.

The database commit and queue publication are not atomic. A bounded periodic reconciler closes the
process-exit window between them by selecting old, unclaimed pending runs in deterministic order
and republishing their IDs. Republishing does not mutate a run; the worker execution lease remains
the authoritative claim and duplicate delivery is safe. Broker failures remain pending and are
eligible for a later reconciliation tick. Ordinary API publication errors are persisted as failed
runs because the API observes those failures directly.

Before a model or evidence provider is called, the graph persists an external-attempt marker. If a
worker disappears after that boundary, a later delivery records an inspectable unknown-outcome
failure instead of repeating a possibly completed and billable external call. An expired worker
cannot overwrite a newer owner because every save verifies the execution lease.

The attempt record is bounded to the graph's external nodes and stores a request ID where
available, start/finish timestamps, outcome status, error type, and conservative retry
eligibility. A live worker records `known_failure` when an external step raises; a delivery that
finds only the committed pre-call marker records `unknown_outcome`. Neither is automatically
retried. Error messages and provider URLs are excluded from persisted failure reasons, while
controlled provider attempt summaries may be retained for integrity failures. Expected evidence
gaps also use controlled error types instead of raw provider messages. Successful market evidence
rejects unsafe source identifiers and writes bounded, sanitized provider-attempt records.
The same pre-call and unknown-outcome rule applies to Intent, Planner, market evidence, News
acquisition, and Replan. Intent, Planner, and Replan share the model-call checkpoint and budget
accounting path.

News has no production loader configured and makes no external request by default. Its ingestion
and resume behavior are qualified with offline fixtures. Accepted article text remains untrusted
data and carries source type, content hash, sanitization status, injection risk, and scanner
version. This first News slice collects source documents; model-based event extraction and a
qualified live news adapter remain pending.

## Outcomes

- `complete`: a validated plan and all required capabilities have qualified evidence.
- `insufficient_evidence`: planning may have succeeded, but qualified evidence is unavailable.
- `failed`: execution raised an error; its type and a controlled reason are saved with a blocked
  quality assessment. Raw exception messages are excluded.
- Budget exhaustion uses `insufficient_evidence` as the run status and
  `budget_exhausted` as the more precise research-completion reason.

The production worker composes the free market-data route only when `MARKET_DATA_ENABLED=true`.
The default remains disabled. When enabled, a qualified cache is checked first, Alpha Vantage is
preferred, and yfinance may supply the complete request only after a typed operational failure.
Fallback reasons are explicitly allowlisted in configuration. Integrity failures stop the route
without fallback. Ordered provider attempts are written into successful evidence; if every
provider is unavailable, the terminal gap reason retains the attempt summary. No live market-data
trial has been performed; live model tests and providers remain opt-in because they may consume
credentials or quota.

Fixed-cutoff runs freeze `analysis_timestamp` at submission. A provider record first observed after
that cutoff remains ineligible even if its market timestamp is earlier, so realistic queue delay
can make a newly fetched response end as `insufficient_evidence`. ADR-0016 preserves this fail-closed
behavior. ADR-0018 adds an explicit `current_research` mode whose cutoff remains absent until a
current-capable evidence adapter completes acquisition. The evidence orchestrator then reads its
trusted clock and validates the acquired data against that cutoff. The initial
production adapter derives bars and observed actions from one request-scoped yfinance snapshot and
has offline fixture coverage. It remains behind the default-off market-data setting, fails closed
when yfinance is excluded from provider configuration, and is not live-data qualified.

The Docker-backed qualification submits both timestamp modes with `max_llm_calls=0`. This exercises
the real API, Redis, Celery, and PostgreSQL path and reaches durable `budget_exhausted` completion
without making a model or provider call. Re-delivering both terminal runs is an idempotent no-op.
It qualifies timestamp transport, nullable persistence, and redelivery—not current acquisition or
atomic cutoff-plus-evidence persistence, which are covered by offline adapter/workflow fixtures.

The reconciler Docker qualification inserts an old unclaimed pending run without publishing it,
then invokes the named reconciliation task. The reconciler republishes one ID, the worker reaches
`budget_exhausted`, and the logs and persisted state show zero model calls, tool calls, evidence,
or provider-request markers. Terminal redelivery remains an idempotent no-op.

## Durable cancellation

`POST /research/{research_run_id}/cancel` marks a pending or running run `cancelled` in
PostgreSQL, records a blocked quality assessment and cancellation timestamp, and revokes the
worker lease in the same transaction. Repeated requests return the existing terminal state;
already completed, insufficient-evidence, or failed runs keep their original outcome. Unknown
IDs return 404. A queued delivery or pending-run reconciliation cannot restart a cancelled run.

The worker commits checkpoints before external calls. A cancellation committed before the
pre-call checkpoint prevents the call. Once that checkpoint has committed, cancellation cannot
guarantee that an in-flight external call stops or that no call begins during the race to revoke
the lease. Its late result cannot be persisted, and a redelivery never repeats that attempt.
The worker returns the cancelled state after detecting the revoked lease. Cancellation is not
Celery task revocation or a provider-side cancellation request.

Offline tests cover pending cancellation, repeated requests, terminal redelivery, and cancellation
while a model call is blocked, including a call that fails after cancellation. In an isolated
Docker Compose project, the API accepted run `149c1851-b97f-4ed5-9809-ec50fb3a503b` while
the worker was stopped. The API cancelled it, then the restarted worker received the queued task
and returned `cancelled`. PostgreSQL retained the cancelled status with no execution lease;
model and tool call counts remained zero. This qualifies the queue path for pre-execution
cancellation, not provider-side interruption of an in-flight call.

## Remaining Phase 5 path

1. Request separate authorization before a narrow recorded live market-data trial.
2. Durable cancellation is qualified offline and through the Docker queue path. External-attempt
   observability now distinguishes completed, known-failure, and unknown-outcome steps with
   bounded secret-free metadata; pending-run reconciliation is implemented.
3. Intent, provider-neutral News ingestion, a deterministic Gap Judge, and bounded News Replan
   are implemented with offline fixture coverage. Extend the graph through model-based event
   extraction and
   Synthesis, then qualify the full Gate C limits.

ADR-0019 closes the provider/cache architecture decision: current acquisition remains
yfinance-only until a second adapter is independently qualified, and the fixed-cutoff qualified
cache is a configurable bounded LRU owned by each worker process rather than durable research
state.

An isolated frontend clone lab may run alongside these steps under ADR-0017. It uses mock data and
cannot widen Phase 5 scope, change domain contracts, or claim that the Phase 10 product UI exists.
