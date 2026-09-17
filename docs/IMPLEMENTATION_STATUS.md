# First Milestone Status

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

## Verified locally

- Python 3.12.10 virtual environment installs the complete `dev` and `codex` extras
- Node.js 24.21.0 is selected through nvm
- 33 ordinary tests pass; the live-provider test is skipped unless explicitly enabled
- Live Gate A passed on 2026-09-17: Codex, Qwen, and DeepSeek returned the same
  validated `ResearchPlan`, with reasoning configuration, tracing, and usage metering active
- statement and branch coverage are both 100%
- Ruff passes
- strict mypy passes
- Docker Compose configuration parses successfully
- Git whitespace validation passes

## Intentionally pending

- Live Gate A remains excluded from the ordinary test suite so routine development does not
  consume provider API funds or subscription quota.
- Persistence, Celery wiring, research graph, market data, RAG, backtesting, frontend, and Azure deployment remain deferred to their documented phases.
