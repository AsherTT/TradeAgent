"""Lexical NULL storage, mode wiring and official accession admission regressions."""

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from backend.app.config import Settings
from backend.app.contracts.instrument import Instrument
from backend.app.financials.sec import SecFinancialFact
from backend.app.persistence.base import Base
from backend.app.persistence.models import RagChunkRow
from backend.app.persistence.rag import RagRepository
from backend.app.persistence.repositories import SecurityMasterRepository
from backend.app.persistence.session import Database
from backend.app.rag.embedding import build_rag_embedding_provider
from backend.app.rag.ingestion import ingest_document
from backend.app.rag.sec_documents import (
    SecDocumentError,
    SecFilingExcerptClient,
    primary_document_uri,
)
from backend.tests.test_phase7_storage import _source

NOW = datetime(2026, 10, 2, tzinfo=UTC)


def fact() -> SecFinancialFact:
    return SecFinancialFact(
        cik=319201, concept="Assets", value=Decimal(1), period_end=date(2026, 6, 30),
        filed_on=date(2026, 8, 6), form="10-K", accession="0000319201-26-000027", observed_at=NOW,
    )


def index(link: str) -> bytes:
    return (f'<table class="tableFile"><tr><td>1</td><td>Primary</td>'
            f'<td><a href="{link}">filing</a></td><td>10-K</td></tr></table>').encode()


def test_lexical_mode_never_builds_configured_paid_embedder() -> None:
    settings = Settings(_env_file=None, rag_retrieval_mode="lexical_only",
                        rag_embedding_api_key="fixture", rag_embedding_model="fixture",
                        rag_embedding_base_url="https://example.org")
    assert build_rag_embedding_provider(settings) is None
    assert Settings(_env_file=None).rag_retrieval_mode == "hybrid"


@pytest.mark.asyncio
async def test_lexical_storage_has_null_vector_and_immutable_retry(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'lexical.db'}")
    try:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session:
            instrument = Instrument(current_symbol="KLAC", exchange="NASDAQ", currency="USD",
                                    asset_type="equity", company_name="KLA")
            await SecurityMasterRepository(session).add_instrument(instrument)
            result = ingest_document(_source(instrument.instrument_id, "KLA revenue fixture."))
            await RagRepository(session).store(result, embeddings=None)
            await session.commit()
            rows = (await session.scalars(select(RagChunkRow))).all()
            assert rows and all(
                row.embedding is None and row.embedding_model is None for row in rows
            )
            await RagRepository(session).store(result, embeddings=None)
            assert len((await session.scalars(select(RagChunkRow))).all()) == len(rows)
    finally:
        await database.dispose()


@pytest.mark.parametrize("link", [
    "https://evil.invalid/file.htm", "/Archives/edgar/data/42/other/file.htm",
    "javascript:alert(1)", "/ix?doc=https://evil.invalid/file.htm",
    "other.htm?secret=1",
])
def test_primary_document_cannot_escape_expected_accession(link: str) -> None:
    with pytest.raises(SecDocumentError):
        primary_document_uri(index(link), fact())


@pytest.mark.asyncio
async def test_current_filing_capture_is_labeled_and_stamped_after_acquisition() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("-index.html"):
            return httpx.Response(200, content=index("primary.htm"))
        return httpx.Response(
            200, content=b"<html><p>FORM 10-K</p><p>KLA revenue information.</p></html>",
        )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source, raw, digest = await SecFilingExcerptClient(
            user_agent="Fixture fixture@example.org", client=client,
        ).load_current(uuid4(), fact())
    assert source.observed_at == source.available_at
    assert source.published_at is None
    assert b"Start-of-filing excerpt" in source.raw_content
    assert raw and len(digest) == 64
    assert source.source_uri is not None and source.source_uri.endswith("primary.htm")


@pytest.mark.asyncio
async def test_redirect_or_wrong_form_response_is_rejected() -> None:
    for response in (httpx.Response(302), httpx.Response(200, content=b"error page")):
        def handler(request: httpx.Request, result: httpx.Response = response) -> httpx.Response:
            return httpx.Response(200, content=index("primary.htm")) if request.url.path.endswith(
                "-index.html"
            ) else result
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(SecDocumentError):
                await SecFilingExcerptClient(
                    user_agent="Fixture fixture@example.org", client=client,
                ).load_current(uuid4(), fact())
