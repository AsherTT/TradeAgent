"""Watchlist-page change summaries through the authenticated portal HTTP boundary."""

import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.api.research import get_research_enqueuer
from backend.app.main import app
from backend.app.persistence.accounts import UserResearchRow
from backend.app.persistence.models import InstrumentRow, ResearchRunRow
from backend.app.persistence.session import Database
from backend.tests.test_accounts import ACCOUNT, INSTRUMENT_ID, ORIGIN
from backend.tests.test_accounts import account_client as shared_account_client
from backend.tests.test_research_change import CUTOFF, amend_run, finished_run

account_client = shared_account_client


def test_portal_watchlist_changes_match_company_history_independently_of_research_paging(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2, gaps=("market", "news"))
        latest = finished_run(client, database, day=-1, gaps=("market",))
        response = client.get("/workspace/portal", params={"limit": 1, "research_offset": 2})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["recent_research"]["items"] == []
        changes = response.json()["research_changes"]
        assert len(changes) == 1 and changes[0]["instrument_id"] == INSTRUMENT_ID
        change = changes[0]["research_change"]
        assert change["latest"]["research_run_id"] == latest
        assert change["previous"]["research_run_id"] == prior
        assert change["evidence_gap_count_delta"] == -1
        assert change["qualified_evidence_count_delta"] == 0
        assert change == client.get(f"/workspace/companies/{INSTRUMENT_ID}").json()[
            "research_change"
        ]
        assert "PRIVATE" not in response.text and "state_json" not in response.text
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_portal_full_page_keeps_each_company_comparison_inside_its_first_50_records(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    registered = client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    user_id = UUID(registered.json()["user_id"])
    company_ids = [UUID(INSTRUMENT_ID), *[uuid4() for _ in range(20)]]
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        template_id = finished_run(client, database, day=-1, gaps=("market",))

        async def seed() -> None:
            async with database.sessions() as session, session.begin():
                template = await session.get(ResearchRunRow, UUID(template_id))
                assert template is not None
                for company_id in company_ids[1:]:
                    session.add(InstrumentRow(
                        instrument_id=company_id, current_symbol=f"PAGE{company_id.hex[:8]}",
                        exchange="NASDAQ", currency="USD", asset_type="equity",
                        company_name="Full page fixture", status="active",
                    ))
                for company_id in company_ids:
                    for position in range(1, 53):
                        if company_id == company_ids[0] and position == 1:
                            continue
                        run_id = uuid4()
                        cutoff = CUTOFF - timedelta(days=position)
                        query = template.query if position == 1 or position >= 51 else (
                            "Incompatible question"
                        )
                        session.add(ResearchRunRow(
                            research_run_id=run_id, instrument_id=company_id, query=query,
                            horizon=template.horizon, status="insufficient_evidence",
                            created_at=cutoff, analysis_timestamp=cutoff,
                            state_json={**template.state_json, "research_id": str(run_id),
                                        "instrument_id": str(company_id), "query": query,
                                        "requested_at": cutoff.isoformat(),
                                        "analysis_timestamp": cutoff.isoformat()},
                        ))
                        session.add(UserResearchRow(
                            user_id=user_id, research_run_id=run_id, request_id=uuid4(),
                            request_digest="offline-full-page-checkpoint",
                        ))
        asyncio.run(seed())
        for company_id in company_ids:
            followed = client.post(f"/workspace/watchlist/{company_id}", headers=ORIGIN)
            assert followed.status_code == 204
        response = client.get("/workspace/portal", params={"limit": 20})
        assert response.status_code == 200
        body = response.json()
        assert body["watchlist"]["total"] == 21
        assert len(body["research_changes"]) == 20
        assert [item["instrument_id"] for item in body["research_changes"]] == [
            item["instrument_id"] for item in body["watchlist"]["items"]
        ]
        for item in body["research_changes"]:
            change = item["research_change"]
            assert change["window_limit"] == 50 and change["has_more"] is True
            assert change["latest"]["analysis_timestamp"] == "2026-10-08T00:00:00Z"
            assert change["availability"] == "no_comparable_previous"
            assert change["previous"] is None and change["evidence_gap_count_delta"] is None
        next_page = client.get("/workspace/portal", params={
            "limit": 20, "watchlist_offset": 20,
        }).json()
        assert len(next_page["research_changes"]) == 1
        assert next_page["research_changes"][0]["instrument_id"] not in {
            item["instrument_id"] for item in body["research_changes"]
        }
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_portal_changes_are_only_for_the_current_owned_available_watchlist_page(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    assert client.get("/workspace/portal").status_code == 401
    second_id = uuid4()

    async def seed() -> None:
        async with database.sessions() as session, session.begin():
            session.add(InstrumentRow(
                instrument_id=second_id, current_symbol="SECOND", exchange="NASDAQ",
                currency="USD", asset_type="equity", company_name="Second", status="active",
            ))
    asyncio.run(seed())
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    assert client.get("/workspace/portal").json()["research_changes"] == []
    client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
    client.post(f"/workspace/watchlist/{second_id}", headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        finished_run(client, database, day=-2)
        finished_run(client, database, day=-1)
        for offset in (0, 1):
            body = client.get("/workspace/portal", params={
                "limit": 1, "watchlist_offset": offset,
            }).json()
            assert [item["instrument_id"] for item in body["research_changes"]] == [
                item["instrument_id"] for item in body["watchlist"]["items"]
            ]
            change = body["research_changes"][0]
            expected = "available" if change["instrument_id"] == INSTRUMENT_ID else (
                "no_finished_research"
            )
            assert change["research_change"]["availability"] == expected
        assert client.get("/workspace/portal", params={"watchlist_offset": 2}).json()[
            "research_changes"
        ] == []
        client.delete(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
        assert [item["instrument_id"] for item in client.get("/workspace/portal").json()[
            "research_changes"
        ]] == [str(second_id)]
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/register", json={**ACCOUNT, "email": "other@example.test"},
                    headers=ORIGIN)
        client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
        empty = client.get("/workspace/portal").json()["research_changes"][0]["research_change"]
        assert empty["availability"] == "no_finished_research"
        assert empty["latest"] is None and empty["evidence_gap_count_delta"] is None

        async def delist() -> None:
            async with database.sessions() as session, session.begin():
                company = await session.get(InstrumentRow, UUID(INSTRUMENT_ID))
                assert company is not None
                company.delisted_at = CUTOFF.date()
        asyncio.run(delist())
        assert client.get("/workspace/portal").json()["research_changes"] == []
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


@pytest.mark.parametrize("changes", [
    {"query": "Other question"}, {"horizon": "1 year"},
    {"runtime_metadata": {"submission_mode": "model_research"}},
    {"timestamp_mode": "fixed_cutoff", "parametric_lookahead_risk": True},
    {"analysis_timestamp": "2026-10-08T00:00:00Z"},
    {"analysis_timestamp": "2026-10-07T00:00:00"},
    {"status": "cancelled"}, {"status": "failed"},
])
def test_portal_unknown_and_incompatible_histories_keep_null_deltas(
    account_client: tuple[TestClient, Database], changes: dict[str, object],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2)
        finished_run(client, database, day=-1)
        amend_run(database, prior, **changes)
        body = client.get("/workspace/portal", params={"limit": 1}).json()
        change = body["research_changes"][0]["research_change"]
        assert change["availability"] == "no_comparable_previous"
        assert change["previous"] is None
        assert change["evidence_gap_count_delta"] is None
        assert change["qualified_evidence_count_delta"] is None
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_portal_windows_are_per_company_and_exclude_unowned_records_before_ranking(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    registered = client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    user_id = UUID(registered.json()["user_id"])
    client.post(f"/workspace/watchlist/{INSTRUMENT_ID}", headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    second_id = uuid4()
    try:
        finished_run(client, database, day=-100)
        latest = finished_run(client, database, day=-1)

        async def seed() -> None:
            async with database.sessions() as session, session.begin():
                template = await session.get(ResearchRunRow, UUID(latest))
                assert template is not None
                session.add(InstrumentRow(
                    instrument_id=second_id, current_symbol="SECOND", exchange="NASDAQ",
                    currency="USD", asset_type="equity", company_name="Second", status="active",
                ))
                for day in range(-50, 51):
                    run_id = uuid4()
                    cutoff = CUTOFF + timedelta(days=day)
                    session.add(ResearchRunRow(
                        research_run_id=run_id, instrument_id=UUID(INSTRUMENT_ID),
                        query="Other question", horizon=template.horizon,
                        status="insufficient_evidence", created_at=cutoff,
                        analysis_timestamp=cutoff,
                        state_json={**template.state_json, "research_id": str(run_id),
                                    "query": "Other question",
                                    "requested_at": cutoff.isoformat(),
                                    "analysis_timestamp": cutoff.isoformat()},
                    ))
                    if day < -1:
                        session.add(UserResearchRow(
                            user_id=user_id, research_run_id=run_id, request_id=uuid4(),
                            request_digest="offline-checkpoint",
                        ))
        asyncio.run(seed())
        client.post(f"/workspace/watchlist/{second_id}", headers=ORIGIN)
        second_latest = finished_run(client, database, day=-2, instrument_id=str(second_id))
        response = client.get("/workspace/portal")
        assert response.status_code == 200
        changes = {item["instrument_id"]: item["research_change"]
                   for item in response.json()["research_changes"]}
        first = changes[INSTRUMENT_ID]
        assert first["latest"]["research_run_id"] == latest
        assert first["availability"] == "no_comparable_previous"
        assert first["window_limit"] == 50 and first["has_more"] is True
        assert first["previous"] is None and first["evidence_gap_count_delta"] is None
        second = changes[str(second_id)]
        assert second["latest"]["research_run_id"] == second_latest
        assert second["has_more"] is False
        assert second["availability"] == "no_comparable_previous"
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)
