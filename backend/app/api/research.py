"""Research-run submission and status endpoints."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.research import ResearchBudget, ResearchState, ResearchStatus
from backend.app.jobs.celery_app import enqueue_research_run
from backend.app.persistence.repositories import ResearchRunRepository
from backend.app.persistence.session import get_session

ResearchEnqueuer = Callable[[str], str]


class ResearchSubmission(BaseModel):
    """JSON transport model; domain contracts remain strict after parsing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_id: UUID
    ticker: str = Field(min_length=1, max_length=32)
    query: str = Field(min_length=1)
    horizon: str = Field(min_length=1, max_length=64)
    analysis_timestamp: datetime = Field(default_factory=utc_now)
    budget: ResearchBudget = Field(default_factory=ResearchBudget)


class ResearchAccepted(ContractModel):
    research_run_id: UUID
    status: ResearchStatus
    task_id: str


def get_research_enqueuer() -> ResearchEnqueuer:
    return enqueue_research_run


router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchAccepted, status_code=status.HTTP_202_ACCEPTED)
async def submit_research(
    submission: ResearchSubmission,
    session: Annotated[AsyncSession, Depends(get_session)],
    enqueue: Annotated[ResearchEnqueuer, Depends(get_research_enqueuer)],
) -> ResearchAccepted:
    state = ResearchState(
        instrument_id=submission.instrument_id,
        ticker=submission.ticker,
        query=submission.query,
        analysis_timestamp=submission.analysis_timestamp,
        horizon=submission.horizon,
        research_budget=submission.budget,
    )
    await ResearchRunRepository(session).create(state)
    task_id = enqueue(str(state.research_id))
    return ResearchAccepted(
        research_run_id=state.research_id,
        status=state.status,
        task_id=task_id,
    )


@router.get("/{research_run_id}", response_model=ResearchState)
async def get_research(
    research_run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResearchState:
    state = await ResearchRunRepository(session).get(research_run_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="research run not found")
    return state
