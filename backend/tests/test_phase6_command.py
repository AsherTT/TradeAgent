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
from backend.app.contracts.research import ResearchState, ResearchStatus
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
        current_symbol="KLAC", exchange="NASDAQ", currency="USD",
        asset_type="equity", company_name="KLA Corporation",
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
    run = ResearchState(
        instrument_id=instrument.instrument_id,
        ticker="KLAC",
        query="Assess setup",
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        status=ResearchStatus.COMPLETE,
        evidence=(evidence,),
        model_history=({"execution_id": str(uuid4()), "status": "success"},),
        research_synthesis=ResearchSynthesis(
            summary="Cautious view", bull_case="Trend persists", bear_case="Trend weakens",
            limitations=("Fixture only",), evidence_ids=(evidence.evidence_id,),
            confidence=0.5,
        ),
    )

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(run)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async for session in database.session():
            yield session

    asyncio.run(prepare())
    app.dependency_overrides[get_session] = override_session
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
            thesis_api, "get_settings",
            lambda: Settings(_env_file=None, phase6_write_token="test-secret"),
        )
        assert client.post(path, json=payload).status_code == 403
        headers = {"X-Phase6-Write-Token": "test-secret"}
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["revision"]["version"] == 1
        assert body["forecast"]["frozen"] is True
        assert body["forecast"]["evidence_ids"] == [str(evidence.evidence_id)]
        assert client.post(path, json=payload, headers=headers).status_code == 409
        async def verify() -> None:
            async with database.sessions() as session:
                assert await session.get(ThesisRow, thesis_id) is not None
                forecast = await session.get(
                    ForecastRecordRow, UUID(body["forecast"]["forecast_id"])
                )
                assert forecast is not None
        asyncio.run(verify())
    finally:
        app.dependency_overrides.clear()
        asyncio.run(database.dispose())
