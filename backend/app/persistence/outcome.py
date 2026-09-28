"""Freeze one auditable forward outcome after its configured forecast horizon."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from math import isfinite
from uuid import UUID

from pydantic import Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.thesis import Direction, ForecastRecord, OutcomeRecord
from backend.app.persistence.models import ForecastRecordRow, OutcomeRecordRow
from backend.app.persistence.repositories import _as_utc


class OutcomeIntegrityError(ValueError):
    """A proposed outcome lacks a matured, frozen forecast or valid observation."""


class OutcomePolicy(ContractModel):
    """Horizon labels are explicitly mapped to days by the deployment."""

    horizon_days: dict[str, int] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_horizons(self) -> OutcomePolicy:
        if any(not label or days < 1 for label, days in self.horizon_days.items()):
            raise ValueError("horizon mappings require labels and positive days")
        return self


class OutcomeObservation(ContractModel):
    observed_at: datetime
    available_at: datetime
    actual_return: float
    benchmark_return: float
    mfe: float
    mae: float
    invalidation_hit: bool
    source_name: str = Field(min_length=1)
    source_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_observation(self) -> OutcomeObservation:
        for timestamp in (self.observed_at, self.available_at):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("outcome timestamps must be timezone-aware")
        if self.available_at < self.observed_at:
            raise ValueError("outcome cannot be available before observation")
        if not all(isfinite(value) for value in (
            self.actual_return, self.benchmark_return, self.mfe, self.mae
        )):
            raise ValueError("outcome returns and excursions must be finite")
        if self.mfe < 0 or self.mae > 0:
            raise ValueError("MFE must be nonnegative and MAE nonpositive")
        return self


class OutcomeRepository:
    def __init__(self, session: AsyncSession, *, clock: Callable[[], datetime] = utc_now) -> None:
        self._session = session
        self._clock = clock

    async def record(
        self,
        forecast_id: UUID,
        observation: OutcomeObservation,
        *,
        policy: OutcomePolicy,
    ) -> OutcomeRecord:
        row = await self._session.get(ForecastRecordRow, forecast_id)
        if row is None:
            raise OutcomeIntegrityError("forecast is not frozen in persistence")
        forecast = ForecastRecord.model_validate_json(json.dumps(row.record_json))
        days = policy.horizon_days.get(forecast.horizon)
        if days is None:
            raise OutcomeIntegrityError("forecast horizon has no configured maturity rule")
        due_at = _as_utc(row.created_at) + timedelta(days=days)
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise OutcomeIntegrityError("outcome clock must be timezone-aware")
        now = now.astimezone(UTC)
        if now < due_at or observation.observed_at < due_at:
            raise OutcomeIntegrityError("forecast horizon has not matured")
        if observation.available_at > now:
            raise OutcomeIntegrityError("outcome observation is not yet available")
        existing = await self._session.get(OutcomeRecordRow, forecast_id)
        payload = observation.model_dump(mode="json")
        if existing is not None:
            if existing.observation_json != payload or _as_utc(existing.horizon_end_at) != due_at:
                raise OutcomeIntegrityError("outcome is immutable and differs from recorded value")
            return OutcomeRecord.model_validate_json(json.dumps(existing.record_json))
        if forecast.direction is Direction.BULLISH:
            correct = observation.actual_return > 0
        elif forecast.direction is Direction.BEARISH:
            correct = observation.actual_return < 0
        else:
            raise OutcomeIntegrityError("neutral or uncertain forecasts need an outcome definition")
        result = OutcomeRecord(
            forecast_id=forecast_id,
            actual_return=observation.actual_return,
            benchmark_return=observation.benchmark_return,
            excess_return=observation.actual_return - observation.benchmark_return,
            direction_correct=correct,
            mfe=observation.mfe,
            mae=observation.mae,
            invalidation_hit=observation.invalidation_hit,
            evaluated_at=now,
        )
        self._session.add(OutcomeRecordRow(
            forecast_id=forecast_id,
            evaluated_at=now,
            horizon_end_at=due_at,
            observation_json=payload,
            record_json=result.model_dump(mode="json"),
        ))
        await self._session.flush()
        return result

    async def list_for_forecasts(self, forecast_ids: tuple[UUID, ...]) -> tuple[OutcomeRecord, ...]:
        if not forecast_ids:
            return ()
        rows = await self._session.scalars(
            select(OutcomeRecordRow)
            .where(OutcomeRecordRow.forecast_id.in_(forecast_ids))
            .order_by(OutcomeRecordRow.evaluated_at, OutcomeRecordRow.forecast_id)
        )
        return tuple(
            OutcomeRecord.model_validate_json(json.dumps(row.record_json)) for row in rows
        )
