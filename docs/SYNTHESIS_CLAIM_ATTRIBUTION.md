# Source-bound synthesis claims

This Phase 5 increment adds auditable per-claim attribution without claiming verified
business/catalyst analysis or enabling a complete report.

- ResearchSynthesis accepts at most eight optional typed claims. Legacy persisted
  synthesis without claims remains readable and explicitly lacks individual attribution.
- Each claim has a bounded text, section, one selected/global-cited evidence UUID and
  an exact supporting quote (10–300 characters) from the first 1,000 characters of
  the selected source. Empty/whitespace text and quotes are invalid.
- Section vocabulary is summary, bull_case, bear_case, business, financial, catalyst
  or price. Financial and price claims require financial_fact and market_technical_snapshot
  respectively; catalyst claims require news_document or rag_document. Claim IDs and
  exact quotes must be valid; duplicate claims are rejected.
- The model context supplies evidence_type and escaped excerpts. Instructions ask
  for these optional claims only when supported; source text remains untrusted.
- Graph validation checks claims before checkpointing model output. The report
  rechecks claims against currently eligible evidence. Any invalid claim suppresses
  the entire synthesis and its claims, recording an attribution gap.
- The report provides a typed claims field and per-claim sections with one citation;
  it labels them model interpretations. Supporting quotations prove traceability,
  not factual correctness or source independence. complete_analysis remains false.
- Offline checks cover valid attribution, unknown IDs, absent global citations,
  altered quotes, wrong source types, duplicates, legacy output and report-time
  suppression after source changes or cutoff expiry. No real synthesis success is
  inferred from fixture or live intent/planning qualification.
