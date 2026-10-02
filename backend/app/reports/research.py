"""Deterministic, evidence-linked presentation of a persisted research run."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import DataQualityStatus, QualityGateDecision
from backend.app.contracts.evidence import SynthesisClaim
from backend.app.contracts.market import MarketAcquisitionSummary
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.financials.admission import admitted_financial_fact, select_financial_group
from backend.app.financials.sec import SecFinancialFact
from backend.app.graph.evidence_gap import qualified_evidence
from backend.app.graph.synthesis import validate_synthesis_claims


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
    financial_observations: tuple[FinancialReportObservation, ...] = Field(default=(), max_length=4)
    claims: tuple[SynthesisClaim, ...] = Field(default=(), max_length=8)


class FinancialReportObservation(ContractModel):
    evidence_id: UUID
    fact: SecFinancialFact


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
    attribution_invalid = False
    if synthesis is not None and synthesis_cited:
        try:
            validate_synthesis_claims(synthesis, tuple(eligible.values()))
        except ValueError:
            attribution_invalid = True
            synthesis_cited = False
    claims = synthesis.claims if synthesis is not None and synthesis_cited else ()
    cited_synthesis = tuple(
        ReportCitation(
            evidence_id=eligible[evidence_id].evidence_id,
            evidence_type=eligible[evidence_id].evidence_type,
            source_name=eligible[evidence_id].source_name,
            source_uri=_safe_source_uri(eligible[evidence_id].source_uri),
            published_at=eligible[evidence_id].published_at,
            observed_at=eligible[evidence_id].observed_at,
            available_at=eligible[evidence_id].available_at,
        )
        for evidence_id in cited_ids
        if synthesis_cited
    )
    eligible_news = sorted(
        (item for item in eligible.values() if item.evidence_type == "news_document"),
        key=lambda item: (item.published_at or item.available_at, str(item.evidence_id)),
        reverse=True,
    )
    news_citations = tuple(
        ReportCitation(
            evidence_id=item.evidence_id,
            evidence_type=item.evidence_type,
            source_name=item.source_name,
            source_uri=_safe_source_uri(item.source_uri),
            published_at=item.published_at,
            observed_at=item.observed_at,
            available_at=item.available_at,
        )
        for item in eligible_news[:8]
    )
    financial_items = (
        select_financial_group(tuple(eligible.values()), cutoff=state.analysis_timestamp)
        if state.analysis_timestamp is not None
        else ()
    )
    financial_observations = []
    for item in financial_items:
        assert state.analysis_timestamp is not None
        fact = admitted_financial_fact(item, cutoff=state.analysis_timestamp)
        assert fact is not None
        financial_observations.append(
            FinancialReportObservation(evidence_id=item.evidence_id, fact=fact)
        )
    financial_citations = tuple(
        ReportCitation(
            evidence_id=item.evidence_id,
            evidence_type=item.evidence_type,
            source_name=item.source_name,
            source_uri=_safe_source_uri(item.source_uri),
            published_at=None,
            observed_at=item.observed_at,
            available_at=item.available_at,
        )
        for item in financial_items
    )
    citations_by_id = {
        citation.evidence_id: citation
        for citation in (*cited_synthesis, *news_citations, *financial_citations)
    }
    citations = tuple(citations_by_id.values())
    sections = [
        ReportSection(
            title="Research status",
            text=(
                "A cited research synthesis is available."
                if synthesis_cited
                else "Collection-only run; no model synthesis was requested."
                if state.runtime_metadata.get("submission_mode") == "collection_only"
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
    sections.extend(
        ReportSection(
            title=f"Model interpretation: {claim.section}",
            text=claim.text + " Supporting quote establishes attribution, not verified analysis.",
            evidence_ids=(claim.evidence_id,),
        )
        for claim in claims
    )
    if financial_observations:
        sections.extend(
            ReportSection(
                title=f"Annual financial observation: {observation.fact.concept}",
                text=(
                    f"SEC reported {observation.fact.value} USD; period "
                    f"{observation.fact.period_start or 'instant'} to "
                    f"{observation.fact.period_end}; filed {observation.fact.filed_on}; "
                    f"{observation.fact.form}, accession {observation.fact.accession}. "
                    "Current acquired observation; not a business conclusion "
                    "or historical PIT proof."
                ),
                evidence_ids=(observation.evidence_id,),
            )
            for observation in financial_observations
        )
    sections.append(
        ReportSection(
            title="Catalysts",
            text="No separately verified catalyst analysis is available in this run.",
        )
    )
    if eligible_news:
        published = [item.published_at for item in eligible_news if item.published_at is not None]
        publication_range = (
            f" Published from {min(published).isoformat()} to {max(published).isoformat()}."
            if published
            else ""
        )
        sections.append(
            ReportSection(
                title="News observations",
                text=(
                    f"{len(eligible_news)} point-in-time eligible news documents were collected; "
                    f"{len(news_citations)} recent source records are linked below."
                    f"{publication_range} Headlines and summaries are unverified source content, "
                    "not an established catalyst analysis."
                ),
                evidence_ids=tuple(item.evidence_id for item in news_citations),
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
        and state.data_quality_status in {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
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
                *(("synthesis claim attribution is invalid",) if attribution_invalid else ()),
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
            "Summary and bull/bear citations support the synthesis as a whole; "
            "those paragraphs lack individual attribution. News observation citations identify "
            "source records only, not verified catalyst claims."
            " Optional model interpretation claims each have their own source citation and "
            "supporting quote; quote matching does not verify the interpretation."
        ),
        sections=tuple(sections),
        citations=citations,
        gaps=gaps,
        financial_observations=tuple(financial_observations),
        claims=claims,
    )
