# ADR-0019: Current-provider fallback and qualified-cache ownership

Status: accepted

## Context

The fixed-cutoff route has two independently qualified provider adapters and can safely retry a
complete request after an allowlisted operational failure. Current research initially has only one
qualified acquisition adapter. Adding a nominal fallback without a second current-capable adapter
would create configuration that cannot deliver the behavior it advertises.

The qualified fixed-cutoff cache improves latency and reduces provider usage, but cached data is
not authoritative. Every key already includes the exact analysis cutoff, request window,
adjustment mode, strictness, provider, and bar/action qualification versions. A cache miss must be
behaviorally equivalent to a process restart.

## Decision

- Current research remains yfinance-only. A fallback candidate may be added only after its
  current-acquisition adapter has its own offline provider qualification and returns a complete
  request result through the existing current-acquisition seam. Integrity failures remain terminal.
- The fixed-cutoff qualified cache is owned by each worker process. It is not persisted in
  PostgreSQL or shared through Redis because it is an expendable optimization, not evidence or
  replay state.
- The process-local cache is a configurable bounded LRU. The default limit is 256 complete request
  results. Reads refresh recency; inserting beyond the limit evicts the least recently used entry.
- Current acquisition continues to bypass this cache until the evidence orchestrator has selected
  and persisted an analysis cutoff, as required by ADR-0018.

## Consequences

- Configuration does not imply a current fallback that has never been qualified.
- Worker restart, scale-out, or eviction can increase provider calls but cannot change research
  correctness. Provider budgets and external-attempt markers remain authoritative.
- Cache memory is bounded independently in every Celery worker process. A deployment can lower the
  bound through `MARKET_DATA_CACHE_MAX_ENTRIES` or disable the cache entirely.
- A shared durable cache can be reconsidered only if measured provider pressure justifies the
  extra invalidation, concurrency, and operational ownership.
