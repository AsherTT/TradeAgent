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
