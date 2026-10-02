# Architecture Baseline

The source-of-truth architecture is **Agentic Equity Research Workbench v1.1.1 — Quant Integrity + Operational Reliability Hardened** dated 2026-09-16.

Current audit (2026-10-02): Phases 6–9 have their recorded fixture qualifications;
Phase 5 live completion remains open and Phase 10 has not started. Current model
intent/planning, news and SEC financial acquisition have passed the real local
HTTP/Redis/Celery/PostgreSQL path. Corporate-action completeness, live RAG inputs and
verified financial/catalyst analysis still prevent a complete report. See
`docs/DEVELOPMENT_PROGRESS_20261002.md` for the current layer-by-layer assessment.
The stage descriptions below retain their original implementation context.

Subsequent current-source qualification added explicit lexical-only RAG without
embeddings. Official SEC filing excerpt intake and PostgreSQL FTS/PIT storage were
verified through the real research graph, removing its RAG gap. The optional hybrid
route remains available but has no live embedding qualification. An offline action
material audit supplies intake diagnostics, never provider qualification. Market/action
completeness and verified analysis still prevent a complete report. See
`docs/RAG_LEXICAL_QUALIFICATION.md` and `docs/ACTION_COVERAGE_AUDIT.md`.

This repository has completed Phases 0-4 and implements the first Phase 5 vertical slice. PostgreSQL/pgvector migrations, the API-to-Redis-to-Celery path, point-in-time corporate-action visibility, deterministic price normalization, provider quality gates, and deterministic indicators have passed their local and Docker-backed qualifications. The Phase 5 LangGraph slice adds bounded planning, qualified-evidence collection, durable node transitions, terminal outcomes, failure persistence, durable cancellation, and bounded external-attempt records without changing the frozen provider boundaries.

Phase 5 is in progress rather than complete. Planner, market evidence, deterministic quant,
BudgetGuard enforcement, durable transitions, cancellation, external-attempt observability, and
safe terminal outcomes exist. Intent is a bounded persisted model step. A default-off News
ingestion node now enforces document budgets, point-in-time admission, and untrusted-text guards;
event extraction and a qualified live news adapter remain pending. A deterministic Gap Judge now
checks required plan capabilities against eligible evidence and records coverage. A bounded
model-assisted Replan can retry missing required News without removing original requirements;
evidence-cited Synthesis now runs only after sufficient coverage. Gate C passes with offline
loop-safety tests and a mock-provider Docker API/Redis/Celery/PostgreSQL complete path; live
provider qualification remains separate.

Phase 6 has append-only relational evidence persistence, explicit point-in-time reads, versioned
Thesis memory, a forward-only ForecastRecord repository, and an opt-in, token-guarded application
command. Forecast freezing now requires the Thesis prediction to match one immutable, persisted
Synthesis model execution and its structured output. PostgreSQL blocks direct changes to Thesis
history, model execution history, and Forecast records. The rebuilt Docker
API/Redis/Celery/PostgreSQL mock path has passed qualification. Phase 6 implementation is complete
within that fixture scope;
live provider qualification and real forward accumulation remain separate. Phase 7 Secure RAG
has begun with bounded document intake, prompt-injection quarantine, and append-only
document/chunk storage with pgvector and FTS indexes. PIT-filtered hybrid retrieval and a
bounded untrusted ContextBuilder exist. Default-off guarded APIs and a durable RAG research
node are integrated. Gate D and PostgreSQL/pgvector retrieval are fixture-qualified; real
embedding and live document providers remain separate. Phase 8 replay/evaluation follows.

ADR-0018 separates immutable fixed-cutoff research from current research whose decision cutoff is
persisted only after evidence acquisition. The transport, state, migration, model context, and
workflow tracer are implemented. The initial production current-acquisition route uses one
request-scoped yfinance history snapshot for bars and observed corporate actions, is qualified only
against offline fixtures, remains default-off, and fails closed when yfinance is not configured.

ADR-0017 permits an isolated frontend clone lab during Phase 5 for early visual and interaction
learning. It does not move the formal product UI out of Phase 10: only reviewed design artifacts
and components may enter `apps/web`. Gate C now permits research API integration; later screens
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

Phase 9 produces restricted deterministic fixture signals and a non-executable
TradeIntent. No component places broker orders or establishes historical alpha;
current reports do not establish complete investment analysis.
