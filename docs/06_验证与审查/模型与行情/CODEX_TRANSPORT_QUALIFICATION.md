# Local Codex transport qualification (2026-10-01)

## Reproduction and cause

The minimal read-only SDK prompt timed out at 20 seconds; a 45-second event trace
also timed out. `thread/start` and `turn/start` succeeded, but no final response
or terminal event arrived. Controlled stderr classification detected upstream
stream-disconnect and timeout symptoms, without authentication or rate-limit signs.
Disabling the one configured MCP server did not fix the reproduction.

The Windows user had an enabled loopback HTTP proxy, while HTTP(S) proxy environment
variables were absent from the SDK process. Supplying that same configured proxy to
the SDK child changed the trace to an agent response and `turn/completed` at about
6 seconds. The original minimal prompt then passed, with unchanged 20-second timeout,
in 6.7 seconds. This qualifies the local proxy fix for this workstation, not every
network or account deployment.

`CODEX_PROXY_URL` now explicitly supplies HTTP(S) proxy configuration to the child
environment only. It defaults empty and rejects credential-bearing URLs. The real
workstation value is in ignored `.env`, not repository source. Global proxy settings
and model selection were not changed. SDK failures use bounded public diagnostics.

The SDK completion status is an Enum, not a string; the adapter checks its `.value`
and requires a text result. Offline regressions reproduce this real shape, child
proxy options, environment isolation, and interrupted-result rejection.

Official [app-server documentation](https://learn.chatgpt.com/docs/app-server)
describes the thread/turn lifecycle. This qualification requires a completed turn,
not just initialization or a model catalog entry.

## Actual structured and durable probes

- `python -m backend.tests.codex_current_probe`: two real Codex requests returned
  validated ResearchIntent and ResearchPlan outputs. No data provider was called.
  A bounded diagnostic is stored in the system temporary directory.
- `python -m backend.tests.current_model_durable_probe`: local HTTP POST, Redis,
  Windows solo Celery worker, PostgreSQL at migration `0013`, and report GET passed
  for run `c11a6a2a-b952-4f59-8fb8-905e368420d2`.
- That run completed two model nodes and two data-provider calls in 23.58 seconds,
  scanned/admitted eight news records, and persisted a 41-bar Yahoo acquisition.
  Yahoo action quality stayed `UNVERIFIED`; market/technical evidence and synthesis
  were withheld. Status was `insufficient_evidence`, `complete_analysis=false`.
- The live plan exposed an additional prompt gap: the capability vocabulary had
  not been supplied, so several step names were used as capabilities. The gap
  judge rejected these safely. The planner prompt now supplies the exact supported
  capability names and asks that exploratory extras remain optional; unknown
  capabilities still fail closed rather than being rewritten after output.
- After the prompt change, run `6dbc59d4-c8fb-4281-ba43-36fad58c1966` completed
  in 21.50 seconds with two model nodes, two provider calls, eight admitted news
  records and 41 Yahoo bars. The plan used supported capability names. Market,
  quant, filing and RAG evidence gaps still prevented synthesis; the outcome
  remained `insufficient_evidence`.
- Financials stayed disabled because the operator SEC User-Agent is not configured.
  No SEC financial values were qualified in this run. Full synthesis remains pending
  qualified market evidence and financial/catalyst report coverage.
- Context-token and cost metering remain unavailable in this subscription adapter;
  zero budget counters in this diagnostic are not claims of zero actual usage/cost.

The temporary API and worker were stopped after the probe. PostgreSQL/Redis remain
available for subsequent qualification. The ordinary suite never runs these probes.
