# Phase 8 PostgreSQL outcome-storage qualification

Date: 2026-09-29. Local Docker Desktop PostgreSQL 18 with pgvector.

- Reconnected the local Docker engine and started the existing `tradeagent-postgres-1`
  container without replacing its data volume.
- Confirmed Alembic started at `0011_phase7_rag_storage`, upgraded it to
  `0012_phase8_outcome_record`, and confirmed `0012` is the database head.
- Inserted one synthetic Outcome row against an existing fixture Forecast inside a
  transaction. Direct SQL UPDATE and DELETE both raised the PostgreSQL
  `outcome records are immutable` trigger error. The transaction was rolled back;
  a follow-up read confirmed that the synthetic Outcome was absent.
- An insert referencing a nonexistent Forecast failed the PostgreSQL foreign key.
- With a synthetic future clock and observation against an existing fixture Forecast,
  `OutcomeRepository.record` derived the Outcome, accepted an exact retry, and the
  transaction was rolled back. A follow-up read confirmed no Outcome remained.
- The configured cohort reader returned one existing fixture Forecast, zero Outcomes,
  `ACCUMULATING` maturity, and all ten empty buckets from PostgreSQL.
- Upgraded from `0012` to `0013_phase8_outcome_observation`. A synthetic source
  observation passed through `PersistedOutcomeSource` and the due runner into an
  OutcomeRecord. PostgreSQL rejected direct UPDATE and DELETE of the observation;
  the observation and Outcome were both rolled back and confirmed absent.
- After adding observation-backed candidate selection and Forecast row locks, the
  due runner again produced one Outcome on PostgreSQL; a second run produced zero.
  Both rows were rolled back and confirmed absent.
- A linked synthetic observation and Outcome were read through the configured cohort
  reader in the same transaction. It reported one sample and `ACCUMULATING` maturity;
  the transaction was rolled back afterward.

This qualifies the migration, repository write/read, foreign key, and direct-mutation
trigger on the local container. It does not evaluate a real forecast, qualify a live
observation provider, or establish forward prediction performance.
