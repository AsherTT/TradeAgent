from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from backend.app.contracts.evaluation import DataQualityStatus, QualityGateDecision
from backend.app.contracts.evidence import Evidence, ResearchSynthesis, TrustLevel
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketAcquisitionSummary
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.reports.research import build_research_report


def _evidence(instrument_id: UUID, when: datetime) -> Evidence:
    return Evidence(
        instrument_id=instrument_id,
        evidence_type="market_technical_snapshot",
        source_name="fixture",
        source_uri="https://example.org/market",
        observed_at=when,
        retrieved_at=when,
        available_at=when,
        content="fixture market observation",
        confidence=0.8,
        freshness=1,
        trust_level=TrustLevel.TRUSTED_PROVIDER,
        source_type="market_data",
        content_hash="fixture",
        sanitization_status="structured",
        injection_risk=0,
    )


def test_completed_run_report_retains_only_persisted_cited_claims() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    item = _evidence(instrument_id, cutoff)
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.COMPLETE,
        data_quality_status=DataQualityStatus.ACCEPTABLE,
        quality_gate_decision=QualityGateDecision.DEGRADED,
        evidence=(item,),
        research_synthesis=ResearchSynthesis(
            summary="Market setup is mixed.",
            bull_case="Momentum may continue.",
            bear_case="Momentum may reverse.",
            limitations=("No verified financial statements.",),
            evidence_ids=(item.evidence_id,),
            confidence=0.4,
        ),
    )

    report = build_research_report(state)

    assert report.complete_analysis is False
    assert [section.title for section in report.sections[:4]] == [
        "Research status", "Summary", "Bull case", "Bear case"
    ]
    assert report.sections[1].evidence_ids == (item.evidence_id,)
    assert report.citations[0].source_uri == item.source_uri
    assert report.citations[0].available_at == cutoff
    assert any(section.title == "Business and financials" for section in report.sections)
    assert "No verified financial statements." in report.gaps


def test_incomplete_run_does_not_publish_synthesis_or_future_citations() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    future = _evidence(instrument_id, cutoff + timedelta(minutes=1))
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.INSUFFICIENT_EVIDENCE,
        evidence=(future,),
        evidence_gaps=("market quality below acceptable",),
    )

    report = build_research_report(state)

    assert report.citations == ()
    assert all(section.title != "Summary" for section in report.sections)
    assert report.gaps[0] == "market quality below acceptable"
    assert "separately verified catalyst analysis unavailable" in report.gaps
    assert "unavailable" in next(
        section.text for section in report.sections if section.title == "Price and technicals"
    )


def test_report_drops_non_web_source_uri() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    item = _evidence(instrument_id, cutoff).model_copy(
        update={"source_uri": "javascript:alert(1)"}
    )
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.COMPLETE,
        evidence=(item,),
        research_synthesis=ResearchSynthesis(
            summary="Mixed.",
            bull_case="Possible upside.",
            bear_case="Possible downside.",
            limitations=(),
            evidence_ids=(item.evidence_id,),
            confidence=0.4,
        ),
    )

    assert build_research_report(state).citations[0].source_uri is None


def test_completed_run_suppresses_all_model_text_when_citation_is_ineligible() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    future = _evidence(instrument_id, cutoff + timedelta(minutes=1))
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.COMPLETE,
        evidence=(future,),
        research_synthesis=ResearchSynthesis(
            summary="Unsupported summary.",
            bull_case="Unsupported bull case.",
            bear_case="Unsupported bear case.",
            limitations=("Unsupported model limitation.",),
            evidence_ids=(future.evidence_id,),
            confidence=0.4,
        ),
    )

    report = build_research_report(state)

    assert report.citations == ()
    assert "synthesis citations are unavailable at the analysis cutoff" in report.gaps
    assert "Unsupported model limitation." not in report.gaps
    assert all("Unsupported" not in section.text for section in report.sections)
    assert all(
        section.title not in {"Summary", "Bull case", "Bear case"}
        for section in report.sections
    )


def test_report_shows_unqualified_acquisition_without_technical_claims() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    acquisition = MarketAcquisitionSummary(
        instrument_id=instrument_id,
        analysis_timestamp=cutoff,
        first_bar_at=cutoff - timedelta(days=60),
        latest_bar_at=cutoff - timedelta(days=1),
        observed_at=cutoff,
        bar_count=41,
        source_names=("yfinance",),
        provider_quality_versions=("yfinance-daily-raw-v1",),
        adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
        data_quality_status=DataQualityStatus.UNVERIFIED,
    )
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.INSUFFICIENT_EVIDENCE,
        market_acquisition=acquisition,
    )

    persisted = ResearchState.model_validate_json(state.model_dump_json())
    report = build_research_report(persisted)

    assert report.market_acquisition == acquisition
    assert "41 bars" in next(
        section.text for section in report.sections if section.title == "Market acquisition"
    )
    assert report.citations == ()
    assert "unavailable" in next(
        section.text for section in report.sections if section.title == "Price and technicals"
    )


def test_incomplete_report_lists_bounded_eligible_news_metadata() -> None:
    cutoff = datetime(2026, 9, 30, tzinfo=UTC)
    instrument_id = uuid4()
    news = tuple(
        Evidence(
            instrument_id=instrument_id,
            evidence_type="news_document",
            source_name="finnhub",
            source_uri="https://example.org/story?token=private",
            published_at=cutoff - timedelta(hours=index + 1),
            observed_at=cutoff,
            retrieved_at=cutoff,
            available_at=cutoff,
            content="Unverified headline text",
            confidence=0.5,
            freshness=1,
            trust_level=TrustLevel.PUBLIC_SOURCE,
            source_type="news",
            content_hash=f"news-{index}",
            sanitization_status="html_cleaned_and_scanned",
            injection_risk=0,
        )
        for index in range(10)
    )
    future = news[0].model_copy(
        update={"evidence_id": uuid4(), "published_at": cutoff + timedelta(minutes=1)}
    )
    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess KLAC",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3 months",
        status=ResearchStatus.INSUFFICIENT_EVIDENCE,
        evidence=(*news, future),
    )

    report = build_research_report(state)

    section = next(item for item in report.sections if item.title == "News observations")
    assert "10 point-in-time eligible" in section.text
    assert "Unverified headline text" not in section.text
    assert len(section.evidence_ids) == 8
    assert len(report.citations) == 8
    assert all(item.evidence_id != future.evidence_id for item in report.citations)
    assert all(item.source_uri == "https://example.org/story" for item in report.citations)
    assert report.complete_analysis is False
