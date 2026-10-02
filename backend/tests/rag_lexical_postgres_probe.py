"""Opt-in rolled-back lexical/PIT/isolation/immutability/NULL-pair PostgreSQL qualification."""

import asyncio
import json
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.app.config import Settings
from backend.app.contracts.base import utc_now
from backend.app.contracts.rag import (
    DocumentFormat,
    DocumentSourceType,
    RagSearchRequest,
    RagSource,
)
from backend.app.persistence.models import InstrumentRow, RagChunkRow
from backend.app.persistence.rag import RagRepository
from backend.app.persistence.session import Database
from backend.app.rag.ingestion import ingest_document
from backend.app.rag.retrieval import RagRetriever


async def main() -> None:
    database = Database(Settings().database_url)
    try:
        async with database.sessions() as session:
            instrument = await session.scalar(select(InstrumentRow).where(
                InstrumentRow.current_symbol == "KLAC", InstrumentRow.exchange == "NASDAQ",
            ))
            if instrument is None:
                raise ValueError("Initialize the KLAC permanent instrument first")
            captured = utc_now()
            result = ingest_document(RagSource(
                instrument_id=instrument.instrument_id, source_type=DocumentSourceType.USER_NOTE,
                source_name="rolled-back qualification fixture",
                document_format=DocumentFormat.TEXT,
                raw_content=b"lexicalqualificationfixture revenue verification",
                observed_at=captured, available_at=captured,
            ))
            await RagRepository(session).store(result, embeddings=None)
            retriever = RagRetriever(session, embeddings=None)
            request = RagSearchRequest(
                instrument_id=instrument.instrument_id, query="lexicalqualificationfixture",
                analysis_timestamp=captured + timedelta(seconds=1),
            )
            hits = await retriever.search(request)
            assert any(hit.document_id == result.document.document_id for hit in hits)
            assert not await retriever.search(request.model_copy(update={"instrument_id": uuid4()}))
            assert not await retriever.search(request.model_copy(update={
                "analysis_timestamp": captured - timedelta(microseconds=1),
            }))
            chunk = result.chunks[0]
            for command in (
                update(RagChunkRow).where(RagChunkRow.chunk_id == chunk.chunk_id).values(
                    content="changed"
                ),
                delete(RagChunkRow).where(RagChunkRow.chunk_id == chunk.chunk_id),
            ):
                try:
                    async with session.begin_nested():
                        await session.execute(command)
                except DBAPIError:
                    pass
                else:
                    raise ValueError("immutable lexical chunk accepted mutation")
            try:
                async with session.begin_nested():
                    session.add(RagChunkRow(
                        chunk_id=uuid4(), document_id=result.document.document_id, ordinal=999,
                        content="pair fixture", content_hash="a"*64,
                        embedding=None, embedding_model="invalid-pair",
                    ))
                    await session.flush()
            except IntegrityError:
                pass
            else:
                raise ValueError("NULL embedding with non-NULL model was accepted")
            await session.rollback()
            print(json.dumps({"lexical": True, "pit": True, "isolation": True,
                              "immutable": True, "null_pair": True, "rolled_back": True}))
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
