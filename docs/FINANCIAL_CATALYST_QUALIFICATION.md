# Partial financial/catalyst analysis qualification — 2026-10-02

Run `78e1521e-38cf-451b-b6a6-2c72fe78b7b5` used the real local HTTP/Redis/Celery/
PostgreSQL/report route with financials, lexical RAG and optional catalysts enabled.

- Three successful model nodes: intent, planning and news extraction.
- Five tool calls: four external acquisition requests and one internal RAG retrieval.
- Four financial facts, eight news records, nine lexical RAG records and 43 Yahoo bars.
- Recorded wall time: 31.36 seconds. Source/model checkpoints were persisted.
- The report derived annual net margin `0.3557406044239114970268366762` and
  cash/assets `0.09190534402768342651477993386`, both decimal fractions. Each has
  a formula and the two input evidence UUIDs; period end is 2026-06-30.
- The actual catalyst assessment returned zero interpretations, rather than creating
  unsupported events. This qualifies the real node's valid empty-output path, not
  successful extraction of a confirmed catalyst. Limitations are retained in the
  persisted assessment and exposed by the report's subsequent additive projection.
- Market/quant quality still prevents synthesis. No complete financial/business,
  catalyst or investment analysis is claimed; status remains insufficient_evidence
  and complete_analysis=false.
- Temporary API/worker were stopped; datastore services remain available.

Ordinary regression coverage independently exercises nonempty source-reported
interpretations and citation suppression with fixtures. It is not a live-event claim.
The opt-in harness flag `--catalysts` allows at most three model nodes; existing runs
without the flag retain the two-node limit. No credentials or broker actions are involved
in metric derivation. Subscription usage/cost counters are unavailable, not proven zero.
