"""Deterministic current annual fractions; source linkage is retained per input."""

from datetime import date, datetime
from decimal import Context, Decimal, DecimalException, localcontext
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

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


class FinancialMetricAssessment(ContractModel):
    name: MetricName
    metric: FinancialMetric | None = None
    interpretation: str | None = Field(default=None, max_length=1000)
    unavailable_reason: Literal[
        "analysis_cutoff_unavailable", "qualified_financial_group_unavailable",
        "nonpositive_denominator", "negative_cash", "arithmetic_unavailable",
    ] | None = None
    limitations: tuple[str, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def coherent_result(self) -> "FinancialMetricAssessment":
        if self.metric is None:
            if self.unavailable_reason is None or self.interpretation is not None:
                raise ValueError("unavailable metric requires a reason and no interpretation")
        elif (self.metric.name != self.name or not self.interpretation
              or self.unavailable_reason is not None):
            raise ValueError("available metric requires matching identity and interpretation")
        return self


def derive_financial_metrics(
    evidence: tuple[Evidence, ...], *, cutoff: datetime,
) -> tuple[FinancialMetric, ...]:
    return tuple(result.metric for result in assess_financial_metrics(evidence, cutoff=cutoff)
                 if result.metric is not None)


def assess_financial_metrics(
    evidence: tuple[Evidence, ...], *, cutoff: datetime | None,
) -> tuple[FinancialMetricAssessment, ...]:
    if cutoff is None:
        return tuple(FinancialMetricAssessment(name=name,
                     unavailable_reason="analysis_cutoff_unavailable")
                     for name, _, _, _ in _DEFINITIONS)
    if not financial_coverage(evidence, cutoff=cutoff):
        return tuple(FinancialMetricAssessment(name=name,
                     unavailable_reason="qualified_financial_group_unavailable")
                     for name, _, _, _ in _DEFINITIONS)
    group = select_financial_group(evidence, cutoff=cutoff)
    facts = {fact.concept: (fact, item) for item in group
             if (fact := admitted_financial_fact(item, cutoff=cutoff)) is not None}
    results: list[FinancialMetricAssessment] = []
    for name, formula, numerator_concept, denominator_concept in _DEFINITIONS:
        numerator, numerator_item = facts[numerator_concept]
        denominator, denominator_item = facts[denominator_concept]
        if denominator.value <= 0:
            results.append(FinancialMetricAssessment(
                name=name, unavailable_reason="nonpositive_denominator"))
            continue
        if name == "cash_to_assets" and numerator.value < 0:
            results.append(FinancialMetricAssessment(name=name, unavailable_reason="negative_cash"))
            continue
        try:
            with localcontext(Context(prec=28)):
                value = numerator.value / denominator.value
        except DecimalException:
            results.append(FinancialMetricAssessment(
                name=name, unavailable_reason="arithmetic_unavailable"))
            continue
        metric = FinancialMetric(
            name=name, formula=formula, value=value,
            numerator=numerator.value, denominator=denominator.value,
            period_start=numerator.period_start, period_end=numerator.period_end,
            filed_on=(numerator.filed_on, denominator.filed_on),
            evidence_ids=(numerator_item.evidence_id, denominator_item.evidence_id),
        )
        if name == "annual_net_margin":
            outcome = ("profit" if numerator.value > 0 else "loss" if numerator.value < 0
                       else "break-even net income")
            interpretation = (
                f"Reported annual {outcome} for {metric.period_start} to {metric.period_end}; "
                f"net income / revenue is {metric.value} (decimal fraction)."
            )
            limitations: tuple[str, ...] = (
                "One annual period does not establish growth or recurring profitability.",
            )
        else:
            interpretation = (
                f"Reported cash and cash equivalents / total assets is {metric.value} "
                f"(decimal fraction) at {metric.period_end}."
            )
            limitations = ("Asset share does not establish cash flow, unrestricted cash or "
                           "liquidity sufficiency.",)
        if value > 1:
            limitations += ("Ratio exceeds one; reconcile the reported inputs before "
                            "drawing further conclusions.",)
        results.append(FinancialMetricAssessment(
            name=name, metric=metric, interpretation=interpretation,
            limitations=limitations,
        ))
    return tuple(results)
