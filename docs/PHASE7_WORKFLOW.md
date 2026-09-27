# Phase 7 — Secure RAG and Gate D

Phase 7 follows the fixture-qualified Phase 6. The architecture requires bounded parsing,
sanitization, injection scanning, trust metadata, chunking, embeddings, PostgreSQL FTS and
pgvector retrieval, RRF, and a ContextBuilder. Gate D requires isolated untrusted content,
quarantine of high-risk content, structural permission invariants, and recorded red-team metrics.

## 1. Document intake — implemented offline

`RagSource` accepts bounded UTF-8 HTML, Markdown, text, JSON, and PDF bytes. PDF parsing is
limited to 40 pages; every source is capped at 2 MB and 64 resulting chunks. The intake path
normalizes Unicode, removes hidden/script HTML, preserves section headings, requires aware
timestamps and safe HTTPS source URIs, and hashes the cleaned content. SEC filing URIs must use
`sec.gov`. Caller-provided bytes are `USER_CONTENT` by default; only a trusted adapter may pass
`verified_source=True` to classify verified SEC or public content at a higher trust level.

The versioned scanner detects instruction overrides, role spoofing, tool commands, policy
changes, and credential requests in both raw and cleaned text. High-risk documents are
quarantined and produce no retrievable chunks. Offline tests cover every supported format,
hidden text, multilingual and invisible-character attacks, trust classification, and bounds.

## 2. Relational and vector storage — implemented offline

Migration `0011` adds immutable `rag_document` and `rag_chunk` tables. Accepted chunks carry
384-dimensional embeddings and an embedding model ID; quarantined documents store their risk
record with no chunk or embedding. PostgreSQL creates a functional English FTS GIN index and
an HNSW cosine index for pgvector, and blocks direct UPDATE/DELETE on both tables. The repository
requires the current scanner version, exact regenerated chunk content, complete idempotent
retries, finite nonzero vectors of the schema dimension, and one embedding per accepted chunk.
An `EmbeddingProvider` protocol keeps the model choice outside the repository. Offline SQLite
tests cover persistence, quarantine, idempotence, mutation rejection, and bad embedding output.

## 3. Hybrid retrieval and context — implemented offline

PostgreSQL lexical search uses FTS and semantic search uses pgvector cosine distance; both
apply instrument identity, explicit aware point-in-time cutoff, source type, accepted status,
scanner version, sanitization status, trust, injection-risk, and embedding-model filters before
ranking. Each arm is bounded to at most 50 candidates; application-level reciprocal rank fusion
produces deterministic top-K results. A query embedding must have the configured 384 dimensions
and finite nonzero values. The `ContextBuilder` rechecks each selected hit, limits characters and
chunks, records selected chunk IDs, and wraps JSON-escaped source content in explicit untrusted
evidence markers. Offline tests cover fusion, bounded context, marker escaping, and rejection of
future, poisoned, foreign, or unknown-trust hits. PostgreSQL query execution still needs its
container qualification.

## 4. Application and research integration — implemented offline

`/rag/documents` and `/rag/search` are default-off token-guarded endpoints. Intake accepts
bounded base64 source bytes but never accepts a caller-selected trust level: uploaded SEC-labeled
text remains `USER_CONTENT`. The write commits before returning success. A configurable
OpenAI-compatible HTTP embedding adapter requests exactly 384 dimensions and validates indexed,
finite, nonzero responses; no provider or credential is enabled by default. The worker gains a
default-off RAG node after News. It records a durable external-attempt marker, respects tool and
RAG chunk budgets, converts only ContextBuilder-selected hits into cited research evidence, and
fails closed on an interrupted call. Filing and general RAG requirements are now recognized by
the deterministic gap judge. Offline API, adapter, and graph tests pass.

## Remaining work

- Run Gate D red-team regression and PostgreSQL-backed migration/retrieval qualification; record metrics.

The code-review skill is reserved for one complete Phase 7 review after these parts are finished.
