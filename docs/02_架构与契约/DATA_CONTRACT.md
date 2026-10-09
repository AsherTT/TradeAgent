# Data Contract Baseline

The Phase 1 contracts live in `backend/app/contracts`. They are strict, immutable Pydantic v2 models with unknown fields rejected at boundaries.

Key rules represented in code:

- `instrument_id`, not ticker, is permanent identity.
- Market bars state an explicit `PriceAdjustmentMode` and provider quality version.
- Historical LLM replay declares parametric look-ahead risk.
- Forecast records are immutable and default to `frozen=true`.
- Model probability is separate from `SystemConfidence` and `QualityAssessment`.
- Research loops have a typed `ResearchBudget` and `BudgetUsage`.
- Evidence carries trust, sanitization, and injection-risk metadata.

Contracts are persistence-neutral. SQLAlchemy mappings and Alembic migrations begin in Phase 3.


## Planned option-B equity research contracts (2026-10-09)

The models above remain the implemented Phase 1 baseline. The following are planned
extensions, not exported Pydantic models or live endpoints. See the
[equity backend addendum](EQUITY_RESEARCH_BACKEND_EXTENSION_20261009.md) and
[maintained tasks BE-12–17](../01_项目总览/DEVELOPMENT_PLAN.md).

- Securities/capital: issuer/security/listing identity and time-valid relationships,
  share-class/ADR ratio, dated outstanding-share facts, currency and source IDs;
  distinguish point-in-time shares from weighted-average basic/diluted EPS denominators.
- Financial series: concept/segment/KPI identity, period type/start/end, unit/currency,
  filing/revision, source location, observed/available time and normalized mapping version.
- Market reads: instrument identity, bounded window, trade/observation/availability time,
  adjustment mode, delay, source quality/version and permitted analytical use.
- Valuation/comparisons: formula/assumption version, input price/share/financial snapshot
  IDs and as-of times, currency/period, result or explicit unavailable/incomparable reason.
  Zero, missing, invalid and non-applicable inputs must stay distinct; no client-side
  recalculation may replace a qualified deterministic result.
- Research coverage: requested capabilities/horizon, admitted results/citations, outstanding
  requirements, Critic/claim provenance, graph/tool versions and persisted input snapshots.
  Old reports retain their original capability scope; new support must not relabel old
  partial runs complete. Scenario valuations are not automatically frozen ForecastRecords.

Every public read or command derives account authorization on the server. Schema names,
field limits, URI/methods and migrations freeze in each increment spec; existing internal
token APIs remain separate. Existing PIT, immutable history, budget and confidence rules
continue unchanged. No new contract is implemented or qualified by this documentation.
