"""Owned research change projection through the company HTTP boundary."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.api.research import get_research_enqueuer
from backend.app.main import app
from backend.app.persistence.accounts import UserResearchRow
from backend.app.persistence.models import ResearchRunRow
from backend.app.persistence.session import Database
from backend.tests.test_account_research import submission
from backend.tests.test_accounts import ACCOUNT, INSTRUMENT_ID, ORIGIN
from backend.tests.test_accounts import account_client as shared_account_client

account_client = shared_account_client
PATH = f"/workspace/companies/{INSTRUMENT_ID}"
CUTOFF = datetime(2026, 10, 9, tzinfo=UTC)


def finished_run(
    client: TestClient, database: Database, *, day: int, gaps: tuple[str, ...] = (),
    query: str = "Assess evidence gaps", horizon: str = "3-5 days",
) -> str:
    """Prepare a persisted offline worker checkpoint; inspect it only through HTTP."""
    accepted = client.post("/workspace/research", json={
        **submission(), "query": query, "horizon": horizon,
    }, headers=ORIGIN)
    assert accepted.status_code == 202, accepted.text
    run_id = accepted.json()["research_run_id"]

    async def checkpoint() -> None:
        async with database.sessions() as session, session.begin():
            row = await session.get(ResearchRunRow, UUID(run_id))
            assert row is not None
            cutoff = CUTOFF + timedelta(days=day)
            row.created_at = cutoff
            row.analysis_timestamp = cutoff
            row.status = "insufficient_evidence"
            row.state_json = {
                **row.state_json, "analysis_timestamp": cutoff.isoformat(),
                "requested_at": cutoff.isoformat(), "status": "insufficient_evidence",
                "research_completion": "insufficient_evidence", "evidence_gaps": list(gaps),
                "runtime_metadata": {"submission_mode": "collection_only", "secret": "PRIVATE"},
            }

    asyncio.run(checkpoint())
    return run_id


def test_company_compares_owned_finished_records_independently_of_list_pagination(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2, gaps=("market", "news", "news"))
        latest = finished_run(client, database, day=-1, gaps=("market",))
        response = client.get(PATH, params={"limit": 1, "research_offset": 2})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["research"]["items"] == []
        change = response.json()["research_change"]
        assert change["availability"] == "available"
        assert change["latest"]["research_run_id"] == latest
        assert change["previous"]["research_run_id"] == prior
        assert change["latest"]["analysis_timestamp"] == "2026-10-08T00:00:00Z"
        assert change["latest"]["data_quality_status"] == "unverified"
        assert change["previous"]["evidence_gap_count"] == 2
        assert change["evidence_gap_count_delta"] == -1
        assert change["qualified_evidence_count_delta"] == 0
        assert change["window_limit"] == 50 and change["has_more"] is False
        for private in ("state_json", "runtime_metadata", "PRIVATE", "evidence_gaps"):
            assert private not in response.text
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def amend_run(database: Database, run_id: str, **changes: object) -> None:
    async def checkpoint() -> None:
        async with database.sessions() as session, session.begin():
            row = await session.get(ResearchRunRow, UUID(run_id))
            assert row is not None
            row.state_json = {**row.state_json, **changes}
            if "status" in changes:
                row.status = str(changes["status"])
    asyncio.run(checkpoint())


def test_coverage_counts_only_unique_company_cutoff_and_source_admitted_evidence(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2)
        latest = finished_run(client, database, day=-1)
        valid = {
            "evidence_id": str(uuid4()), "instrument_id": INSTRUMENT_ID,
            "evidence_type": "news_document", "source_name": "Offline source",
            "observed_at": "2026-10-07T00:00:00Z", "available_at": "2026-10-07T00:00:00Z",
            "retrieved_at": "2026-10-07T00:00:00Z", "content": "PRIVATE CONTENT",
            "confidence": 0.5, "freshness": 0.5, "trust_level": "public_source",
            "source_type": "news", "content_hash": "fixture", "injection_risk": 0.0,
            "sanitization_status": "html_cleaned_and_scanned",
        }
        amend_run(database, prior, evidence=[valid])
        amend_run(database, latest, evidence=[valid, valid, {**valid, "evidence_id": str(uuid4())},
            {**valid, "evidence_id": str(uuid4()), "available_at": "2026-10-09T00:00:00Z"},
            {**valid, "evidence_id": str(uuid4()), "instrument_id": str(uuid4())},
            {**valid, "evidence_id": str(uuid4()), "trust_level": "unknown"},
        ])
        response = client.get(PATH)
        change = response.json()["research_change"]
        assert change["previous"]["qualified_evidence_count"] == 1
        assert change["latest"]["qualified_evidence_count"] == 2
        assert change["qualified_evidence_count_delta"] == 1
        assert "PRIVATE CONTENT" not in response.text
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


@pytest.mark.parametrize("mismatch", [
    {"query": "Another question"}, {"horizon": "1 year"},
    {"runtime_metadata": {"submission_mode": "model_research"}},
    {"timestamp_mode": "fixed_cutoff", "parametric_lookahead_risk": True},
    {"replay_integrity_level": "evidence_constrained_replay", "parametric_lookahead_risk": True},
    {"analysis_timestamp": "2026-10-08T00:00:00Z"},
    {"analysis_timestamp": "2026-10-09T00:00:00Z"},
    {"analysis_timestamp": "2026-10-07T00:00:00", "requested_at": "2026-10-07T00:00:00"},
    {"analysis_timestamp": None},
    {"status": "pending"}, {"status": "running"}, {"status": "failed"},
    {"status": "cancelled"},
])
def test_mismatched_undated_and_unfinished_records_do_not_manufacture_a_change(
    account_client: tuple[TestClient, Database], mismatch: dict[str, object],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2)
        latest = finished_run(client, database, day=-1)
        amend_run(database, prior, **mismatch)
        change = client.get(PATH).json()["research_change"]
        assert change["availability"] == "no_comparable_previous"
        assert change["latest"]["research_run_id"] == latest
        assert change["previous"] is None
        assert change["qualified_evidence_count_delta"] is None
        assert change["evidence_gap_count_delta"] is None
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_empty_and_cross_account_histories_remain_unknown(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    assert client.get(PATH).status_code == 401
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    empty = client.get(PATH).json()["research_change"]
    assert empty["availability"] == "no_finished_research"
    assert empty["latest"] is None and empty["previous"] is None
    assert empty["qualified_evidence_count_delta"] is None
    assert empty["evidence_gap_count_delta"] is None
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        finished_run(client, database, day=-2)
        finished_run(client, database, day=-1)
        assert client.get(PATH).json()["research_change"]["availability"] == "available"
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/register", json={**ACCOUNT, "email": "other@example.test"},
                    headers=ORIGIN)
        assert client.get(PATH).json()["research_change"] == empty
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_naive_legacy_cutoff_outside_current_page_cannot_break_company_comparison(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        prior = finished_run(client, database, day=-2)
        latest = finished_run(client, database, day=-1)
        amend_run(database, prior, analysis_timestamp="2026-10-07T00:00:00")
        response = client.get(PATH, params={"limit": 1})
        assert response.status_code == 200
        assert response.json()["research"]["items"][0]["research_run_id"] == latest
        change = response.json()["research_change"]
        assert change["availability"] == "no_comparable_previous"
        assert change["latest"]["research_run_id"] == latest
        assert change["previous"] is None
        assert change["qualified_evidence_count_delta"] is None
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_history_window_discloses_older_records_and_cannot_use_a_match_outside_it(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    registered = client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    user_id = UUID(registered.json()["user_id"])
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        finished_run(client, database, day=-100)
        latest = finished_run(client, database, day=-1)

        async def checkpoints() -> None:
            async with database.sessions() as session, session.begin():
                template = await session.get(ResearchRunRow, UUID(latest))
                assert template is not None
                for day in range(-50, -1):
                    run_id = uuid4()
                    cutoff = CUTOFF + timedelta(days=day)
                    session.add(ResearchRunRow(
                        research_run_id=run_id, instrument_id=UUID(INSTRUMENT_ID),
                        query="Different question", horizon=template.horizon,
                        status="insufficient_evidence", created_at=cutoff,
                        analysis_timestamp=cutoff,
                        state_json={**template.state_json, "research_id": str(run_id),
                                    "query": "Different question",
                                    "requested_at": cutoff.isoformat(),
                                    "analysis_timestamp": cutoff.isoformat()},
                    ))
                    session.add(UserResearchRow(
                        user_id=user_id, research_run_id=run_id, request_id=uuid4(),
                        request_digest="offline-checkpoint",
                    ))
        asyncio.run(checkpoints())
        change = client.get(PATH).json()["research_change"]
        assert change["availability"] == "no_comparable_previous"
        assert change["has_more"] is True and change["window_limit"] == 50
        assert change["latest"]["research_run_id"] == latest
        assert change["previous"] is None and change["evidence_gap_count_delta"] is None
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)
