# Current corporate-action material audit

This is an offline intake/audit seam, not a provider qualification or Daily List parser.
It has no network access and never changes Yahoo's UNVERIFIED quality report.

A trusted caller supplies permanent subject identity, aware UTC window/cutoff, an
explicit sorted session calendar with first/last session bounds and a calendar source
URI/hash. Calendar accuracy is an external prerequisite, not inferred from weekdays.
At most 400 sessions and 1,201 bounded file artifacts are accepted (10 MB total).
The bundle source is Nasdaq Daily List with a specification version and matching identity.

Each artifact has kind, session date, actual raw bytes/SHA256, observation time, source
revision closure and explicit parser attestations: records understood, records complete,
revision chain closed, and either data rows or explicit no-update proof. Empty raw bytes,
missing hash, duplicate slots, unavailable files, unknown records, truncated files,
missing no-update evidence and open revisions fail material checks.

Required artifacts: an outstanding-announcement baseline from before the first session,
plus equity, dividends and next_day files for each supplied session. This catches future
effective events announced before the window. Every artifact must be observed by cutoff
and closure must cover the requested window end without exceeding observation time.

The result lists deterministic gaps and reports material_checks_passed only for the
declared prerequisites. Caller/parser attestations and calendar hash are not independently
authenticated. provider_qualified and historical_pit_qualified always remain false;
no actions, price adjustments or coverage=1 quality report are generated. A real parser,
licensed export, source semantics review, independent positive cases and price-unit
reconciliation are still required before considering a current qualified provider.
