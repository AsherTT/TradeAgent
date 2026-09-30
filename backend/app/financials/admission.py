"""Revalidate persisted financial evidence before gap, synthesis or report use."""

import json
from datetime import UTC, date, datetime

from pydantic import ValidationError

from backend.app.contracts.evidence import Evidence, TrustLevel
from backend.app.financials.sec import (
    CONCEPTS,
    MAX_FILING_AGE_DAYS,
    MAX_PERIOD_AGE_DAYS,
    SecFinancialFact,
)


def admitted_financial_fact(item: Evidence, *, cutoff: datetime) -> SecFinancialFact | None:
    if (
        cutoff.tzinfo is None
        or cutoff.utcoffset() is None
        or item.evidence_type != "financial_fact"
        or item.trust_level is not TrustLevel.OFFICIAL_PRIMARY
        or item.source_name != "sec.companyfacts"
        or item.source_type != "sec_xbrl_current_observation"
        or item.sanitization_status != "typed_numeric_allowlist_v1"
        or item.injection_risk != 0
        or item.observed_at > cutoff
        or item.available_at > cutoff
        or item.published_at is not None
    ):
        return None
    data = dict(item.structured_data)
    taxonomy = data.pop("taxonomy", None)
    uri = data.pop("companyfacts_uri", None)
    try:
        fact = SecFinancialFact.model_validate_json(json.dumps(data))
        expected = fact.to_evidence(item.instrument_id, cutoff=cutoff)
    except (ValidationError, ValueError, TypeError):
        return None
    today = cutoff.astimezone(UTC).date()
    if (
        taxonomy != "us-gaap"
        or uri != expected.structured_data["companyfacts_uri"]
        or item.source_uri != fact.source_uri
        or item.content != expected.content
        or item.content_hash != expected.content_hash
        or item.observed_at != fact.observed_at
        or item.available_at != fact.observed_at
        or item.retrieved_at != fact.observed_at
        or (today - fact.period_end).days > MAX_PERIOD_AGE_DAYS
        or (today - fact.filed_on).days > MAX_FILING_AGE_DAYS
    ):
        return None
    return fact


def financial_coverage(evidence: tuple[Evidence, ...], *, cutoff: datetime) -> bool:
    selected = select_financial_group(evidence, cutoff=cutoff)
    if len(selected) != len(CONCEPTS):
        return False
    durations = {
        fact.period_start
        for item in selected
        if (fact := admitted_financial_fact(item, cutoff=cutoff)) is not None
        and fact.period_start is not None
    }
    return len(durations) == 1


def select_financial_group(
    evidence: tuple[Evidence, ...], *, cutoff: datetime
) -> tuple[Evidence, ...]:
    groups: dict[tuple[int, date], dict[str, tuple[SecFinancialFact, Evidence]]] = {}
    conflicts: set[tuple[int, date]] = set()
    for item in evidence:
        fact = admitted_financial_fact(item, cutoff=cutoff)
        if fact is not None:
            key = (fact.cik, fact.period_end)
            group = groups.setdefault(key, {})
            previous = group.get(fact.concept)
            if previous is not None:
                if previous[0].filed_on == fact.filed_on and previous[0].value != fact.value:
                    conflicts.add(key)
                if (previous[0].filed_on, previous[0].observed_at) >= (
                    fact.filed_on,
                    fact.observed_at,
                ):
                    continue
            group[fact.concept] = (fact, item)
    if not groups or len({cik for cik, _ in groups}) != 1:
        return ()
    latest = max(groups, key=lambda key: key[1])
    if latest in conflicts:
        return ()
    group = groups[latest]
    return tuple(group[concept][1] for concept in CONCEPTS if concept in group)
