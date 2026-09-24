"""Research-run submission and status endpoints."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.research import (
    ResearchBudget,
    ResearchState,
    ResearchStatus,
    ResearchTimestampMode,
)
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
    timestamp_mode: ResearchTimestampMode
    analysis_timestamp: datetime | None = None
    budget: ResearchBudget = Field(default_factory=ResearchBudget)

    @model_validator(mode="after")
    def validate_timestamp_intent(self) -> ResearchSubmission:
        if (
            self.timestamp_mode is ResearchTimestampMode.CURRENT_RESEARCH
            and self.analysis_timestamp is not None
        ):
            raise ValueError("current research cannot supply analysis_timestamp")
        return self


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
    requested_at = utc_now()
    analysis_timestamp = submission.analysis_timestamp
    if submission.timestamp_mode is ResearchTimestampMode.FIXED_CUTOFF:
        analysis_timestamp = analysis_timestamp or requested_at
    state = ResearchState(
        instrument_id=submission.instrument_id,
        ticker=submission.ticker,
        query=submission.query,
        requested_at=requested_at,
        timestamp_mode=submission.timestamp_mode,
        analysis_timestamp=analysis_timestamp,
        horizon=submission.horizon,
        research_budget=submission.budget,
    )
    repository = ResearchRunRepository(session)
    await repository.create(state)
    await session.commit()
    try:
        task_id = enqueue(str(state.research_id))
    except Exception as exc:
        reason = f"queue dispatch failed: {type(exc).__name__}"
        await repository.set_status(
            state.research_id, ResearchStatus.FAILED, failure_reason=reason
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="research queue is unavailable",
        ) from exc
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
