"""Narrow SEC Company Facts client and conservative current annual normalization."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from time import monotonic
from typing import Any
from uuid import UUID

import httpx
from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.evidence import Evidence, TrustLevel

CONCEPTS = (
    "Assets",
    "CashAndCashEquivalentsAtCarryingValue",
    "NetIncomeLoss",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
)
_INSTANT = frozenset(CONCEPTS[:2])
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_TICKER = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,14}$")
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
MAX_BYTES = 10_000_000
MAX_PERIOD_AGE_DAYS = 550
MAX_FILING_AGE_DAYS = 400


class SecFinancialError(Exception):
    """Controlled acquisition/normalization failure, without response or contact data."""


def _supported_period(concept: str, start: date | None, end: date) -> bool:
    if concept in _INSTANT:
        return start is None
    return start is not None and 350 <= (end - start).days + 1 <= 380


class SecFinancialFact(ContractModel):
    cik: int = Field(ge=1, le=9_999_999_999)
    concept: str
    value: Decimal
    unit: str = "USD"
    period_start: date | None = None
    period_end: date
    filed_on: date
    form: str
    accession: str = Field(pattern=r"^\d{10}-\d{2}-\d{6}$")
    observed_at: datetime

    @model_validator(mode="after")
    def validate_observation(self) -> SecFinancialFact:
        if self.concept not in CONCEPTS or self.unit != "USD" or not self.value.is_finite():
            raise ValueError("unsupported financial value or concept")
        if self.form not in {"10-K", "10-K/A"}:
            raise ValueError("unsupported financial form")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("financial observation requires an aware timestamp")
        if (
            self.period_end > self.filed_on
            or self.filed_on > self.observed_at.astimezone(UTC).date()
        ):
            raise ValueError("financial period or filing is in the future")
        if not _supported_period(self.concept, self.period_start, self.period_end):
            raise ValueError("financial period is not a supported instant or annual duration")
        return self

    @property
    def source_uri(self) -> str:
        compact = self.accession.replace("-", "")
        return (
            f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{compact}/"
            f"{self.accession}-index.html"
        )

    def to_evidence(self, instrument_id: UUID, *, cutoff: datetime) -> Evidence:
        if cutoff.tzinfo is None or self.observed_at > cutoff:
            raise ValueError("financial observation exceeds analysis cutoff")
        data = self.model_dump(mode="json")
        data["taxonomy"] = "us-gaap"
        data["companyfacts_uri"] = (
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik:010d}.json"
        )
        content = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return Evidence(
            instrument_id=instrument_id,
            evidence_type="financial_fact",
            source_name="sec.companyfacts",
            source_uri=self.source_uri,
            observed_at=self.observed_at,
            retrieved_at=self.observed_at,
            available_at=self.observed_at,
            content=content,
            structured_data=data,
            confidence=1.0,
            freshness=max(
                0.0,
                1
                - (self.observed_at.astimezone(UTC).date() - self.period_end).days
                / MAX_PERIOD_AGE_DAYS,
            ),
            trust_level=TrustLevel.OFFICIAL_PRIMARY,
            source_type="sec_xbrl_current_observation",
            content_hash=sha256(content.encode()).hexdigest(),
            sanitization_status="typed_numeric_allowlist_v1",
            injection_risk=0.0,
        )


class SecFinancialSnapshot(ContractModel):
    ticker: str
    cik: int
    observed_at: datetime
    facts: tuple[SecFinancialFact, ...]
    gaps: tuple[str, ...]

    @model_validator(mode="after")
    def consistent_snapshot(self) -> SecFinancialSnapshot:
        if (
            not _TICKER.fullmatch(self.ticker)
            or not 1 <= self.cik <= 9_999_999_999
            or self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() is None
            or any(
                fact.cik != self.cik or fact.observed_at != self.observed_at for fact in self.facts
            )
        ):
            raise ValueError("financial snapshot identity or acquisition time mismatch")
        return self


def resolve_cik(payload: Any, ticker: str) -> int:
    """Current ticker mapping only, with no guessed or hardcoded identity fallback."""
    if not _TICKER.fullmatch(ticker) or not isinstance(payload, dict):
        raise SecFinancialError("invalid SEC ticker request or index")
    matches: set[int] = set()
    for item in payload.values():
        if isinstance(item, dict) and item.get("ticker") == ticker:
            cik = item.get("cik_str")
            if type(cik) is not int or not 1 <= cik <= 9_999_999_999:
                raise SecFinancialError("invalid SEC ticker CIK")
            matches.add(cik)
    if len(matches) != 1:
        raise SecFinancialError("SEC ticker is missing or ambiguous")
    return matches.pop()


def normalize_companyfacts(
    payload: Any, *, ticker: str, cik: int, observed_at: datetime
) -> SecFinancialSnapshot:
    if (
        not _TICKER.fullmatch(ticker)
        or not 1 <= cik <= 9_999_999_999
        or observed_at.tzinfo is None
        or observed_at.utcoffset() is None
    ):
        raise SecFinancialError("invalid SEC snapshot identity or observation time")
    observed_at = observed_at.astimezone(UTC)
    if (
        not isinstance(payload, dict)
        or type(payload.get("cik")) is not int
        or payload["cik"] != cik
    ):
        raise SecFinancialError("SEC Company Facts identity mismatch")
    if not isinstance(payload.get("entityName"), str) or not payload["entityName"].strip():
        raise SecFinancialError("SEC Company Facts missing entity name")
    try:
        gaap = payload["facts"]["us-gaap"]
        if not isinstance(gaap, dict):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise SecFinancialError("SEC Company Facts missing US-GAAP facts") from None
    facts: list[SecFinancialFact] = []
    gaps: list[str] = []
    for concept in CONCEPTS:
        node = gaap.get(concept)
        if node is None:
            gaps.append(f"missing annual USD concept: {concept}")
            continue
        try:
            rows = node["units"].get("USD", [])
            if not isinstance(rows, list) or len(rows) > 40_000:
                raise ValueError
        except (KeyError, TypeError, AttributeError, ValueError):
            raise SecFinancialError("invalid SEC concept units") from None
        selected = _annual_rows(rows, concept=concept, cik=cik, observed_at=observed_at)
        if selected:
            # Retain only the latest period for this small current-observation slice.
            latest_end = max(fact.period_end for fact in selected)
            latest = [fact for fact in selected if fact.period_end == latest_end]
            if len(latest) != 1:
                raise SecFinancialError("ambiguous SEC annual period boundaries")
            facts.append(latest[0])
        else:
            gaps.append(f"missing annual USD concept: {concept}")
    return SecFinancialSnapshot(
        ticker=ticker, cik=cik, observed_at=observed_at, facts=tuple(facts), gaps=tuple(gaps)
    )


def _annual_rows(
    rows: list[Any], *, concept: str, cik: int, observed_at: datetime
) -> tuple[SecFinancialFact, ...]:
    revisions: dict[tuple[date | None, date], SecFinancialFact] = {}
    observations: dict[tuple[date | None, date, date], Decimal] = {}
    accession_values: dict[tuple[date | None, date, str], Decimal] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise SecFinancialError("invalid SEC financial record")
        if not isinstance(row.get("form"), str):
            raise SecFinancialError("invalid SEC financial form")
        if row["form"] not in {"10-K", "10-K/A"}:
            continue
        try:
            end = date.fromisoformat(row["end"])
            filed = date.fromisoformat(row["filed"])
            start = date.fromisoformat(row["start"]) if "start" in row else None
            if end > observed_at.date() or filed > observed_at.date():
                continue
            if not _supported_period(concept, start, end):
                continue
            value = row["val"]
            accession = row["accn"]
            if type(value) not in {int, float, Decimal} or not _ACCESSION.fullmatch(accession):
                raise ValueError
            fact = SecFinancialFact(
                cik=cik,
                concept=concept,
                value=Decimal(str(value)),
                period_start=start,
                period_end=end,
                filed_on=filed,
                form=row["form"],
                accession=accession,
                observed_at=observed_at,
            )
        except (KeyError, TypeError, ValueError):
            raise SecFinancialError("invalid SEC annual USD financial record") from None
        identity = (start, end, filed)
        if identity in observations and observations[identity] != fact.value:
            raise SecFinancialError("conflicting SEC financial observations")
        observations[identity] = fact.value
        accession_key = (start, end, accession)
        if accession_key in accession_values and accession_values[accession_key] != fact.value:
            raise SecFinancialError("conflicting SEC accession values")
        accession_values[accession_key] = fact.value
        period = (start, end)
        previous = revisions.get(period)
        if previous is None or (filed, accession) > (previous.filed_on, previous.accession):
            revisions[period] = fact
    return tuple(revisions.values())


def validate_sec_user_agent(user_agent: str) -> None:
    if (
        not user_agent.strip()
        or len(user_agent) > 256
        or "@" not in user_agent
        or any(not 32 <= ord(char) <= 126 for char in user_agent)
    ):
        raise ValueError("SEC requires an identifying User-Agent with contact email")


class SecFinancialClient:
    """Single-client five-RPS bound, with an optional shared worker admission gate."""

    def __init__(
        self,
        *,
        user_agent: str,
        client: httpx.AsyncClient | None = None,
        observed_at: Callable[[], datetime] = utc_now,
        before_request: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        validate_sec_user_agent(user_agent)
        self._user_agent = user_agent
        self._client = client
        self._clock = observed_at
        self._before_request = before_request
        self.requests_made = 0
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def load_current(self, ticker: str) -> SecFinancialSnapshot:
        self.requests_made = 0
        ticker = ticker.strip().upper()
        if not _TICKER.fullmatch(ticker):
            raise SecFinancialError("invalid SEC ticker request")
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15, follow_redirects=False)
        try:
            index = await self._get(client, TICKERS_URL)
            cik = resolve_cik(index, ticker)
            payload = await self._get(
                client, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
            )
            return normalize_companyfacts(
                payload, ticker=ticker, cik=cik, observed_at=self._clock()
            )
        finally:
            if owns_client:
                await client.aclose()

    async def _get(self, client: httpx.AsyncClient, url: str) -> Any:
        async with self._lock:
            await asyncio.sleep(max(0.0, 0.2 - (monotonic() - self._last_request)))
            self._last_request = monotonic()
            try:
                if self._before_request is not None:
                    await self._before_request()
                self.requests_made += 1
                async with (
                    asyncio.timeout(20),
                    client.stream(
                        "GET",
                        url,
                        headers={"User-Agent": self._user_agent},
                        timeout=15,
                        follow_redirects=False,
                    ) as response,
                ):
                    if response.status_code != 200:
                        raise SecFinancialError(f"SEC returned HTTP {response.status_code}")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > MAX_BYTES:
                            raise SecFinancialError("SEC response exceeds size limit")
                        body.extend(chunk)
                return json.loads(body, parse_float=Decimal)
            except httpx.RequestError:
                raise SecFinancialError("SEC network request failed") from None
            except TimeoutError:
                raise SecFinancialError("SEC request exceeded wall-time limit") from None
            except (ValueError, UnicodeError):
                raise SecFinancialError("SEC returned invalid JSON") from None
