"""Read a configured forward cohort without changing frozen observations."""

from __future__ import annotations

import json
from typing import Literal
from uuid import UUID

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import ContractModel
from backend.app.contracts.thesis import ForecastRecord
from backend.app.evaluation.forecast import (
    ForecastEvaluationPolicy,
    ForecastEvaluationReport,
    evaluate_forecasts,
)
from backend.app.persistence.models import ForecastRecordRow
from backend.app.persistence.outcome import OutcomeRepository


class EvaluationCohortConfig(ContractModel):
    universe_id: str = Field(min_length=1)
    instrument_ids: tuple[UUID, ...] = Field(min_length=1)
    horizon: str = Field(min_length=1)
    outcome_definition: Literal["directional_return"] = "directional_return"
    policy: ForecastEvaluationPolicy


class CohortEvaluationReport(ContractModel):
    universe_id: str
    horizon: str
    outcome_definition: str
    policy: ForecastEvaluationPolicy
    evaluation: ForecastEvaluationReport


async def read_cohort_evaluation(
    session: AsyncSession, config: EvaluationCohortConfig, *, max_forecasts: int = 1000
) -> CohortEvaluationReport:
    if max_forecasts < 1:
        raise ValueError("max_forecasts must be positive")
    rows = (
        await session.scalars(
            select(ForecastRecordRow)
            .where(
                ForecastRecordRow.instrument_id.in_(config.instrument_ids),
                ForecastRecordRow.horizon == config.horizon,
            )
            .order_by(ForecastRecordRow.created_at, ForecastRecordRow.forecast_id)
            .limit(max_forecasts + 1)
        )
    ).all()
    if len(rows) > max_forecasts:
        raise ValueError("evaluation cohort exceeds configured forecast limit")
    forecasts = tuple(
        ForecastRecord.model_validate_json(json.dumps(row.record_json)) for row in rows
    )
    outcomes = await OutcomeRepository(session).list_for_forecasts(
        tuple(forecast.forecast_id for forecast in forecasts)
    )
    return CohortEvaluationReport(
        universe_id=config.universe_id,
        horizon=config.horizon,
        outcome_definition=config.outcome_definition,
        policy=config.policy,
        evaluation=evaluate_forecasts(forecasts, outcomes, policy=config.policy),
    )
