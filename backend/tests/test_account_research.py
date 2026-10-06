"""Account research authorization through the HTTP boundary (offline database/queue)."""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.api.research import get_research_enqueuer
from backend.app.main import app
from backend.app.persistence.models import ResearchRunRow
from backend.app.persistence.session import Database
from backend.tests.test_accounts import ACCOUNT, INSTRUMENT_ID, ORIGIN
from backend.tests.test_accounts import account_client as shared_account_client

account_client = shared_account_client


def submission() -> dict[str, object]:
    return {
        "request_id": str(uuid4()), "instrument_id": INSTRUMENT_ID,
        "query": "Assess evidence gaps", "horizon": "3-5 days", "collection_only": True,
        "budget": {"max_llm_calls": 0, "max_estimated_cost_usd": 0.1},
    }


def test_only_owner_can_list_read_cancel_and_open_reports(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    path = "/workspace/research"
    assert client.get(path).status_code == 401
    assert client.post(path, json=submission(), headers=ORIGIN).status_code == 401
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        assert client.post("/auth/register", json=ACCOUNT, headers=ORIGIN).status_code == 201
        accepted = client.post(path, json=submission(), headers=ORIGIN)
        assert accepted.status_code == 202, accepted.text
        run_id = accepted.json()["research_run_id"]
        own_path = f"{path}/{run_id}"
        assert client.get(path).json()[0]["research_run_id"] == run_id
        assert client.get(own_path).json()["ticker"] == "TEST"
        report = client.get(own_path + "/report")
        assert report.status_code == 200 and report.json()["complete_analysis"] is False
        for suffix, method in (("", "GET"), ("/report", "GET"), ("/cancel", "POST")):
            assert client.request(method, f"/research/{run_id}{suffix}").status_code == 404
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/register", json={**ACCOUNT, "email": "other@example.test"},
                    headers=ORIGIN)
        assert client.get(path).json() == []
        for suffix, method in (("", "GET"), ("/report", "GET"), ("/cancel", "POST")):
            assert client.request(method, own_path + suffix, headers=ORIGIN).status_code == 404
        client.post("/auth/logout", headers=ORIGIN)
        client.post("/auth/login", json=ACCOUNT, headers=ORIGIN)
        cancelled = client.post(own_path + "/cancel", headers=ORIGIN)
        assert cancelled.json()["status"] == "cancelled"
        assert client.post(own_path + "/cancel", headers=ORIGIN).json() == cancelled.json()
        assert client.get(own_path).json()["status"] == "cancelled"
        assert client.get(path).headers["cache-control"] == "no-store"
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_submission_retries_are_durable_and_content_conflicts_are_rejected(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    dispatched: list[str] = []

    def enqueue(run_id: str) -> str:
        dispatched.append(run_id)
        return "offline-task"

    app.dependency_overrides[get_research_enqueuer] = lambda: enqueue
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        body = submission()
        first = client.post("/workspace/research", json=body, headers=ORIGIN)
        retry = client.post("/workspace/research", json=body, headers=ORIGIN)
        assert retry.status_code == 202 and retry.json() == first.json()
        assert dispatched == [first.json()["research_run_id"]]
        conflict = client.post("/workspace/research", json={**body, "query": "Different"},
                               headers=ORIGIN)
        assert conflict.status_code == 409
        assert len(client.get("/workspace/research").json()) == 1
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_queue_failure_is_owned_and_retry_does_not_dispatch_again(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client

    def unavailable(_: str) -> str:
        raise RuntimeError("private queue credentials")

    app.dependency_overrides[get_research_enqueuer] = lambda: unavailable
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        body = submission()
        failed = client.post("/workspace/research", json=body, headers=ORIGIN)
        assert failed.status_code == 503 and "private" not in failed.text
        rows = client.get("/workspace/research").json()
        assert len(rows) == 1 and rows[0]["status"] == "failed"
        retry = client.post("/workspace/research", json=body, headers=ORIGIN)
        assert retry.status_code == 202 and retry.json()["status"] == "failed"
        detail = client.get(f"/workspace/research/{rows[0]['research_run_id']}")
        assert detail.json()["failure_code"] == "queue_unavailable"
        assert "private" not in detail.text
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_bounded_submission_validates_company_budget_origin_and_active_limit(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        assert client.get("/workspace/research/options").json() == {"models_enabled": False}
        assert client.post("/workspace/research", json=submission()).status_code == 403
        missing = {**submission(), "instrument_id": str(uuid4())}
        assert client.post("/workspace/research", json=missing, headers=ORIGIN).status_code == 404
        for change in ({"max_wall_time_seconds": 121}, {"max_llm_calls": 1},
                       {"max_estimated_cost_usd": 1.01}, {"max_context_tokens": 100001}):
            body = {**submission(), "budget": change}
            assert client.post("/workspace/research", json=body, headers=ORIGIN).status_code == 422
        for change in ({"user_id": str(uuid4())}, {"ticker": "FAKE"}, {"query": "  "}):
            assert client.post("/workspace/research", json={**submission(), **change},
                               headers=ORIGIN).status_code == 422
        full = {**submission(), "collection_only": False, "budget": {
            "max_llm_calls": 4, "max_estimated_cost_usd": 0.1,
        }}
        assert client.post("/workspace/research", json=full, headers=ORIGIN).status_code == 409
        for _ in range(3):
            assert client.post("/workspace/research", json=submission(),
                               headers=ORIGIN).status_code == 202
        assert client.post("/workspace/research", json=submission(),
                           headers=ORIGIN).status_code == 429
        assert client.get("/workspace/research/not-a-uuid").status_code == 422
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_historical_unowned_runs_remain_hidden_and_enabled_models_keep_explicit_budget(
    account_client: tuple[TestClient, Database], monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.app.config import Settings

    client, _ = account_client
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    monkeypatch.setattr("backend.app.api.workspace_research.get_settings", lambda: Settings(
        _env_file=None, account_research_models_enabled=True,
    ))
    try:
        legacy = client.post("/research", json={
            "instrument_id": INSTRUMENT_ID, "ticker": "TEST", "query": "Legacy", "horizon": "1d",
            "timestamp_mode": "fixed_cutoff", "replay_integrity_level": "research_replay",
        }).json()["research_run_id"]
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        assert client.get("/workspace/research").json() == []
        assert client.get(f"/workspace/research/{legacy}").status_code == 404
        assert client.get(f"/workspace/research/{legacy}/report").status_code == 404
        assert client.post(
            f"/workspace/research/{legacy}/cancel", headers=ORIGIN,
        ).status_code == 404
        full = {**submission(), "collection_only": False, "budget": {
            "max_llm_calls": 4, "max_estimated_cost_usd": 0.2,
        }}
        accepted = client.post("/workspace/research", json=full, headers=ORIGIN).json()
        detail = client.get(f"/workspace/research/{accepted['research_run_id']}").json()
        assert detail["research_budget"]["max_llm_calls"] == 4
        assert detail["actual_cost_usd"] is None
        assert detail["collection_only"] is False
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)


def test_persisted_budget_exhaustion_is_distinct_from_complete_analysis(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "offline-task"
    try:
        client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
        run_id = client.post("/workspace/research", json=submission(),
                             headers=ORIGIN).json()["research_run_id"]

        async def worker_checkpoint() -> None:
            async with database.sessions() as session, session.begin():
                row = await session.scalar(select(ResearchRunRow))
                assert row
                row.state_json = {**row.state_json,
                                  "research_completion": "budget_exhausted",
                                  "status": "insufficient_evidence", "runtime_metadata": {
                                      "submission_mode": "collection_only",
                                      "transitions": ["start", "budget_exhausted", "SECRET"],
                                  }}
                row.status = "insufficient_evidence"

        asyncio.run(worker_checkpoint())
        detail = client.get(f"/workspace/research/{run_id}").json()
        assert detail["research_completion"] == "budget_exhausted"
        assert detail["progress_steps"] == ["start", "budget_exhausted"]
        assert "runtime_metadata" not in detail and "state_json" not in detail
        report = client.get(f"/workspace/research/{run_id}/report").json()
        assert report["complete_analysis"] is False
        cancelled = client.post(f"/workspace/research/{run_id}/cancel", headers=ORIGIN).json()
        assert cancelled["research_completion"] == "budget_exhausted"
    finally:
        app.dependency_overrides.pop(get_research_enqueuer, None)
