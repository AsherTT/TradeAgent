"""Research-run submission and status endpoints."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.evaluation import EvaluationMaturity, ReplayIntegrityLevel
from backend.app.contracts.research import (
    ResearchBudget,
    ResearchState,
    ResearchStatus,
    ResearchTimestampMode,
)
from backend.app.evaluation.reporting import maturity_for_research
from backend.app.jobs.celery_app import enqueue_research_run
from backend.app.persistence.repositories import ResearchRunRepository
from backend.app.persistence.session import get_session
from backend.app.reports.research import ResearchReport, build_research_report

ResearchEnqueuer = Callable[[str], str]


class ResearchSubmission(BaseModel):
    """JSON transport model; domain contracts remain strict after parsing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_id: UUID
    ticker: str = Field(min_length=1, max_length=32)
    query: str = Field(min_length=1)
    horizon: str = Field(min_length=1, max_length=64)
    timestamp_mode: ResearchTimestampMode
    replay_integrity_level: ReplayIntegrityLevel
    analysis_timestamp: datetime | None = None
    budget: ResearchBudget = Field(default_factory=ResearchBudget)

    @model_validator(mode="after")
    def validate_timestamp_intent(self) -> ResearchSubmission:
        if self.analysis_timestamp is not None and (
            self.analysis_timestamp.tzinfo is None
            or self.analysis_timestamp.utcoffset() is None
        ):
            raise ValueError("analysis_timestamp must be timezone-aware")
        if self.replay_integrity_level not in {
            ReplayIntegrityLevel.RESEARCH_REPLAY,
            ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        }:
            raise ValueError("research execution only supports explicit replay modes")
        if self.replay_integrity_level is ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY and (
            self.timestamp_mode is not ResearchTimestampMode.FIXED_CUTOFF
            or self.analysis_timestamp is None
        ):
            raise ValueError("evidence-constrained replay requires an explicit fixed cutoff")
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
    evaluation_maturity = (
        await maturity_for_research(
            session,
            instrument_id=submission.instrument_id,
            horizon=submission.horizon,
            configured_cohorts=get_settings().evaluation_cohorts,
        )
        if submission.timestamp_mode is ResearchTimestampMode.CURRENT_RESEARCH
        else EvaluationMaturity.COLD_START
    )
    state = ResearchState(
        instrument_id=submission.instrument_id,
        ticker=submission.ticker,
        query=submission.query,
        requested_at=requested_at,
        timestamp_mode=submission.timestamp_mode,
        analysis_timestamp=analysis_timestamp,
        horizon=submission.horizon,
        evaluation_maturity=evaluation_maturity,
        replay_integrity_level=submission.replay_integrity_level,
        parametric_lookahead_risk=(
            submission.replay_integrity_level
            is ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY
            or (
                analysis_timestamp is not None
                and analysis_timestamp < requested_at - timedelta(minutes=5)
            )
        ),
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


@router.post("/{research_run_id}/cancel", response_model=ResearchState)
async def cancel_research(
    research_run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResearchState:
    cancelled = await ResearchRunRepository(session).cancel(research_run_id)
    if cancelled is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="research run not found")
    await session.commit()
    return cancelled


@router.get("/{research_run_id}/report", response_model=ResearchReport)
async def get_research_report(
    research_run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResearchReport:
    state = await ResearchRunRepository(session).get(research_run_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="research run not found")
    return build_research_report(state)
