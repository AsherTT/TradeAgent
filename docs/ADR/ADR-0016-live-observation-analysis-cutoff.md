# ADR-0016: Live observations do not move a frozen analysis cutoff

Status: accepted

## Context

A research run currently freezes `analysis_timestamp` when the API accepts the request. A worker
may fetch market data later because queueing and provider requests take time. The free-provider
adapters conservatively record the actual `observed_at` and use it as the earliest defensible
`available_at` when the provider does not supply a qualified historical publication timestamp.
Consequently, a record first observed after the frozen analysis cutoff is not point-in-time
eligible for that run, even when its market timestamp is earlier.

## Decision

Keep `analysis_timestamp` as the information cutoff and continue to require
`available_at <= analysis_timestamp`. A queue-delayed observation made after that cutoff produces
insufficient evidence. A retrieval timestamp may be retained for provenance and operations, but
must not act as a second eligibility cutoff or override the point-in-time invariant.

The existing API contract therefore supports fixed-cutoff and historical research safely, but the
default current-research path is not considered live-data qualified. ADR-0018 defines the explicit
current-research mode in which evidence acquisition completes before the decision cutoff is frozen,
while keeping an explicitly supplied historical cutoff immutable.

## Consequences

- Routine and Docker qualification remain offline and keep market data disabled by default.
- A worker observation after the run cutoff cannot be admitted merely to make a live trial pass.
- Recorded live-provider qualification still requires separate user authorization.
- Current-research usability needs a later contract change; it is not solved by provider-specific
  timestamp exceptions.
