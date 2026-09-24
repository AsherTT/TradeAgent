"""Deterministic gap judgement over point-in-time, typed evidence."""

from __future__ import annotations

from backend.app.contracts.evidence import Evidence, EvidenceGapResult, TrustLevel
from backend.app.contracts.research import ResearchState

SUPPORTED_EVIDENCE_REQUIREMENTS = {
    "market data": "market",
    "point-in-time market data": "market",
    "technical indicators": "quant",
    "news documents": "news",
}
_SUPPORTED_CAPABILITIES = frozenset(SUPPORTED_EVIDENCE_REQUIREMENTS.values())


def judge_evidence_gaps(state: ResearchState) -> EvidenceGapResult:
    """Fail closed for unsupported required capabilities and ineligible evidence."""
    required = ["market"]
    if state.research_plan is not None:
        required.extend(
            (
                step.capability.strip().lower()
                if step.capability.strip().lower() in _SUPPORTED_CAPABILITIES
                else f"unsupported_capability[{step.step_id}]"
            )
            for step in state.research_plan.steps
            if step.required
        )
        required.extend(
            SUPPORTED_EVIDENCE_REQUIREMENTS.get(
                " ".join(text.lower().split()), f"unsupported_requirement[{index}]"
            )
            for index, text in enumerate(state.research_plan.evidence_requirements, start=1)
        )
    capabilities = tuple(dict.fromkeys(required))
    eligible = tuple(item for item in state.evidence if _eligible(item, state))
    market = any(
        item.evidence_type == "market_technical_snapshot"
        and item.trust_level is TrustLevel.TRUSTED_PROVIDER
        for item in eligible
    )
    news = any(
        item.evidence_type == "news_document"
        and item.trust_level is TrustLevel.PUBLIC_SOURCE
        and item.sanitization_status == "html_cleaned_and_scanned"
        for item in eligible
    )
    cutoff = state.analysis_timestamp
    market_snapshot = state.market_snapshot
    technical_snapshot = state.technical_snapshot
    snapshots_eligible = (
        cutoff is not None
        and market_snapshot is not None
        and market_snapshot.instrument_id == state.instrument_id
        and market_snapshot.analysis_timestamp == cutoff
        and market_snapshot.latest_bar.instrument_id == state.instrument_id
        and market_snapshot.latest_bar.timestamp <= cutoff
        and market_snapshot.latest_bar.observed_at <= cutoff
        and market_snapshot.latest_bar.available_at <= cutoff
        and technical_snapshot is not None
        and technical_snapshot.instrument_id == state.instrument_id
        and technical_snapshot.analysis_timestamp == cutoff
    )
    supported = {
        "market": market and snapshots_eligible,
        "quant": market and snapshots_eligible,
        "news": news,
    }
    missing = tuple(
        capability for capability in capabilities if not supported.get(capability, False)
    )
    coverage = (len(capabilities) - len(missing)) / len(capabilities)
    return EvidenceGapResult(
        required_capabilities=capabilities,
        missing_capabilities=missing,
        coverage=coverage,
        sufficient=state.research_plan is not None and not missing,
    )


def _eligible(item: Evidence, state: ResearchState) -> bool:
    cutoff = state.analysis_timestamp
    return (
        cutoff is not None
        and item.instrument_id == state.instrument_id
        and item.observed_at <= cutoff
        and item.available_at <= cutoff
        and (item.published_at is None or item.published_at <= cutoff)
    )
