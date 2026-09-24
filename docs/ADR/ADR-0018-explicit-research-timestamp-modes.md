# ADR-0018: Explicit fixed-cutoff and current-research timestamp modes

Status: accepted

## Context

ADR-0016 keeps `analysis_timestamp` as the only information-eligibility cutoff. A run that freezes
that cutoff when the API accepts the request cannot admit an observation first made later by a
queued worker. Moving the cutoff implicitly, or adding a separate retrieval cutoff, would weaken
point-in-time semantics and make replay ambiguous.

## Decision

Research submission and persisted state distinguish two timestamp modes:

- `fixed_cutoff` freezes an explicit (or API-assigned) `analysis_timestamp` at submission. It is
  immutable for the lifetime of the run.
- `current_research` persists `requested_at` but leaves `analysis_timestamp` absent until a
  current-capable evidence adapter finishes acquisition. After the adapter returns qualified data,
  the evidence orchestration module reads its trusted clock, validates the result against that
  acquisition-completion instant, freezes it as the cutoff, and persists it in the same transition
  as the evidence derived from it.

All admitted records still satisfy `available_at <= analysis_timestamp`; market timestamps must
also be no later than the frozen cutoff. A retrieval timestamp is provenance only. It never acts
as an eligibility cutoff.

The transport makes `timestamp_mode` explicit. A supplied `analysis_timestamp` is valid only for
`fixed_cutoff`; the API assigns the acceptance time when that mode omits it. Current research
rejects a caller-supplied cutoff. Persisted current-research runs therefore have a nullable cutoff
only while acquisition is pending or when they terminate before evidence acquisition.

The planning model receives the mode, `requested_at`, and either the frozen cutoff or an explicit
`pending_evidence_acquisition` marker. It must not infer a cutoff from wall-clock time.

A current-capable evidence adapter is a separate seam from fixed-cutoff loading. It returns data,
not a caller-selected cutoff. The evidence orchestration module owns cutoff selection and validates
every returned record against its post-acquisition clock reading. For multiple sources, the selected
cutoff is read after all selected observations exist; source-specific observation and availability
timestamps remain attached to each record. A later multi-source aggregator may choose an earlier
cutoff, but never one earlier than an admitted record's `observed_at` or `available_at`.

The external-attempt marker is persisted before acquisition. If a worker disappears before the
evidence-and-cutoff transition is saved, redelivery keeps the existing unknown-outcome failure
behavior and does not repeat the call. Once frozen, the cutoff is never recomputed. Replay uses the
persisted cutoff and ordinary fixed-cutoff eligibility rules.

If acquisition completes and establishes an auditable observation time but downstream
qualification or deterministic indicator construction yields no evidence, the workflow may still
persist the frozen cutoff and terminate as `insufficient_evidence`. This records what the failed
decision attempt could have known and prevents a replay from silently selecting a later cutoff; it
does not make the run complete or authorize retrying the external acquisition.

Current acquisition does not read or write the qualified fixed-cutoff cache before cutoff
selection. After the cutoff is frozen, cache identity remains the existing identity including
instrument, window, adjustment mode, strictness, provider qualification versions, and the exact
`analysis_timestamp`.

## Consequences

- Historical requests preserve their existing point-in-time behavior.
- A current-research run can survive queue delay without pretending the request-acceptance time was
  the final knowledge cutoff.
- Current mode remains fail closed unless the configured evidence adapter explicitly implements
  current acquisition.
- Offline tests may qualify the contract without enabling a live provider. Live qualification and
  credentials still require separate authorization.
- `research_run.analysis_timestamp` becomes nullable while the complete serialized state remains
  authoritative for timestamp mode and request time.
