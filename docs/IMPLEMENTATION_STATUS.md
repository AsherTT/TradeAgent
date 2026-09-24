# Implementation Status

Last audited: 2026-09-22

## Implemented

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
- Latest ordinary suite: 159 passed, 1 live-model test deselected, with 94.33% combined
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
- Phase 5 is partially complete. Planner, Market, Quant, market Evidence, BudgetGuard enforcement,
  durable execution, cancellation, and safe terminal outcomes are implemented. Stronger external-
  attempt observability, Intent and News graph nodes, an explicit Gap Judge, bounded Replan
  behavior, and Synthesis remain; Gate C has not passed.
- ADR-0017 and `docs/FRONTEND_STRATEGY.md` approve an isolated Phase 5 frontend clone lab using a
  reviewed and pinned `ai-website-cloner-template` revision. `apps/web` is still unimplemented,
  real Research API integration waits for Gate C, and the formal frontend milestone remains
  Phase 10.

## Intentionally pending

- Live Gate A remains excluded from the ordinary test suite so routine development does not
  consume provider API funds or subscription quota.
- Live external market-data authorization and credentials, recorded live qualification, optional
  broader current-provider coverage after independent qualification, research/RAG graph nodes,
  backtesting, integrated frontend implementation, and Azure deployment remain deferred to their
  documented gates.
