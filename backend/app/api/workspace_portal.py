"""Read-only, account-scoped product entry projections."""

import json
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.accounts import AuthenticatedUser, BrowserSession
from backend.app.api.workspace import Company
from backend.app.api.workspace_changes import (
    RESEARCH_CHANGE_WINDOW,
    ResearchChange,
    research_change,
)
from backend.app.api.workspace_research import ResearchSummary, summary
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.persistence.accounts import UserResearchRow, WatchlistRow
from backend.app.persistence.models import InstrumentRow, ResearchRunRow

router = APIRouter(prefix="/workspace", tags=["account portal"])
PageLimit = Annotated[int, Query(ge=1, le=20)]
PageOffset = Annotated[int, Query(ge=0, le=10_000)]


class WorkspacePage[T](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[T]
    total: int
    offset: int
    limit: int


class CompanyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    company: Company
    is_followed: bool
    directory_scope: Literal["local_directory"] = "local_directory"
    research: WorkspacePage[ResearchSummary]
    research_change: ResearchChange


class PortalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    directory_scope: Literal["local_directory"] = "local_directory"
    watchlist: WorkspacePage[Company]
    recent_research: WorkspacePage[ResearchSummary]
    active_research: list[ResearchSummary]
    active_research_total: int


async def research_page(
    session: AsyncSession, statement: Select[ResearchRunRow], limit: int, offset: int,
) -> WorkspacePage[ResearchSummary]:
    total = await session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = await session.scalars(statement.order_by(
        ResearchRunRow.created_at.desc(), ResearchRunRow.research_run_id.desc(),
    ).offset(offset).limit(limit))
    return WorkspacePage(
        items=[
            summary(ResearchState.model_validate_json(json.dumps(row.state_json))) for row in rows
        ],
        total=total or 0, offset=offset, limit=limit,
    )


@router.get("/portal", response_model=PortalSummary)
async def portal_summary(
    user: AuthenticatedUser, session: BrowserSession,
    limit: PageLimit = 12, watchlist_offset: PageOffset = 0, research_offset: PageOffset = 0,
) -> PortalSummary:
    followed = select(InstrumentRow).join(WatchlistRow).where(
        WatchlistRow.user_id == user.user_id, InstrumentRow.delisted_at.is_(None),
    )
    followed_total = await session.scalar(select(func.count()).select_from(followed.subquery()))
    companies = await session.scalars(followed.order_by(
        WatchlistRow.created_at.desc(), InstrumentRow.instrument_id.desc(),
    ).offset(watchlist_offset).limit(limit))
    owned = select(ResearchRunRow).join(UserResearchRow).where(
        UserResearchRow.user_id == user.user_id,
    )
    active = await research_page(session, owned.where(ResearchRunRow.status.in_(
        (ResearchStatus.PENDING.value, ResearchStatus.RUNNING.value),
    )), 3, 0)
    return PortalSummary(
        watchlist=WorkspacePage(
            items=[Company.model_validate(company) for company in companies],
            total=followed_total or 0, offset=watchlist_offset, limit=limit,
        ),
        recent_research=await research_page(session, owned, limit, research_offset),
        active_research=active.items, active_research_total=active.total,
    )


@router.get("/companies/{instrument_id}", response_model=CompanyDetail)
async def company_detail(
    instrument_id: UUID, user: AuthenticatedUser, session: BrowserSession,
    limit: PageLimit = 12, research_offset: PageOffset = 0,
) -> CompanyDetail:
    company = await session.get(InstrumentRow, instrument_id)
    if company is None or company.delisted_at is not None:
        raise HTTPException(404, detail="company_not_found")
    followed = await session.scalar(select(WatchlistRow.watchlist_id).where(
        WatchlistRow.user_id == user.user_id, WatchlistRow.instrument_id == instrument_id,
    ))
    owned = select(ResearchRunRow).join(UserResearchRow).where(
        UserResearchRow.user_id == user.user_id, ResearchRunRow.instrument_id == instrument_id,
    )
    finished = list(await session.scalars(owned.where(ResearchRunRow.status.in_(
        (ResearchStatus.COMPLETE.value, ResearchStatus.INSUFFICIENT_EVIDENCE.value),
    )).order_by(
        ResearchRunRow.created_at.desc(), ResearchRunRow.research_run_id.desc(),
    ).limit(RESEARCH_CHANGE_WINDOW + 1)))
    return CompanyDetail(
        company=Company.model_validate(company), is_followed=followed is not None,
        research=await research_page(session, owned, limit, research_offset),
        research_change=research_change([
            ResearchState.model_validate_json(json.dumps(row.state_json))
            for row in finished[:RESEARCH_CHANGE_WINDOW]
        ], has_more=len(finished) > RESEARCH_CHANGE_WINDOW),
    )
