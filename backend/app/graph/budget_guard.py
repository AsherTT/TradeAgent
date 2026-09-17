"""Deterministic research-loop budget enforcement."""

from dataclasses import dataclass

from backend.app.contracts.research import BudgetUsage, ResearchBudget


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    allowed: bool
    exhausted_fields: tuple[str, ...]


class BudgetGuard:
    @staticmethod
    def evaluate(budget: ResearchBudget, usage: BudgetUsage) -> BudgetDecision:
        exhausted = usage.exceeded_fields(budget)
        return BudgetDecision(allowed=not exhausted, exhausted_fields=exhausted)
