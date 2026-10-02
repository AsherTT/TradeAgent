# Explicit lexical-only RAG

Add default-hybrid `RAG_RETRIEVAL_MODE` with optional `lexical_only`. RAG itself
remains default-off and API access remains token guarded. Hybrid mode still requires
the existing configured 384-dimensional embedding service and filters its model ID.

Lexical-only storage writes NULL vector and model provenance, never a zero/padded
vector. Migration 0014 permits both fields NULL together or both populated, retaining
all immutable rows and HNSW behavior. Lexical-only retrieval uses bounded PostgreSQL
English FTS with the same identity, PIT, trust, status, risk and scanner checks;
the query uses at most twelve unique ASCII alphanumeric terms joined by OR, ranked
by English ts_rank. Unsupported languages or all-stopword queries may return no hits.
it may search eligible chunks from all embedding models because it uses no vector.
It never invokes an embedding service. Evidence records the selected retrieval mode.
This mode is keyword retrieval, not multilingual or semantic retrieval qualification.

An opt-in official SEC filing importer resolves the primary 10-K document through its
official filing index, restricts all fetches to the expected SEC accession directory,
rejects redirects and bounded response failures, and captures a labeled bounded text
excerpt. Availability is the actual acquisition completion, not filing-date backfill.
The trusted adapter alone uses verified_source; public uploads remain USER_CONTENT.
Raw files/hashes are retained outside the repository. An excerpt is not the entire filing.
No source instruction is executed, and scanner quarantine blocks indexing.

Opt-in probes: `python -m backend.tests.sec_rag_current_probe` imports an official
KLAC filing start excerpt; `python -m backend.tests.local_current_probe --financials
--rag-lexical` exercises the research graph with at most two model calls and six
tool calls. The importer and graph do not download embedding models or call paid
embedding APIs. The start excerpt may omit important sections and is not a complete filing.

Offline cases cover mode configuration, NULL-vector storage, caller trust, future/source
exclusion, no embedding invocation and importer URI/size/parser guards. Real PostgreSQL
FTS and source acquisition are recorded separately, including any controlled failures.
This increment does not qualify corporate actions or full investment analysis.
