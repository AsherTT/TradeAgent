# Phase 6 — Evidence, Thesis, Forecast

Phase 6 begins after the fixture-scoped Gate C qualification. The implementation order is
Evidence Repository, Thesis Lifecycle, then frozen ForecastRecord. Each slice is reviewed and
committed with its tests and this progress record.

## Evidence Repository — implemented offline

Research checkpoints now append each point-in-time eligible evidence item to a relational
`evidence` table in the same transaction as the research state. Ineligible items are removed from
the persisted research state as well. Its UUID and serialized content are immutable: a repeated
identical checkpoint is idempotent, while reuse with different content or another run is rejected.
Instrument identity must match the run. The repository requires an explicit aware cutoff and
only returns items whose observed, available, and published times are no later than that cutoff.
All evidence timestamps must be timezone-aware and indexed timestamps are normalized to UTC.
The table carries a point-in-time lookup index. Alembic migration `0007` also backfills eligible
evidence from existing research-run state and removes future items from legacy state JSON.

Offline tests cover checkpoint persistence, idempotent replay, mutation rejection, instrument
identity, non-UTC offsets, historical backfill, and future-evidence exclusion. No live provider
qualification is claimed by this slice.

## Thesis Lifecycle — implemented offline

Alembic migration `0008` adds `thesis`, `thesis_version`, `thesis_transition`, and
`thesis_evidence`. A Thesis version must originate from a completed research run with Synthesis;
its evidence IDs must be unique citations from that run and present in the evidence repository.
New versions are appended under an expected-version check and a locked Thesis root. Instrument
identity and horizon stay fixed, analysis time cannot move backward, invalidated or superseded
Theses are terminal, and each transition requires a new research run. Earlier versions and
transition history remain queryable; as-of reads require an aware timestamp and hide versions
recorded later. This repository does not infer a direction or probability from Synthesis.

Offline tests cover version history, stale-version rejection, transition rules, source-run
requirements, citation checks, and as-of visibility.

## Next slices

1. Freeze forward ForecastRecords linked to completed research, Thesis, model executions, and
   cited evidence. Keep forecast probability separate from system confidence.
2. Qualify the completed Phase 6 lifecycle across the database and worker boundaries.
