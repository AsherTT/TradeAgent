"""Bounded context selection and citation checks for research synthesis."""

from __future__ import annotations

import re
from typing import Any

from backend.app.contracts.evidence import Evidence, ResearchSynthesis, TrustLevel
from backend.app.contracts.research import ResearchState
from backend.app.financials.admission import financial_coverage, select_financial_group
from backend.app.graph.evidence_gap import qualified_evidence

_BOUNDARY_MARKER = re.compile(r"(?i)\b(BEGIN|END)\s+UNTRUSTED\s+EVIDENCE\b")
_EVIDENCE_TYPE_BY_CAPABILITY = {
    "market": "market_technical_snapshot",
    "quant": "market_technical_snapshot",
    "news": "news_document",
    "rag": "rag_document",
    "filing": "rag_document",
    "financials": "financial_fact",
}


def select_synthesis_evidence(state: ResearchState) -> tuple[Evidence, ...]:
    eligible = qualified_evidence(state)
    required = (
        state.evidence_gap_result.required_capabilities
        if state.evidence_gap_result is not None
        else ("market",)
    )
    priority_types = tuple(
        dict.fromkeys(
            _EVIDENCE_TYPE_BY_CAPABILITY[capability]
            for capability in required
            if capability in _EVIDENCE_TYPE_BY_CAPABILITY
        )
    )
    selected: list[Evidence] = []
    if "financials" in required and state.analysis_timestamp is not None:
        selected.extend(select_financial_group(eligible, cutoff=state.analysis_timestamp))
    if "filing" in required:
        filing = next(
            (
                item
                for item in eligible
                if item.evidence_type == "rag_document"
                and item.source_type == "sec_filing"
                and item.trust_level is TrustLevel.OFFICIAL_PRIMARY
            ),
            None,
        )
        if filing is not None:
            selected.append(filing)
    for evidence_type in priority_types:
        if evidence_type == "financial_fact":
            continue
        match = next(
            (
                item
                for item in eligible
                if item.evidence_type == evidence_type
                and item.evidence_id not in {chosen.evidence_id for chosen in selected}
            ),
            None,
        )
        if match is not None:
            selected.append(match)
    selected_ids = {item.evidence_id for item in selected}
    selected.extend(item for item in eligible if item.evidence_id not in selected_ids)
    return tuple(selected[:8])


def synthesis_context(state: ResearchState, selected: tuple[Evidence, ...]) -> dict[str, Any]:
    return {
        "research_plan": (
            state.research_plan.model_dump(mode="json") if state.research_plan is not None else None
        ),
        "technical_snapshot": (
            state.technical_snapshot.model_dump(mode="json")
            if state.technical_snapshot is not None
            else None
        ),
        "selected_evidence": [
            {
                "evidence_id": str(item.evidence_id),
                "source_name": item.source_name,
                "trust_level": item.trust_level.value,
                "source_type": item.source_type,
                "evidence_type": item.evidence_type,
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
    synthesis: ResearchSynthesis,
    selected: tuple[Evidence, ...],
    required_capabilities: tuple[str, ...],
) -> None:
    validate_synthesis_claims(synthesis, selected)
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
        for capability in required_capabilities
        if capability in _EVIDENCE_TYPE_BY_CAPABILITY
    }
    if not required_types <= cited_types:
        raise ValueError("synthesis omits required evidence capability")
    if "filing" in required_capabilities and not any(
        item.evidence_type == "rag_document"
        and item.source_type == "sec_filing"
        and item.trust_level is TrustLevel.OFFICIAL_PRIMARY
        and item.evidence_id in synthesis.evidence_ids
        for item in selected
    ):
        raise ValueError("synthesis omits required SEC filing citation")
    if "financials" in required_capabilities:
        cited_financials = tuple(
            item
            for item in selected
            if item.evidence_id in synthesis.evidence_ids and item.evidence_type == "financial_fact"
        )
        # Admission already bounded these observations to the research cutoff.
        cutoff = max((item.available_at for item in selected), default=None)
        if cutoff is None or not financial_coverage(cited_financials, cutoff=cutoff):
            raise ValueError("synthesis omits required annual financial concepts")


def validate_synthesis_claims(synthesis: ResearchSynthesis, selected: tuple[Evidence, ...]) -> None:
    sources = {item.evidence_id: item for item in selected}
    seen: set[tuple[str, str, object]] = set()
    allowed_types = {
        "financial": {"financial_fact"},
        "price": {"market_technical_snapshot"},
        "catalyst": {"news_document", "rag_document"},
    }
    for claim in synthesis.claims:
        source = sources.get(claim.evidence_id)
        if source is None or claim.evidence_id not in synthesis.evidence_ids:
            raise ValueError("claim citation must be selected and globally cited")
        if claim.supporting_quote not in source.content[:1000]:
            raise ValueError("claim supporting quote is outside selected source excerpt")
        if (
            claim.section in allowed_types
            and source.evidence_type not in allowed_types[claim.section]
        ):
            raise ValueError("claim source type does not match its section")
        identity = (claim.section, claim.text.strip(), claim.evidence_id)
        if identity in seen:
            raise ValueError("synthesis contains duplicate claims")
        seen.add(identity)
