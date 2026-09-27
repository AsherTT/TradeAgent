"""Parse bounded external documents and quarantine instruction-bearing content."""

from __future__ import annotations

import json
import re
import unicodedata
from hashlib import sha256
from urllib.parse import urlsplit, urlunsplit

import pymupdf
from bs4 import BeautifulSoup

from backend.app.contracts.evidence import TrustLevel
from backend.app.contracts.rag import (
    DocumentFormat,
    DocumentSourceType,
    DocumentStatus,
    RagChunk,
    RagDocument,
    RagIngestResult,
    RagSource,
)

SCANNER_VERSION = "rag-guard-v1"
_INSTRUCTION_PATTERNS = {
    "instruction_override": re.compile(
        r"\b(ignore|disregard|override)\s+(all\s+)?(previous|prior|above|system|developer)\s+"
        r"(instructions?|messages?|prompts?)\b|忽略.{0,8}(指令|提示词)|覆盖.{0,8}(系统|开发者)",
        re.I,
    ),
    "role_spoofing": re.compile(
        r"\b(system|developer)\s*(prompt|message|instruction)\s*:|"
        r"\[/?(?:INST|SYS)\]|<\|(?:im_start|im_end)\|>|系统提示词|开发者指令",
        re.I,
    ),
    "tool_instruction": re.compile(
        r"\b(call|invoke|run|execute)\s+(a\s+|the\s+)?(tool|command|shell|code|function)\b|"
        r"\btool[_ -]?call\b|调用.{0,6}工具|执行.{0,6}(命令|代码)",
        re.I,
    ),
    "permission_escalation": re.compile(
        r"\b(change|increase|disable|bypass|override)\s+(the\s+)?"
        r"(budget|runtime profile|tool permissions?|security guard|safety filter)\b|"
        r"修改.{0,8}(预算|权限|运行配置)|关闭.{0,8}(安全|过滤)",
        re.I,
    ),
    "credential_request": re.compile(
        r"\b(reveal|print|send|exfiltrate)\s+(the\s+)?"
        r"(api key|token|password|credential|secret)s?\b|"
        r"(泄露|发送|输出).{0,8}(密钥|口令|凭证|令牌)",
        re.I,
    ),
}
_INVISIBLE = {"Cf", "Cc", "Cs"}
_HEADING = re.compile(r"^#{1,6}\s+(.+)$")


class RagIngestionError(ValueError):
    """An input cannot be parsed or safely bounded."""


def _normalize(raw: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw)
    visible = "".join(
        character
        for character in normalized
        if character in "\n\t" or unicodedata.category(character) not in _INVISIBLE
    )
    return "\n".join(" ".join(line.split()) for line in visible.splitlines()).strip()


def _safe_uri(uri: str | None, source_type: DocumentSourceType) -> str | None:
    if uri is None:
        if source_type is DocumentSourceType.USER_NOTE:
            return None
        raise RagIngestionError("external document requires a HTTPS source URI")
    try:
        parsed = urlsplit(uri)
        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
        ):
            raise RagIngestionError("source URI must be canonical HTTPS without credentials")
    except ValueError as exc:
        raise RagIngestionError("source URI is invalid") from exc
    if source_type is DocumentSourceType.SEC_FILING and parsed.hostname not in {
        "sec.gov",
        "www.sec.gov",
    }:
        raise RagIngestionError("SEC filing URI must use sec.gov")
    return urlunsplit(("https", parsed.hostname.lower(), parsed.path, "", ""))


def _html_text(raw: str) -> str:
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup.find_all(["script", "style", "template", "noscript", "iframe", "svg"]):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if tag.parent is None:
            continue
        style = str(tag.get("style", "")).replace(" ", "").lower()
        if (
            tag.has_attr("hidden")
            or tag.get("aria-hidden") == "true"
            or any(marker in style for marker in ("display:none", "visibility:hidden", "opacity:0"))
        ):
            tag.decompose()
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        tag.insert_before("\n# ")
        tag.insert_after("\n")
    for tag in soup.find_all(["p", "div", "li", "blockquote", "section", "article"]):
        tag.insert_before("\n")
        tag.insert_after("\n")
    return soup.get_text("")


def _pdf_text(raw: bytes) -> str:
    try:
        with pymupdf.open(stream=raw, filetype="pdf") as document:  # type: ignore[no-untyped-call]
            if document.page_count > 40:
                raise RagIngestionError("PDF exceeds 40-page limit")
            return "\n".join(
                f"# Page {index + 1}\n{page.get_text()}" for index, page in enumerate(document)
            )
    except RagIngestionError:
        raise
    except Exception as exc:
        raise RagIngestionError("PDF parsing failed") from exc


def _json_text(raw: str) -> str:
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise RagIngestionError("JSON parsing failed") from exc
    if not isinstance(parsed, (dict, list)):
        raise RagIngestionError("JSON document must be an object or array")
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True)


def _parse(source: RagSource) -> tuple[str, str]:
    if source.document_format is DocumentFormat.PDF:
        parsed = _pdf_text(source.raw_content)
        return parsed, parsed
    try:
        raw = source.raw_content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RagIngestionError("text document must be UTF-8") from exc
    if source.document_format is DocumentFormat.JSON:
        return _json_text(raw), raw
    if source.document_format in {DocumentFormat.HTML, DocumentFormat.MARKDOWN}:
        return _html_text(raw), raw
    return raw, raw


def _scan(raw: str, cleaned: str) -> tuple[float, tuple[str, ...]]:
    searchable = _normalize(raw + "\n" + cleaned)
    reasons = tuple(
        name for name, pattern in _INSTRUCTION_PATTERNS.items() if pattern.search(searchable)
    )
    return (1.0 if reasons else 0.0), reasons


def _split_piece(piece: str, limit: int = 1000) -> list[str]:
    words = piece.split()
    result: list[str] = []
    current = ""
    for word in words:
        for fragment in (word[index : index + limit] for index in range(0, len(word), limit)):
            if current and len(current) + len(fragment) + 1 > limit:
                result.append(current)
                current = ""
            current = f"{current} {fragment}".strip()
    if current:
        result.append(current)
    return result


def _chunks(document: RagDocument) -> tuple[RagChunk, ...]:
    heading: str | None = None
    pieces: list[tuple[str | None, str]] = []
    buffer = ""
    for line in document.content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _HEADING.match(stripped)
        if match:
            if buffer:
                pieces.append((heading, buffer))
                buffer = ""
            heading = match.group(1)[:200]
            continue
        for fragment in _split_piece(stripped):
            if buffer and len(buffer) + len(fragment) + 1 > 1000:
                pieces.append((heading, buffer))
                buffer = ""
            buffer = f"{buffer} {fragment}".strip()
    if buffer:
        pieces.append((heading, buffer))
    if len(pieces) > 64:
        raise RagIngestionError("document exceeds 64-chunk limit")
    return tuple(
        RagChunk(
            document_id=document.document_id,
            ordinal=index,
            heading=section,
            content=content,
            content_hash=sha256(content.encode()).hexdigest(),
        )
        for index, (section, content) in enumerate(pieces)
    )


def ingest_document(source: RagSource, *, verified_source: bool = False) -> RagIngestResult:
    """The caller controls bytes, never trust or policy. Verified provenance is adapter-only."""
    for timestamp in (source.observed_at, source.available_at, source.published_at):
        if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
            raise RagIngestionError("document timestamps must be timezone-aware")
    uri = _safe_uri(source.source_uri, source.source_type)
    parsed, raw_text = _parse(source)
    content = _normalize(parsed)
    if not content:
        raise RagIngestionError("document has no visible text")
    risk, reasons = _scan(raw_text, content)
    trust = TrustLevel.USER_CONTENT
    if verified_source:
        trust = (
            TrustLevel.OFFICIAL_PRIMARY
            if source.source_type is DocumentSourceType.SEC_FILING
            else TrustLevel.PUBLIC_SOURCE
        )
    status = DocumentStatus.QUARANTINED if risk >= 0.7 else DocumentStatus.ACCEPTED
    document = RagDocument(
        instrument_id=source.instrument_id,
        source_type=source.source_type,
        source_name=source.source_name,
        source_uri=uri,
        document_format=source.document_format,
        observed_at=source.observed_at,
        available_at=source.available_at,
        published_at=source.published_at,
        content=content,
        content_hash=sha256(content.encode()).hexdigest(),
        trust_level=trust,
        sanitization_status="parsed_normalized_scanned",
        injection_risk=risk,
        scanner_version=SCANNER_VERSION,
        status=status,
        risk_reasons=reasons,
    )
    return RagIngestResult(document=document, chunks=() if risk >= 0.7 else _chunks(document))
