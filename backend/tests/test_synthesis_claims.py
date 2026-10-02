"""Per-claim citation boundaries and report-time suppression."""

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.contracts.evidence import ResearchSynthesis, SynthesisClaim
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.graph.synthesis import validate_synthesis, validate_synthesis_claims
from backend.app.reports.research import build_research_report
from backend.tests.test_research_report import _evidence

NOW = datetime(2026, 10, 2, tzinfo=UTC)


def attributed_state() -> ResearchState:
    instrument = uuid4()
    item = _evidence(instrument, NOW)
    claim = SynthesisClaim(
        section="price", text="The fixture contains a market observation.",
        evidence_id=item.evidence_id, supporting_quote="fixture market observation",
    )
    synthesis = ResearchSynthesis(
        summary="Fixture summary", bull_case="Fixture upside", bear_case="Fixture downside",
        evidence_ids=(item.evidence_id,), confidence=0.3, claims=(claim,), limitations=(),
    )
    return ResearchState(
        instrument_id=instrument, ticker="KLAC", query="Fixture", horizon="3 days",
        requested_at=NOW, analysis_timestamp=NOW, status=ResearchStatus.COMPLETE,
        evidence=(item,), research_synthesis=synthesis,
    )


def test_valid_claim_has_own_quote_citation_and_incomplete_report() -> None:
    state = attributed_state()
    assert state.research_synthesis is not None
    validate_synthesis(state.research_synthesis, state.evidence, ("market",))
    report = build_research_report(state)
    assert report.claims == state.research_synthesis.claims
    section = next(item for item in report.sections if item.title == "Model interpretation: price")
    assert section.evidence_ids == (report.claims[0].evidence_id,)
    assert not report.complete_analysis
    assert "not verified" in section.text
    assert ResearchState.model_validate_json(state.model_dump_json()) == state


@pytest.mark.parametrize("change", [
    {"evidence_id": uuid4()}, {"supporting_quote": "fabricated supporting quote"},
    {"section": "financial"}, {"section": "catalyst"},
])
def test_invalid_claim_rejected_by_graph_and_suppressed_by_report(
    change: dict[str, object],
) -> None:
    state = attributed_state()
    assert state.research_synthesis is not None
    synthesis = state.research_synthesis.model_copy(update={
        "claims": (state.research_synthesis.claims[0].model_copy(update=change),),
    })
    with pytest.raises(ValueError):
        validate_synthesis_claims(synthesis, state.evidence)
    report = build_research_report(state.model_copy(update={"research_synthesis": synthesis}))
    assert report.claims == ()
    assert report.citations == ()
    assert not any(item.title == "Summary" for item in report.sections)
    assert "synthesis claim attribution is invalid" in report.gaps


def test_claim_must_be_globally_cited_and_not_duplicated() -> None:
    state = attributed_state()
    assert state.research_synthesis is not None
    for change in (
        {"evidence_ids": (uuid4(),)},
        {"claims": state.research_synthesis.claims * 2},
    ):
        with pytest.raises(ValueError):
            validate_synthesis_claims(
                state.research_synthesis.model_copy(update=change), state.evidence,
            )


@pytest.mark.parametrize("change", ["content", "available_at"])
def test_report_rechecks_quote_and_source_cutoff(change: str) -> None:
    state = attributed_state()
    update = {"content": "changed source content"} if change == "content" else {
        "available_at": NOW + timedelta(seconds=1),
    }
    report = build_research_report(state.model_copy(update={
        "evidence": (state.evidence[0].model_copy(update=update),),
    }))
    assert report.claims == ()
    assert report.citations == ()
    assert not any(item.title == "Summary" for item in report.sections)


def test_legacy_synthesis_without_claims_remains_readable() -> None:
    state = attributed_state()
    assert state.research_synthesis is not None
    data = state.research_synthesis.model_dump(mode="json")
    data.pop("claims")
    legacy = ResearchSynthesis.model_validate_json(json.dumps(data))
    assert legacy.claims == ()
    report = build_research_report(state.model_copy(update={"research_synthesis": legacy}))
    assert report.claims == ()
    assert any(item.title == "Summary" for item in report.sections)


@pytest.mark.parametrize("change", [{"text": " "}, {"supporting_quote": " " * 10}])
def test_whitespace_claim_fields_are_invalid(change: dict[str, str]) -> None:
    state = attributed_state()
    assert state.research_synthesis is not None
    data = state.research_synthesis.claims[0].model_dump()
    with pytest.raises(ValidationError):
        SynthesisClaim.model_validate({**data, **change})
