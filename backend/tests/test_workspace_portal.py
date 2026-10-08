"""Portal and company projections through authenticated HTTP interfaces."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.api.research import get_research_enqueuer
from backend.app.main import app
from backend.app.persistence.models import InstrumentRow
from backend.app.persistence.session import Database
from backend.tests.test_account_research import submission
from backend.tests.test_accounts import ACCOUNT, INSTRUMENT_ID, ORIGIN
from backend.tests.test_accounts import account_client as shared_account_client

account_client = shared_account_client


def test_company_identity_and_follow_state_require_a_session(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    path = f"/workspace/companies/{INSTRUMENT_ID}"
    assert client.get(path).status_code == 401
    assert client.post("/auth/register", json=ACCOUNT, headers=ORIGIN).status_code == 201
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["company"]["company_name"] == "Test Research Company"
    assert body["is_followed"] is False
    assert body["directory_scope"] == "local_directory"
    assert body["research"]["items"] == [] and body["research"]["total"] == 0
    assert client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN).status_code == 204
    assert client.get(path).json()["is_followed"] is True


def test_company_research_is_paginated_and_excludes_other_accounts_companies_and_unowned_runs(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    second_id = str(uuid4())

    async def seed_company() -> None:
        async with database.sessions() as session, session.begin():
            session.add(InstrumentRow(
                instrument_id=UUID(second_id), current_symbol="OTHER", exchange="NASDAQ",
                currency="USD", asset_type="equity", company_name="Other Company", status="active",
            ))

    asyncio.run(seed_company())
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        client.post("/research", json={
            "instrument_id": INSTRUMENT_ID, "ticker": "TEST", "query": "Historical unowned",
            "horizon": "1d", "timestamp_mode": "fixed_cutoff",
            "replay_integrity_level": "research_replay",
        })
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        ids = [client.post("/workspace/research", json=submission(), headers=ORIGIN)
               .json()["research_run_id"] for _ in range(2)]
        other_company = client.post("/workspace/research", json={
            **submission(), "instrument_id": second_id,
        }, headers=ORIGIN).json()["research_run_id"]
        path = f"/workspace/companies/{INSTRUMENT_ID}"
        first = client.get(path, params={"limit": 1}).json()["research"]
        assert first["total"] == 2
        assert first["items"][0]["research_run_id"] == ids[1]
        second = client.get(path, params={"limit": 1, "research_offset": 1}).json()["research"]
        assert second["items"][0]["research_run_id"] == ids[0]
        assert second["total"] == 2 and second["offset"] == 1
        assert client.get(path, params={"research_offset": 2}).json()["research"]["items"] == []
        assert client.get(f"/workspace/companies/{second_id}").json()["research"]["items"][0][
            "research_run_id"
        ] == other_company
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/register", json={**ACCOUNT, "email": "other@example.test"},
                    headers=ORIGIN)
        assert client.get(path).json()["research"]["total"] == 0
        assert client.get(path).json()["is_followed"] is False
        own = client.post("/workspace/research", json=submission(), headers=ORIGIN)
        assert client.get(path).json()["research"]["items"][0]["research_run_id"] == own.json()[
            "research_run_id"
        ]
        assert "state_json" not in client.get(path).text
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_portal_bounds_watchlist_paging_and_delisted_company_visibility(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    second_id = uuid4()

    async def seed_company() -> None:
        async with database.sessions() as session, session.begin():
            session.add(InstrumentRow(
                instrument_id=second_id, current_symbol="SECOND", exchange="NASDAQ",
                currency="USD", asset_type="equity", company_name="Second Company", status="active",
            ))

    asyncio.run(seed_company())
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    for instrument_id in (INSTRUMENT_ID, str(second_id)):
        followed = client.post(f"/workspace/watchlist/{instrument_id}", headers=ORIGIN)
        assert followed.status_code == 204
    first = client.get("/workspace/portal", params={"limit": 1}).json()["watchlist"]
    second = client.get("/workspace/portal", params={"limit": 1, "watchlist_offset": 1}).json()[
        "watchlist"
    ]
    assert first["total"] == second["total"] == 2
    assert {first["items"][0]["instrument_id"], second["items"][0]["instrument_id"]} == {
        INSTRUMENT_ID, str(second_id),
    }
    for params in ({"limit": 0}, {"limit": 21}, {"watchlist_offset": -1},
                   {"research_offset": 10_001}):
        response = client.get("/workspace/portal", params=params)
        assert response.status_code == 422
        assert response.headers["cache-control"] == "no-store"
    assert client.get(f"/workspace/companies/{uuid4()}").status_code == 404
    assert client.get("/workspace/companies/invalid").status_code == 422
    invalid_page = client.get(f"/workspace/companies/{INSTRUMENT_ID}", params={"limit": 21})
    assert invalid_page.status_code == 422

    async def delist_company() -> None:
        async with database.sessions() as session, session.begin():
            company = await session.get(InstrumentRow, second_id)
            assert company is not None
            company.delisted_at = datetime.now(UTC)

    asyncio.run(delist_company())
    response = client.get(f"/workspace/companies/{second_id}")
    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"
    remaining = client.get("/workspace/portal").json()["watchlist"]
    assert remaining["total"] == 1
    assert remaining["items"][0]["instrument_id"] == INSTRUMENT_ID


def test_portal_projects_only_owned_watchlist_recent_research_and_active_tasks(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    assert client.get("/workspace/portal").status_code == 401
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
        ids = [client.post("/workspace/research", json=submission(), headers=ORIGIN)
               .json()["research_run_id"] for _ in range(3)]
        client.post(f"/workspace/research/{ids[0]}/cancel", headers=ORIGIN)
        fourth = client.post("/workspace/research", json=submission(), headers=ORIGIN)
        assert fourth.status_code == 202
        ids.append(fourth.json()["research_run_id"])
        response = client.get("/workspace/portal", params={"limit": 1})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        body = response.json()
        assert body["watchlist"]["total"] == 1
        assert body["watchlist"]["items"][0]["instrument_id"] == INSTRUMENT_ID
        assert body["recent_research"]["total"] == 4
        assert body["recent_research"]["items"][0]["research_run_id"] == ids[3]
        assert body["active_research_total"] == 3
        assert {item["research_run_id"] for item in body["active_research"]} == set(ids[1:])
        next_page = client.get("/workspace/portal", params={"limit": 1, "research_offset": 3})
        assert next_page.json()["recent_research"]["items"][0]["status"] == "cancelled"
        assert next_page.json()["recent_research"]["total"] == 4
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/register", json={**ACCOUNT, "email": "private@example.test"},
                    headers=ORIGIN)
        other = client.get("/workspace/portal").json()
        assert other["watchlist"]["total"] == other["recent_research"]["total"] == 0
        assert other["active_research"] == []
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)
