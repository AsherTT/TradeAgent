# SEC financial source qualification

Research date: 2026-10-01 (Asia/Shanghai). This document separates verified SEC
semantics from conservative TradeAgent admission rules. It supports the narrow
[current financial slice](SEC_FINANCIAL_SLICE.md), not historical backtests or
completed fundamental analysis.

## Verified official source semantics

SEC exposes unauthenticated JSON submissions and XBRL APIs. CIKs in API URLs
have ten digits with leading zeros. Company Facts combines an entity's
standard-taxonomy, entity-wide concepts; facts are grouped by reported unit.
Custom concepts and dimensional detail are outside that aggregation. Frames
align observations with calendar periods and select the last filed fact, so
frame membership is not a fiscal-period or historical-availability proof.
SEC reports typical delays below one second for submissions and one minute for
XBRL, with potentially longer delays at peak times; APIs are updated as filings
are disseminated. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

CIKs identify filers and are not recycled. SEC periodically updates the ticker
association files without guaranteeing their accuracy or coverage. An accession
identifies a submission; its leading CIK can belong to a filing agent rather
than the subject company. SEC documents filing archive paths and notes that
corrections and removals can alter current indexes. [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

The present official ticker index identifies `KLAC`, `KLA CORP`, CIK `319201`.
Its API form is `0000319201`. [SEC ticker index](https://www.sec.gov/files/company_tickers.json)
The official annual filing index independently identifies KLA CORP and that
CIK, accession `0000319201-26-000027`, form 10-K, filing date 2026-08-06,
report period 2026-06-30, and a separately displayed acceptance time. It links
the original annual report and extracted XBRL instance. [KLA 2026 filing index](https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/0000319201-26-000027-index.html)

## Endpoint and identity policy

The following are implementation rules, not SEC guarantees:

| Purpose | Allowed official endpoint | Qualification |
| --- | --- | --- |
| Current ticker lookup | `https://www.sec.gov/files/company_tickers.json` | Exact normalized ticker; one unique positive CIK; preserve source and acquisition time. |
| Filing metadata, future extension | `https://data.sec.gov/submissions/CIK0000319201.json` | Require payload CIK agreement; join facts by exact accession, never by accession prefix or period alone. |
| Current facts | `https://data.sec.gov/api/xbrl/companyfacts/CIK0000319201.json` | Require payload CIK agreement and valid entity name; retain the exact returned facts and provenance. |

Only build URLs from validated CIKs and fixed official host/path templates.
Never accept caller-supplied hosts, redirects, or document paths as acquisition
targets. A unique current ticker match qualifies only current identity. It does
not establish historical ticker identity, mergers, symbol changes, or listing
continuity. Missing, duplicate-CIK matches, malformed identity records, or
payload disagreement are explicit failures rather than guessed identities.

Submissions is researched here for provenance and later qualification work;
the initial standalone current-facts client needs only ticker and Company Facts
requests. It does not claim that accession joins or historical source validation
have been implemented.

## Availability and point-in-time policy

Company Facts observations include filing dates, but the API documentation does
not promise an exact historical public-availability timestamp for each fact.
API processing can lag filing dissemination. The official EDGAR access guide
also describes some late submissions disseminated the next business day.
[SEC API update schedule](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
[EDGAR dissemination rules](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

Consequently, the following conservative rules are project inference/policy:

- Keep `period_start`/`period_end`, `filed_date`, optional filing acceptance
  metadata, and `retrieved_at` as distinct concepts. Period end is an accounting
  date; filing date has no intraday precision. Acceptance describes filing
  handling, not the time that this Company Facts observation was available.
- Set `observed_at`, `retrieved_at`, and `available_at` to successful completion
  of the actual acquisition. Do not backdate any of them to `filed`, fiscal year,
  report period, frame label, an estimated delay, or acceptance time.
- Evidence may be admitted only when `available_at <= cutoff`. A download made
  today cannot support a cutoff yesterday even when every filing is older.
  Persisted, verifiable earlier captures may later support their own acquisition
  cutoffs, but today's API cannot reconstruct them.
- Reject impossible/future filing or period dates relative to acquisition.
  Date-only comparisons must use a declared calendar basis; they must never
  fabricate an instant from the date. The acquisition instant remains decisive.
- No fixed next-day delay qualifies historical intraday PIT. Joining submissions
  or reading a filing header alone is insufficient: any future historical mode
  must qualify public dissemination, API availability, immutable captures, and
  changes after corrections separately.
- Retain later revisions as observations acquired later. Never let revised facts
  enter an earlier cutoff by selecting the latest value for an old period.

## Narrow fact admission and revision rules

These restrictions are deliberately narrower than SEC's API capabilities and
are TradeAgent design choices:

| US-GAAP concept | Allowed unit | Period shape |
| --- | --- | --- |
| `Assets` | `USD` | Instant, valid end, no start. |
| `CashAndCashEquivalentsAtCarryingValue` | `USD` | Instant, valid end, no start. |
| `NetIncomeLoss` | `USD` | Duration, valid start/end, 350–380 inclusive calendar days. |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | `USD` | Duration, valid start/end, 350–380 inclusive calendar days. |

Admit only 10-K and 10-K/A observations with finite numeric values, valid ISO
dates, and a syntactically valid accession. Preserve taxonomy, exact concept,
unit, period, value, form, filing date, and accession. Preserve `fy`, `fp`, and
`frame` when used or retained as metadata, but never let these substitute for
the actual period dates. A 10-K can repeat older comparison periods; `fy` may
describe the filing's fiscal year rather than the observation's period.
Duration eligibility must be derived from start/end, not only `fp=FY`.

Do not derive fourth quarters, sum YTD records, convert currencies, rescale
values by filing display headings, or substitute superficially similar tags.
Unsupported units, concepts, forms, and nonannual durations are excluded and
reported as gaps where appropriate. Missing exact concepts remain gaps.
Malformed records within the supported USD annual slice are rejected explicitly;
they must not silently create a successful partial qualification.

Deduplicate identical semantic observations (concept, unit, period, accession,
filing date, form, value). For a concept/unit/period, prefer a later filed
observation only for the current acquired snapshot. Same-period, same-filed-date
contradictory values are ambiguous even if accessions differ: reject rather than
invent intraday revision order. Same-accession contradictions also fail. Choosing
a later observation means latest reported value, not necessarily an explicit
restatement; do not claim all 10-K/A filings revise every financial concept.

The frames API's calendar-alignment rules are broader than this project's
350–380-day annual rule. No `frame` presence or absence independently admits
or rejects a valid annual period. [SEC frames documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## Provenance back to raw SEC filings

Each admitted fact must keep its Company Facts acquisition URL and a filing
index link built from subject CIK and the fact's exact accession:

`https://www.sec.gov/Archives/edgar/data/{cik_without_leading_zeros}/{accession_without_dashes}/{accession}-index.html`

For the verified example, the [filing index](https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/0000319201-26-000027-index.html)
links the [original 10-K](https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/klac-20260630.htm).
Archive path conventions come from the [SEC access guide](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).
Generated index URLs are provenance locators, not proof that the client fetched
or validated those indexes. Do not assert primary-document inspection without
performing it. Never infer the subject CIK from the accession's first digits.

## Transport, limits, and failure policy

SEC asks automated clients to identify themselves in `User-Agent`, including an
organization/contact. It limits each user to no more than ten requests per
second across machines and may block excessive traffic.
[Declared User-Agent guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
[aggregate fair-access policy](https://www.sec.gov/about/developer-resources)

TradeAgent policy: require a configured identifying User-Agent with a real
operator contact; make no request if absent. The contact is configuration,
not a secret, but need not be printed in diagnostics. Restrict a standalone
client to at most five requests per second, bounded timeout and body size,
HTTPS official endpoints, no redirects, and no automatic retry. A per-client
limit alone cannot guarantee SEC's aggregate limit; multi-worker deployment
requires a shared budget/limiter before worker wiring.

Reject timeout, connection/TLS errors, HTTP non-success (including 403/429),
redirects, oversized bodies, non-JSON/block-page responses, malformed JSON,
invalid schema, identity conflicts, unsupported cutoff, and ambiguous facts
with bounded diagnostics. Do not replace a failed live request with an
unmarked cached fixture, request through proxies to evade blocking, or treat
empty facts as completed analysis. All diagnostics must distinguish unavailable
source access, no supported facts, and successful current acquisition.

## KLAC verification status and acceptance boundaries

On the research date, the browser research tool retrieved the official ticker
index and KLA filing index. Its Company Facts and Assets company-concept opens
returned a tool-level internal/unavailable error; its submissions open exposed
no readable payload. These observations do not prove an SEC outage, specific
HTTP status, or successful access from the production client. Numeric financial
values were not qualified by this research.

An opt-in real client probe must use its declared User-Agent, the two acquisition
endpoints above, and the same admission rules as offline qualification. Report
exact success/failure honestly and write bounded diagnostics outside the repo.
Offline fixtures must cover current identity, mismatches, units, instant and
annual periods, YTD/quarter exclusion, duplicates, amendments, same-date
conflicts, future dates, acquisition cutoff exclusion, and transport limits.

Successful SEC acquisition supplies a narrow set of current reported financial
evidence only. It does not supply adjusted market prices, company actions,
technical evidence, complete financial statements, or an investment conclusion.
