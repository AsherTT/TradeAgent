# Phase 5 Research Workflow

The first Phase 5 slice turns a persisted research request into a bounded durable LangGraph run.
It is deliberately provider-neutral and does not claim investment advice or live-data support.

## Graph

1. `start` changes a pending run to running and consumes one iteration.
2. `plan` checks the relevant budget and calls a model only through `ModelGateway`.
3. `collect_evidence` optionally loads point-in-time bars through `MarketDataService`, then calls
   the deterministic indicator implementation.
4. `finish` records a complete or insufficient-evidence quality assessment.

Each externally visible transition is saved by `ResearchRunRepository`. The API commits the run
before publishing its task and persists queue-dispatch failures. A database execution lease admits
only one worker at a time; busy or not-yet-visible deliveries retry without a fixed retry limit.
The Celery composition commits after every transition so a later delivery can resume from the
persisted plan or evidence. Already-terminal runs return unchanged.

The database commit and queue publication are not yet atomic. If the API process exits after the
commit but before publication, the run can remain pending until an operator intervenes. A
transactional outbox or pending-run reconciler is required before this queue boundary is considered
production hardened; ordinary publication errors are already persisted as failed runs.

Before a model or evidence provider is called, the graph persists an external-attempt marker. If a
worker disappears after that boundary, a later delivery records an inspectable unknown-outcome
failure instead of repeating a possibly completed and billable external call. An expired worker
cannot overwrite a newer owner because every save verifies the execution lease.

## Outcomes

- `complete`: a validated plan and qualified evidence are both present.
- `insufficient_evidence`: planning may have succeeded, but qualified evidence is unavailable.
- `failed`: execution raised an error; the type and message are saved with a blocked quality
  assessment.
- Budget exhaustion uses `insufficient_evidence` as the run status and
  `budget_exhausted` as the more precise research-completion reason.

The production worker currently has no live market-data adapter, so it cannot honestly produce a
live-stock `complete` result. Offline qualification supplies deterministic mock model output and
qualified in-memory market data. Live model tests and providers remain opt-in because they may
consume credentials or quota.

The Docker-backed qualification submits a run with `max_llm_calls=0`. This exercises the real API,
Redis, Celery, and PostgreSQL path and reaches durable `budget_exhausted` completion without making
a model or provider call.
