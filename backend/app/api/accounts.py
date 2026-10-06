"""Email/password accounts backed by the configured PostgreSQL database."""

import asyncio
import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.accounts.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from backend.app.accounts.sessions import (
    SESSION_COOKIE,
    create_browser_session,
    current_user,
    require_browser_origin,
    revoke_browser_session,
    throttle_credentials,
)
from backend.app.config import get_settings
from backend.app.persistence.accounts import UserRow
from backend.app.persistence.session import get_session


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        pattern = r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
        if not re.fullmatch(pattern, value):
            raise ValueError("invalid email address")
        return value


class Registration(Credentials):
    password: SecretStr = Field(min_length=12, max_length=128)


class AccountProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    created_at: datetime


router = APIRouter(prefix="/auth", tags=["accounts"])
BrowserSession = Annotated[AsyncSession, Depends(get_session)]
AuthenticatedUser = Annotated[UserRow, Depends(current_user)]


@router.post("/register", response_model=AccountProfile, status_code=201,
             dependencies=[Depends(require_browser_origin)])
async def register(
    credentials: Registration, request: Request, response: Response, session: BrowserSession,
) -> UserRow:
    await throttle_credentials(request, session, action="register", email=credentials.email)
    password_hash = await asyncio.to_thread(hash_password, credentials.password.get_secret_value())
    user = UserRow(email=credentials.email, password_hash=password_hash)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, detail="email_unavailable") from exc
    await create_browser_session(request, response, session, user)
    return user


@router.post("/login", response_model=AccountProfile,
             dependencies=[Depends(require_browser_origin)])
async def login(
    credentials: Credentials, request: Request, response: Response, session: BrowserSession,
) -> UserRow:
    await throttle_credentials(request, session, action="login", email=credentials.email)
    user = await session.scalar(select(UserRow).where(UserRow.email == credentials.email))
    valid = await asyncio.to_thread(
        verify_password, credentials.password.get_secret_value(),
        user.password_hash if user else DUMMY_PASSWORD_HASH,
    )
    if not valid or user is None:
        raise HTTPException(401, detail="invalid_credentials")
    await create_browser_session(request, response, session, user)
    return user


@router.get("/me", response_model=AccountProfile)
async def me(user: AuthenticatedUser, response: Response) -> UserRow:
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204, dependencies=[Depends(require_browser_origin)])
async def logout(request: Request, session: BrowserSession) -> Response:
    await revoke_browser_session(request, session)
    await session.commit()
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True,
        secure=get_settings().auth_cookie_secure, samesite="lax",
    )
    return response
