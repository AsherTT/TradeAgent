"""Bounded source routing from research policy and the model-produced plan."""

from __future__ import annotations

import re

from backend.app.contracts.evidence import TrustLevel
from backend.app.contracts.rag import DocumentSourceType, RagHit
from backend.app.contracts.research import ResearchState

_LONG_HORIZON = re.compile(r"\b(?:long|year|years|month|months|quarter|quarters|annual)\b", re.I)


def route_rag_hits(state: ResearchState, hits: tuple[RagHit, ...]) -> tuple[RagHit, ...]:
    """Prefer sources relevant to the horizon and required plan capabilities."""
    plan = state.research_plan
    filing_required = plan is not None and (
        any(step.required and step.capability.strip().lower() == "filing" for step in plan.steps)
        or any(
            requirement.strip().lower() == "filing documents"
            for requirement in plan.evidence_requirements
        )
    )
    long_term = _LONG_HORIZON.search(state.horizon) is not None
    if long_term or filing_required:
        priority = (
            DocumentSourceType.SEC_FILING,
            DocumentSourceType.EXTERNAL_RESEARCH,
            DocumentSourceType.WEB_ARTICLE,
            DocumentSourceType.USER_NOTE,
        )
    else:
        priority = (
            DocumentSourceType.WEB_ARTICLE,
            DocumentSourceType.EXTERNAL_RESEARCH,
            DocumentSourceType.SEC_FILING,
            DocumentSourceType.USER_NOTE,
        )
    ranks = {source: index for index, source in enumerate(priority)}
    return tuple(sorted(
        hits,
        key=lambda hit: (
            len(priority)
            if hit.source_type is DocumentSourceType.SEC_FILING
            and hit.trust_level is not TrustLevel.OFFICIAL_PRIMARY
            else ranks[hit.source_type],
            -hit.score,
            str(hit.chunk_id),
        ),
    ))
