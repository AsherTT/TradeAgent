# SEC source slice review and qualification (2026-10-01)

## Scope

Reviewed `git diff 39556a49511cc6cdd6311d2d046ba035db724372...0ce0361`
with independent Standards and Spec agents under `skills/code-review/SKILL.md`.
Commits: `c6792b9` (collection-only), `b9fd5a0` (timeout fallback),
`0ce0361` (SEC current financial adapter). The earlier already-reviewed scope
was not repeated. No issue references were present; local feature documents
provided the specification. The repository has no configured issue-tracker
skill file; review did not invent or initialize a tracker.

## Standards

Documented violations: 0. One low-priority possible Duplicated Code finding:
instant/annual period policy was repeated in the model and normalizer.
Resolved with a shared `_supported_period` rule while preserving boundary
rejection versus unsupported-period exclusion. The Standards reviewer
confirmed the original finding closed.

## Spec

Three P2 findings, all fixed and confirmed closed by the Spec reviewer:

1. HTTP model adapters still wrapped timeouts as ordinary unavailability,
   causing another same-provider attempt. They now raise `ProviderTimeoutError`
   and apply the request timeout explicitly. HTTP mock-to-gateway cases cover
   Qwen, DeepSeek and OpenAI, one call followed by fallback.
2. A non-string SEC form could raise an uncontrolled TypeError. Explicit form
   schema validation now produces `SecFinancialError`, covered by a regression.
3. Invalid value/accession fields in a clearly nonannual 10-K observation could
   reject valid annual data. Supported-period filtering now precedes those
   validations; malformed supported annual records still reject. A regression
   verifies that invalid quarterly values do not invalidate annual observations.

Only original findings were rechecked after fixes; no repeated phase review.
The existing owned-HTTP-client test double was updated to accept and verify
the explicit request timeout. It still verifies client cleanup.

## Verification and remaining qualification

- Ordinary suite: **303 passed, 1 skipped**, **90.10%** combined coverage.
- Ruff, strict `mypy backend/app`, and whitespace checks passed.
- SEC-specific offline suite has 23 golden cases. Ordinary tests use no live
  SEC, market or model requests.
- The opt-in `python -m backend.tests.sec_current_probe` reported
  `SEC_USER_AGENT is not configured` and made no network requests.
- Real KLAC Company Facts client qualification remains pending an operator
  contact User-Agent. The official-source research establishes semantics and
  KLAC CIK, not qualified financial values.
- Worker budgeting/checkpoints, financial gap requirements, freshness policy,
  report projections and synthesis remain future work after live source
  qualification. This independent source slice does not complete Phase 5.
- Changes remain local; push is deferred to the agreed completed-phase gate.
