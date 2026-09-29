"""One immutable OutcomeRecord after the configured forward horizon."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from backend.app.contracts.thesis import Direction, ForecastRecord
from backend.app.evaluation.forward import ForwardEvaluationRunner
from backend.app.persistence.base import Base
from backend.app.persistence.models import ForecastRecordRow
from backend.app.persistence.outcome import (
    OutcomeIntegrityError,
    OutcomeObservation,
    OutcomePolicy,
    OutcomeRepository,
)
from backend.app.persistence.outcome_observation import (
    OutcomeObservationRepository,
    PersistedOutcomeSource,
)
from backend.app.persistence.session import Database


def test_forward_outcome_requires_maturity_and_is_append_only(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'outcome.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        created = datetime(2020, 1, 1, tzinfo=UTC)
        forecast = ForecastRecord(
            research_run_id=uuid4(), instrument_id=uuid4(), created_at=created,
            analysis_timestamp=created, horizon="5d", direction=Direction.BULLISH,
            probability=0.7, thesis_id=uuid4(), thesis_version=1,
            model_execution_ids=(uuid4(),), evidence_ids=(uuid4(),),
        )
        async with database.sessions() as session, session.begin():
            session.add(ForecastRecordRow(
                forecast_id=forecast.forecast_id,
                research_run_id=forecast.research_run_id,
                instrument_id=forecast.instrument_id,
                thesis_id=forecast.thesis_id,
                thesis_version=forecast.thesis_version,
                created_at=forecast.created_at,
                analysis_timestamp=forecast.analysis_timestamp,
                horizon=forecast.horizon,
                direction=forecast.direction.value,
                probability=forecast.probability,
                record_json=forecast.model_dump(mode="json"),
            ))
        observation = OutcomeObservation(
            observed_at=created + timedelta(days=5),
            available_at=created + timedelta(days=5, hours=1),
            actual_return=0.1,
            benchmark_return=0.03,
            mfe=0.2,
            mae=-0.05,
            invalidation_hit=False,
            source_name="offline fixture",
            source_version="v1",
        )
        policy = OutcomePolicy(horizon_days={"5d": 5})
        async with database.sessions() as session, session.begin():
            early = OutcomeRepository(session, clock=lambda: created + timedelta(days=4))
            with pytest.raises(OutcomeIntegrityError, match="not matured"):
                await early.record(forecast.forecast_id, observation, policy=policy)
            repository = OutcomeRepository(
                session, clock=lambda: created + timedelta(days=6)
            )
            result = await repository.record(forecast.forecast_id, observation, policy=policy)
            assert result.excess_return == pytest.approx(0.07)
            assert result.direction_correct is True
            assert (
                await repository.record(forecast.forecast_id, observation, policy=policy)
                == result
            )
            changed = observation.model_copy(update={"actual_return": -0.1})
            with pytest.raises(OutcomeIntegrityError, match="immutable"):
                await repository.record(forecast.forecast_id, changed, policy=policy)
            assert await repository.list_for_forecasts((forecast.forecast_id,)) == (result,)
        second = forecast.model_copy(update={
            "forecast_id": uuid4(),
            "research_run_id": uuid4(),
            "thesis_id": uuid4(),
        })
        async with database.sessions() as session, session.begin():
            session.add(ForecastRecordRow(
                forecast_id=second.forecast_id,
                research_run_id=second.research_run_id,
                instrument_id=second.instrument_id,
                thesis_id=second.thesis_id,
                thesis_version=second.thesis_version,
                created_at=second.created_at,
                analysis_timestamp=second.analysis_timestamp,
                horizon=second.horizon,
                direction=second.direction.value,
                probability=second.probability,
                record_json=second.model_dump(mode="json"),
            ))

        async with database.sessions() as session, session.begin():
            observed_at = created + timedelta(days=6)
            observations = OutcomeObservationRepository(
                session, clock=lambda: observed_at
            )
            await observations.store(second.forecast_id, observation, policy=policy)
            await observations.store(second.forecast_id, observation, policy=policy)
            with pytest.raises(OutcomeIntegrityError, match="immutable"):
                await observations.store(
                    second.forecast_id,
                    observation.model_copy(update={"actual_return": -0.1}),
                    policy=policy,
                )
            source = PersistedOutcomeSource(session, clock=lambda: observed_at)
            runner = ForwardEvaluationRunner(
                session, source=source, policy=policy,
                clock=lambda: observed_at,
            )
            produced = await runner.run_due()
            assert len(produced) == 1
            assert produced[0].forecast_id == second.forecast_id
            assert await runner.run_due() == ()
        await database.dispose()

    asyncio.run(scenario())
