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

## Remaining work

- Persist documents, chunks, and embedding references in PostgreSQL/pgvector.
- Build PIT-filtered lexical/vector retrieval, application RRF, trust filtering, and top-K bounds.
- Build a bounded ContextBuilder and opt-in research integration.
- Run Gate D red-team regression and PostgreSQL-backed qualification; record metrics.

The code-review skill is reserved for one complete Phase 7 review after these parts are finished.
