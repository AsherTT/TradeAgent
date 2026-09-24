# Agentic Equity Research Workbench

Production-minded research and quantitative decision-support workbench. The current implementation contains the completed Phase 0-4 foundation and the first Phase 5 vertical slice:

- Phase 0: repository, tooling, configuration, Docker and CI skeletons
- Phase 1: versioned Pydantic contracts
- Phase 2: pluggable multi-model runtime proof of concept
- Phase 3 foundation: SQLAlchemy/Alembic persistence, SecurityMaster storage, research-run API, and Celery/Redis queue boundaries
- Phase 4: point-in-time corporate actions, provider-neutral market data, deterministic price normalization, provider qualification, and technical indicators
- Phase 5 slice: bounded LangGraph planning and evidence workflow, durable state transitions,
  execution leases, retry/redelivery protection, pending-run reconciliation, budget enforcement,
  and terminal Celery execution

Phase 4 is covered by golden-case tests and a Docker-backed PostgreSQL migration qualification.
The Phase 5 slice is qualified offline with deterministic model and market-data adapters. The
free market-data route checks a qualified local cache, prefers Alpha Vantage, and retries the
complete request through yfinance only after typed operational failures. It is wired behind the
default-off `MARKET_DATA_ENABLED` setting and has made no live market-data request. Broader
research/RAG nodes, a backtesting engine, the integrated product UI, and Azure deployment remain
deferred to later architecture gates. Phase 5 may begin an isolated frontend design clone lab,
but real API integration is gated by stable backend contracts and does not count as Phase 10.
See `docs/ALPHA_VANTAGE_QUALIFICATION.md`, `docs/YFINANCE_QUALIFICATION.md`, and
`docs/FRONTEND_STRATEGY.md`.

## Requirements

- Python 3.12.10 (pinned in `.python-version`)
- Node.js 24.21.0 (pinned in `.nvmrc`; isolated frontend design work may begin in Phase 5)
- Docker Desktop with Compose (optional for infrastructure)
- Provider credentials only for explicitly selected live-model tests

## Local setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,codex]"
python -m pytest
python -m ruff check .
python -m mypy backend/app
```

Copy `.env.example` to `.env` before enabling live executors. Ordinary tests never call a real model.

On Windows with nvm, select the pinned Node runtime with `nvm use 24.21.0`.
`CODEX_MODEL` is a model selector, not a secret. The Codex subscription executor
reuses the local `codex login` session and does not require an API key in `.env`.

## Run the API and worker foundation

```powershell
uvicorn backend.app.main:app --reload
```

The health endpoint is available at `GET /health`.

`POST /research` persists and queues a run. The worker executes the bounded graph and
`GET /research/{research_run_id}` returns its durable state. Market data remains disabled by
default; enabling it composes the qualified cache and Alpha Vantage-to-yfinance route from the
SecurityMaster symbol epoch. The fixed-cutoff cache is a bounded worker-local LRU configured by
`MARKET_DATA_CACHE_MAX_ENTRIES`; current research remains yfinance-only until a second adapter is
independently qualified. Ordinary tests use deterministic offline adapters and never spend model
or provider quota.

Celery Beat periodically republishes old, unclaimed pending runs to close the database-commit/
broker-publication crash window. `RESEARCH_RECONCILE_INTERVAL_SECONDS`,
`RESEARCH_RECONCILE_GRACE_SECONDS`, and `RESEARCH_RECONCILE_BATCH_SIZE` bound that work. A
republication never changes run state; the worker execution lease remains authoritative.

## Runtime design

Business code submits a typed `ModelRequest` to `ModelGateway`. The gateway validates capabilities, selects an executor according to `TaskPolicy`, applies retry/fallback rules, validates the provider response against the requested Pydantic schema, and records execution metadata. Provider-specific behavior stays inside executor adapters.

See `docs/MODEL_GATEWAY.md`, `docs/DATA_CONTRACT.md`, and `docs/ADR/` for the milestone decisions.
