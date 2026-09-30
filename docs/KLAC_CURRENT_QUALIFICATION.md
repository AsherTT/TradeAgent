# KLAC current acquisition qualification (2026-09-30)

This is a narrow live provider-composition trial on the local workstation. It is not an
API-to-Redis-to-Celery-to-PostgreSQL run and does not qualify model synthesis or a full report.
The instrument resolver was scoped to KLAC for this probe; no permanent security-master row was
created. The Finnhub key was read from a local ignored `.env` and was not logged or committed.

## Observations

- A direct Finnhub free-tier company-news request returned eight parseable KLAC-linked records
  from an eight-record sample, with publication timestamps and article URLs. The observed
  publication range was 2026-09-24 through 2026-09-29 UTC. This proves this account's key and
  endpoint entitlement worked for the sampled request, not the relevance or accuracy of every
  article.
- The combined current-news-plus-market collection made two provider calls, scanned 19 news
  records, and admitted 19 sanitized `news_document` evidence items. It froze a current cutoff
  after Yahoo acquisition.
- Yahoo returned bars, but the normalized bars inherited `UNVERIFIED` corporate-action quality.
  The technical indicator gate correctly rejected them with
  `IndicatorError: market-bar quality is below ACCEPTABLE`. No market or technical snapshot was
  emitted, so the baseline market requirement remains unsatisfied. News cannot make this a
  complete research run.

## Next qualification steps

1. Qualify a current corporate-action source or a separately defined price mode with evidence of
   action completeness and independent golden cases. Do not promote the Yahoo report by setting
   its quality field to `ACCEPTABLE`.
2. Resolve the market quality gate, then run a current KLAC request through the durable path
   with a configured model to qualify synthesis and its report citations.
3. Assess news relevance and source diversity, then add source-specific financial and catalyst
   evidence with claim-level report citations.

## Durable queue-path observation

An opt-in current-research probe on 2026-09-30 exercised PostgreSQL state creation, Redis
dispatch, a Celery worker, and read-only API state/report retrieval. Run
`2430c488-058c-482e-a4a2-521cc6ef6fe8` used a prepopulated market plan and a zero model-call
budget, so it did not qualify HTTP submission, planning, synthesis, or model output. The worker
used the locally configured Finnhub key without printing or persisting it.

- The worker made two provider calls and persisted 15 eligible Finnhub news documents.
- Yahoo returned 41 bars, with the latest dated 2026-09-29 UTC. The new market-acquisition
  summary persisted the bar count, provider, cutoff, and `UNVERIFIED` quality.
- The indicator quality gate withheld market and technical snapshots. The durable outcome was
  `insufficient_evidence`, and the report did not claim a qualified price analysis.
- The report initially omitted the collected news. A subsequent read-only projection change
  adds a bounded news-observation section with eligible source metadata and explicit unverified
  status; it does not expose article text or convert news into catalyst conclusions.

The reproducible opt-in driver is `backend/tests/klac_current_durable_probe.py`. It needs a
running API, PostgreSQL, Redis, and a worker started with `MARKET_DATA_ENABLED=true` and
`NEWS_ENABLED=true`; the worker must have a Finnhub key in its environment. It uses current
provider data and should not run as part of ordinary tests.

An additional real `POST /research` request, run
`ed73761a-46be-4b22-8295-eb637cbcc7c2`, was accepted through the API and claimed by a
local Celery worker with the configured Codex subscription executor. Its intent call reached
the 120-second wall-time limit and ended in `AllProvidersFailedError`; no plan, provider call,
or synthesis was produced. This demonstrates the HTTP submission and queue claim but does
not qualify live model execution. The public state retains a controlled failure type and
does not expose the underlying SDK error. A reliable model route or a separately defined
server-generated collection-only mode is needed before unseeded live requests can reach
provider acquisition.

The server-generated `collection_only` mode was subsequently implemented and qualified through
real HTTP submission, Redis dispatch, Celery execution, PostgreSQL persistence, and report
retrieval in run `720f6591-8adc-4c3c-8d0a-6392e71f8603`. It made zero model calls and two
provider calls, saved 15 eligible news documents and a 41-bar Yahoo acquisition summary, and
linked eight recent news source records in the report. Yahoo action quality remained
`UNVERIFIED`; the run ended `insufficient_evidence` with no market or technical snapshot and
`complete_analysis=false`. This validates the collection-only path, not model synthesis.

A separate minimal local Codex SDK probe also timed out, confirming the model issue occurs
outside the research graph. The gateway now treats an explicit provider timeout as one failed
attempt and moves to the next configured provider rather than spending another full timeout
window on the same provider. No live model success is claimed.
