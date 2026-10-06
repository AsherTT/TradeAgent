"""Real local PostgreSQL/BFF qualification; no worker or model calls.

Only this probe's UUID-namespaced accounts are cleaned; cancelled synthetic run
tombstones remain so queued redeliveries safely terminate. An optional
preview fixture is explicitly synthetic and cancelled before any worker could execute it.
"""

import argparse
import asyncio
import json
import re
from datetime import timedelta
from pathlib import Path
from secrets import token_urlsafe
from uuid import UUID, uuid4

import httpx
from sqlalchemy import delete, select, text

from backend.app.contracts.base import utc_now
from backend.app.contracts.evidence import Evidence, TrustLevel
from backend.app.persistence.accounts import SessionRow, UserResearchRow, UserRow
from backend.app.persistence.models import ResearchRunRow
from backend.app.persistence.repositories import ResearchRunRepository
from backend.app.persistence.session import get_database

ORIGIN = "http://127.0.0.1:3107"
API = ORIGIN + "/api/backend"


async def cleanup_probe_accounts(emails: list[str]) -> int:
    matches = [re.fullmatch(r"research-probe-([0-9a-f]{32})-([ab])@example.test", email)
               for email in emails]
    assert len(matches) == 2 and all(matches), "Only namespaced probe accounts may be cleaned"
    valid = [match for match in matches if match is not None]
    assert valid[0].group(1) == valid[1].group(1)
    assert {match.group(2) for match in valid} == {"a", "b"}
    database = get_database()
    async with database.sessions() as session, session.begin():
        user_ids = select(UserRow.user_id).where(UserRow.email.in_(emails))
        run_ids = list(await session.scalars(select(UserResearchRow.research_run_id).where(
            UserResearchRow.user_id.in_(user_ids),
        )))
        for run_id in run_ids:
            await ResearchRunRepository(session).cancel(run_id)
        # Never delete queued runs: workers must see a durable terminal state on redelivery.
        await session.execute(delete(UserResearchRow).where(UserResearchRow.user_id.in_(user_ids)))
        await session.execute(delete(SessionRow).where(SessionRow.user_id.in_(user_ids)))
        await session.execute(delete(UserRow).where(UserRow.email.in_(emails)))
    return len(run_ids)


async def cleanup_preview(identity_path: Path) -> None:
    module_path = await asyncio.to_thread(Path(__file__).resolve)
    resolved_identity = await asyncio.to_thread(identity_path.resolve)
    allowed = module_path.parents[1] / ".test-output"
    assert resolved_identity.is_relative_to(allowed), "Use the probe's local identity file"
    identity = json.loads(await asyncio.to_thread(identity_path.read_text, encoding="utf-8"))
    try:
        count = await cleanup_probe_accounts(identity["emails"])
        await asyncio.to_thread(identity_path.unlink)
        print(json.dumps({"probe_accounts": "removed", "terminal_tombstones": count}))
    finally:
        await get_database().dispose()


async def qualify(preview: Path | None) -> None:
    database = get_database()
    assert database.engine.dialect.name == "postgresql"
    async with database.sessions() as session:
        assert await session.scalar(text("select version_num from alembic_version")) == (
            "0016_account_research"
        )
    namespace = uuid4().hex
    emails = [f"research-probe-{namespace}-{suffix}@example.test" for suffix in ("a", "b")]
    password = token_urlsafe(24)
    clients = [httpx.AsyncClient(timeout=20, trust_env=False) for _ in emails]
    preserve = False
    headers = {"Origin": ORIGIN}
    evidence: dict[str, object] = {"engine": "postgresql", "schema": "0016_account_research"}
    try:
        first, second = clients
        assert (await first.get(API + "/workspace/research")).status_code == 401
        for client, email in zip(clients, emails, strict=True):
            result = await client.post(API + "/auth/register", headers=headers,
                                       json={"email": email, "password": password})
            assert result.status_code == 201, result.status_code
        companies = (await first.get(API + "/workspace/companies")).json()
        assert companies, "Existing company records are required"
        assert (await first.get(API + "/workspace/research/options")).json() == {
            "models_enabled": False,
        }
        body = {
            "request_id": str(uuid4()), "instrument_id": companies[0]["instrument_id"],
            "query": "离线界面验收 · 合成测试记录 / Offline UI verification · synthetic fixture",
            "horizon": "UI verification", "collection_only": True,
            "budget": {"max_llm_calls": 0, "max_estimated_cost_usd": 0.1},
        }
        assert (await first.post(API + "/workspace/research", json=body)).status_code == 403
        concurrent = await asyncio.gather(*[
            first.post(API + "/workspace/research", json=body, headers=headers) for _ in range(4)
        ])
        assert all(result.status_code == 202 for result in concurrent), [
            result.status_code for result in concurrent
        ]
        ids = {result.json()["research_run_id"] for result in concurrent}
        assert len(ids) == 1
        run_id = ids.pop()
        path = API + "/workspace/research/" + run_id
        try:
            conflict = await first.post(API + "/workspace/research", headers=headers,
                                        json={**body, "query": "different"})
            assert conflict.status_code == 409
            assert len((await first.get(API + "/workspace/research")).json()) == 1
            assert (await second.get(API + "/workspace/research")).json() == []
            for suffix, method in (("", "GET"), ("/report", "GET"), ("/cancel", "POST")):
                assert (await second.request(method, path + suffix,
                                             headers=headers)).status_code == 404
                async with httpx.AsyncClient(timeout=15, trust_env=False) as internal:
                    result = await internal.request(
                        method, f"http://127.0.0.1:8000/research/{run_id}{suffix}",
                    )
                    assert result.status_code == 404
            report = (await first.get(path + "/report")).json()
            assert report["complete_analysis"] is False
            async with httpx.AsyncClient(
                timeout=15, trust_env=False, cookies=first.cookies,
            ) as refreshed:
                detail = await refreshed.get(path)
                assert detail.status_code == 200
                assert detail.headers["cache-control"] == "no-store"
                assert detail.json()["actual_cost_usd"] is None
                assert (await refreshed.get(ORIGIN + "/app/research/" + run_id)).status_code == 200
            evidence["concurrent_idempotency_and_conflict"] = "passed"
            evidence["cross_account_and_legacy_isolation"] = "passed"
            evidence["refresh_report_and_unknown_fees"] = "passed"
        finally:
            cancelled = await first.post(path + "/cancel", headers=headers)
            assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
        assert (await first.post(path + "/cancel", headers=headers)).json() == cancelled.json()
        evidence["durable_idempotent_cancellation"] = "passed"
        if preview:
            # Test fixture setup only: this is not a real market acquisition/report.
            async with database.sessions() as session, session.begin():
                row = await session.get(ResearchRunRow, UUID(run_id))
                state = await ResearchRunRepository(session).get(UUID(run_id))
                assert row and state
                cutoff = utc_now()
                fixture = Evidence(
                    instrument_id=state.instrument_id, evidence_type="news_document",
                    source_name="OFFLINE FIXTURE · 合成测试来源", source_uri="https://example.org/",
                    published_at=cutoff - timedelta(hours=1), observed_at=cutoff,
                    retrieved_at=cutoff, available_at=cutoff,
                    content="Synthetic browser verification record; not real research or news.",
                    confidence=0.5, freshness=1, trust_level=TrustLevel.PUBLIC_SOURCE,
                    source_type="news", content_hash="offline-fixture",
                    sanitization_status="html_cleaned_and_scanned", injection_risk=0,
                )
                synthetic = state.model_copy(update={
                    "analysis_timestamp": cutoff, "evidence": (fixture,),
                    "evidence_gaps": ("OFFLINE FIXTURE: no real source acquisition or synthesis.",),
                })
                row.analysis_timestamp = cutoff
                row.state_json = synthetic.model_dump(mode="json")
            await asyncio.to_thread(preview.parent.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(
                preview.write_text,
                json.dumps({"email": emails[0], "password": password,
                            "run_id": run_id, "emails": emails}), encoding="utf-8",
            )
            preserve = True
            evidence["synthetic_preview_fixture"] = "saved; cancelled, no model calls"
        print(json.dumps(evidence, ensure_ascii=False))
    finally:
        for client in clients:
            await client.aclose()
        if not preserve:
            await cleanup_probe_accounts(emails)
        await database.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview-identity", type=Path)
    mode.add_argument("--cleanup-preview", type=Path)
    arguments = parser.parse_args()
    if arguments.cleanup_preview:
        asyncio.run(cleanup_preview(arguments.cleanup_preview))
    else:
        asyncio.run(qualify(arguments.preview_identity))
