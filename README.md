# Agentic Equity Research Workbench

Production-minded research and quantitative decision-support workbench. The current implementation is intentionally limited to the first architecture milestone:

- Phase 0: repository, tooling, configuration, Docker and CI skeletons
- Phase 1: versioned Pydantic contracts
- Phase 2: pluggable multi-model runtime proof of concept

Research agents, market-data ingestion, RAG, persistence, backtesting, the web application, and Azure deployment are deliberately deferred to later architecture gates.

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

## Run the API skeleton

```powershell
uvicorn backend.app.main:app --reload
```

The health endpoint is available at `GET /health`.

## Runtime design

Business code submits a typed `ModelRequest` to `ModelGateway`. The gateway validates capabilities, selects an executor according to `TaskPolicy`, applies retry/fallback rules, validates the provider response against the requested Pydantic schema, and records execution metadata. Provider-specific behavior stays inside executor adapters.

See `docs/MODEL_GATEWAY.md`, `docs/DATA_CONTRACT.md`, and `docs/ADR/` for the milestone decisions.
