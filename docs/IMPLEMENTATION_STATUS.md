# Implementation Status

Last updated: 2026-10-03

The 2026-10-03 bounded P5 increment adds deterministic source-linked partial financial
interpretations and per-metric unavailability reasons to reports. It preserves the
four-concept admission gate, existing metric API and complete_analysis=false, with
no additional source/model calls. Ordinary checks: 411 passed, 1 skipped, 90.08%
coverage; Ruff and strict mypy (97 files) passed. Read-only regeneration from a prior
real PostgreSQL run could not execute because the database refused connections and
the local Docker engine was not running; no new live qualification is claimed.
Spec: `docs/FINANCIAL_PARTIAL_ASSESSMENT.md`. Independent Standards/Spec reviews
both have zero findings, including final report-language polish; 23 affected report
tests and final static checks pass. See `docs/FINANCIAL_PARTIAL_ASSESSMENT_REVIEW.md`.
P10 remains unstarted.

Current assessment: `docs/DEVELOPMENT_PROGRESS_20261002.md`. The earlier entries below
are chronological qualification records; later live qualification supersedes historical
statements that no request had yet been made. SEC contact configuration and real current
financial acquisition/persistence are now qualified. Complete analysis remains blocked
by market/action completeness and verified source-specific analysis.

Later 2026-10-02 qualification removed the missing-RAG-input gap using explicit
lexical-only PostgreSQL retrieval: official SEC excerpt intake, migration 0014 and
real research queue execution passed. An offline action-material audit is implemented
without granting provider qualification. This stage passed Standards and Spec with
zero findings; 374 ordinary tests pass, 1 is skipped, coverage is 90.00%.
See `docs/RAG_ACTION_AUDIT_REVIEW.md` and `docs/RAG_LEXICAL_QUALIFICATION.md`.
Market/action completeness, verified analysis and full synthesis remain outstanding.

The later partial-analysis increment adds two reproducible annual SEC financial
fractions and a default-off source-bound catalyst node. Live run
`78e1521e-38cf-451b-b6a6-2c72fe78b7b5` persisted three model nodes and two metrics;
the catalyst assessment returned zero interpretations with three limitations. This
qualifies the empty-output path, not confirmed event extraction. Ordinary checks:
395 passed, 1 skipped, 90.11% coverage; Ruff and strict mypy (97 files) passed.
See `docs/FINANCIAL_CATALYST_QUALIFICATION.md` for the bounded qualification.
Standards reported zero findings; Spec's one P2 was corrected and closed. See
`docs/FINANCIAL_CATALYST_REVIEW.md` for the pinned review and regression evidence.
P10 remains unstarted; development must pause before that phase.

The 2026-10-02 source-bound claim increment passed Standards and Spec review with
zero findings. Ordinary suite: 350 passed, 1 skipped, 90.21% coverage; Ruff and
strict mypy passed. See `docs/SYNTHESIS_CLAIM_REVIEW.md` and
`docs/SEC_CURRENT_QUALIFICATION.md` for the current reviewed and live-qualified scope.

## Implemented

- Phase 5 SEC financial-source slice and default-off current worker integration (2026-10-01):
  exact current ticker/CIK
  resolution, bounded official Company Facts client, typed USD annual facts, conservative
  acquisition-time availability, revision/conflict checks and filing-index citations.
  Offline golden cases pass. Shared Redis request admission, actual HTTP-call budgeting,
  freshness/provenance admission, same-period concept coverage, required synthesis citations
  and individually cited report observations are implemented. See
  `docs/SEC_FINANCIAL_INTEGRATION.md` and `docs/SEC_FINANCIAL_SOURCE.md`. Live client
  qualification remains pending an identifying SEC User-Agent. No complete financial
  research or historical PIT qualification is claimed.
- Phase 5 local Codex SDK transport recovered using an explicit child-process proxy matching
  the workstation's existing network configuration. Real structured intent/plan and durable
  HTTP/Redis/Celery/PostgreSQL acquisition passed; the KLAC result remains insufficient
  evidence because Yahoo action quality is UNVERIFIED. See `docs/CODEX_TRANSPORT_QUALIFICATION.md`.
- This increment passed dual-axis review after three Spec corrections. Ordinary checks:
  339 passed, 1 skipped, 90.14% coverage; Ruff and strict mypy passed. See
  `docs/FINANCIAL_INTEGRATION_REVIEW.md`. Live SEC access and complete corporate-action
  coverage remain outstanding; P10 has not started.

- Phase 0 repository and Python 3.12 project baseline
- FastAPI health skeleton
- Docker Compose service boundaries for API, worker, PostgreSQL/pgvector, and Redis
- Azure Pipelines quality-check skeleton
- Ruff, mypy, pytest, coverage, and pre-commit configuration
- Phase 1 Pydantic contracts for research, budgets, instruments, corporate actions, market data, evidence, thesis, forecasts, replay integrity, maturity, quality, and model execution
- deterministic `BudgetGuard`
- Phase 2 provider-neutral `ModelGateway`
- capability validation, bounded retry, ordered fallback, structured-output validation, and execution metadata
- Codex subscription, Qwen, DeepSeek, OpenAI API, and mock executor boundaries
- offline Gate A adapter test proving one task validates to the same `ResearchPlan` contract through Codex/Qwen/DeepSeek adapters
- attempt-level model tracing, successful-use aggregation, and model capability/limit profiles
- opt-in live Gate A qualification test for Codex, Qwen, and DeepSeek
- Phase 3 SQLAlchemy models and repositories for instruments, symbol history, corporate actions,
  research runs, plans, and budgets
- Phase 6 Evidence Repository slice: append-only relational evidence checkpoints, explicit
  point-in-time reads, immutable UUID/content enforcement, timezone normalization, and Alembic
  migration `0007` with eligible historical backfill. See
  `docs/PHASE6_WORKFLOW.md` for the remaining Thesis and Forecast work.
- Phase 6 Thesis Lifecycle slice: append-only versions, transitions, evidence links, optimistic
  version checks, point-in-time history, and migration `0008`. Thesis creation requires a
  completed cited research run; direction and probability are supplied explicitly. Migration
  `0010` blocks direct PostgreSQL UPDATE/DELETE of version, transition, and evidence history.
- Phase 6 ForecastRecord slice: forward-only freezing from a persisted Thesis version, completed
  recent research, one persisted successful Synthesis execution with matching direction and
  probability, and cited evidence; append-only supersession and as-of reads. Migration `0009`
  blocks Forecast mutation; `0010` stores immutable typed model execution metadata and output.
- Phase 6 opt-in Thesis/Forecast command: a token-guarded HTTP write composes completed cited
  research, versioned Thesis, and a forward ForecastRecord in one transaction. It defaults off
  until `PHASE6_WRITE_TOKEN` is configured; offline command coverage is in place.
- Phase 6 mock-path qualification: rebuilt API/worker/Beat/migration images, PostgreSQL at
  Alembic `0010`, real Redis/Celery execution, cited Thesis/Forecast persistence, exact model
  output provenance, and direct PostgreSQL UPDATE/DELETE rejection. See
  `docs/PHASE6_QUALIFICATION.md`.
- Phase 7 document-intake slice: bounded HTML/Markdown/text/JSON/PDF parsing, Unicode and
  hidden-content cleanup, versioned prompt-injection scanning, trust classification, high-risk
  quarantine, and structure-aware chunking. See `docs/PHASE7_WORKFLOW.md`.
- Phase 7 storage slice: migration `0011` adds append-only RAG documents/chunks, 384-dimensional
  pgvector embeddings, PostgreSQL FTS/HNSW indexes, model provenance, and mutation triggers;
  repository validation and SQLite boundary tests pass. PostgreSQL qualification follows.
- Phase 7 retrieval slice: PIT-filtered PostgreSQL FTS and pgvector query, bounded application
  RRF, trust/risk filtering, and bounded untrusted ContextBuilder have offline boundary tests.
  Container query qualification follows.
- Phase 7 application slice: default-off token-guarded document and search APIs, configurable
  HTTP embedding adapter, and a durable budgeted RAG research node with cited evidence. Offline
  API and graph tests pass; no live embedding provider is configured or qualified.
- Phase 7 Gate D: 13/13 poisoned fixtures quarantined, 5/5 policy/trust-field injections
  rejected, and PostgreSQL migration `0011` qualified with FTS/pgvector retrieval, PIT exclusion,
  and immutable document/chunk rows. See `docs/GATE_D_QUALIFICATION.md`.
- Phase 8 replay submission slice: research requests explicitly select Research Replay or
  Evidence-Constrained Replay; historical cutoffs retain parametric look-ahead risk metadata,
  and the research workflow rejects strict quant and forward evaluation modes. See
  `docs/PHASE8_WORKFLOW.md`.
- Phase 8 evidence-constrained replay slice: a separate worker path reads bounded immutable
  evidence at the requested cutoff and avoids live market/RAG calls; PIT fields and embedded
  market snapshots are checked before graph use. Offline tests cover future-evidence exclusion.
- Phase 8 Gate E is qualified with local contract, SQLite, and worker-composition fixtures:
  explicit modes, historical LLM risk metadata, evidence time filtering, and the strict
  quant-backtest exclusion. See `docs/GATE_E_QUALIFICATION.md`; no live-source result is claimed.
- Phase 8 forward-statistics slice: configurable evaluation maturity and bucket thresholds,
  linked Forecast/Outcome descriptive scores, per-bucket sample counts and Wilson intervals,
  with cold-start and small-sample limits.
- Phase 8 OutcomeRecord slice: migration `0012` and an append-only repository link matured
  observations to frozen forecasts with configured horizon policy and derived returns/direction.
  A bounded due-runner accepts an injected observation source and skips already evaluated
  forecasts. Offline SQLite checks pass; a production source and schedule follow.
- Phase 8 Agent and Integrity evaluation slice: labeled engineering metrics and observable
  PIT, future-evidence, budget, and security-state violation counts have offline tests;
  external structural invariants are not inferred from these reports.
- Phase 8 PostgreSQL `0012` qualification: migration upgrade, Outcome foreign key, and direct
  UPDATE/DELETE rejection passed in the restored local Docker environment using rolled-back
  synthetic rows. See `docs/PHASE8_POSTGRES_QUALIFICATION.md`.
- Phase 8 read-only evaluation endpoint: a server-configured universe/horizon/outcome cohort
  exposes policy, maturity, coverage, scores, and all sample-counted buckets. Offline HTTP
  tests cover exploratory low-sample output and unconfigured cohort rejection. PostgreSQL
  fixture checks cover a zero-Outcome cohort and a rolled-back due Outcome write/retry.
- Phase 8 immutable observation source: migration `0013` stores one validated source
  observation per Forecast for the due runner. SQLite and PostgreSQL fixtures exercise
  observation-to-Outcome flow; direct PostgreSQL observation UPDATE/DELETE is rejected.
- Phase 8 default-off scheduled evaluation: Celery Beat registers the due task only
  with explicit positive horizon mappings. The task reads available immutable
  observations, locks Forecast rows, and freezes Outcomes; offline tests verify one
  write and a zero-write retry. No live observation adapter is configured.
- Phase 8 whole-phase review completed before the final Phase 8 push. Review gaps
  were closed for calibration and invalidation metrics, bounded observation windows
  and benchmark identity, blocked-state classification, and configured cohort
  maturity propagation into research quality metadata. Ruff, strict mypy, and the
  ordinary suite pass: 252 passed, one opt-in live-model test skipped, 91.03%
  combined coverage. PostgreSQL due-runner and cohort reads passed again after the
  fixes with rolled-back synthetic rows.
- Phase 9 strict PIT feature-input slice: deterministic historical features require
  a timestamped universe, qualified market and action providers, raw execution
  bars, and only point-in-time-visible corporate actions. Unsupported lifecycle
  changes fail closed. See `docs/PHASE9_WORKFLOW.md`.
- Phase 9 deterministic signal/backtest slice: point-in-time moving-average signals
  execute at the following raw open in a bounded long-or-cash simulation with
  split/dividend accounting, costs, NAV, and reproducible metrics. This remains
  offline fixture-qualified and does not regenerate historical LLM signals.
- Phase 9 deterministic risk/TradeIntent slice: quality, age, loss, exposure,
  liquidity, price, hours, duplicate, and kill-switch checks produce only a
  non-executable, externally authorized intent. Gate F is fixture-qualified for
  the restricted deterministic path. See `docs/GATE_F_QUALIFICATION.md`.
- Phase 9 whole-phase review identified and closed historical-universe provenance,
  loss-at-stop sizing, and signal/instrument lineage gaps. The two maintainability
  suggestions were addressed by separating input validation, action accounting,
  and metrics from the main calculation paths. Ruff and strict mypy pass; the
  ordinary suite has 260 passed, one opt-in live-model test skipped, and 90.52%
  combined coverage.
- Alembic migration for the Phase 3 PostgreSQL schema and pgvector extension
- `POST /research` and `GET /research/{research_run_id}` service boundaries
- Celery/Redis JSON-only queue configuration and worker task boundary
- PostgreSQL 18-compatible data-volume layout and loopback-only host port bindings
- non-root API, migration, and worker container runtime
- Phase 4 provider-neutral market-data and corporate-action interfaces with offline adapters
- point-in-time corporate-action queries enforcing `available_at <= analysis_timestamp`
- deterministic RAW, SPLIT_ADJUSTED, TOTAL_RETURN, and POINT_IN_TIME_ADJUSTED behavior
- split, reverse-split, cash-dividend, symbol-change, delisting, duplicate, and invalid-event golden cases
- versioned provider qualification and per-bar quality gates that fail closed for strict backtests
- deterministic return, SMA, EMA, RSI, realized-volatility, and trend-slope indicators
- Alembic Phase 4 point-in-time lookup index
- Phase 5 bounded LangGraph workflow with planning, qualified market evidence, deterministic
  technical analysis, and explicit terminal outcomes
- durable transition persistence from the Celery task, terminal-state idempotency, budget
  exhaustion, and inspectable failure persistence
- commit-before-publish submission, durable worker leases, pre-call external-attempt markers, and
  stale-owner write rejection for retry/redelivery safety
- offline HTTP-to-registered-Celery-task-to-GET terminal-state qualification
- Alpha Vantage raw-daily and corporate-action adapters behind the provider-neutral boundary,
  qualified against saved offline response shapes with fail-closed provider-error handling
- yfinance raw-daily and observed-action adapters qualified with synthetic offline fixtures for
  ordinary personal research, while remaining ineligible for strict backtesting
- typed market-data operational failures and whole-request Alpha Vantage-to-yfinance fallback;
  configured allowlists decide fallback eligibility, integrity failures stop without fallback,
  and ordered attempts persist in evidence or terminal gap reasons
- validated provider-attempt contracts and API-key-safe Alpha Vantage error/log handling prevent
  malformed audit provenance and credential-bearing request URLs from entering ordinary logs or
  persisted evidence gaps
- provider/action-quality-version-aware worker-process cache in front of the fallback loader,
  bounded by a configurable LRU limit so cache ownership cannot cause unbounded memory growth
- default-off worker composition using point-in-time SecurityMaster symbol epochs; no live
  market-data request or credential was used during qualification
- offline queue-delay tracer bullet proving that provider observations after a frozen analysis
  cutoff remain ineligible and end as insufficient evidence, as recorded in ADR-0016
- ADR-0018 explicit fixed-cutoff/current-research transport and persisted-state contract, with an
  offline workflow tracer that freezes the current-research cutoff only after evidence acquisition,
  resumes without reacquisition, and preserves unknown-outcome safety after interruption
- immutable frozen-cutoff repository enforcement and a final generic evidence-time gate preventing
  observations or availability timestamps after the decision cutoff
- stable replay-risk classification relative to `requested_at`, so persisted current-at-submission
  runs do not become invalid merely because wall-clock time advances; legacy state JSON backfills
  the request time from the durable run creation timestamp
- request-scoped yfinance history reuse so bars and corporate actions are derived from one snapshot,
  including quality propagation from unverified actions into normalized bars
- offline-qualified production current acquisition through yfinance; it freezes the cutoff only
  after acquisition, remains default-off, fails closed when yfinance is not configured, and records
  terminal provider attempts on failure
- per-Celery-delivery database disposal, preventing async connection pools from crossing the
  separate event loops created by consecutive synchronous worker tasks
- ADR-0019 closes the current-provider and cache-ownership decisions: current acquisition remains
  yfinance-only pending a separately qualified second adapter, while fixed-cutoff cache state is an
  expendable bounded worker-local optimization rather than PostgreSQL/Redis research state

## Verified locally

- Python 3.12.10 virtual environment installs the complete `dev` and `codex` extras
- Node.js 24.21.0 is selected through nvm
- Ordinary tests pass; the live-model test is skipped unless explicitly enabled
- Live Gate A passed on 2026-09-17: Codex, Qwen, and DeepSeek returned the same
  validated `ResearchPlan`, with reasoning configuration, tracing, and usage metering active
- Latest ordinary suite: 183 passed, 1 live-model test deselected, with 94.03% combined
  statement/branch coverage.
- Ruff passes
- strict mypy passes
- Docker Compose qualification passes with PostgreSQL 18/pgvector, Redis, Alembic, API, and Celery
- rebuilt Phase 5 API and worker images pass an API-to-Redis-to-Celery-to-PostgreSQL budget-stop
  trial without invoking a model; the task reaches durable `budget_exhausted` completion
- migration reaches `0006_current_research_cutoff`; consecutive fixed-cutoff and current-research
  requests, followed by terminal redelivery, preserve their expected cutoff state and transitions
- Git whitespace validation passes

## Docker-backed Phase 3 qualification

- PostgreSQL 18 starts healthy and the `vector` extension is installed.
- Alembic reaches revision `0001_phase3` and creates all Phase 3 tables.
- Redis starts healthy and the Celery worker responds to inspection pings.
- A real `POST /research` request persists its `ResearchRun` in PostgreSQL, publishes the task
  through Redis, and receives a successful result from the Celery worker.
- Application containers run as UID/GID 10001 instead of root.
- Host ports 8000, 5432, and 6379 bind only to `127.0.0.1`.

## Gate B qualification

- Golden corporate-action and normalization cases pass offline.
- Future-available actions and bars are excluded at the analysis timestamp.
- Strict backtests reject underqualified providers and degraded individual bars.
- Deterministic indicators consume only explicit, normalized price modes.
- PostgreSQL migration reaches `0004_phase4_constraints`, creates point-in-time lookup indexes,
  and enforces corporate-action value constraints.
- The rebuilt non-root application image imports pandas, NumPy, and SciPy successfully.
- Detailed evidence is recorded in `docs/GATE_B_QUALIFICATION.md`.

## Phase 5 first-slice qualification

- A deterministic mock model produces a validated `ResearchPlan` only through `ModelGateway`.
- Qualified in-memory point-in-time bars flow through `MarketDataService` and the deterministic
  indicator implementation before becoming graph evidence.
- Every externally visible transition is saved; the worker commits each node transition.
- Complete, insufficient-evidence, budget-exhausted, and failed terminal paths are covered.
- Redelivery of a terminal run is a no-op, and model/output failures persist their reason instead
  of leaving the run pending.
- Concurrent deliveries are rejected by a durable lease. Interrupted external calls are not
  repeated, and expected data unavailability becomes `insufficient_evidence` rather than a worker
  failure.
- Queue publication is not transactionally coupled to run creation. A bounded Celery Beat
  reconciler republishes old, unclaimed pending runs, closing the process-exit window between the
  database commit and publication while leaving execution leases authoritative. Broker failures
  are retried on later ticks without corrupting run state.
- The automated offline service test crosses HTTP POST, the registered Celery task, persistence,
  and HTTP GET.
- Before the external-adapter slice, statement and branch coverage were 100%.
- Docker images rebuild successfully, migration reaches `0005_phase5_execution_lease`, API and
  worker run as UID 10001, and the real queue path reaches a retrievable terminal state.
- Rebuilt API and worker images include yfinance 1.7.0. With market data resolving to disabled,
  provider order and fallback reasons parse correctly, and a fresh API-to-Redis-to-Celery-to-
  PostgreSQL qualification reaches `budget_exhausted` with zero model calls, tool calls, or
  evidence. Provider-request and credential markers are absent from the API/worker logs and the
  persisted research state.
- The latest Docker qualification uses fixed run `42d99e86-f25a-428b-92f8-a750364918b2` and current
  run `21a3ae6d-f9fc-4b56-bc3d-69ad566adec8`. Both stop at `budget_exhausted` with zero model/tool
  calls and no evidence; redelivery is an idempotent no-op. The fixed cutoff remains frozen and the
  current cutoff correctly remains absent because acquisition never starts.
- Pending-run reconciliation is Docker-qualified with run
  `8557ccb5-bf4d-4235-9ba7-d2dfbf56ce6d`: an old unclaimed pending row was selected and
  republished, the reconciliation result logged `eligible=1 published=1 failed=0`, and the run
  reached `budget_exhausted` with zero model calls, tool calls, evidence, or provider markers.
- This Docker trial qualifies timestamp transport, nullable persistence, queue execution, and
  terminal redelivery only. Current acquisition and atomic cutoff-plus-evidence persistence remain
  offline fixture-qualified at the workflow/adapter boundary rather than through the container path.
- Durable cancellation now has a research API endpoint and a PostgreSQL terminal transition that
  revokes the worker lease. Offline tests cover pending and running cancellation, idempotent
  requests, redelivery, and rejection of a late model-call result. An external call already in
  flight may still complete, but its result cannot replace the cancelled state.
- An isolated Docker Compose queue-path trial submitted run
  `149c1851-b97f-4ed5-9809-ec50fb3a503b` while the worker was stopped, cancelled it via API,
  then started the rebuilt worker. The queued task returned `cancelled`; PostgreSQL retained the
  terminal status with a cleared lease and zero model/tool calls. No provider call was made.
- External-attempt records now carry bounded timing, outcome, error-type, and retry-eligibility
  metadata. Offline checks distinguish known failures from unknown outcomes after interruption
  and verify that failure text and evidence gaps containing a credential-bearing URL are not
  persisted. Successful evidence also rejects unsafe market source identifiers and sanitizes
  provider-attempt fields before persistence. Automatic retry remains disallowed after an
  external call might have begun.
- Intent is now a persisted, bounded model step before Planner. Offline tests cover its checkpoint,
  budget consumption, resumed unknown-outcome safety, legacy plan-only recovery, and use of its
  output in planning. This
  slice has not made or qualified a live model call or a new Docker queue-path run.
- News ingestion is now a provider-neutral, default-off graph step after market evidence. Offline
  tests cover a strict document limit, tool/document budget accounting, cutoff rejection,
  HTML/script cleaning, instruction-like content rejection, URL userinfo rejection and query
  removal, trust
  metadata, persisted pre-call checkpoints, unknown-outcome redelivery, and news-only
  insufficient-evidence behavior. A zero news-document budget skips the optional node without
  blocking complete market/technical evidence. No live news request or new Docker queue-path
  trial was made for that slice. A later opt-in Finnhub company-news adapter now captures current
  news before cutoff freeze, persists accepted headline/summary evidence with market evidence,
  and rejects fresh retrieval for historical cutoffs. HTTP behavior has offline tests; no live
  entitlement or network qualification has been claimed.
- A deterministic Gap Judge now persists a typed coverage result before completion. Required plan
  capabilities are checked against eligible, typed evidence; unsupported capabilities, missing
  required News, unrecognized text requirements, future-available evidence, and mismatched
  instrument or cutoff snapshots fail closed. Market and technical evidence remain the baseline
  requirement. This slice was qualified offline only.
- Bounded model-assisted Replan now retries a missing required News capability when a configured
  loader and all relevant budgets permit. Offline tests cover success after an empty first result,
  a changed search objective reaching the News loader, replan budget exhaustion, prevention of
  requirement deletion, time-budget expiry between replan and retry, and unknown-outcome safety after
  interruption. Repeated completed News attempts retain bounded audit history. This slice makes
  no live model or news-provider calls and does not retry market acquisition.
- Evidence-cited Synthesis now follows a sufficient Gap Judge result. The model receives at most
  eight bounded evidence excerpts with trust metadata and explicit untrusted-content markers;
  selection and citations must cover each required evidence type. Offline tests cover citation
  rejection, delimiter escaping, context bounds, required News beyond the first eight evidence
  items, model-budget exhaustion, and interrupted-call redelivery.
  This is a research summary contract, not a Phase 6 persisted thesis lifecycle.
- Gate C passes within its recorded fixture scope. Offline qualification exercises each Replan
  loop budget with persistently missing News, and the complete mock-provider
  submission-to-Celery-task-to-SQLite-to-query path retains Synthesis citations. The rebuilt
  Docker API/Redis/Celery/PostgreSQL path also completed run
  `148af5f8-8d69-4fdd-9e1d-c8c16a1519f3` with persisted citations and idempotent task
  redelivery. `docs/GATE_C_QUALIFICATION.md` records the outcome matrix and provider limits.
  The ordinary suite has 188 passing tests and one opt-in live-model test skipped, with 94.35%
  combined statement/branch coverage.

## Current phase assessment

- Phases 0-4 and Gate B are complete.
- The first Phase 5 vertical slice is implemented, qualified offline, and verified across the
  Docker-backed queue path. The free-provider market-data route is qualified offline and wired
  behind a default-off setting; an explicitly authorized recorded live response remains before a
  meaningful live-stock trial.
- The fixed-cutoff workflow remains point-in-time safe under realistic worker delay. The explicit
  current-research mode now has an offline-qualified production yfinance acquisition slice and
  nullable persisted cutoff. It is not live-data qualified, and no live request has been made.
- The market-data architecture decision is closed offline. Live qualification remains optional and
  separately authorized rather than a prerequisite for the provider/cache interface.
- Phase 5 is partially complete. Intent, Planner, Market, Quant, market Evidence, default-off News
  ingestion, deterministic Gap Judge, BudgetGuard enforcement, durable execution, cancellation,
  external-attempt observability, and safe terminal outcomes are implemented. News event
  extraction, live qualification of the Finnhub news adapter, and broader Replan routing remain.
  Synthesis and
  Gate C research-loop safety are qualified with fixtures; recorded live external-provider
  qualification remains separate and is not a Gate C claim.
- A read-only research report projection now exposes persisted synthesis, eligible citation
  metadata, quality state, and explicit missing sections through
  `GET /research/{research_run_id}/report`. It is deliberately marked incomplete while verified
  financial/catalyst evidence and claim-level attribution are unavailable. See
  `docs/RESEARCH_REPORT.md`.
- A 2026-09-30 live KLAC provider-composition probe verified Finnhub free-key access and admitted
  19 news items alongside a frozen Yahoo cutoff. Yahoo action quality remained `UNVERIFIED`, so
  the technical and market evidence requirement correctly stayed unsatisfied. This did not
  exercise the durable API/Redis/worker/PostgreSQL/model path. See
  `docs/KLAC_CURRENT_QUALIFICATION.md`.
- Subsequent Phase 5 work records a typed, bounded market acquisition summary even when returned
  bars fail the technical quality gate. It exposes provider/count/date/quality diagnostics in the
  report without promoting an unqualified price or evidence claim.
- A later current KLAC probe traversed PostgreSQL, Redis, Celery, and API retrieval with a
  prepopulated plan and zero model-call budget. It persisted 15 Finnhub news records and 41
  Yahoo bars as an `UNVERIFIED` acquisition, ending `insufficient_evidence` without market or
  technical claims. The report now projects bounded eligible news source metadata without
  showing untrusted article text or claiming verified catalysts. HTTP submission, live planning,
  model synthesis, and a complete report remain unqualified.
- A separate live API submission was accepted and claimed by a local Celery worker but stopped
  at the first configured Codex subscription intent call after its 120-second limit. It
  persisted a controlled `AllProvidersFailedError` and made no provider call. This leaves
  unseeded model planning unqualified; see `docs/KLAC_CURRENT_QUALIFICATION.md`.
- A server-generated `collection_only` submission mode now lets ordinary HTTP requests reach
  provider acquisition with zero model calls while preserving all quality gates. A live KLAC
  request completed the API/Redis/Celery/PostgreSQL/report path with 15 Finnhub news records,
  41 unverified Yahoo bars, and an explicit incomplete report. This improves partial-result
  usability without claiming synthesis or a qualified price analysis.
- Phase 6 implementation and mock-path qualification are complete after a single whole-phase
  code review and closure of its provenance and storage-immutability findings. The application
  command remains default-off, and no live forward forecasts or provider qualification are claimed.
  Phase 7 Secure RAG and Gate D are fixture-qualified after the single whole-phase code review.
  SEC filing eligibility now requires verified primary provenance, API uploads receive a
  server-side observation timestamp, and RAG source routing uses the research horizon and
  model-produced plan. Its ordinary suite passes 231 tests with one opt-in live-model test
  skipped and 91.92% combined coverage. RAG remains default-off; no real embedding service
  or live document source is claimed. Phase 8 Gate E and offline Gate G slices are
  fixture-qualified after one whole-phase code review. Production forward-observation
  wiring and live performance qualification remain pending.
- ADR-0017 and `docs/FRONTEND_STRATEGY.md` approve an isolated Phase 5 frontend clone lab using a
  reviewed and pinned `ai-website-cloner-template` revision. `apps/web` is still unimplemented,
  Gate C now permits real Research API integration under that strategy, while the formal frontend
  milestone remains Phase 10.
- Phase 9 Gate F is fixture-qualified for a restricted deterministic strategy and
  non-executable TradeIntent. Historical universe, market, and corporate-action
  sources are represented by explicit qualified inputs; real provider completeness,
  LLM historical Alpha, and broker execution are outside this claim.

## Intentionally pending

- Live Gate A remains excluded from the ordinary test suite so routine development does not
  consume provider API funds or subscription quota.
- Live external market-data authorization and credentials, recorded live qualification, optional
  broader current-provider coverage after independent qualification, remaining Phase 5 research
  extensions, broader/live backtesting, integrated frontend implementation, and Azure deployment remain
  deferred to their documented gates.
