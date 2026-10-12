"""Read-only company discovery through authenticated public HTTP endpoints."""

import asyncio
from collections.abc import Iterator
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.api.company_discovery import get_company_directory
from backend.app.company_directory import SecCompanyDirectory
from backend.app.main import app
from backend.app.persistence.models import InstrumentRow
from backend.app.persistence.session import Database
from backend.tests.test_accounts import ACCOUNT, INSTRUMENT_ID, ORIGIN
from backend.tests.test_accounts import account_client as shared_account_client

account_client = shared_account_client


@pytest.fixture
def directory_source() -> Iterator[None]:
    payload = {"fields": ["cik", "name", "ticker", "exchange"], "data": [
        [1, "Testing Systems", "TESTS", "Nasdaq"],
        [2, "Test Research Company", "TEST", "Nasdaq"],
        [3, "Other Test Company", "OTHER", "NYSE"],
        [4, "Berkshire Hathaway", "BRK-A", "NYSE"],
        [4, "Berkshire Hathaway", "BRK-B", "NYSE"],
        [5, "Unspecified Exchange", "UNKNOWN", None],
    ]}
    directory = SecCompanyDirectory("Test contact@example.test", transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json=payload),
    ))
    app.dependency_overrides[get_company_directory] = lambda: directory
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_company_directory, None)


def test_search_requires_session_and_exact_listing_resolves_without_admitting_candidates(
    account_client: tuple[TestClient, Database], directory_source: None,
) -> None:
    client, _ = account_client
    path = "/workspace/company-discovery"
    assert client.get(path).status_code == 401
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    response = client.get(path, params={"query": "test", "limit": 1})
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["total"] == 3 and body["directory_total"] == 6
    assert body["items"][0]["instrument_id"] == INSTRUMENT_ID
    assert body["source"] == "sec_company_tickers_exchange" and body["stale"] is False
    second = client.get(path, params={"query": "test", "limit": 1, "offset": 1}).json()
    assert second["items"][0]["symbol"] == "TESTS"
    assert second["items"][0]["instrument_id"] is None
    candidate = client.get(path + "/0000000001", params={"symbol": "TESTS", "exchange": "NASDAQ"})
    assert candidate.json()["company"]["instrument_id"] is None
    assert client.get("/workspace/companies", params={"query": "TESTS"}).json() == []
    assert client.get(path + "/0000000001", params={
        "symbol": "TESTS", "exchange": "NYSE",
    }).status_code == 404


def test_directory_bounds_literals_and_issuer_listing_identity(
    account_client: tuple[TestClient, Database], directory_source: None,
) -> None:
    client, _ = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    path = "/workspace/company-discovery"
    for params in ({"query": "x" * 65}, {"limit": 0}, {"limit": 51},
                   {"offset": -1}, {"offset": 100_001}):
        assert client.get(path, params=params).status_code == 422
    assert client.get(path, params={"query": "%"}).json()["items"] == []
    companies = client.get(path, params={"query": "Berkshire"}).json()["items"]
    assert [item["symbol"] for item in companies] == ["BRK-A", "BRK-B"]
    for symbol in ("BRK-A", "BRK-B"):
        result = client.get(path + "/4", params={"symbol": symbol, "exchange": "NYSE"})
        assert result.status_code == 200 and result.json()["company"]["symbol"] == symbol
    assert client.get(path + "/4", params={
        "symbol": "BRK-C", "exchange": "NYSE",
    }).status_code == 404
    assert client.get(path + "/invalid", params={"symbol": "BRK-A"}).status_code == 422
    unknown = client.get(path + "/5", params={"symbol": "UNKNOWN", "exchange": ""}).json()
    assert unknown["company"]["exchange"] is None
    assert unknown["company"]["instrument_id"] is None


def test_unconfigured_source_returns_unavailable_instead_of_false_empty_directory(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    directory = SecCompanyDirectory(None)
    app.dependency_overrides[get_company_directory] = lambda: directory
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        response = client.get("/workspace/company-discovery", params={"query": "AAPL"})
        assert response.status_code == 503
        assert response.json() == {"detail": "directory_not_configured"}
    finally:
        app.dependency_overrides.pop(get_company_directory, None)


def test_inactive_and_ambiguous_local_codes_never_resolve_to_a_research_company(
    account_client: tuple[TestClient, Database], directory_source: None,
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)

    async def change_status(status: str, duplicate: bool = False) -> None:
        async with database.sessions() as session, session.begin():
            record = await session.get(InstrumentRow, UUID(INSTRUMENT_ID))
            assert record is not None
            record.status = status
            if duplicate:
                session.add(InstrumentRow(
                    instrument_id=uuid4(), current_symbol="test", exchange="nasdaq",
                    company_name="Ambiguous case variant", currency="USD", asset_type="equity",
                    status="active",
                ))

    asyncio.run(change_status("inactive"))
    path = "/workspace/company-discovery?query=TEST&limit=1"
    assert client.get(path).json()["items"][0]["instrument_id"] is None
    asyncio.run(change_status("active", duplicate=True))
    assert client.get(path).json()["items"][0]["instrument_id"] is None
