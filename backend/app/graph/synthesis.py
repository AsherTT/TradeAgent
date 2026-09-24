"""Bounded context selection and citation checks for research synthesis."""

from __future__ import annotations

import re
from typing import Any

from backend.app.contracts.evidence import Evidence, ResearchSynthesis
from backend.app.contracts.research import ResearchState
from backend.app.graph.evidence_gap import qualified_evidence

_BOUNDARY_MARKER = re.compile(r"(?i)\b(BEGIN|END)\s+UNTRUSTED\s+EVIDENCE\b")
_EVIDENCE_TYPE_BY_CAPABILITY = {
    "market": "market_technical_snapshot",
    "quant": "market_technical_snapshot",
    "news": "news_document",
}


def select_synthesis_evidence(state: ResearchState) -> tuple[Evidence, ...]:
    eligible = qualified_evidence(state)
    required = (
        state.evidence_gap_result.required_capabilities
        if state.evidence_gap_result is not None else ("market",)
    )
    priority_types = tuple(dict.fromkeys(
        _EVIDENCE_TYPE_BY_CAPABILITY[capability]
        for capability in required if capability in _EVIDENCE_TYPE_BY_CAPABILITY
    ))
    selected: list[Evidence] = []
    for evidence_type in priority_types:
        match = next((item for item in eligible if item.evidence_type == evidence_type), None)
        if match is not None:
            selected.append(match)
    selected_ids = {item.evidence_id for item in selected}
    selected.extend(
        item for item in eligible
        if item.evidence_id not in selected_ids
    )
    return tuple(selected[:8])


def synthesis_context(state: ResearchState, selected: tuple[Evidence, ...]) -> dict[str, Any]:
    return {
        "research_plan": (
            state.research_plan.model_dump(mode="json")
            if state.research_plan is not None else None
        ),
        "technical_snapshot": (
            state.technical_snapshot.model_dump(mode="json")
            if state.technical_snapshot is not None else None
        ),
        "selected_evidence": [
            {
                "evidence_id": str(item.evidence_id),
                "source_name": item.source_name,
                "trust_level": item.trust_level.value,
                "source_type": item.source_type,
                "content_hash": item.content_hash,
                "sanitization_status": item.sanitization_status,
                "content": (
                    "BEGIN UNTRUSTED EVIDENCE\n"
                    + _BOUNDARY_MARKER.sub("[escaped evidence marker]", item.content[:1000])
                    + "\nEND UNTRUSTED EVIDENCE"
                ),
            }
            for item in selected
        ],
    }


def validate_synthesis(
    synthesis: ResearchSynthesis, selected: tuple[Evidence, ...],
    required_capabilities: tuple[str, ...]
) -> None:
    allowed_ids = {item.evidence_id for item in selected}
    if len(set(synthesis.evidence_ids)) != len(synthesis.evidence_ids):
        raise ValueError("synthesis contains duplicate evidence citations")
    if not set(synthesis.evidence_ids) <= allowed_ids:
        raise ValueError("synthesis cites evidence outside selected context")
    cited_types = {
        item.evidence_type for item in selected if item.evidence_id in synthesis.evidence_ids
    }
    required_types = {
        _EVIDENCE_TYPE_BY_CAPABILITY[capability]
        for capability in required_capabilities if capability in _EVIDENCE_TYPE_BY_CAPABILITY
    }
    if not required_types <= cited_types:
        raise ValueError("synthesis omits required evidence capability")
