"""Opt-in official current filing excerpt intake and real PostgreSQL lexical retrieval."""

import asyncio
import json
import tempfile
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

from backend.app.config import Settings
from backend.app.contracts.base import utc_now
from backend.app.contracts.rag import RagSearchRequest
from backend.app.financials.limiter import RedisSecRequestLimiter
from backend.app.financials.sec import SecFinancialClient
from backend.app.persistence.models import InstrumentRow
from backend.app.persistence.rag import RagRepository
from backend.app.persistence.session import Database
from backend.app.rag.ingestion import ingest_document
from backend.app.rag.retrieval import RagRetriever
from backend.app.rag.sec_documents import SecFilingExcerptClient


async def main() -> None:
    settings = Settings()
    if not settings.sec_user_agent:
        raise ValueError("SEC identifying contact is required")
    database = Database(settings.database_url)
    try:
        async with database.sessions() as session:
            instrument = await session.scalar(select(InstrumentRow).where(
                InstrumentRow.current_symbol == "KLAC", InstrumentRow.exchange == "NASDAQ",
            ))
            if instrument is None:
                raise ValueError("The KLAC permanent identity must be initialized first")
            limiter = RedisSecRequestLimiter(settings.redis_broker_url)
            financials = await SecFinancialClient(
                user_agent=settings.sec_user_agent, before_request=limiter,
            ).load_current("KLAC")
            source, raw, raw_hash = await SecFilingExcerptClient(
                user_agent=settings.sec_user_agent, before_request=limiter,
            ).load_current(instrument.instrument_id, financials.facts[0])
            result = ingest_document(source, verified_source=True)
            await RagRepository(session).store(result, embeddings=None)
            await session.commit()
            request = RagSearchRequest(
                instrument_id=instrument.instrument_id, query="KLA business revenue",
                analysis_timestamp=utc_now(),
            )
            hits = await RagRetriever(session, embeddings=None).search(request)
            # Earlier persisted captures may remain eligible; only this new document is excluded.
            before = request.model_copy(update={
                "analysis_timestamp": source.observed_at - timedelta(microseconds=1),
            })
            older = await RagRetriever(session, embeddings=None).search(before)
            if any(hit.document_id == result.document.document_id for hit in older):
                raise ValueError("new document became visible before acquisition")
            artifact = Path(tempfile.gettempdir()) / "tradeagent-sec-current-filing.html"
            artifact.write_bytes(raw)
            diagnostic = {
                "document_id": str(result.document.document_id),
                "status": result.document.status.value, "chunks": len(result.chunks),
                "source_uri": source.source_uri, "raw_hash": raw_hash,
                "observed_at": source.observed_at.isoformat(),
                "mode": "lexical_only", "hits": len(hits),
                "new_document_retrieved": any(
                    h.document_id == result.document.document_id for h in hits
                ),
                "complete_analysis": False, "historical_pit_qualified": False,
            }
            (artifact.with_suffix(".json")).write_text(json.dumps(diagnostic), encoding="utf-8")
            print(json.dumps(diagnostic))
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
