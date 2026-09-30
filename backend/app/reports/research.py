"""Deterministic, evidence-linked presentation of a persisted research run."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import DataQualityStatus, QualityGateDecision
from backend.app.contracts.market import MarketAcquisitionSummary
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.graph.evidence_gap import qualified_evidence


class ReportCitation(ContractModel):
    evidence_id: UUID
    evidence_type: str
    source_name: str
    source_uri: str | None
    published_at: datetime | None
    observed_at: datetime
    available_at: datetime


class ReportSection(ContractModel):
    title: str
    text: str
    evidence_ids: tuple[UUID, ...] = ()


class ResearchReport(ContractModel):
    research_id: UUID
    ticker: str
    status: ResearchStatus
    analysis_timestamp: datetime | None
    data_quality_status: DataQualityStatus
    market_acquisition: MarketAcquisitionSummary | None
    quality_gate_decision: QualityGateDecision | None
    complete_analysis: bool
    citation_note: str
    sections: tuple[ReportSection, ...] = Field(min_length=1)
    citations: tuple[ReportCitation, ...] = ()
    gaps: tuple[str, ...] = ()


def _safe_source_uri(uri: str | None) -> str | None:
    if uri is None:
        return None
    try:
        parsed = urlsplit(uri)
        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or any(char.isspace() for char in uri)
        ):
            return None
    except ValueError:
        return None
    return urlunsplit(("https", parsed.hostname.lower(), parsed.path, "", ""))


def build_research_report(state: ResearchState) -> ResearchReport:
    """Expose only persisted claims and point-in-time eligible citation metadata."""
    synthesis = state.research_synthesis if state.status is ResearchStatus.COMPLETE else None
    eligible = {item.evidence_id: item for item in qualified_evidence(state)}
    cited_ids = (
        tuple(evidence_id for evidence_id in synthesis.evidence_ids if evidence_id in eligible)
        if synthesis is not None
        else ()
    )
    synthesis_cited = (
        synthesis is not None
        and len(cited_ids) == len(synthesis.evidence_ids)
        and len(set(cited_ids)) == len(cited_ids)
    )
    citations = tuple(
        ReportCitation(
            evidence_id=eligible[evidence_id].evidence_id,
            evidence_type=eligible[evidence_id].evidence_type,
            source_name=eligible[evidence_id].source_name,
            source_uri=_safe_source_uri(eligible[evidence_id].source_uri),
            published_at=eligible[evidence_id].published_at,
            observed_at=eligible[evidence_id].observed_at,
            available_at=eligible[evidence_id].available_at,
        )
        for evidence_id in cited_ids if synthesis_cited
    )
    sections = [
        ReportSection(
            title="Research status",
            text=(
                "A cited research synthesis is available."
                if synthesis_cited
                else "A complete, cited research synthesis is not available."
            ),
        )
    ]
    if synthesis is not None and synthesis_cited:
        sections.extend(
            (
                ReportSection(title="Summary", text=synthesis.summary, evidence_ids=cited_ids),
                ReportSection(title="Bull case", text=synthesis.bull_case, evidence_ids=cited_ids),
                ReportSection(title="Bear case", text=synthesis.bear_case, evidence_ids=cited_ids),
            )
        )
    sections.append(
        ReportSection(
            title="Business and financials",
            text="No separately verified business or financial analysis is available in this run.",
        )
    )
    sections.append(
        ReportSection(
            title="Catalysts",
            text="No separately verified catalyst analysis is available in this run.",
        )
    )
    acquisition = state.market_acquisition
    sections.append(
        ReportSection(
            title="Market acquisition",
            text=(
                f"Provider acquisition recorded {acquisition.bar_count} bars from "
                f"{', '.join(acquisition.source_names)}; latest bar at "
                f"{acquisition.latest_bar_at.isoformat()}; quality "
                f"{acquisition.data_quality_status.value}. Acquisition alone does not "
                "qualify technical evidence."
                if acquisition is not None
                else "No market acquisition record is available."
            ),
        )
    )
    technical = state.technical_snapshot
    market_citations = tuple(
        evidence_id
        for evidence_id in cited_ids
        if eligible[evidence_id].evidence_type == "market_technical_snapshot"
    )
    if (
        technical is not None
        and state.market_snapshot is not None
        and market_citations
        and state.data_quality_status
        in {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
        and state.market_snapshot.latest_bar.data_quality_status
        in {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
    ):
        indicator_text = ", ".join(
            f"{name}: {value:g}" if isinstance(value, int | float) else f"{name}: {value}"
            for name, value in sorted(technical.indicators.items())
            if value is not None
        )
        sections.append(
            ReportSection(
                title="Price and technicals",
                text=(
                    f"Latest close: {state.market_snapshot.latest_bar.close:g} "
                    f"{state.market_snapshot.currency}; technical feature version: "
                    f"{technical.feature_version}. Data quality: "
                    f"{state.data_quality_status.value}. "
                    f"Indicators: {indicator_text or 'none available'}."
                ),
                evidence_ids=market_citations,
            )
        )
    else:
        sections.append(
            ReportSection(
                title="Price and technicals",
                text="Qualified price and technical evidence is unavailable.",
            )
        )
    limitations = tuple(synthesis.limitations) if synthesis is not None and synthesis_cited else ()
    citation_gap = (
        ("synthesis citations are unavailable at the analysis cutoff",)
        if synthesis is not None and not synthesis_cited
        else ()
    )
    gaps = tuple(
        dict.fromkeys(
            (
                *state.evidence_gaps,
                *citation_gap,
                *limitations,
                "separately verified business and financial analysis unavailable",
                "separately verified catalyst analysis unavailable",
            )
        )
    )
    sections.append(
        ReportSection(
            title="Risks and limitations",
            text="; ".join(gaps),
        )
    )
    return ResearchReport(
        research_id=state.research_id,
        ticker=state.ticker,
        status=state.status,
        analysis_timestamp=state.analysis_timestamp,
        data_quality_status=state.data_quality_status,
        market_acquisition=acquisition,
        quality_gate_decision=state.quality_gate_decision,
        complete_analysis=False,
        citation_note=(
            "Synthesis citations support the synthesis as a whole; individual claims have "
            "not been mapped to individual sources."
        ),
        sections=tuple(sections),
        citations=citations,
        gaps=gaps,
    )
