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
2. Run a current KLAC request through the durable API, Redis, worker, and PostgreSQL path after
   the market quality decision is resolved. Record the actual quality gate and model output.
3. Assess news relevance and source diversity, then add source-specific financial and catalyst
   evidence with claim-level report citations.
