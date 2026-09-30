# SEC current financial evidence slice

This Phase 5 slice adds an independently testable SEC Company Facts acquisition boundary,
not a completed research report or a historical financial database. It is default-unwired
from the worker until durable budgeting and financial gap/synthesis contracts are qualified.

## Acceptance requirements

- Resolve an exact current ticker from SEC's official company ticker index to one unique CIK;
  require payload CIK agreement. A current index cannot resolve historical symbol identity.
- Request only official HTTPS endpoints with an explicit identifying User-Agent, no redirects,
  bounded timeout/response size and at most five requests/second per client. No automatic retry.
  Production multi-worker usage needs a shared limiter before wiring this client.
- Admit only USD US-GAAP Assets, CashAndCashEquivalentsAtCarryingValue, NetIncomeLoss and
  RevenueFromContractWithCustomerExcludingAssessedTax in 10-K/10-K/A annual observations.
  Duration facts need 350–380 inclusive calendar days; instant facts have no start.
  Do not derive quarters, substitute taxonomy concepts, or interpret business conclusions.
- Retain exact concept, value, unit, period, form, filing date, accession and SEC filing index URL.
  Values must be finite numbers. Reject malformed supported USD annual records, identity errors
  and contradictory values with the same period and filing date; missing concepts remain gaps.
- Deduplicate identical observations and prefer later filed revisions for the same concept/period.
  Reject future periods/filing dates; latest observations remain explicitly current reported values.
- Company Facts provides filing dates, not a guaranteed public dissemination instant.
  Use completion of acquisition for observed/retrieved/available timestamps. Never backdate
  availability to period end or filing date; no historical qualification is claimed.
- Conversion to typed financial evidence requires a cutoff at or after acquisition, preserves
  all provenance and never fulfills market/technical requirements or enables complete analysis.
- Offline golden cases verify annual versus YTD/quarter periods, amendments, conflicts, units,
  identity, malformed data, transport limits and future/cutoff exclusion. A separate opt-in
  KLAC probe makes only two requests, saves a bounded diagnostic outside the repository and
  reports unavailable access honestly. No model, database or credential is required.

Official API semantics and sources are recorded in SEC_FINANCIAL_SOURCE.md.

Offline implementation and dual-axis review results are recorded in
SEC_FINANCIAL_REVIEW.md. Live qualification is still pending the operator's
identifying User-Agent; the opt-in probe made no request without that setting.
