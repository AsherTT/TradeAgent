# ADR-0005: Celery and Redis background jobs

Status: accepted

Celery is the background-job boundary for research runs and Redis is its broker and transient
result backend. Messages use JSON serialization only, late acknowledgement, worker-loss
rejection, UTC timestamps, and application-specific key prefixes. Redis is not a source of truth
for research state or long-term memory; durable state belongs in PostgreSQL.

The Phase 3 worker task establishes the queue boundary only. LangGraph execution is introduced in
Phase 5. Phase 3 closes after API submission, Redis delivery, Celery execution, and PostgreSQL
visibility are qualified together through the Docker Compose stack.

## Phase 5 pending-run reconciliation

The API commits a research run before publishing its Celery task. To recover from a process exit
between those actions, one Celery Beat scheduler periodically publishes IDs of old, unclaimed
`pending` runs. The query is ordered and bounded; publication does not change run state. Worker
leases make duplicate deliveries safe, including when a second scheduler briefly overlaps during
deployment. A broker failure leaves the run eligible for the next tick.

Compose owns the single normal scheduler instance. Its local Beat schedule file lives at
`/tmp/celerybeat-schedule`, which is writable by the non-root image user and is expendable on
restart. PostgreSQL remains the source of truth for run state; the schedule file stores no
research payload or credential. Interval, grace period, and batch size are environment settings.
