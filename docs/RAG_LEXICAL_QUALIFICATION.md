# Lexical RAG and declared action material qualification — 2026-10-02

No licensed Daily List export is available. The operator explicitly requested that
interface development continue. The new offline action audit is limited to declared
materials; no current action source is qualified and Yahoo stays UNVERIFIED.

## PostgreSQL and official source

- Migration 0014 succeeded on the local PostgreSQL database, preserving immutable
  rows and allowing genuine NULL embeddings paired with NULL model provenance.
- The rolled-back PostgreSQL probe verified lexical retrieval, foreign-subject and
  future-acquisition exclusion, direct UPDATE/DELETE rejection and invalid NULL-pair
  rejection. All fixture rows were rolled back.
- The official current SEC importer resolved and fetched the primary 10-K from the
  filing index: https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/klac-20260630.htm.
- Document `b37cff1c-b44c-48a8-8359-efd911d9a6f6` was accepted, produced 40 chunks,
  and appeared among eight lexical query hits. Acquisition time was 2026-10-02
  11:36:34 UTC. It was not visible one microsecond before its capture.
- Raw filing SHA256: `c7892130c9358b3729f1909ae59924de9402843d7dc3c33bf4c7151f5c0d5826`.
  Raw HTML and bounded diagnostics remain in the operator temporary directory.
- The indexed data are a labeled start-of-filing excerpt, not the whole filing. No
  historical availability instant is inferred from the form's filing date.

## Real current graph

Run `8f880203-4026-4f06-9b29-1fd7c4e1e754` passed the local HTTP/Redis/Celery/
PostgreSQL/report path with lexical RAG enabled and no embedding service:

- Two successful real model nodes (intent/planning), approximately 29.43 seconds.
- Four external acquisition requests plus one internal RAG retrieval, five tool calls.
- Four financial facts, eight news records, 43 Yahoo bars and nine persisted RAG
  evidence records explicitly marked `lexical_only`.
- Twelve report citations (financial/news). No synthesis was admitted, so retrieved
  RAG chunks were not published as model-supported conclusions.
- The RAG capability gap disappeared. Market/quant gaps remain; the report also
  discloses unavailable verified business/catalyst analysis. Status remains
  insufficient_evidence, complete_analysis=false.
- Temporary API/worker were stopped; local PostgreSQL and Redis remain running.

This demonstrates current source intake and English keyword retrieval without a
paid embedding service. It does not qualify semantic/multilingual retrieval,
corporate-action completeness, full synthesis or investment conclusions.
