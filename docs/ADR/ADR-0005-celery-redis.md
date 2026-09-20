# ADR-0005: Celery and Redis background jobs

Status: accepted

Celery is the background-job boundary for research runs and Redis is its broker and transient
result backend. Messages use JSON serialization only, late acknowledgement, worker-loss
rejection, UTC timestamps, and application-specific key prefixes. Redis is not a source of truth
for research state or long-term memory; durable state belongs in PostgreSQL.

The Phase 3 worker task establishes the queue boundary only. LangGraph execution is introduced in
Phase 5. Phase 3 closes after API submission, Redis delivery, Celery execution, and PostgreSQL
visibility are qualified together through the Docker Compose stack.
