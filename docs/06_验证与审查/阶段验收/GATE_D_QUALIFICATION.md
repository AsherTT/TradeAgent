# Gate D — RAG Trust Boundary Qualification

Qualified: 2026-09-28 (Asia/Shanghai). Scope: offline red-team fixtures and rebuilt local
PostgreSQL/pgvector containers. No live document or embedding provider was called.

## Security regression metrics

| Measure | Result |
| --- | ---: |
| Malicious document fixtures | 13 |
| Quarantined with zero retrievable chunks | 13 / 13 |
| Attempts to inject budget, runtime, tool permission, credential, or trust fields | 5 |
| Rejected by strict source and API schemas | 5 / 5 |
| Benign control documents accepted | 1 / 1 |
| PostgreSQL safe documents retrieved at the cutoff | 1 / 1 |
| Future, foreign-instrument, and poisoned documents returned | 0 |
| Direct RAG chunk UPDATE / document DELETE accepted | 0 / 2 |
| User-supplied historical observation timestamp accepted | 0 / 1 |
| User-labeled SEC upload accepted as verified filing evidence | 0 / 1 |

The security fixtures include English and Chinese instruction overrides, full-width and
zero-width obfuscation, hidden HTML, script tags, role spoofing, tool invocation, budget/runtime
changes, permission escalation, credential requests, and poisoned JSON. The ContextBuilder
rechecks trust, risk, scanner version, point-in-time timestamps, and content hash before wrapping
selected source text as untrusted evidence. The research graph also checks the returned evidence
count, budget, identity, timestamps, trust, risk, and hash before saving it.

## PostgreSQL evidence

The rebuilt API, worker, Beat, and migration images applied Alembic head
`0011_phase7_rag_storage`. `backend/tests/phase7_container_qualify.py` stored one accepted,
one future, one poisoned, and one foreign-instrument document. The real FTS query for
`quarterly revenue` returned one matching chunk, and the production `RagRetriever` returned
only chunk `04c52797-afc6-46c6-9535-2ca95048c717` from document
`01b8453d-6735-4040-a507-2646221131c4`. The poisoned document
`63969cf7-e253-4411-a241-6510450454a4` produced no chunks. PostgreSQL rejected a direct
chunk UPDATE and document DELETE through the migration trigger.

The ordinary suite passed with 231 tests, one opt-in live-model test skipped, and 91.92%
combined coverage after the whole-phase review. Ruff and strict mypy passed. Azure
Pipelines runs the ordinary pytest suite on `main`, so Gate D security tests rerun with the
other regression tests after relevant code changes.

## Scope

Phase 7 and Gate D are qualified with fixtures and PostgreSQL. RAG remains disabled unless
`RAG_ENABLED`, `RAG_WRITE_TOKEN`, and the embedding endpoint/model/credential settings are
configured. A real embedding provider, live document sources, and operational security testing
are not claimed by this qualification.
