"""Opt-in application command for cited Thesis and frozen forward forecasts."""

from __future__ import annotations

from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.contracts.base import ContractModel
from backend.app.contracts.research import ResearchStatus
from backend.app.contracts.thesis import (
    Direction,
    ForecastRecord,
    Thesis,
    ThesisRevision,
    ThesisStatus,
)
from backend.app.persistence.forecast import ForecastIntegrityError, ForecastRepository
from backend.app.persistence.repositories import ResearchRunRepository
from backend.app.persistence.session import get_session
from backend.app.persistence.thesis import ThesisLifecycleError, ThesisRepository

router = APIRouter(prefix="/research", tags=["thesis"])


class ThesisSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thesis_id: UUID
    expected_version: int | None = Field(default=None, ge=1)
    status: ThesisStatus = ThesisStatus.CREATED
    direction: Direction
    direction_probability: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1)
    bull_case: str = Field(min_length=1)
    bear_case: str = Field(min_length=1)
    invalidation_conditions: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)
    freeze_forecast: bool = True
    benchmark_id: UUID | None = None
    supersedes_forecast_id: UUID | None = None


class ThesisRecorded(ContractModel):
    revision: ThesisRevision
    forecast: ForecastRecord | None = None


@router.post("/{research_run_id}/theses", response_model=ThesisRecorded)
async def record_thesis(
    research_run_id: UUID,
    submission: ThesisSubmission,
    session: Annotated[AsyncSession, Depends(get_session)],
    write_token: Annotated[str | None, Header(alias="X-Phase6-Write-Token")] = None,
) -> ThesisRecorded:
    configured = get_settings().phase6_write_token
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phase 6 writes are disabled",
        )
    if write_token is None or not compare_digest(write_token, configured):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid write token")
    run = await ResearchRunRepository(session).get(research_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    if (
        run.status is not ResearchStatus.COMPLETE
        or run.analysis_timestamp is None
        or run.research_synthesis is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research run is not complete with cited synthesis",
        )
    thesis = Thesis(
        thesis_id=submission.thesis_id,
        instrument_id=run.instrument_id,
        analysis_timestamp=run.analysis_timestamp,
        horizon=run.horizon,
        direction=submission.direction,
        direction_probability=submission.direction_probability,
        summary=submission.summary,
        bull_case=submission.bull_case,
        bear_case=submission.bear_case,
        invalidation_conditions=submission.invalidation_conditions,
        confidence=submission.confidence,
        evidence_ids=run.research_synthesis.evidence_ids,
        status=submission.status,
    )
    repository = ThesisRepository(session)
    try:
        if submission.expected_version is None:
            revision = await repository.create(thesis, research_run_id=research_run_id)
        else:
            revision = await repository.transition(
                thesis,
                research_run_id=research_run_id,
                expected_version=submission.expected_version,
            )
        forecast = (
            await ForecastRepository(session).freeze(
                revision,
                benchmark_id=submission.benchmark_id,
                supersedes_forecast_id=submission.supersedes_forecast_id,
            )
            if submission.freeze_forecast else None
        )
    except (ThesisLifecycleError, ForecastIntegrityError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ThesisRecorded(revision=revision, forecast=forecast)
