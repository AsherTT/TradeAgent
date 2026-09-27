"""Freeze genuine forward ForecastRecords from completed research and Thesis versions."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.base import utc_now
from backend.app.contracts.research import ResearchStatus
from backend.app.contracts.thesis import ForecastRecord, ThesisRevision
from backend.app.persistence.models import ForecastRecordRow, ThesisVersionRow
from backend.app.persistence.repositories import ResearchRunRepository, _as_utc


class ForecastIntegrityError(ValueError):
    """A proposed forecast is not a new, traceable forward observation."""


class ForecastRepository:
    def __init__(
        self, session: AsyncSession, *, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._session = session
        self._clock = clock

    async def freeze(
        self,
        revision: ThesisRevision,
        *,
        benchmark_id: UUID | None = None,
        supersedes_forecast_id: UUID | None = None,
    ) -> ForecastRecord:
        thesis = revision.thesis
        version_row = await self._session.get(
            ThesisVersionRow, (thesis.thesis_id, revision.version)
        )
        if (
            version_row is None
            or version_row.research_run_id != revision.research_run_id
            or version_row.thesis_json != thesis.model_dump(mode="json")
        ):
            raise ForecastIntegrityError("Thesis revision is not the persisted version")
        run = await ResearchRunRepository(self._session).get(revision.research_run_id)
        if run is None or run.status is not ResearchStatus.COMPLETE:
            raise ForecastIntegrityError("forecast source research must be complete")
        existing = await self._session.scalar(
            select(ForecastRecordRow).where(
                ForecastRecordRow.research_run_id == revision.research_run_id,
                ForecastRecordRow.thesis_id == thesis.thesis_id,
            )
        )
        if existing is not None:
            recorded = self._record(existing)
            if (
                recorded.thesis_version != revision.version
                or recorded.benchmark_id != benchmark_id
                or recorded.supersedes_forecast_id != supersedes_forecast_id
            ):
                raise ForecastIntegrityError("forecast for this research run already differs")
            return recorded
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ForecastIntegrityError("forecast clock must be timezone-aware")
        now = now.astimezone(UTC)
        cutoff = run.analysis_timestamp
        if (
            cutoff is None
            or run.parametric_lookahead_risk
            or cutoff < run.requested_at - timedelta(minutes=5)
            or cutoff > now
            or now - cutoff > timedelta(minutes=15)
        ):
            raise ForecastIntegrityError(
                "historical or stale research cannot create a forward forecast"
            )
        if run.instrument_id != thesis.instrument_id or run.horizon != thesis.horizon:
            raise ForecastIntegrityError("Thesis and research identity differ")
        execution_ids: list[UUID] = []
        for item in run.model_history:
            if item.get("status") != "success":
                continue
            try:
                execution_id = UUID(str(item["execution_id"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ForecastIntegrityError("model execution history is invalid") from exc
            if execution_id not in execution_ids:
                execution_ids.append(execution_id)
        if not execution_ids:
            raise ForecastIntegrityError("forward forecast requires model execution provenance")

        if supersedes_forecast_id is not None:
            prior = await self._session.get(ForecastRecordRow, supersedes_forecast_id)
            if (
                prior is None
                or prior.instrument_id != thesis.instrument_id
                or prior.horizon != thesis.horizon
                or prior.research_run_id == revision.research_run_id
                or _as_utc(prior.created_at) >= now
            ):
                raise ForecastIntegrityError(
                    "superseded forecast must be an earlier matching record"
                )
        record = ForecastRecord(
            research_run_id=revision.research_run_id,
            instrument_id=thesis.instrument_id,
            created_at=now,
            analysis_timestamp=thesis.analysis_timestamp,
            horizon=thesis.horizon,
            direction=thesis.direction,
            probability=thesis.direction_probability,
            benchmark_id=benchmark_id,
            thesis_id=thesis.thesis_id,
            thesis_version=revision.version,
            model_execution_ids=tuple(execution_ids),
            evidence_ids=thesis.evidence_ids,
            supersedes_forecast_id=supersedes_forecast_id,
        )
        self._session.add(ForecastRecordRow(
            forecast_id=record.forecast_id,
            research_run_id=record.research_run_id,
            instrument_id=record.instrument_id,
            thesis_id=record.thesis_id,
            thesis_version=record.thesis_version,
            supersedes_forecast_id=record.supersedes_forecast_id,
            created_at=record.created_at,
            analysis_timestamp=record.analysis_timestamp,
            horizon=record.horizon,
            direction=record.direction.value,
            probability=record.probability,
            record_json=record.model_dump(mode="json"),
        ))
        await self._session.flush()
        return record

    async def get_as_of(
        self, forecast_id: UUID, *, at: datetime
    ) -> ForecastRecord | None:
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("as-of time must be timezone-aware")
        row = await self._session.get(ForecastRecordRow, forecast_id)
        if row is None or _as_utc(row.created_at) > at.astimezone(UTC):
            return None
        return self._record(row)

    @staticmethod
    def _record(row: ForecastRecordRow) -> ForecastRecord:
        return ForecastRecord.model_validate_json(json.dumps(row.record_json))
