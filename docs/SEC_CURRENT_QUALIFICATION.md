# SEC current financial qualification — 2026-10-02

The operator supplied an identifying contact User-Agent, configured only in the ignored
local `.env`. Its contact value is not stored in this document, logs, commits or diagnostics.

## Official current-client probe

`python -m backend.tests.sec_current_probe` returned four KLAC annual USD facts and zero
gaps. The exact index resolved CIK 319201; Company Facts matched that identity. All facts
refer to period end 2026-06-30 and 10-K accession `0000319201-26-000027`, filed
2026-08-06. Duration facts cover 2025-07-01 through 2026-06-30. Observed acquisition
was 2026-10-02 10:59:35 UTC (18:59:35 Asia/Shanghai).

The bounded typed diagnostic is retained outside the repository as
`tradeagent-sec-klac-current.json` in the operator temporary directory. It remains explicitly
`complete_analysis=false` and `historical_pit_qualified=false`. Values are current reported
facts, not proof that they were available at a guessed historical instant.

Official sources: [ticker index](https://www.sec.gov/files/company_tickers.json),
[KLAC Company Facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000319201.json),
[filing index](https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/0000319201-26-000027-index.html).

## Real durable current run

Run `9f8326f4-ca4b-4403-8796-f6b6d2ffa0ea` used real local HTTP submission, Redis,
Windows solo Celery, PostgreSQL at migration 0013 and report retrieval. The temporary
owned API/worker were stopped after completion; the local datastore services remain running.

- Intent and planning: two successful real model calls.
- Acquisition: two SEC requests, one news request and one market acquisition.
- Persisted records: four financial facts, eight admitted news records, 43 Yahoo bars.
- Report: twelve source citations, financial observations retained, no synthesis.
- Recorded wall time: 30.17 seconds. Status: `insufficient_evidence`.
- Financial facts were acquired before the frozen cutoff, revalidated for provenance,
  freshness and period consistency, and read back through the report endpoint.
- Market/quant and RAG evidence gaps remain. Yahoo corporate-action quality stays
  `UNVERIFIED`; `complete_analysis=false`. No verified business or catalyst conclusion,
  forward forecast, full model synthesis or complete historical source coverage is claimed.

The successful run used the initial owned-process harness; the reusable asynchronous
version is `backend.tests.local_current_probe`. Ordinary tests never run these probes.
Subscription token/cost metadata are unavailable; zero counters do not prove zero usage.

This supersedes earlier records saying SEC current access was pending contact configuration.
