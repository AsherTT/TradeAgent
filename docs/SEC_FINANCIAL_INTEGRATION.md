# Current financial research integration

This Phase 5 increment integrates the source-qualified annual financial adapter without
claiming full fundamental analysis. Real source qualification remains separately gated.

## Acceptance

- Default-off `FINANCIALS_ENABLED`, requiring a local identifying `SEC_USER_AGENT` and market
  acquisition to freeze the current cutoff. Fixed-cutoff and evidence-constrained replay never
  acquire current financial data. Permanent identity resolves through SecurityMaster rather
  than the submitted ticker. The SEC index must agree with the returned Company Facts CIK.
- Capture financials before news/market acquisition. Reserve two SEC HTTP calls plus at least
  one market call; charge actual initiated HTTP requests, including controlled failures.
  Pass remaining call/time budget to downstream acquisition; never begin market acquisition
  after financial acquisition exhausts wall time. A shared Redis 250-ms admission slot bounds
  all configured worker SEC requests to four/second; limiter errors prevent external access.
- Reuse the existing committed `collect_evidence` pre-call marker and atomic acquisition
  checkpoint. Interrupted acquisition remains unknown-outcome; do not repeat it. Once a
  completed checkpoint is present, resume must not reacquire even if no evidence was admitted.
- Admit typed numeric `financial_fact` evidence only with matching SEC provenance/content hash,
  acquisition-time timestamps, no future dates, zero injection risk and current freshness:
  period end no older than 550 days and filing date no older than 400 days at the cutoff.
  Evidence outside this policy remains a gap rather than a financial conclusion.
- `financials` / `annual financial facts` coverage requires all four allowed annual concepts
  for one period end and subject CIK, with matching starts for duration facts. It never
  fulfills baseline market or quant requirements.
  Synthesis must select and cite all four required concepts within the eight-evidence limit;
  inability to cover required evidence fails closed.
- The report exposes at most four typed financial observations, each with concept, USD value,
  period, filing date, accession and its own evidence citation. It labels these reported
  observations, not business/catalyst analysis, and retains `complete_analysis=false`.
- Offline checks cover request budgeting, ordering/cutoff, controlled errors, freshness,
  malformed/forged metadata, required-concept coverage, citation omission, report suppression,
  checkpoint redelivery and default-off/fixed/replay worker wiring. Live probes are separate.

The 550/400-day freshness limits are explicit application policy, not SEC guarantees.
