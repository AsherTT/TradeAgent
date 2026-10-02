"""Deterministic current annual fractions; source linkage is retained per input."""

from datetime import date, datetime
from decimal import Context, Decimal, DecimalException, localcontext
from typing import Literal
from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evidence import Evidence
from backend.app.financials.admission import (
    admitted_financial_fact,
    financial_coverage,
    select_financial_group,
)

MetricName = Literal["annual_net_margin", "cash_to_assets"]
MetricFormula = Literal["NetIncomeLoss / Revenue", "CashAndCashEquivalents / Assets"]
_DEFINITIONS: tuple[tuple[MetricName, MetricFormula, str, str], ...] = (
    ("annual_net_margin", "NetIncomeLoss / Revenue", "NetIncomeLoss",
     "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("cash_to_assets", "CashAndCashEquivalents / Assets",
     "CashAndCashEquivalentsAtCarryingValue", "Assets"),
)


class FinancialMetric(ContractModel):
    name: MetricName
    formula: MetricFormula
    value: Decimal
    numerator: Decimal
    denominator: Decimal
    unit: Literal["decimal_fraction"] = "decimal_fraction"
    period_start: date | None
    period_end: date
    filed_on: tuple[date, ...] = Field(min_length=2, max_length=2)
    evidence_ids: tuple[UUID, ...] = Field(min_length=2, max_length=2)


def derive_financial_metrics(
    evidence: tuple[Evidence, ...], *, cutoff: datetime,
) -> tuple[FinancialMetric, ...]:
    if not financial_coverage(evidence, cutoff=cutoff):
        return ()
    group = select_financial_group(evidence, cutoff=cutoff)
    facts = {fact.concept: (fact, item) for item in group
             if (fact := admitted_financial_fact(item, cutoff=cutoff)) is not None}
    metrics: list[FinancialMetric] = []
    for name, formula, numerator_concept, denominator_concept in _DEFINITIONS:
        numerator, numerator_item = facts[numerator_concept]
        denominator, denominator_item = facts[denominator_concept]
        if denominator.value <= 0 or (name == "cash_to_assets" and numerator.value < 0):
            continue
        try:
            with localcontext(Context(prec=28)):
                value = numerator.value / denominator.value
        except DecimalException:
            continue
        metrics.append(FinancialMetric(
            name=name, formula=formula, value=value,
            numerator=numerator.value, denominator=denominator.value,
            period_start=numerator.period_start, period_end=numerator.period_end,
            filed_on=(numerator.filed_on, denominator.filed_on),
            evidence_ids=(numerator_item.evidence_id, denominator_item.evidence_id),
        ))
    return tuple(metrics)
