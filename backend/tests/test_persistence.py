import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.research import (
    ResearchSubmission,
    get_research,
    get_research_enqueuer,
    submit_research,
)
from backend.app.main import app
from backend.app.config import Settings
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    Instrument,
    SymbolHistory,
)
from backend.app.contracts.research import (
    ResearchPlan,
    ResearchState,
    ResearchStatus,
    ResearchStep,
)
from backend.app.jobs.celery_app import (
    celery_app,
    create_celery,
    enqueue_research_run,
    run_research,
)
from backend.app.persistence.base import Base
from backend.app.persistence.models import ResearchPlanRow
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database, get_database, get_session


def _instrument() -> Instrument:
    return Instrument(
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA Corporation",
    )


def _state(instrument_id: Any, now: datetime) -> ResearchState:
    return ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess the setup",
        analysis_timestamp=now,
        horizon="3-5 days",
        research_plan=ResearchPlan(
            question="Assess the setup",
            instrument_symbol="KLAC",
            horizon="3-5 days",
            steps=(
                ResearchStep(
                    step_id="market_snapshot",
                    objective="Collect current market state",
                    capability="market",
                ),
            ),
            stop_conditions=("evidence collected",),
            evidence_requirements=("market data",),
        ),
    )


def test_security_master_and_research_run_repositories(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase3.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        now = datetime.now(UTC)
        instrument = _instrument()
        async with database.sessions() as session, session.begin():
            security = SecurityMasterRepository(session)
            assert await security.add_instrument(instrument) == instrument
            assert await security.get_instrument(instrument.instrument_id) == instrument
            assert await security.get_instrument(uuid4()) is None

            history = SymbolHistory(
                instrument_id=instrument.instrument_id,
                symbol="KLAC",
                exchange="NASDAQ",
                valid_from=now - timedelta(days=1),
            )
            assert await security.add_symbol_history(history) == history
            assert await security.resolve_symbol("KLAC", "NASDAQ", now) == instrument
            assert await security.resolve_symbol("OLD", "NASDAQ", now) is None

            action = CorporateAction(
                instrument_id=instrument.instrument_id,
                action_type=CorporateActionType.SPLIT,
                effective_at=now,
                available_at=now,
                ratio=2,
                source="fixture",
            )
            assert await security.add_corporate_action(action) == action

            repository = ResearchRunRepository(session)
            state = _state(instrument.instrument_id, now)
            assert await repository.create(state) == state
            assert await repository.get(state.research_id) == state
            assert await repository.get(uuid4()) is None

            running = await repository.set_status(state.research_id, ResearchStatus.RUNNING)
            assert running.status is ResearchStatus.RUNNING
            saved = await repository.save(running.model_copy(update={"horizon": "5 days"}))
            assert saved.horizon == "5 days"
            without_plan = saved.model_copy(update={"research_plan": None})
            await repository.save(without_plan)
            assert await session.get(ResearchPlanRow, state.research_id) is None
            await repository.save(without_plan)
            with pytest.raises(LookupError, match="does not exist"):
                await repository.save(state.model_copy(update={"research_id": uuid4()}))
            with pytest.raises(LookupError, match="does not exist"):
                await repository.set_status(uuid4(), ResearchStatus.FAILED)

        async for session in database.session():
            assert isinstance(session, AsyncSession)
        await database.dispose()

    asyncio.run(scenario())


def test_session_dependency_uses_configured_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'dependency.db'}")
        monkeypatch.setattr("backend.app.persistence.session.get_database", lambda: database)
        sessions = [session async for session in get_session()]
        assert len(sessions) == 1
        await database.dispose()

    asyncio.run(scenario())

    get_database.cache_clear()
    configured = get_database()
    assert configured.engine.url.drivername == "postgresql+asyncpg"
    asyncio.run(configured.dispose())
    get_database.cache_clear()


def test_celery_configuration_task_and_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        redis_broker_url="redis://fixture.invalid:6379/2",
        redis_result_url="redis://fixture.invalid:6379/3",
    )
    app = create_celery(settings)
    assert app.conf.broker_url.endswith("/2")
    assert app.conf.result_backend.endswith("/3")
    assert app.conf.task_serializer == "json"
    assert run_research("run-id") == {"research_run_id": "run-id", "state": "accepted"}

    monkeypatch.setattr(
        celery_app,
        "send_task",
        lambda *args, **kwargs: SimpleNamespace(id="task-id"),
    )
    assert enqueue_research_run("run-id") == "task-id"
    assert get_research_enqueuer() is enqueue_research_run


def test_research_api_service_boundary(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'api.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            accepted = await submit_research(
                ResearchSubmission(
                    instrument_id=instrument.instrument_id,
                    ticker="KLAC",
                    query="Assess the setup",
                    horizon="3-5 days",
                ),
                session,
                lambda _: "task-id",
            )
            assert accepted.status is ResearchStatus.PENDING
            assert accepted.task_id == "task-id"
            state = await get_research(accepted.research_run_id, session)
            assert state.research_id == accepted.research_run_id
            with pytest.raises(HTTPException) as exc_info:
                await get_research(uuid4(), session)
            assert exc_info.value.status_code == 404
        await database.dispose()

    asyncio.run(scenario())


def test_research_http_submission(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'http.db'}")
    instrument = _instrument()

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)

    async def override_session() -> Any:
        async with database.sessions() as session, session.begin():
            yield session

    asyncio.run(prepare())
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_research_enqueuer] = lambda: lambda _: "http-task"
    try:
        client = TestClient(app)
        response = client.post(
            "/research",
            json={
                "instrument_id": str(instrument.instrument_id),
                "ticker": "KLAC",
                "query": "Assess the setup",
                "horizon": "3-5 days",
            },
        )
        assert response.status_code == 202
        payload = response.json()
        assert payload["task_id"] == "http-task"
        assert client.get(f"/research/{payload['research_run_id']}").status_code == 200
        assert client.get(f"/research/{uuid4()}").status_code == 404
    finally:
        app.dependency_overrides.clear()
        asyncio.run(database.dispose())
