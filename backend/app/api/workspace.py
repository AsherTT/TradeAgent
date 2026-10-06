"""Authenticated company discovery and personally owned watchlists."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from backend.app.accounts.sessions import require_browser_origin
from backend.app.api.accounts import AuthenticatedUser, BrowserSession
from backend.app.persistence.accounts import WatchlistRow
from backend.app.persistence.models import InstrumentRow


class Company(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_id: UUID
    current_symbol: str
    company_name: str
    exchange: str
    currency: str


router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/companies", response_model=list[Company])
async def companies(
    user: AuthenticatedUser, session: BrowserSession,
    query: Annotated[str, Query(max_length=64)] = "",
) -> list[InstrumentRow]:
    del user
    statement = select(InstrumentRow).where(InstrumentRow.delisted_at.is_(None))
    query = query.strip()
    if query:
        statement = statement.where(
            InstrumentRow.current_symbol.icontains(query, autoescape=True)
            | InstrumentRow.company_name.icontains(query, autoescape=True)
        )
    return list(await session.scalars(statement.order_by(InstrumentRow.current_symbol).limit(50)))


@router.get("/watchlist", response_model=list[Company])
async def watchlist(user: AuthenticatedUser, session: BrowserSession) -> list[InstrumentRow]:
    return list(await session.scalars(
        select(InstrumentRow).join(WatchlistRow).where(WatchlistRow.user_id == user.user_id)
        .order_by(WatchlistRow.created_at.desc())
    ))


@router.post("/watchlist/{instrument_id}", status_code=204,
             dependencies=[Depends(require_browser_origin)])
async def follow_company(
    instrument_id: UUID, user: AuthenticatedUser, session: BrowserSession,
) -> None:
    instrument = await session.get(InstrumentRow, instrument_id)
    if instrument is None or instrument.delisted_at is not None:
        raise HTTPException(404, detail="company_not_found")
    existing = await session.scalar(select(WatchlistRow).where(
        WatchlistRow.user_id == user.user_id, WatchlistRow.instrument_id == instrument_id,
    ))
    if existing is None:
        session.add(WatchlistRow(user_id=user.user_id, instrument_id=instrument_id))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            # Concurrent duplicate follows are idempotent only if the record now exists.
            existing = await session.scalar(select(WatchlistRow).where(
                WatchlistRow.user_id == user.user_id, WatchlistRow.instrument_id == instrument_id,
            ))
            if existing is None:
                raise


@router.delete("/watchlist/{instrument_id}", status_code=204,
               dependencies=[Depends(require_browser_origin)])
async def unfollow_company(
    instrument_id: UUID, user: AuthenticatedUser, session: BrowserSession,
) -> None:
    await session.execute(delete(WatchlistRow).where(
        WatchlistRow.user_id == user.user_id, WatchlistRow.instrument_id == instrument_id,
    ))
    await session.commit()
