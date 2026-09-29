"""Append-only source observations for the scheduled forward evaluator."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import utc_now
from backend.app.contracts.thesis import ForecastRecord
from backend.app.persistence.models import ForecastRecordRow, OutcomeObservationRow
from backend.app.persistence.outcome import OutcomeIntegrityError, OutcomeObservation, OutcomePolicy
from backend.app.persistence.repositories import _as_utc


class OutcomeObservationRepository:
    def __init__(self, session: AsyncSession, *, clock: Callable[[], datetime] = utc_now) -> None:
        self._session = session
        self._clock = clock

    async def store(
        self, forecast_id: UUID, observation: OutcomeObservation, *, policy: OutcomePolicy
    ) -> None:
        row = await self._session.get(ForecastRecordRow, forecast_id)
        if row is None:
            raise OutcomeIntegrityError("observation requires a frozen forecast")
        forecast = ForecastRecord.model_validate_json(json.dumps(row.record_json))
        days = policy.horizon_days.get(forecast.horizon)
        if days is None:
            raise OutcomeIntegrityError("forecast horizon has no configured maturity rule")
        due_at = _as_utc(row.created_at) + timedelta(days=days)
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise OutcomeIntegrityError("observation clock must be timezone-aware")
        if observation.observed_at < due_at or observation.available_at > now.astimezone(UTC):
            raise OutcomeIntegrityError("observation is early or not yet available")
        payload = observation.model_dump(mode="json")
        existing = await self._session.get(OutcomeObservationRow, forecast_id)
        if existing is not None:
            if existing.observation_json != payload:
                raise OutcomeIntegrityError("stored observation is immutable")
            return
        self._session.add(OutcomeObservationRow(
            forecast_id=forecast_id,
            available_at=observation.available_at.astimezone(UTC),
            observation_json=payload,
        ))
        await self._session.flush()


class PersistedOutcomeSource:
    def __init__(self, session: AsyncSession, *, clock: Callable[[], datetime] = utc_now) -> None:
        self._session = session
        self._clock = clock

    async def observe(
        self, forecast: ForecastRecord, *, horizon_end_at: datetime
    ) -> OutcomeObservation | None:
        row = await self._session.get(OutcomeObservationRow, forecast.forecast_id)
        if row is None:
            return None
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise OutcomeIntegrityError("observation source clock must be timezone-aware")
        if _as_utc(row.available_at) > now.astimezone(UTC):
            return None
        observation = OutcomeObservation.model_validate_json(json.dumps(row.observation_json))
        if observation.observed_at < horizon_end_at:
            raise OutcomeIntegrityError("stored observation precedes forecast horizon")
        return observation
