"""Browser-session authentication and origin/rate boundaries."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.contracts.base import utc_now
from backend.app.persistence.accounts import AuthThrottleRow, SessionRow, UserRow
from backend.app.persistence.session import get_session

SESSION_COOKIE = "tradeagent_session"


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def require_browser_origin(request: Request) -> None:
    if request.headers.get("origin") not in get_settings().auth_allowed_origins:
        raise HTTPException(403, detail="origin_not_allowed")


async def throttle_credentials(
    request: Request, session: AsyncSession, *, action: str, email: str,
) -> None:
    now = utc_now()
    window = int(now.timestamp()) // 600
    expiry = datetime.fromtimestamp((window + 1) * 600, tz=UTC)
    ip = request.client.host if request.client else "unknown"
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    await session.execute(delete(AuthThrottleRow).where(AuthThrottleRow.expires_at <= now))
    over_limit = False
    for identity in (f"ip:{ip}", f"account:{email}"):
        key = token_digest(f"{action}:{identity}:{window}")
        statement = insert(AuthThrottleRow).values(
            bucket_key=key, attempts=1, expires_at=expiry,
        ).on_conflict_do_update(
            index_elements=[AuthThrottleRow.bucket_key],
            set_={"attempts": AuthThrottleRow.attempts + 1},
        ).returning(AuthThrottleRow.attempts)
        count = await session.scalar(statement)
        limit = get_settings().auth_attempt_limit * (10 if identity.startswith("ip:") else 1)
        if count is not None and count > limit:
            over_limit = True
    # Failed logins must consume their allowance even when a later HTTP error rolls back.
    await session.commit()
    if over_limit:
        retry_after = max(1, int((expiry - now).total_seconds()))
        raise HTTPException(
            429, detail="too_many_attempts", headers={"Retry-After": str(retry_after)},
        )


async def current_user(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRow:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or len(token) > 128:
        raise HTTPException(401, detail="authentication_required")
    user = await session.scalar(
        select(UserRow).join(SessionRow, SessionRow.user_id == UserRow.user_id).where(
            SessionRow.token_hash == token_digest(token), SessionRow.expires_at > utc_now(),
        )
    )
    if user is None:
        raise HTTPException(401, detail="authentication_required")
    return user


async def revoke_browser_session(request: Request, session: AsyncSession) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token and len(token) <= 128:
        await session.execute(
            delete(SessionRow).where(SessionRow.token_hash == token_digest(token))
        )


async def create_browser_session(
    request: Request, response: Response, session: AsyncSession, user: UserRow,
) -> None:
    settings = get_settings()
    await revoke_browser_session(request, session)
    await session.execute(delete(SessionRow).where(SessionRow.expires_at <= utc_now()))
    token = token_urlsafe(32)
    session.add(SessionRow(
        token_hash=token_digest(token), user_id=user.user_id,
        expires_at=utc_now() + timedelta(hours=settings.auth_session_hours),
    ))
    await session.commit()
    response.set_cookie(
        SESSION_COOKIE, token, max_age=settings.auth_session_hours * 3600,
        httponly=True, secure=settings.auth_cookie_secure, samesite="lax", path="/",
    )
    response.headers["Cache-Control"] = "no-store"
