# Phase 6 Qualification

Qualified: 2026-09-28 (Asia/Shanghai), with mock research inputs.

## Result and scope

Phase 6 Evidence Repository, Thesis Lifecycle, frozen ForecastRecord, and the opt-in write
command are implemented. The offline suite and a rebuilt Docker API/Redis/Celery/PostgreSQL path
qualify their storage, prediction provenance, and lifecycle behavior. This does not qualify live market/news/model
providers or claim that real forward forecasts have started accumulating. The write command
remains disabled without `PHASE6_WRITE_TOKEN`.

## Evidence

- Ordinary suite: 193 passed, one opt-in live-model test skipped. Ruff and strict mypy pass.
- API, worker, Beat, and migration images were rebuilt. PostgreSQL Alembic head is
  `0010_phase6_execution_integrity`, applying Evidence, Thesis, Forecast, and execution
  integrity migrations in order.
- The qualification-only mock worker supplied the Phase 5 complete research run through Redis.
  Run `a24f4363-a1b6-4d80-85e2-1ba84bb5e990` completed with persisted evidence and
  structured Synthesis output.
- The token-guarded application command created Thesis
  `46781cfe-b25b-495b-9b0c-d383923811eb` and frozen ForecastRecord
  `8325574f-90ca-407a-8661-aec8ecd8dbca` in PostgreSQL. Thesis and Forecast both cited
  evidence `5c86e504-15c3-4d6b-bd2d-9015f6704c68`. The Forecast's execution ID resolved
  to a persisted Synthesis output with exactly matching direction and probability.
- PostgreSQL rejected direct UPDATE and DELETE of both ForecastRecord and ThesisVersion, and
  a direct UPDATE of ModelExecution, through immutability triggers. The records remained queryable.
- Offline tests cover point-in-time evidence admission and historical backfill, Thesis versions
  and transitions, stale-version rejection, genuine forward-only freezing, later idempotent
  retry, supersession without changing an old record, disabled/invalid write tokens, and
  transactional rollback when a submitted prediction disagrees with model output or historical
  research cannot be frozen as forward. The API commits before acknowledging the write.

The Docker run used `backend/tests/gate_c_container_worker.py` and
`backend/tests/phase6_container_qualify.py` with a temporary qualification-only token. No
external model, market-data, or news request was made. The temporary token and containers were
removed after qualification.
