"""Bounded record coverage comparisons; never a market or investment score."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict

from backend.app.api.workspace_research import ResearchSummary, summary
from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import DataQualityStatus, QualityGateDecision
from backend.app.contracts.research import ResearchState
from backend.app.graph.evidence_gap import qualified_evidence

RESEARCH_CHANGE_WINDOW = 50


class ResearchChangeSnapshot(ResearchSummary):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis_timestamp: datetime
    data_quality_status: DataQualityStatus
    quality_gate_decision: QualityGateDecision | None
    qualified_evidence_count: int
    evidence_gap_count: int


class ResearchChange(ContractModel):
    availability: Literal["available", "no_finished_research", "no_comparable_previous"]
    window_limit: int = RESEARCH_CHANGE_WINDOW
    has_more: bool
    latest: ResearchChangeSnapshot | None = None
    previous: ResearchChangeSnapshot | None = None
    qualified_evidence_count_delta: int | None = None
    evidence_gap_count_delta: int | None = None


def _snapshot(state: ResearchState) -> ResearchChangeSnapshot:
    assert state.analysis_timestamp is not None
    return ResearchChangeSnapshot(
        **summary(state).model_dump(), analysis_timestamp=state.analysis_timestamp,
        data_quality_status=state.data_quality_status,
        quality_gate_decision=state.quality_gate_decision,
        qualified_evidence_count=len({item.evidence_id for item in qualified_evidence(state)}),
        evidence_gap_count=len(set(state.evidence_gaps)),
    )


def research_change(states: list[ResearchState], *, has_more: bool) -> ResearchChange:
    """Input is the owned company's newest-first, bounded finished-record window."""
    dated = [state for state in states if state.analysis_timestamp is not None
             and state.analysis_timestamp.utcoffset() is not None]
    if not dated:
        return ResearchChange(availability="no_finished_research", has_more=has_more)
    latest = dated[0]
    latest_snapshot = _snapshot(latest)
    previous = next((state for state in dated[1:] if (
        state.query == latest.query and state.horizon == latest.horizon
        and state.timestamp_mode == latest.timestamp_mode
        and state.replay_integrity_level == latest.replay_integrity_level
        and summary(state).collection_only == latest_snapshot.collection_only
        and state.analysis_timestamp is not None
        and state.analysis_timestamp < latest_snapshot.analysis_timestamp
    )), None)
    if previous is None:
        return ResearchChange(
            availability="no_comparable_previous", has_more=has_more, latest=latest_snapshot,
        )
    previous_snapshot = _snapshot(previous)
    return ResearchChange(
        availability="available", has_more=has_more,
        latest=latest_snapshot, previous=previous_snapshot,
        qualified_evidence_count_delta=(
            latest_snapshot.qualified_evidence_count - previous_snapshot.qualified_evidence_count
        ),
        evidence_gap_count_delta=(
            latest_snapshot.evidence_gap_count - previous_snapshot.evidence_gap_count
        ),
    )
