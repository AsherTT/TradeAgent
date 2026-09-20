# ADR-0007: Point-in-time corporate actions and provider-neutral market data

Status: accepted

Permanent instrument identity is separated from temporal symbols, and corporate-action visibility is governed by `available_at <= analysis_timestamp`. Market-data and corporate-action sources implement narrow provider-neutral interfaces; deterministic application code, rather than provider-adjusted close fields, owns price normalization. Split ratios mean new shares per old share, and unsupported or underqualified inputs fail closed so future knowledge or degraded data cannot silently enter strict backtests.
