"""HTTP command from completed research to cited Thesis and forward Forecast."""

import asyncio
import importlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.thesis import get_session
from backend.app.config import Settings
from backend.app.contracts.evidence import Evidence, ResearchSynthesis, TrustLevel
from backend.app.contracts.instrument import Instrument
from backend.app.contracts.model import (
    ExecutorMetadata,
    ModelExecutionSnapshot,
    ProviderName,
    ReasoningLevel,
    TaskKind,
)
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.contracts.thesis import Direction
from backend.app.main import app
from backend.app.persistence.base import Base
from backend.app.persistence.models import ForecastRecordRow, ThesisRow
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database

thesis_api = importlib.import_module("backend.app.api.thesis")


def test_phase6_write_command_is_guarded_and_transactional(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase6-command.db'}")
    instrument = Instrument(
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA Corporation",
    )
    cutoff = datetime.now(UTC) - timedelta(minutes=1)
    evidence = Evidence(
        instrument_id=instrument.instrument_id,
        evidence_type="market_technical_snapshot",
        source_name="fixture",
        observed_at=cutoff - timedelta(minutes=1),
        retrieved_at=cutoff - timedelta(minutes=1),
        available_at=cutoff - timedelta(minutes=1),
        content="PIT fixture",
        confidence=1,
        freshness=1,
        trust_level=TrustLevel.TRUSTED_PROVIDER,
        source_type="market_data",
        content_hash="fixture",
        sanitization_status="structured_verified",
        injection_risk=0,
    )
    synthesis = ResearchSynthesis(
        summary="Cautious view",
        bull_case="Trend persists",
        bear_case="Trend weakens",
        limitations=("Fixture only",),
        evidence_ids=(evidence.evidence_id,),
        confidence=0.5,
        forecast_direction=Direction.BULLISH,
        forecast_probability=0.6,
    )
    metadata = ExecutorMetadata(
        request_id=uuid4(),
        provider=ProviderName.MOCK,
        model="fixture",
        reasoning_level=ReasoningLevel.MEDIUM,
        started_at=cutoff,
        completed_at=cutoff + timedelta(seconds=1),
        latency_ms=1,
        status="success",
    )
    run = ResearchState(
        instrument_id=instrument.instrument_id,
        ticker="KLAC",
        query="Assess setup",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        status=ResearchStatus.COMPLETE,
        evidence=(evidence,),
        model_history=(
            ModelExecutionSnapshot(
                task_kind=TaskKind.SYNTHESIS,
                metadata=metadata,
                output=synthesis.model_dump(mode="json"),
            ).model_dump(mode="json"),
        ),
        research_synthesis=synthesis,
    )
    past = cutoff - timedelta(days=2)
    past_evidence = evidence.model_copy(
        update={
            "evidence_id": uuid4(),
            "observed_at": past - timedelta(minutes=1),
            "retrieved_at": past - timedelta(minutes=1),
            "available_at": past - timedelta(minutes=1),
        }
    )
    historical = run.model_copy(
        update={
            "research_id": uuid4(),
            "requested_at": past,
            "analysis_timestamp": past,
            "evidence": (past_evidence,),
            "model_history": (),
            "research_synthesis": run.research_synthesis.model_copy(
                update={"evidence_ids": (past_evidence.evidence_id,)}
            ),
            "parametric_lookahead_risk": True,
        }
    )

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(run)
            await ResearchRunRepository(session).create(historical)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async for session in database.session():
            yield session

    asyncio.run(prepare())
    app.dependency_overrides[get_session] = override_session
    monkeypatch.setattr(
        thesis_api, "get_settings", lambda: Settings(_env_file=None, phase6_write_token=None)
    )
    thesis_id = uuid4()
    payload = {
        "thesis_id": str(thesis_id),
        "direction": "bullish",
        "direction_probability": 0.6,
        "summary": "Cautious bullish view",
        "bull_case": "Trend persists",
        "bear_case": "Trend weakens",
        "invalidation_conditions": ["close below 90"],
        "confidence": 0.5,
    }
    try:
        client = TestClient(app)
        path = f"/research/{run.research_id}/theses"
        disabled = client.post(path, json=payload)
        assert disabled.status_code == 503
        monkeypatch.setattr(
            thesis_api,
            "get_settings",
            lambda: Settings(_env_file=None, phase6_write_token="test-secret"),
        )
        assert client.post(path, json=payload).status_code == 403
        headers = {"X-Phase6-Write-Token": "test-secret"}
        bad_thesis_id = uuid4()
        bad_forecast = client.post(
            path,
            json={**payload, "thesis_id": str(bad_thesis_id), "direction_probability": 0.9},
            headers=headers,
        )
        assert bad_forecast.status_code == 409
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["revision"]["version"] == 1
        assert body["forecast"]["frozen"] is True
        assert body["forecast"]["evidence_ids"] == [str(evidence.evidence_id)]
        assert client.post(path, json=payload, headers=headers).status_code == 409
        historical_thesis_id = uuid4()
        historical_payload = {**payload, "thesis_id": str(historical_thesis_id)}
        historical_path = f"/research/{historical.research_id}/theses"
        assert (
            client.post(historical_path, json=historical_payload, headers=headers).status_code
            == 409
        )
        recorded_only = client.post(
            historical_path,
            json={**historical_payload, "freeze_forecast": False},
            headers=headers,
        )
        assert recorded_only.status_code == 200
        assert recorded_only.json()["forecast"] is None

        async def verify() -> None:
            async with database.sessions() as session:
                assert await session.get(ThesisRow, thesis_id) is not None
                assert await session.get(ThesisRow, bad_thesis_id) is None
                assert await session.get(ThesisRow, historical_thesis_id) is not None
                forecast = await session.get(
                    ForecastRecordRow, UUID(body["forecast"]["forecast_id"])
                )
                assert forecast is not None

        asyncio.run(verify())
    finally:
        app.dependency_overrides.clear()
        asyncio.run(database.dispose())
