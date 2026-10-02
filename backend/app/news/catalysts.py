"""Source-bound optional interpretations, never verified events or market evidence."""

from hashlib import sha256

from backend.app.contracts.evidence import CatalystAssessment, Evidence, TrustLevel
from backend.app.contracts.research import ResearchState
from backend.app.graph.evidence_gap import qualified_evidence
from backend.app.graph.synthesis import validate_source_claims
from backend.app.news.research import SCANNER_VERSION as NEWS_SCANNER_VERSION


def catalyst_sources(state: ResearchState) -> tuple[Evidence, ...]:
    candidates = tuple(item for item in qualified_evidence(state) if (
        item.evidence_type in {"news_document", "rag_document"}
        and item.injection_risk == 0
        and item.content_hash == sha256(item.content.encode()).hexdigest()
        and (item.evidence_type != "news_document" or item.scanner_version == NEWS_SCANNER_VERSION)
        and item.trust_level in {
            TrustLevel.PUBLIC_SOURCE, TrustLevel.OFFICIAL_PRIMARY, TrustLevel.TRUSTED_PROVIDER,
        }
    ))
    return tuple(sorted(candidates, key=lambda item: (
        item.published_at or item.available_at, str(item.evidence_id),
    ), reverse=True)[:5])


def validate_catalysts(assessment: CatalystAssessment, sources: tuple[Evidence, ...]) -> None:
    validate_source_claims(assessment.claims, sources, {item.evidence_id for item in sources})
