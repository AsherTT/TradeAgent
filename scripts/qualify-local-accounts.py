"""Exercise the real local web/API/PostgreSQL flow with disposable test accounts."""

import asyncio
import json
from datetime import timedelta
from secrets import token_urlsafe
from uuid import uuid4

import httpx
from sqlalchemy import delete, select, update

from backend.app.accounts.sessions import token_digest
from backend.app.contracts.base import utc_now
from backend.app.persistence.accounts import SessionRow, UserRow, WatchlistRow
from backend.app.persistence.session import get_database

ORIGIN = "http://127.0.0.1:3107"
API = ORIGIN + "/api/backend"


async def qualify() -> None:
    database = get_database()
    assert database.engine.dialect.name == "postgresql", "Real PostgreSQL is required"
    test_id = uuid4().hex
    password = token_urlsafe(24)
    emails = [f"account-probe-{test_id}-{suffix}@example.test" for suffix in ("a", "b")]
    headers = {"Origin": ORIGIN}
    clients = [httpx.AsyncClient(timeout=15, trust_env=False) for _ in emails]
    evidence: dict[str, object] = {"engine": "postgresql", "schema": "0015_local_accounts"}
    try:
        first, second = clients
        assert (await first.get(API + "/auth/me")).status_code == 401
        assert (
            await first.post(
                API + "/auth/login",
                json={"email": emails[0], "password": password},
                headers={"Origin": "https://untrusted.example"},
            )
        ).status_code == 403
        assert (await first.get(API + "/research")).status_code == 404
        for client, email in zip(clients, emails, strict=True):
            result = await client.post(
                API + "/auth/register", json={"email": email, "password": password}, headers=headers
            )
            assert result.status_code == 201, result.status_code
            assert "HttpOnly" in result.headers["set-cookie"]
            assert "SameSite=lax" in result.headers["set-cookie"]
            assert (await client.get(API + "/auth/me")).json()["email"] == email
        evidence["registration_and_origin"] = "passed"
        async with database.sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.email == emails[0]))
            assert user and user.password_hash.startswith("scrypt-v1$")
            assert user.password_hash != password
            raw_token = first.cookies.get("tradeagent_session")
            assert raw_token
            stored_session = await session.get(SessionRow, token_digest(raw_token))
            assert stored_session and stored_session.token_hash != raw_token
        evidence["password_and_session_stored_as_hashes"] = "passed"
        companies = (await first.get(API + "/workspace/companies")).json()
        assert companies, "Existing local company records are needed for watchlist qualification"
        follow_path = API + "/workspace/watchlist/" + companies[0]["instrument_id"]
        assert (await first.post(follow_path, headers=headers)).status_code == 204
        assert (await first.post(follow_path, headers=headers)).status_code == 204
        assert len((await first.get(API + "/workspace/watchlist")).json()) == 1
        assert (await second.get(API + "/workspace/watchlist")).json() == []
        assert (await second.delete(follow_path, headers=headers)).status_code == 204
        assert len((await first.get(API + "/workspace/watchlist")).json()) == 1
        async with httpx.AsyncClient(
            timeout=15, trust_env=False, cookies=first.cookies
        ) as refreshed:
            assert (await refreshed.get(API + "/auth/me")).json()["email"] == emails[0]
            assert len((await refreshed.get(API + "/workspace/watchlist")).json()) == 1
            assert (await refreshed.get(ORIGIN + "/app")).status_code == 200
        evidence["reload_and_cross_account_isolation"] = "passed"
        assert (await first.post(API + "/auth/logout", headers=headers)).status_code == 204
        assert (await first.get(API + "/auth/me")).status_code == 401
        async with httpx.AsyncClient(
            timeout=15, trust_env=False, cookies={"tradeagent_session": raw_token}
        ) as revoked:
            assert (await revoked.get(API + "/auth/me")).status_code == 401
        wrong = await first.post(
            API + "/auth/login",
            headers=headers,
            json={"email": emails[0], "password": "wrong-password"},
        )
        assert wrong.status_code == 401
        assert (
            await first.post(
                API + "/auth/login",
                headers=headers,
                json={"email": emails[0], "password": password},
            )
        ).status_code == 200
        second_token = second.cookies.get("tradeagent_session")
        assert second_token
        async with database.sessions() as session, session.begin():
            await session.execute(
                update(SessionRow)
                .where(SessionRow.token_hash == token_digest(second_token))
                .values(expires_at=utc_now() - timedelta(hours=1))
            )
        assert (await second.get(API + "/auth/me")).status_code == 401
        evidence["login_logout_revocation_expiry"] = "passed"
        assert (await first.delete(follow_path, headers=headers)).status_code == 204
        assert (await first.get(API + "/workspace/watchlist")).json() == []
        print(json.dumps(evidence, ensure_ascii=False))
    finally:
        for client in clients:
            await client.aclose()
        # These two UUID-namespaced accounts were created above by this probe only.
        async with database.sessions() as session, session.begin():
            user_ids = list(
                await session.scalars(select(UserRow.user_id).where(UserRow.email.in_(emails)))
            )
            if user_ids:
                await session.execute(
                    delete(WatchlistRow).where(WatchlistRow.user_id.in_(user_ids))
                )
                await session.execute(delete(SessionRow).where(SessionRow.user_id.in_(user_ids)))
                await session.execute(delete(UserRow).where(UserRow.user_id.in_(user_ids)))
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(qualify())
