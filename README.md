# Agentic Equity Research Workbench

Production-minded research and quantitative decision-support workbench. The current implementation contains the completed Phase 0-4 foundation and the first Phase 5 vertical slice:

- Phase 0: repository, tooling, configuration, Docker and CI skeletons
- Phase 1: versioned Pydantic contracts
- Phase 2: pluggable multi-model runtime proof of concept
- Phase 3 foundation: SQLAlchemy/Alembic persistence, SecurityMaster storage, research-run API, and Celery/Redis queue boundaries
- Phase 4: point-in-time corporate actions, provider-neutral market data, deterministic price normalization, provider qualification, and technical indicators
- Phase 5 slice: bounded LangGraph planning and evidence workflow, durable state transitions,
  execution leases, retry/redelivery protection, budget enforcement, and terminal Celery execution

Phase 4 is covered by golden-case tests and a Docker-backed PostgreSQL migration qualification. The Phase 5 slice is qualified offline with deterministic model and market-data adapters. An Alpha Vantage adapter now has offline contract qualification for raw daily bars and conservative corporate-action mapping, but remains disconnected from the production worker and has not made a live provider request. Broader research/RAG nodes, a backtesting engine, web application, and Azure deployment remain deferred to later architecture gates. See `docs/ALPHA_VANTAGE_QUALIFICATION.md`.

## Requirements

- Python 3.12.10 (pinned in `.python-version`)
- Node.js 24.21.0 (pinned in `.nvmrc`; frontend work remains deferred)
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

`POST /research` persists and queues a run. The worker now executes the bounded graph and
`GET /research/{research_run_id}` returns its durable state. Without a configured qualified
market-data adapter, a successfully planned live run intentionally ends as
`insufficient_evidence`; ordinary tests use deterministic offline adapters and never spend model
or provider quota.

## Runtime design

Business code submits a typed `ModelRequest` to `ModelGateway`. The gateway validates capabilities, selects an executor according to `TaskPolicy`, applies retry/fallback rules, validates the provider response against the requested Pydantic schema, and records execution metadata. Provider-specific behavior stays inside executor adapters.

See `docs/MODEL_GATEWAY.md`, `docs/DATA_CONTRACT.md`, and `docs/ADR/` for the milestone decisions.
