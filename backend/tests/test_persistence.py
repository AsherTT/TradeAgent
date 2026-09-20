import asyncio
import importlib
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.api.research import (
    ResearchSubmission,
    get_research,
    get_research_enqueuer,
    submit_research,
)
from backend.app.config import Settings
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    Instrument,
    SymbolHistory,
)
from backend.app.contracts.model import ProviderName
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
    execute_research_run,
    run_research,
)
from backend.app.main import app
from backend.app.persistence.base import Base
from backend.app.persistence.models import ResearchPlanRow, ResearchRunRow
from backend.app.persistence.repositories import (
    ResearchRunBusyError,
    ResearchRunNotReadyError,
    ResearchRunRepository,
    SecurityMasterIntegrityError,
    SecurityMasterRepository,
)
from backend.app.persistence.session import Database, get_database, get_session

celery_module = importlib.import_module("backend.app.jobs.celery_app")


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
                available_at=now - timedelta(days=1),
            )
            assert await security.add_symbol_history(history) == history
            assert await security.resolve_symbol("KLAC", "NASDAQ", now) == instrument
            assert await security.resolve_symbol("OLD", "NASDAQ", now) is None

            future_history = SymbolHistory(
                instrument_id=instrument.instrument_id,
                symbol="FUTURE",
                exchange="NASDAQ",
                valid_from=now - timedelta(days=1),
                available_at=now + timedelta(days=1),
            )
            await security.add_symbol_history(future_history)
            assert (
                await security.resolve_symbol(
                    "FUTURE", "NASDAQ", now, analysis_timestamp=now
                )
                is None
            )

            overlapping = SymbolHistory(
                instrument_id=instrument.instrument_id,
                symbol="KLAC",
                exchange="NASDAQ",
                valid_from=now - timedelta(days=2),
                available_at=now - timedelta(days=2),
            )
            await security.add_symbol_history(overlapping)
            with pytest.raises(SecurityMasterIntegrityError, match="overlapping"):
                await security.resolve_symbol("KLAC", "NASDAQ", now)

            action = CorporateAction(
                instrument_id=instrument.instrument_id,
                action_type=CorporateActionType.SPLIT,
                effective_at=now,
                available_at=now,
                ratio=2,
                source="fixture",
                provider_quality_version="fixture-v1",
            )
            assert await security.add_corporate_action(action) == action
            future_action = action.model_copy(
                update={
                    "action_id": uuid4(),
                    "effective_at": now + timedelta(days=1),
                    "available_at": now + timedelta(days=2),
                }
            )
            await security.add_corporate_action(future_action)
            visible_actions = await security.list_corporate_actions(
                instrument.instrument_id,
                effective_from=now - timedelta(days=1),
                effective_to=now + timedelta(days=3),
                analysis_timestamp=now,
            )
            assert visible_actions == (action,)

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
    research_run_id = uuid4()

    async def fake_execute(run_id: Any, *, execution_id: str) -> ResearchState:
        assert run_id == research_run_id
        assert execution_id
        return _state(uuid4(), datetime.now(UTC)).model_copy(
            update={"research_id": research_run_id, "status": ResearchStatus.COMPLETE}
        )

    monkeypatch.setattr(celery_module, "execute_research_run", fake_execute)
    assert run_research(str(research_run_id)) == {
        "research_run_id": str(research_run_id),
        "state": "complete",
    }

    monkeypatch.setattr(
        celery_app,
        "send_task",
        lambda *args, **kwargs: SimpleNamespace(id="task-id"),
    )
    assert enqueue_research_run("run-id") == "task-id"
    assert get_research_enqueuer() is enqueue_research_run


def test_celery_retries_busy_run(monkeypatch: pytest.MonkeyPatch) -> None:
    async def busy_execute(run_id: Any, *, execution_id: str) -> ResearchState:
        raise ResearchRunBusyError(f"{run_id} is busy for {execution_id}")

    monkeypatch.setattr(celery_module, "execute_research_run", busy_execute)
    with pytest.raises(ResearchRunBusyError):
        run_research(str(uuid4()))


def test_submitted_run_executes_to_durable_terminal_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, research_plan_payload: dict[str, Any]
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase5.db'}")
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
                lambda _: "offline-task",
            )

        monkeypatch.setattr(celery_module, "get_database", lambda: database)
        executor = MockExecutor(lambda _request: research_plan_payload)
        executor.provider = ProviderName.CODEX_SUBSCRIPTION
        monkeypatch.setattr(
            celery_module, "build_model_gateway", lambda _: ModelGateway([executor])
        )
        result = await execute_research_run(accepted.research_run_id)
        assert result.status is ResearchStatus.INSUFFICIENT_EVIDENCE
        assert result.research_plan is not None
        assert result.runtime_metadata["transitions"] == (
            "start",
            "plan_started",
            "plan",
            "finish",
        )

        async with database.sessions() as session:
            persisted = await ResearchRunRepository(session).get(accepted.research_run_id)
            assert persisted is not None
            assert persisted.model_dump(mode="json") == result.model_dump(mode="json")
        await database.dispose()

    asyncio.run(scenario())


def test_worker_persists_failure_and_rejects_unknown_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase5-failure.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        monkeypatch.setattr(celery_module, "get_database", lambda: database)

        unknown_id = uuid4()
        with pytest.raises(LookupError, match=str(unknown_id)):
            await execute_research_run(unknown_id)

        instrument = _instrument()
        state = _state(instrument.instrument_id, datetime.now(UTC)).model_copy(
            update={"research_plan": None}
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(state)

        executor = MockExecutor(lambda _request: {})
        executor.provider = ProviderName.CODEX_SUBSCRIPTION
        monkeypatch.setattr(
            celery_module, "build_model_gateway", lambda _: ModelGateway([executor])
        )
        result = await execute_research_run(state.research_id)
        assert result.status is ResearchStatus.FAILED
        assert result.quality_assessment is not None
        assert result.quality_assessment.decision.value == "blocked"
        assert result.runtime_metadata["transitions"] == (
            "start",
            "plan_started",
            "failed",
        )

        async with database.sessions() as session:
            row = await session.get_one(ResearchRunRow, state.research_id)
            assert row.failure_reason is not None
            assert "ValidationError" in row.failure_reason
        await database.dispose()

    asyncio.run(scenario())


def test_execution_lease_rejects_concurrent_worker(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'lease.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        state = _state(instrument.instrument_id, datetime.now(UTC)).model_copy(
            update={"research_plan": None}
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(state)

        async with database.sessions() as first_session:
            first = ResearchRunRepository(first_session)
            claimed = await first.claim_execution(
                state.research_id, execution_id="worker-one", lease_seconds=60
            )
            assert claimed.research_id == state.research_id
            await first_session.commit()

        async with database.sessions() as second_session:
            second = ResearchRunRepository(second_session)
            with pytest.raises(ResearchRunBusyError, match="active worker"):
                await second.claim_execution(
                    state.research_id, execution_id="worker-two", lease_seconds=60
                )
            with pytest.raises(ResearchRunBusyError, match="active worker"):
                await second.claim_execution(
                    state.research_id, execution_id="worker-one", lease_seconds=60
                )
            with pytest.raises(ResearchRunNotReadyError, match="not committed"):
                await second.claim_execution(
                    uuid4(), execution_id="worker-two", lease_seconds=60
                )

        async with database.sessions() as second_session:
            second = ResearchRunRepository(second_session)
            with pytest.raises(ResearchRunBusyError, match="owned by another"):
                await second.save(state, execution_id="worker-two")

        async with database.sessions() as first_session:
            first = ResearchRunRepository(first_session)
            terminal = state.model_copy(update={"status": ResearchStatus.FAILED})
            await first.save(terminal, execution_id="worker-one")
            await first_session.commit()

        async with database.sessions() as second_session:
            second = ResearchRunRepository(second_session)
            assert (
                await second.claim_execution(
                    state.research_id, execution_id="worker-two", lease_seconds=60
                )
            ).status is ResearchStatus.FAILED
        await database.dispose()

    asyncio.run(scenario())


def test_expired_worker_cannot_save_after_lease_takeover(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'lease-takeover.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        state = _state(instrument.instrument_id, datetime.now(UTC)).model_copy(
            update={"research_plan": None}
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(state)

        async with database.sessions() as stale_session:
            stale = ResearchRunRepository(stale_session)
            await stale.claim_execution(
                state.research_id, execution_id="worker-one", lease_seconds=60
            )
            await stale_session.commit()

            async with database.sessions() as takeover_session:
                row = await takeover_session.get_one(ResearchRunRow, state.research_id)
                row.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await takeover_session.commit()
                takeover = ResearchRunRepository(takeover_session)
                await takeover.claim_execution(
                    state.research_id, execution_id="worker-two", lease_seconds=60
                )
                await takeover_session.commit()

            with pytest.raises(ResearchRunBusyError, match=r"another worker|lease expired"):
                await stale.save(
                    state.model_copy(update={"status": ResearchStatus.FAILED}),
                    execution_id="worker-one",
                )

        async with database.sessions() as verification_session:
            row = await verification_session.get_one(ResearchRunRow, state.research_id)
            assert row.execution_id == "worker-two"
            assert row.status == ResearchStatus.PENDING.value
        await database.dispose()

    asyncio.run(scenario())


def test_terminal_worker_redelivery_is_a_no_op(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'terminal.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        terminal = _state(instrument.instrument_id, datetime.now(UTC)).model_copy(
            update={"status": ResearchStatus.FAILED}
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(terminal)
        monkeypatch.setattr(celery_module, "get_database", lambda: database)
        assert await execute_research_run(terminal.research_id) == terminal
        await database.dispose()

    asyncio.run(scenario())


def test_database_session_rolls_back_on_error(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'rollback.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        session_manager = database.session()
        session = await anext(session_manager)
        await SecurityMasterRepository(session).add_instrument(instrument)
        with pytest.raises(RuntimeError, match="abort"):
            await session_manager.athrow(RuntimeError("abort"))
        async with database.sessions() as session:
            assert await SecurityMasterRepository(session).get_instrument(
                instrument.instrument_id
            ) is None
        await database.dispose()

    asyncio.run(scenario())


def test_research_api_service_boundary(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'api.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        async with database.sessions() as session:
            await SecurityMasterRepository(session).add_instrument(instrument)
            await session.commit()
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
        async with database.sessions() as session:
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


def test_queue_dispatch_failure_is_durable(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'queue-failure.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        async with database.sessions() as session:
            await SecurityMasterRepository(session).add_instrument(instrument)
            await session.commit()

            def fail_enqueue(_: str) -> str:
                raise OSError("broker unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await submit_research(
                    ResearchSubmission(
                        instrument_id=instrument.instrument_id,
                        ticker="KLAC",
                        query="Assess the setup",
                        horizon="3-5 days",
                    ),
                    session,
                    fail_enqueue,
                )
            assert exc_info.value.status_code == 503
            statement = select(ResearchRunRow).where(
                ResearchRunRow.instrument_id == instrument.instrument_id
            )
            row = await session.scalar(statement)
            assert row is not None
            assert row.status == ResearchStatus.FAILED.value
            assert row.failure_reason == "queue dispatch failed: OSError"
        await database.dispose()

    asyncio.run(scenario())


def test_http_to_registered_celery_task_to_get_terminal_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, research_plan_payload: dict[str, Any]
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase5-e2e.db'}")
    instrument = _instrument()

    async def prepare() -> None:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)

    async def override_session() -> Any:
        async for session in database.session():
            yield session

    executor = MockExecutor(lambda _request: research_plan_payload)
    executor.provider = ProviderName.CODEX_SUBSCRIPTION
    monkeypatch.setattr(celery_module, "get_database", lambda: database)
    monkeypatch.setattr(
        celery_module, "build_model_gateway", lambda _: ModelGateway([executor])
    )

    def eager_enqueue(research_run_id: str) -> str:
        result: dict[str, Any] = {}
        error: list[BaseException] = []

        def invoke() -> None:
            try:
                result["task"] = run_research.apply(
                    args=[research_run_id], throw=True
                )
            except BaseException as exc:  # pragma: no cover - assertion transport
                error.append(exc)

        thread = threading.Thread(target=invoke)
        thread.start()
        thread.join(timeout=10)
        assert not thread.is_alive()
        if error:
            raise error[0]
        return str(result["task"].id)

    asyncio.run(prepare())
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_research_enqueuer] = lambda: eager_enqueue
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
        research_run_id = response.json()["research_run_id"]
        terminal = client.get(f"/research/{research_run_id}")
        assert terminal.status_code == 200
        assert terminal.json()["status"] == ResearchStatus.INSUFFICIENT_EVIDENCE.value
        assert terminal.json()["runtime_metadata"]["transitions"] == [
            "start",
            "plan_started",
            "plan",
            "finish",
        ]
    finally:
        app.dependency_overrides.clear()
        asyncio.run(database.dispose())
