"""Run due forward evaluations through an injected qualified observation source."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import utc_now
from backend.app.contracts.thesis import ForecastRecord, OutcomeRecord
from backend.app.persistence.models import ForecastRecordRow, OutcomeRecordRow
from backend.app.persistence.outcome import OutcomeObservation, OutcomePolicy, OutcomeRepository
from backend.app.persistence.repositories import _as_utc


class ForwardOutcomeSource(Protocol):
    """Return a source-qualified observation, or None while it is unavailable."""

    async def observe(
        self, forecast: ForecastRecord, *, horizon_end_at: datetime
    ) -> OutcomeObservation | None: ...


class ForwardEvaluationRunner:
    def __init__(
        self,
        session: AsyncSession,
        *,
        source: ForwardOutcomeSource,
        policy: OutcomePolicy,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._source = source
        self._policy = policy
        self._clock = clock

    async def run_due(self, *, limit: int = 100) -> tuple[OutcomeRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("forward evaluation clock must be timezone-aware")
        now = now.astimezone(UTC)
        rows = await self._session.scalars(
            select(ForecastRecordRow)
            .outerjoin(
                OutcomeRecordRow,
                OutcomeRecordRow.forecast_id == ForecastRecordRow.forecast_id,
            )
            .where(OutcomeRecordRow.forecast_id.is_(None))
            .order_by(ForecastRecordRow.created_at, ForecastRecordRow.forecast_id)
            .limit(limit)
            .with_for_update(of=ForecastRecordRow, skip_locked=True)
        )
        repository = OutcomeRepository(self._session, clock=lambda: now)
        recorded: list[OutcomeRecord] = []
        for row in rows:
            days = self._policy.horizon_days.get(row.horizon)
            if days is None:
                continue
            due_at = _as_utc(row.created_at) + timedelta(days=days)
            if now < due_at:
                continue
            forecast = ForecastRecord.model_validate_json(json.dumps(row.record_json))
            observation = await self._source.observe(forecast, horizon_end_at=due_at)
            if observation is None:
                continue
            recorded.append(
                await repository.record(forecast.forecast_id, observation, policy=self._policy)
            )
        return tuple(recorded)
