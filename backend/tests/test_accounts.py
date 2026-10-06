"""Account and owned-workspace behavior through the public HTTP boundary."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import timedelta
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.contracts.base import utc_now
from backend.app.main import app
from backend.app.persistence.accounts import SessionRow
from backend.app.persistence.base import Base
from backend.app.persistence.models import InstrumentRow
from backend.app.persistence.session import Database, get_session

ORIGIN = {"Origin": "http://127.0.0.1:3107"}
ACCOUNT = {"email": "Researcher@example.com", "password": "Research-local-2026!"}
INSTRUMENT_ID = "ddc0c29b-6c1e-43c7-9f37-8a6e43a481ad"


@pytest.fixture
def account_client(tmp_path: Path) -> Iterator[tuple[TestClient, Database]]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'account.db'}")

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session, session.begin():
            session.add(InstrumentRow(
                instrument_id=UUID(INSTRUMENT_ID), current_symbol="TEST", exchange="NASDAQ",
                currency="USD", asset_type="equity", company_name="Test Research Company",
                status="active",
            ))

    async def override_session() -> AsyncIterator[AsyncSession]:
        async for session in database.session():
            yield session

    asyncio.run(prepare())
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client, database
    finally:
        app.dependency_overrides.pop(get_session, None)
        asyncio.run(database.dispose())


def test_registration_login_and_revocable_session(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    assert client.get("/auth/me").status_code == 401
    registered = client.post("/auth/register", json=ACCOUNT, headers=ORIGIN)
    assert registered.status_code == 201
    assert registered.json()["email"] == "researcher@example.com"
    assert "password" not in registered.text
    cookie = registered.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert client.get("/auth/me").json()["user_id"] == registered.json()["user_id"]
    previous_cookie = client.cookies.get("tradeagent_session")
    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204
    assert client.get("/auth/me").status_code == 401
    client.cookies.set("tradeagent_session", previous_cookie or "", domain="testserver.local")
    assert client.get("/auth/me").status_code == 401
    client.cookies.clear()
    wrong = client.post(
        "/auth/login", json={**ACCOUNT, "password": "wrong-password"}, headers=ORIGIN,
    )
    assert wrong.status_code == 401 and wrong.json()["detail"] == "invalid_credentials"
    correct = client.post("/auth/login", json=ACCOUNT, headers=ORIGIN)
    assert correct.status_code == 200
    assert client.get("/auth/me").json()["email"] == "researcher@example.com"


def test_credentials_validation_and_origin_rejection(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    assert client.post("/auth/register", json=ACCOUNT).status_code == 403
    assert client.post("/auth/register", json=ACCOUNT,
                       headers={"Origin": "https://attacker.example"}).status_code == 403
    invalid = client.post("/auth/register", json={**ACCOUNT, "password": "short"}, headers=ORIGIN)
    assert invalid.status_code == 422 and "short" not in invalid.text
    assert client.post("/auth/register", json=ACCOUNT, headers=ORIGIN).status_code == 201
    duplicate = client.post("/auth/register", json={**ACCOUNT, "email": "researcher@example.com"},
                            headers=ORIGIN)
    assert duplicate.status_code == 409
    assert client.post("/auth/logout", headers={"Origin": "null"}).status_code == 403
    assert client.get("/auth/me").status_code == 200


def test_expired_and_forged_sessions_are_rejected(
    account_client: tuple[TestClient, Database],
) -> None:
    client, database = account_client
    assert client.post("/auth/register", json=ACCOUNT, headers=ORIGIN).status_code == 201

    async def expire() -> None:
        async with database.sessions() as session, session.begin():
            await session.execute(
                update(SessionRow).values(expires_at=utc_now() - timedelta(days=1))
            )

    asyncio.run(expire())
    assert client.get("/auth/me").status_code == 401
    client.cookies.clear()
    client.cookies.set("tradeagent_session", "forged-session", domain="testserver.local")
    assert client.get("/auth/me").status_code == 401


def test_followed_companies_persist_and_are_isolated_by_account(
    account_client: tuple[TestClient, Database],
) -> None:
    client, _ = account_client
    path = f"/workspace/watchlist/{INSTRUMENT_ID}"
    assert client.get("/workspace/companies").status_code == 401
    assert client.post(path, headers=ORIGIN).status_code == 401
    assert client.post("/auth/register", json=ACCOUNT, headers=ORIGIN).status_code == 201
    found = client.get("/workspace/companies", params={"query": "Research"})
    assert found.status_code == 200 and found.json()[0]["current_symbol"] == "TEST"
    assert client.get("/workspace/companies", params={"query": "%"}).json() == []
    assert client.post(path, headers=ORIGIN).status_code == 204
    assert client.post(path, headers=ORIGIN).status_code == 204
    assert len(client.get("/workspace/watchlist").json()) == 1
    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204
    other = {**ACCOUNT, "email": "other@example.com"}
    assert client.post("/auth/register", json=other, headers=ORIGIN).status_code == 201
    assert client.get("/workspace/watchlist").json() == []
    assert client.delete(path, headers=ORIGIN).status_code == 204
    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204
    assert client.post("/auth/login", json=ACCOUNT, headers=ORIGIN).status_code == 200
    assert len(client.get("/workspace/watchlist").json()) == 1
    assert client.delete(path, headers=ORIGIN).status_code == 204
    assert client.get("/workspace/watchlist").json() == []


def test_failed_attempts_are_limited_even_after_error_rollbacks(
    account_client: tuple[TestClient, Database], monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = account_client
    monkeypatch.setattr("backend.app.accounts.sessions.get_settings",
                        lambda: Settings(_env_file=None, auth_attempt_limit=2))
    for _ in range(2):
        assert client.post("/auth/login", json=ACCOUNT, headers=ORIGIN).status_code == 401
    blocked = client.post("/auth/login", json=ACCOUNT, headers=ORIGIN)
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_cloud_account_configuration_requires_secure_origins() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, auth_allowed_origins=("http://tradeagent.example",))
    with pytest.raises(ValidationError):
        Settings(_env_file=None, auth_allowed_origins=("https://tradeagent.example",))
    configured = Settings(
        _env_file=None, auth_allowed_origins=("https://tradeagent.example",),
        auth_cookie_secure=True, database_ssl=True,
    )
    assert configured.auth_cookie_secure and configured.database_ssl
