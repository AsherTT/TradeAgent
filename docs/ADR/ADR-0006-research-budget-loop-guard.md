# ADR-0006: Research budget and loop guard

Status: accepted

Every research run owns a typed hard budget. `BudgetGuard` is deterministic and reports exhausted dimensions before another loop iteration. Exhaustion must lead to safe stopping or an insufficient-evidence result, never forced synthesis.
