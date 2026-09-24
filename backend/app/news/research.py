"""Bounded, point-in-time ingestion of untrusted news text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.evidence import Evidence, TrustLevel

SCANNER_VERSION = "news-guard-v1"
_INSTRUCTIONS = re.compile(
    r"(?i)(ignore (?:all )?(?:previous|prior) instructions|system prompt|"
    r"developer message|tool[_ -]?call|execute (?:this )?(?:command|code)|"
    r"disregard (?:the )?(?:above|instructions)|忽略(?:之前|以上|所有)(?:的)?指令|"
    r"系统提示词|开发者指令|执行(?:以下|这个)?(?:命令|代码))"
)


class NewsDocument(ContractModel):
    instrument_id: UUID
    source_name: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    source_uri: str = Field(min_length=1, max_length=2048)
    published_at: datetime
    observed_at: datetime
    available_at: datetime
    content: str = Field(min_length=1, max_length=20_000)


class NewsLoader(Protocol):
    async def load_news(
        self, instrument_id: UUID, *, analysis_timestamp: datetime, limit: int
    ) -> tuple[NewsDocument, ...]: ...


@dataclass(frozen=True, slots=True)
class NewsCollection:
    evidence: tuple[Evidence, ...]
    gaps: tuple[str, ...]
    documents_scanned: int


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def _clean_text(raw: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw)
    normalized = unicodedata.normalize("NFKC", " ".join(parser.parts))
    visible = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    return " ".join(visible.split())


def _safe_uri(raw: str) -> str | None:
    try:
        parsed = urlsplit(raw)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
        ):
            return None
    except ValueError:
        return None
    return urlunsplit(("https", parsed.hostname, parsed.path, "", ""))


class NewsResearchEvidence:
    """Convert bounded provider documents to evidence without trusting their instructions."""

    def __init__(self, loader: NewsLoader) -> None:
        self._loader = loader

    async def collect(
        self, instrument_id: UUID, *, analysis_timestamp: datetime, limit: int
    ) -> NewsCollection:
        documents = await self._loader.load_news(
            instrument_id, analysis_timestamp=analysis_timestamp, limit=limit
        )
        if len(documents) > limit:
            raise ValueError("news provider exceeded document limit")
        evidence: list[Evidence] = []
        gaps: list[str] = []
        for document in documents:
            if document.instrument_id != instrument_id:
                gaps.append("news document instrument mismatch")
                continue
            if (
                document.published_at > analysis_timestamp
                or document.observed_at > analysis_timestamp
                or document.available_at > analysis_timestamp
            ):
                gaps.append("news document exceeds analysis timestamp")
                continue
            uri = _safe_uri(document.source_uri)
            content = _clean_text(document.content)
            if uri is None or not content or _INSTRUCTIONS.search(content):
                gaps.append("news document rejected by source or content guard")
                continue
            evidence.append(
                Evidence(
                    instrument_id=instrument_id,
                    evidence_type="news_document",
                    source_name=document.source_name,
                    source_uri=uri,
                    published_at=document.published_at,
                    observed_at=document.observed_at,
                    retrieved_at=utc_now(),
                    available_at=document.available_at,
                    content=content,
                    confidence=0.5,
                    freshness=1.0,
                    trust_level=TrustLevel.PUBLIC_SOURCE,
                    source_type="news_provider",
                    content_hash=sha256(content.encode()).hexdigest(),
                    sanitization_status="html_cleaned_and_scanned",
                    injection_risk=0.0,
                    scanner_version=SCANNER_VERSION,
                )
            )
        return NewsCollection(tuple(evidence), tuple(gaps), len(documents))
