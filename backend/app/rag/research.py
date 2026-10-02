"""Convert bounded hybrid retrieval into point-in-time research evidence."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from backend.app.contracts.base import utc_now
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.rag import RagSearchRequest
from backend.app.contracts.research import ResearchState
from backend.app.rag.context import build_rag_context
from backend.app.rag.retrieval import RagRetriever
from backend.app.rag.router import route_rag_hits


@dataclass(frozen=True, slots=True)
class RagEvidenceCollection:
    evidence: tuple[Evidence, ...]
    chunks_selected: int


class RagResearchEvidence:
    def __init__(self, retriever: RagRetriever) -> None:
        self._retriever = retriever

    async def collect(self, state: ResearchState) -> RagEvidenceCollection:
        cutoff = state.analysis_timestamp
        if cutoff is None:
            raise ValueError("RAG evidence requires a frozen analysis timestamp")
        remaining = state.research_budget.max_rag_chunks - state.budget_usage.rag_chunks
        if remaining <= 0 or state.research_budget.max_context_tokens < 128:
            return RagEvidenceCollection((), 0)
        hits = await self._retriever.search(
            RagSearchRequest(
                instrument_id=state.instrument_id,
                query=state.query[:500],
                analysis_timestamp=cutoff,
                top_k=12,
            )
        )
        hits = route_rag_hits(state, hits)
        evidence_ids = {hit.chunk_id: uuid4() for hit in hits}
        context = build_rag_context(
            hits,
            instrument_id=state.instrument_id,
            analysis_timestamp=cutoff,
            max_chars=min(12_000, state.research_budget.max_context_tokens * 2),
            max_chunks=min(remaining, 12),
            citation_ids=evidence_ids,
        )
        selected = set(context.chunk_ids)
        evidence = tuple(
            Evidence(
                evidence_id=evidence_ids[hit.chunk_id],
                instrument_id=hit.instrument_id,
                evidence_type="rag_document",
                source_name=hit.source_name,
                source_uri=hit.source_uri,
                published_at=hit.published_at,
                observed_at=hit.observed_at,
                retrieved_at=utc_now(),
                available_at=hit.available_at,
                content=hit.content,
                structured_data={
                    "document_id": str(hit.document_id),
                    "chunk_id": str(hit.chunk_id),
                    "heading": hit.heading,
                    "retrieval_mode": getattr(self._retriever, "mode", "hybrid"),
                },
                confidence=0.5,
                freshness=1.0,
                trust_level=hit.trust_level,
                source_type=hit.source_type.value,
                content_hash=hit.content_hash,
                sanitization_status=hit.sanitization_status,
                injection_risk=hit.injection_risk,
                scanner_version=hit.scanner_version,
            )
            for hit in hits
            if hit.chunk_id in selected
        )
        return RagEvidenceCollection(evidence=evidence, chunks_selected=len(evidence))
