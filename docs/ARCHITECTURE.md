# Architecture Baseline

The source-of-truth architecture is **Agentic Equity Research Workbench v1.1.1 — Quant Integrity + Operational Reliability Hardened** dated 2026-09-16.

This repository has completed Phases 0-4 and implements the first Phase 5 vertical slice. PostgreSQL/pgvector migrations, the API-to-Redis-to-Celery path, point-in-time corporate-action visibility, deterministic price normalization, provider quality gates, and deterministic indicators have passed their local and Docker-backed qualifications. The Phase 5 LangGraph slice adds bounded planning, qualified-evidence collection, durable node transitions, terminal outcomes, and failure persistence without changing the frozen provider boundaries.

## Current boundaries

- FastAPI application skeleton
- strict Pydantic data contracts
- deterministic budget guard
- provider-neutral model gateway
- Codex subscription, Qwen, DeepSeek, OpenAI API, and mock executor boundaries
- bounded retry/fallback and execution metadata
- SQLAlchemy repositories and Alembic migration for the SecurityMaster and research runs
- FastAPI research submission/status boundaries
- JSON-only Celery/Redis queue boundary
- provider-neutral market-data and corporate-action interfaces
- point-in-time-safe corporate-action lookup and deterministic price normalization
- fail-closed provider and per-bar quality gates for strict backtests
- deterministic pandas/NumPy/SciPy technical indicators
- unit and adapter tests

No current component produces investment advice, strategy signals, broker orders, or claims of historical alpha.
