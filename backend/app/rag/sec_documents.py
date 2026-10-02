"""Official current SEC accession acquisition with a clearly labeled bounded excerpt."""

import asyncio
import re
from collections.abc import Awaitable, Callable
from hashlib import sha256
from urllib.parse import parse_qs, urljoin, urlsplit
from uuid import UUID

import httpx
from bs4 import BeautifulSoup

from backend.app.contracts.base import utc_now
from backend.app.contracts.rag import DocumentFormat, DocumentSourceType, RagSource
from backend.app.financials.sec import SecFinancialFact, validate_sec_user_agent
from backend.app.rag.ingestion import _html_text


class SecDocumentError(ValueError):
    """Controlled bounded source failure, without response or contact disclosure."""


def primary_document_uri(index_html: bytes, fact: SecFinancialFact) -> str:
    directory = fact.source_uri.rsplit("/", 1)[0] + "/"
    matches: set[str] = set()
    soup = BeautifulSoup(index_html, "html.parser")
    for row in soup.select("table.tableFile tr"):
        cells = row.find_all("td")
        if len(cells) < 4 or cells[3].get_text(strip=True) != fact.form:
            continue
        anchor = cells[2].find("a", href=True)
        if anchor is None:
            continue
        href = str(anchor["href"])
        uri = urljoin(fact.source_uri, href)
        parsed = urlsplit(uri)
        if parsed.path in {"/ix", "/ixviewer/doc/action"}:
            query = parse_qs(parsed.query)
            if set(query) != {"doc"} or len(query["doc"]) != 1:
                raise SecDocumentError("invalid SEC primary inline-viewer link")
            uri = urljoin("https://www.sec.gov", query["doc"][0])
        suffix = uri.removeprefix(directory)
        if not uri.startswith(directory) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.html?", suffix):
            raise SecDocumentError("primary document is outside expected SEC accession")
        matches.add(uri)
    if len(matches) != 1:
        raise SecDocumentError("SEC primary filing is missing or ambiguous")
    return matches.pop()


class SecFilingExcerptClient:
    def __init__(
        self, *, user_agent: str, client: httpx.AsyncClient | None = None,
        before_request: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        validate_sec_user_agent(user_agent)
        self._agent = user_agent
        self._client = client
        self._before_request = before_request

    async def load_current(
        self, instrument_id: UUID, fact: SecFinancialFact,
    ) -> tuple[RagSource, bytes, str]:
        client = self._client or httpx.AsyncClient(follow_redirects=False)
        try:
            index = await self._fetch(client, fact.source_uri)
            uri = primary_document_uri(index, fact)
            raw = await self._fetch(client, uri)
            text = _html_text(raw.decode("utf-8", errors="replace"))
            if not re.search(r"\bFORM\s+" + re.escape(fact.form) + r"\b", text[:10_000], re.I):
                raise SecDocumentError("primary response lacks the expected filing form")
            # This is a labeled excerpt, not a representation of the complete filing.
            excerpt = text[:32_000]
            captured = utc_now()
            return (
                RagSource(
                    instrument_id=instrument_id, source_type=DocumentSourceType.SEC_FILING,
                    source_name="sec.edgar.current-start-excerpt-v1", source_uri=uri,
                    document_format=DocumentFormat.TEXT,
                    raw_content=("Start-of-filing excerpt (maximum 32000 characters). "
                                 "Full filing analysis is unavailable.\n" + excerpt).encode(),
                    observed_at=captured, available_at=captured,
                ), raw, sha256(raw).hexdigest(),
            )
        finally:
            if self._client is None:
                await client.aclose()

    async def _fetch(self, client: httpx.AsyncClient, uri: str) -> bytes:
        try:
            if self._before_request is not None:
                await self._before_request()
            async with asyncio.timeout(20), client.stream(
                "GET", uri, headers={"User-Agent": self._agent},
                follow_redirects=False, timeout=15,
            ) as response:
                if response.status_code != 200:
                    raise SecDocumentError(f"SEC filing returned HTTP {response.status_code}")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > 10_000_000:
                        raise SecDocumentError("SEC filing exceeds acquisition limit")
                    body.extend(chunk)
                return bytes(body)
        except (httpx.HTTPError, TimeoutError):
            raise SecDocumentError("SEC filing request unavailable") from None
