# Gate B Qualification

Qualified: 2026-09-18 (Asia/Shanghai)

## Scope

Gate B qualifies the deterministic market-data foundation, not a live data vendor or an investment-advice workflow. The qualified seams are provider-neutral market bars, point-in-time corporate actions, explicit price-adjustment modes, provider quality enforcement, and deterministic technical indicators.

## Evidence

- Ruff passes across the repository.
- Strict mypy passes across `backend/app`.
- 64 ordinary tests pass and the opt-in live model test remains skipped.
- Statement and branch coverage are 100%.
- Golden cases cover ordinary splits, reverse splits, cash dividends, symbol changes, delistings, future-unavailable actions, duplicates, invalid events, and degraded data.
- `docker compose config --quiet` passes.
- PostgreSQL migration reaches `0004_phase4_constraints`; point-in-time lookup indexes and
  corporate-action value constraints exist.
- The PostgreSQL `vector` extension remains installed.
- API and worker images rebuild with NumPy, pandas, and SciPy and run as UID 10001.
- API health and Celery worker inspection ping pass.

## Qualified limitations

- In-memory adapters are qualification fixtures, not live vendor integrations.
- `STOCK_DIVIDEND`, `MERGER`, and `SPINOFF` numeric normalization fail closed until explicit golden-case semantics are approved.
- The Phase 4 indicator set is deterministic descriptive analysis; it does not produce a trading signal or claim historical alpha.
- Agent orchestration begins in Phase 5.
