# Architecture Baseline

The source-of-truth architecture is **Agentic Equity Research Workbench v1.1.1 — Quant Integrity + Operational Reliability Hardened** dated 2026-09-16.

This repository has completed Phases 0-4 and implements the first Phase 5 vertical slice. PostgreSQL/pgvector migrations, the API-to-Redis-to-Celery path, point-in-time corporate-action visibility, deterministic price normalization, provider quality gates, and deterministic indicators have passed their local and Docker-backed qualifications. The Phase 5 LangGraph slice adds bounded planning, qualified-evidence collection, durable node transitions, terminal outcomes, failure persistence, durable cancellation, and bounded external-attempt records without changing the frozen provider boundaries.

Phase 5 is in progress rather than complete. Planner, market evidence, deterministic quant,
BudgetGuard enforcement, durable transitions, cancellation, external-attempt observability, and
safe terminal outcomes exist. Intent is a bounded persisted model step. A default-off News
ingestion node now enforces document budgets, point-in-time admission, and untrusted-text guards;
event extraction and a qualified live news adapter remain pending. A real Gap Judge, bounded
replanning, and Synthesis remain before Gate C can pass.

ADR-0018 separates immutable fixed-cutoff research from current research whose decision cutoff is
persisted only after evidence acquisition. The transport, state, migration, model context, and
workflow tracer are implemented. The initial production current-acquisition route uses one
request-scoped yfinance history snapshot for bars and observed corporate actions, is qualified only
against offline fixtures, remains default-off, and fails closed when yfinance is not configured.

ADR-0017 permits an isolated frontend clone lab during Phase 5 for early visual and interaction
learning. It does not move the formal product UI out of Phase 10: only reviewed design artifacts
and components may enter `apps/web`, research API integration waits for Gate C, and later screens
wait for their Phase 6-9 contracts.

ADR-0019 keeps current acquisition yfinance-only until another current-capable adapter is
independently qualified. It also assigns the qualified fixed-cutoff cache to each worker process as
a configurable bounded LRU; cache contents are expendable and never authoritative research state.

## Current boundaries

- FastAPI application skeleton
- strict Pydantic data contracts
- deterministic budget guard
- provider-neutral model gateway
- Codex subscription, Qwen, DeepSeek, OpenAI API, and mock executor boundaries
- bounded retry/fallback and execution metadata
- SQLAlchemy repositories and Alembic migration for the SecurityMaster and research runs
- FastAPI research submission/status boundaries
- explicit fixed-cutoff/current-research timestamp intent with a nullable pending decision cutoff
- JSON-only Celery/Redis queue boundary with bounded pending-run reconciliation
- provider-neutral market-data and corporate-action interfaces
- worker-facing fixed-cutoff and current-acquisition seams; fixed requests use whole-request Alpha
  Vantage-to-yfinance fallback, while current acquisition initially uses yfinance only
- explicitly allowlisted operational fallback, fail-closed integrity failures, and provider
  attempts persisted into successful evidence or terminal gap reasons
- quality-version-aware, worker-process-local bounded LRU caching ahead of external providers
- immutable persisted decision cutoffs and final evidence-time validation against the frozen cutoff
- point-in-time-safe corporate-action lookup and deterministic price normalization
- fail-closed provider and per-bar quality gates for strict backtests
- deterministic pandas/NumPy/SciPy technical indicators
- unit and adapter tests
- documented staged frontend strategy; `apps/web` remains unimplemented

No current component produces investment advice, strategy signals, broker orders, or claims of historical alpha.
