# Implementation Status

Last audited: 2026-09-20

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

## Verified locally

- Python 3.12.10 virtual environment installs the complete `dev` and `codex` extras
- Node.js 24.21.0 is selected through nvm
- 105 ordinary tests pass; the live-model test is skipped unless explicitly enabled
- Live Gate A passed on 2026-09-17: Codex, Qwen, and DeepSeek returned the same
  validated `ResearchPlan`, with reasoning configuration, tracing, and usage metering active
- combined statement/branch coverage is 98.59%
- Ruff passes
- strict mypy passes
- Docker Compose qualification passes with PostgreSQL 18/pgvector, Redis, Alembic, API, and Celery
- rebuilt Phase 5 API and worker images pass an API-to-Redis-to-Celery-to-PostgreSQL budget-stop
  trial without invoking a model; the task reaches durable `budget_exhausted` completion
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
- Queue publication is not transactionally coupled to run creation. A process exit between the
  database commit and publication can leave a pending run; an outbox or reconciler remains a
  production-hardening deliverable.
- The automated offline service test crosses HTTP POST, the registered Celery task, persistence,
  and HTTP GET.
- Before the external-adapter slice, statement and branch coverage were 100%.
- Docker images rebuild successfully, migration reaches `0005_phase5_execution_lease`, API and
  worker run as UID 10001, and the real queue path reaches a retrievable terminal state.

## Current phase assessment

- Phases 0-4 and Gate B are complete.
- The first Phase 5 vertical slice is implemented, qualified offline, and verified across the
  Docker-backed queue path. The first external adapter is qualified offline at the contract level;
  an explicitly authorized recorded live response remains before a meaningful live-stock trial.

## Intentionally pending

- Live Gate A remains excluded from the ordinary test suite so routine development does not
  consume provider API funds or subscription quota.
- Live external market-data credentials and worker configuration, broader research/RAG graph
  nodes, cancellation,
  backtesting engine, frontend, and Azure deployment remain
  deferred to their documented phases.
