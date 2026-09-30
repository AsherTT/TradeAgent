"""Independent golden cases for SEC annual observations and transport failures."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from backend.app.financials.sec import (
    SecFinancialClient,
    SecFinancialError,
    normalize_companyfacts,
    resolve_cik,
)

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def payload() -> dict:
    return {
        "cik": 319201,
        "entityName": "KLA CORP",
        "facts": {
            "us-gaap": {
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2024-07-01",
                                "end": "2025-06-30",
                                "val": 100,
                                "filed": "2025-08-01",
                                "form": "10-K",
                                "accn": "0000319201-25-000001",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2025-06-30",
                                "val": 120,
                                "filed": "2025-08-20",
                                "form": "10-K/A",
                                "accn": "0000319201-25-000002",
                            },
                            {
                                "start": "2025-04-01",
                                "end": "2025-06-30",
                                "val": 30,
                                "filed": "2025-08-01",
                                "form": "10-K",
                                "accn": "0000319201-25-000001",
                            },
                            {
                                "start": "2024-07-01",
                                "end": "2025-03-31",
                                "val": 90,
                                "filed": "2025-05-01",
                                "form": "10-Q",
                                "accn": "0000319201-25-000003",
                            },
                        ]
                    }
                },
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "end": "2025-06-30",
                                "val": 500,
                                "filed": "2025-08-01",
                                "form": "10-K",
                                "accn": "0000319201-25-000001",
                            },
                        ]
                    }
                },
            }
        },
    }


def normalize(data: dict):
    return normalize_companyfacts(data, ticker="KLAC", cik=319201, observed_at=NOW)


def test_annual_revision_and_instant_values_keep_citations_and_current_availability() -> None:
    data = payload()
    data["facts"]["us-gaap"]["Assets"]["units"]["USD"] *= 2
    result = normalize(data)
    assert len(result.facts) == 2
    income = next(fact for fact in result.facts if fact.concept == "NetIncomeLoss")
    assert income.value == Decimal(120)
    assert income.form == "10-K/A"
    assert len(result.gaps) == 2
    assert income.source_uri == (
        "https://www.sec.gov/Archives/edgar/data/319201/000031920125000002/"
        "0000319201-25-000002-index.html"
    )
    evidence = income.to_evidence(uuid4(), cutoff=NOW)
    assert evidence.available_at == evidence.retrieved_at == NOW
    assert evidence.published_at is None
    assert evidence.structured_data["value"] == "120"
    with pytest.raises(ValueError, match="cutoff"):
        income.to_evidence(uuid4(), cutoff=NOW - timedelta(seconds=1))


def test_current_ticker_identity_requires_unique_exact_official_mapping() -> None:
    assert resolve_cik({"0": {"ticker": "KLAC", "cik_str": 319201}}, "KLAC") == 319201
    for index in [
        {},
        {"0": {"ticker": "KLAC", "cik_str": True}},
        {"0": {"ticker": "KLAC", "cik_str": 319201}, "1": {"ticker": "KLAC", "cik_str": 42}},
    ]:
        with pytest.raises(SecFinancialError):
            resolve_cik(index, "KLAC")
    data = payload()
    data["cik"] = 42
    with pytest.raises(SecFinancialError, match="identity"):
        normalize(data)


def test_future_filings_and_other_units_are_not_financial_evidence() -> None:
    data = payload()
    units = data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]
    units["EUR"] = units.pop("USD")
    row = data["facts"]["us-gaap"]["Assets"]["units"]["USD"][0]
    row["filed"] = "2026-10-02"
    assert normalize(data).facts == ()
    assert len(normalize(data).gaps) == 4


@pytest.mark.parametrize(
    "change",
    [
        {"val": True},
        {"val": "100"},
        {"val": float("inf")},
        {"end": "bad"},
        {"filed": "2025-01-01"},
        {"accn": "../../bad"},
    ],
)
def test_malformed_supported_records_fail_closed(change: dict) -> None:
    data = payload()
    data["facts"]["us-gaap"]["Assets"]["units"]["USD"][0].update(change)
    with pytest.raises(SecFinancialError, match="invalid SEC annual"):
        normalize(data)


def test_same_date_conflicting_revisions_fail_even_when_later_revision_exists() -> None:
    data = payload()
    rows = data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"]
    conflicting = deepcopy(rows[0])
    conflicting["val"] = 101
    rows.append(conflicting)
    with pytest.raises(SecFinancialError, match="conflicting"):
        normalize(data)


def test_53_week_annual_period_is_allowed_but_ambiguous_starts_are_rejected() -> None:
    data = payload()
    rows = data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"]
    rows[:] = [rows[0]]
    rows[0]["start"] = "2024-06-25"
    assert normalize(data).facts[-1].value == Decimal(100)
    other = deepcopy(rows[0])
    other["start"] = "2024-07-01"
    rows.append(other)
    with pytest.raises(SecFinancialError, match="ambiguous"):
        normalize(data)


def test_same_accession_cannot_change_value_by_changing_filing_date() -> None:
    data = payload()
    rows = data["facts"]["us-gaap"]["Assets"]["units"]["USD"]
    other = deepcopy(rows[0])
    other.update(val=600, filed="2025-08-02")
    rows.append(other)
    with pytest.raises(SecFinancialError, match="accession"):
        normalize(data)


def test_missing_entity_and_naive_observation_are_rejected() -> None:
    data = payload()
    data.pop("entityName")
    with pytest.raises(SecFinancialError, match="entity name"):
        normalize(data)
    with pytest.raises(SecFinancialError, match="observation time"):
        normalize_companyfacts(
            payload(), ticker="KLAC", cik=319201, observed_at=NOW.replace(tzinfo=None)
        )


def test_malformed_form_is_a_controlled_failure() -> None:
    data = payload()
    data["facts"]["us-gaap"]["Assets"]["units"]["USD"][0]["form"] = []
    with pytest.raises(SecFinancialError, match="financial form"):
        normalize(data)


def test_unsupported_quarter_value_does_not_invalidate_annual_facts() -> None:
    data = payload()
    quarter = data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"][2]
    quarter["val"] = "unsupported quarter value"
    quarter["accn"] = "unsupported quarter accession"
    result = normalize(data)
    assert len(result.facts) == 2
    assert result.facts[-1].value == Decimal(120)


@pytest.mark.asyncio
async def test_network_failure_has_controlled_diagnostic() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("private contact and transport details", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SecFinancialError, match="network request failed") as caught:
            await SecFinancialClient(
                user_agent="TradeAgent offline@example.org", client=client
            ).load_current("KLAC")
    assert "private" not in str(caught.value)


@pytest.mark.asyncio
async def test_client_uses_two_official_requests_and_no_redirects() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(str(request.url))
        assert request.headers["User-Agent"] == "TradeAgent offline@example.org"
        if request.url.host == "www.sec.gov":
            return httpx.Response(200, json={"0": {"ticker": "KLAC", "cik_str": 319201}})
        return httpx.Response(200, json=payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await SecFinancialClient(
            user_agent="TradeAgent offline@example.org", client=client, observed_at=lambda: NOW
        ).load_current("klac")
    assert result.cik == 319201
    assert paths == [
        "https://www.sec.gov/files/company_tickers.json",
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000319201.json",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [301, 403, 429, 500])
async def test_transport_stops_without_retry_or_contact_leak(status: int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, text="private response", headers={"Location": "https://evil"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SecFinancialError, match=f"HTTP {status}") as caught:
            await SecFinancialClient(
                user_agent="TradeAgent offline@example.org", client=client
            ).load_current("KLAC")
    assert calls == 1
    assert "offline@example.org" not in str(caught.value)
    assert "private response" not in str(caught.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"not-json", b"x" * 10_000_001], ids=["invalid", "oversized"])
async def test_invalid_or_oversized_response_is_rejected(body: bytes) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    ) as client:
        with pytest.raises(SecFinancialError):
            await SecFinancialClient(
                user_agent="TradeAgent offline@example.org", client=client
            ).load_current("KLAC")
