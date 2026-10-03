# Deterministic partial financial assessment — 2026-10-03

This bounded P5 increment explains the two existing financial fractions and exposes
why each is unavailable. It does not add source acquisition or model calls.

## Acceptance contract

- Add two typed metric assessments to the read-only research report, one for annual
  net margin and one for cash/assets. Retain the existing financial_metrics API.
- Available assessments contain the exact existing metric, its two source UUIDs,
  formula, period, filing dates and a deterministic explanation. Annual positive,
  negative and zero net income mean reported profit, loss and break-even respectively,
  for that annual period only. Cash/assets describes the reported asset share, not
  cash flow, unrestricted cash or liquidity sufficiency. Ratios above one are not
  clamped or silently presented as ordinary: attach a reconciliation limitation.
- Unavailable assessments contain no metric or explanation and one bounded reason:
  cutoff unavailable, qualified consistent four-concept group unavailable,
  nonpositive denominator, negative cash, or arithmetic unavailable. Group failure
  must not claim a particular missing concept when conflict/freshness may be the cause.
- Reuse shared admission, latest consistent annual group and Decimal precision 28.
  Do not derive isolated pairs when the four-concept group is incomplete. Invalid
  denominator/cash suppresses only the affected metric. Revalidate at report time;
  exclude wrong Instrument, future, stale, tampered or conflicting evidence.
- Render explanations with individual citations and missing metrics with explicit
  reasons. Keep separately verified business/catalyst gaps, complete_analysis=false,
  market/quant gates and default feature switches. No growth, valuation, investment,
  historical PIT or complete business-analysis qualification is inferred.
- Report JSON must round-trip and remain compatible with old reports lacking the
  new field. Existing derivation and report tests continue passing; new report-boundary
  regressions cover signs, suppression, qualification failures and source lineage.

Review baseline: 79d570808c832ab2c16ac4f61a843e343f771097. No tracker issue is
referenced; this repository document is the review spec source.
