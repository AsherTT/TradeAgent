"""Read a configured cohort with maturity and every bucket visible."""

import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.api.evaluation import get_evaluation_cohorts
from backend.app.api.research import ResearchSubmission, submit_research
from backend.app.config import Settings
from backend.app.contracts.instrument import Instrument
from backend.app.contracts.research import ResearchTimestampMode
from backend.app.contracts.thesis import Direction, ForecastRecord, OutcomeRecord
from backend.app.evaluation.forecast import ForecastEvaluationPolicy
from backend.app.evaluation.reporting import EvaluationCohortConfig, maturity_for_research
from backend.app.main import app
from backend.app.persistence.base import Base
from backend.app.persistence.models import ForecastRecordRow, OutcomeRecordRow
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database, get_session


def test_read_only_cohort_api_shows_exploratory_maturity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'cohort.db'}")
    now = datetime(2020, 1, 1, tzinfo=UTC)
    instrument_id = uuid4()
    forecast = ForecastRecord(
        research_run_id=uuid4(), instrument_id=instrument_id, created_at=now,
        analysis_timestamp=now, horizon="5d", direction=Direction.BULLISH,
        probability=0.75, thesis_id=uuid4(), thesis_version=1,
        model_execution_ids=(uuid4(),), evidence_ids=(uuid4(),),
    )
    outcome = OutcomeRecord(
        forecast_id=forecast.forecast_id,
        actual_return=0.1,
        benchmark_return=0.02,
        excess_return=0.08,
        direction_correct=True,
        mfe=0.2,
        mae=-0.05,
        invalidation_hit=False,
        evaluated_at=now + timedelta(days=6),
    )

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
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
            session.add(OutcomeRecordRow(
                forecast_id=forecast.forecast_id,
                evaluated_at=outcome.evaluated_at,
                horizon_end_at=now + timedelta(days=5),
                observation_json={"fixture": True},
                record_json=outcome.model_dump(mode="json"),
            ))

    async def override_session() -> Any:
        async for session in database.session():
            yield session

    config = EvaluationCohortConfig(
        universe_id="fixture-universe",
        instrument_ids=(instrument_id,),
        horizon="5d",
        policy=ForecastEvaluationPolicy(
            horizon_days=5,
            min_early_sample=2,
            min_mature_sample=4,
            min_bucket_usable=3,
            min_outcome_coverage=0.8,
        ),
    )

    async def check_maturity_link() -> None:
        async with database.sessions() as session:
            maturity = await maturity_for_research(
                session,
                instrument_id=instrument_id,
                horizon="5d",
                configured_cohorts=(config.model_dump(mode="json"),),
            )
            assert maturity.value == "accumulating"

    asyncio.run(prepare())
    asyncio.run(check_maturity_link())
    async def check_research_quality_link() -> None:
        instrument = Instrument(
            instrument_id=instrument_id,
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        research_module = importlib.import_module("backend.app.api.research")
        monkeypatch.setattr(
            research_module,
            "get_settings",
            lambda: Settings(
                _env_file=None,
                evaluation_cohorts=(config.model_dump(mode="json"),),
            ),
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
        async with database.sessions() as session:
            accepted = await submit_research(
                ResearchSubmission(
                    instrument_id=instrument_id,
                    ticker="KLAC",
                    query="current setup",
                    horizon="5d",
                    timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
                    replay_integrity_level="research_replay",
                ),
                session,
                lambda _: "fixture-task",
            )
            persisted = await ResearchRunRepository(session).get(accepted.research_run_id)
            assert persisted is not None
            assert persisted.evaluation_maturity.value == "accumulating"

    asyncio.run(check_research_quality_link())
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_evaluation_cohorts] = lambda: (config,)
    try:
        client = TestClient(app)
        response = client.get(
            "/evaluation/forecasts",
            params={
                "universe_id": "fixture-universe", "horizon": "5d",
                "outcome_definition": "directional_return",
            },
        )
        assert response.status_code == 200
        report = response.json()
        assert report["evaluation"]["evaluation_maturity"] == "accumulating"
        assert report["evaluation"]["exploratory"] is True
        assert report["evaluation"]["sample_count"] == 1
        assert report["evaluation"]["buckets"][7]["sample_count"] == 1
        assert report["evaluation"]["buckets"][7]["statistical_status"] == (
            "insufficient_sample"
        )
        assert client.get(
            "/evaluation/forecasts",
            params={"universe_id": "unknown", "horizon": "5d",
                    "outcome_definition": "directional_return"},
        ).status_code == 404
    finally:
        app.dependency_overrides.clear()
        asyncio.run(database.dispose())
