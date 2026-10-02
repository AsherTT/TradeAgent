# Research report projection

`GET /research/{research_run_id}/report` returns a read-only projection of the persisted
research state. It does not call a model or provider, change budgets, or create a new research
artifact. Unknown IDs return 404. Pending, failed, cancelled, and insufficient-evidence runs
return an explicit incomplete report rather than a fabricated analysis.
For `collection_only` submissions, the status section explicitly says no model synthesis was
requested.

The endpoint lists the frozen analysis cutoff, run status, data quality, quality-gate decision,
recorded gaps, and point-in-time eligible metadata for evidence cited by a completed synthesis.
It includes the persisted summary and bull/bear cases only when every synthesis citation is
still eligible at the cutoff. Their citation IDs support the synthesis as a whole.
Optional source-bound model interpretation claims are specified in
`docs/SYNTHESIS_CLAIM_ATTRIBUTION.md`; each has its own supporting quote and citation.
Claims establish attribution, not verified analysis. Invalid attribution suppresses the
entire synthesis and claims. Supporting quotes are bounded excerpts; full untrusted source
text is not reproduced. Eligible news documents receive a metadata-only
observation section with at most eight recent source links. Their presence does not verify a
catalyst. If a synthesis citation is no longer eligible, the
report suppresses all synthesis text and citations and adds an explicit citation gap.

The price section shows stored technical values only when both the run and latest bar are at
least `ACCEPTABLE` and a cited market/technical evidence item is eligible. Business/financial
and catalyst sections explicitly disclose that no separately verified analysis is available.
The market acquisition section can show provider, bar count, dates, and quality when a provider
returned bars that failed the technical gate. It does not show an unqualified price or count as
market evidence.
`complete_analysis` remains false until those source-specific sections, claim-level citations,
and freshness checks are implemented and qualified. This endpoint must not be presented as a
complete KLAC investment report.

The default-off SEC current financial integration now adds at most four typed annual
financial observations. Each shows its own fact citation, USD value, reporting period,
filing date, form and accession. Admission checks provenance, cutoff, freshness and
consistent entity/period; duration concepts must share their start date. These are raw
reported facts and do not establish business analysis or historical point-in-time coverage.
See `docs/SEC_FINANCIAL_INTEGRATION.md` for the acceptance contract.

Next work: qualify a source for current corporate actions without promoting Yahoo's
`UNVERIFIED` action report by fiat; run the live API/worker/Redis/PostgreSQL path with an
authorized model and provider configuration; add typed financial and catalyst evidence; extend
the synthesis contract for section-specific claims and citations.
