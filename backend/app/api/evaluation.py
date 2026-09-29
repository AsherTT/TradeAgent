"""Read-only forward cohort evaluation with server-owned maturity thresholds."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.evaluation.reporting import (
    CohortEvaluationReport,
    EvaluationCohortConfig,
    read_cohort_evaluation,
)
from backend.app.persistence.session import get_session

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def get_evaluation_cohorts() -> tuple[EvaluationCohortConfig, ...]:
    configured = tuple(
        EvaluationCohortConfig.model_validate_json(json.dumps(item))
        for item in get_settings().evaluation_cohorts
    )
    keys = {(item.universe_id, item.horizon, item.outcome_definition) for item in configured}
    if len(keys) != len(configured):
        raise ValueError("evaluation cohort configuration contains duplicate keys")
    return configured


@router.get("/forecasts", response_model=CohortEvaluationReport)
async def get_forecast_evaluation(
    universe_id: Annotated[str, Query(min_length=1)],
    horizon: Annotated[str, Query(min_length=1)],
    outcome_definition: Annotated[str, Query(min_length=1)],
    session: Annotated[AsyncSession, Depends(get_session)],
    cohorts: Annotated[
        tuple[EvaluationCohortConfig, ...], Depends(get_evaluation_cohorts)
    ],
) -> CohortEvaluationReport:
    matching = next(
        (
            item for item in cohorts
            if (item.universe_id, item.horizon, item.outcome_definition)
            == (universe_id, horizon, outcome_definition)
        ),
        None,
    )
    if matching is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="evaluation cohort is not configured",
        )
    try:
        return await read_cohort_evaluation(session, matching)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
