import asyncio
import importlib
import importlib.util
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import JSON, Column, DateTime, MetaData, Table, Uuid, create_engine, select
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
    ResearchTimestampMode,
)
from backend.app.jobs.celery_app import (
    celery_app,
    create_celery,
    enqueue_research_run,
    execute_research_run,
    reconcile_pending_research_runs,
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


def test_current_cutoff_migration_downgrade_restores_legacy_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "0006_current_research_cutoff.py"
    )
    spec = importlib.util.spec_from_file_location("current_cutoff_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine(f"sqlite:///{tmp_path / 'downgrade.db'}")
    table = Table(
        "research_run",
        MetaData(),
        Column("research_run_id", Uuid(), primary_key=True),
        Column("created_at", DateTime(timezone=True)),
        Column("analysis_timestamp", DateTime(timezone=True)),
        Column("state_json", JSON()),
    )
    table.create(engine)
    pending_id, frozen_id = uuid4(), uuid4()
    created = datetime(2026, 9, 22, tzinfo=UTC)
    frozen = created + timedelta(hours=1)
    with engine.begin() as connection:
        connection.execute(
            table.insert(),
            [
                {
                    "research_run_id": pending_id,
                    "created_at": created,
                    "analysis_timestamp": None,
                    "state_json": {
                        "timestamp_mode": "current_research",
                        "requested_at": created.isoformat(),
                        "analysis_timestamp": None,
                    },
                },
                {
                    "research_run_id": frozen_id,
                    "created_at": created,
                    "analysis_timestamp": frozen,
                    "state_json": {
                        "timestamp_mode": "current_research",
                        "requested_at": created.isoformat(),
                        "analysis_timestamp": frozen.isoformat(),
                    },
                },
            ],
        )
        monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(migration.op, "alter_column", lambda *args, **kwargs: None)
        migration.downgrade()
        rows = {
            row.research_run_id: row
            for row in connection.execute(select(table)).all()
        }

    for research_id, expected_cutoff in ((pending_id, created), (frozen_id, frozen)):
        row = rows[research_id]
        assert row.analysis_timestamp == expected_cutoff.replace(tzinfo=None)
        assert row.state_json == {"analysis_timestamp": expected_cutoff.isoformat()}
    engine.dispose()


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
            assert await security.resolve_instrument_epoch(
                instrument.instrument_id,
                at=now,
                analysis_timestamp=now,
            ) == (instrument, history)
            assert (
                await security.resolve_instrument_epoch(uuid4(), at=now, analysis_timestamp=now)
                is None
            )

            future_history = SymbolHistory(
                instrument_id=instrument.instrument_id,
                symbol="FUTURE",
                exchange="NASDAQ",
                valid_from=now - timedelta(days=1),
                available_at=now + timedelta(days=1),
            )
            await security.add_symbol_history(future_history)
            assert (
                await security.resolve_symbol("FUTURE", "NASDAQ", now, analysis_timestamp=now)
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
            with pytest.raises(SecurityMasterIntegrityError, match="overlapping"):
                await security.resolve_instrument_epoch(
                    instrument.instrument_id,
                    at=now,
                    analysis_timestamp=now,
                )

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


def test_repository_lists_only_old_unclaimed_pending_runs_in_bounded_order(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'reconcile-query.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        instrument = _instrument()
        now = datetime.now(UTC)
        states = [_state(instrument.instrument_id, now) for _ in range(6)]
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            for state in states:
                await repository.create(state)

            oldest, tied_left, tied_right, recent, claimed, failed = [
                await session.get_one(ResearchRunRow, state.research_id)
                for state in states
            ]
            oldest.created_at = now - timedelta(minutes=10)
            tied_left.created_at = now - timedelta(minutes=5)
            tied_right.created_at = now - timedelta(minutes=5)
            recent.created_at = now - timedelta(seconds=5)
            claimed.created_at = now - timedelta(minutes=20)
            claimed.execution_id = "active-worker"
            failed.created_at = now - timedelta(minutes=30)
            failed.status = ResearchStatus.FAILED.value

        async with database.sessions() as session:
            repository = ResearchRunRepository(session)
            ids = await repository.list_reconcilable_pending_ids(
                older_than=now - timedelta(minutes=1),
                limit=2,
            )
            tied_ids = tuple(sorted((states[1].research_id, states[2].research_id)))
            assert ids == (states[0].research_id, tied_ids[0])

            ids = await repository.list_reconcilable_pending_ids(
                older_than=now - timedelta(minutes=1),
                limit=10,
            )
            assert ids == (states[0].research_id, *tied_ids)
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
    assert app.conf.beat_schedule["reconcile-pending-research-runs"] == {
        "task": "research.reconcile_pending",
        "schedule": 60,
    }
    research_run_id = uuid4()
    disposed = 0

    class WorkerDatabase:
        async def dispose(self) -> None:
            nonlocal disposed
            disposed += 1

    async def fake_execute(run_id: Any, *, execution_id: str) -> ResearchState:
        assert run_id == research_run_id
        assert execution_id
        return _state(uuid4(), datetime.now(UTC)).model_copy(
            update={"research_id": research_run_id, "status": ResearchStatus.COMPLETE}
        )

    monkeypatch.setattr(celery_module, "execute_research_run", fake_execute)
    monkeypatch.setattr(celery_module, "get_database", lambda: WorkerDatabase())
    assert run_research(str(research_run_id)) == {
        "research_run_id": str(research_run_id),
        "state": "complete",
    }
    assert disposed == 1

    monkeypatch.setattr(
        celery_app,
        "send_task",
        lambda *args, **kwargs: SimpleNamespace(id="task-id"),
    )
    assert enqueue_research_run("run-id") == "task-id"
    assert get_research_enqueuer() is enqueue_research_run


def test_reconciliation_settings_are_bounded() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, research_reconcile_interval_seconds=0)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, research_reconcile_batch_size=1001)


def test_reconciler_republishes_without_mutation_and_retries_broker_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def arrange() -> tuple[Database, tuple[ResearchState, ...]]:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'reconciler.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        now = datetime.now(UTC)
        states = (_state(instrument.instrument_id, now), _state(instrument.instrument_id, now))
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            for state in states:
                await repository.create(state)
                row = await session.get_one(ResearchRunRow, state.research_id)
                row.created_at = now - timedelta(minutes=5)
        return database, states

    database, states = asyncio.run(arrange())
    disposed = 0

    class TrackingDatabase:
        def sessions(self) -> Any:
            return database.sessions()

        async def dispose(self) -> None:
            nonlocal disposed
            disposed += 1
            await database.dispose()

    settings = Settings(
        _env_file=None,
        research_reconcile_grace_seconds=60,
        research_reconcile_batch_size=10,
    )
    monkeypatch.setattr(celery_module, "get_database", lambda: TrackingDatabase())
    monkeypatch.setattr(celery_module, "get_settings", lambda: settings)

    first_attempts: list[str] = []

    def flaky_enqueue(run_id: str) -> str:
        first_attempts.append(run_id)
        if len(first_attempts) == 1:
            raise ConnectionError("broker unavailable")
        return f"task-{run_id}"

    monkeypatch.setattr(celery_module, "enqueue_research_run", flaky_enqueue)
    assert reconcile_pending_research_runs() == {
        "eligible": 2,
        "published": 1,
        "failed": 1,
    }
    assert set(first_attempts) == {str(state.research_id) for state in states}

    second_attempts: list[str] = []
    monkeypatch.setattr(
        celery_module,
        "enqueue_research_run",
        lambda run_id: second_attempts.append(run_id) or f"retry-{run_id}",
    )
    assert reconcile_pending_research_runs() == {
        "eligible": 2,
        "published": 2,
        "failed": 0,
    }
    assert set(second_attempts) == {str(state.research_id) for state in states}
    assert disposed == 2

    async def assert_unchanged() -> None:
        async with database.sessions() as session:
            repository = ResearchRunRepository(session)
            for state in states:
                assert await repository.get(state.research_id) == state
        await database.dispose()

    asyncio.run(assert_unchanged())


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
                    timestamp_mode=ResearchTimestampMode.FIXED_CUTOFF,
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


def test_current_research_submission_persists_a_pending_cutoff(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'current-research.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            accepted = await submit_research(
                ResearchSubmission(
                    instrument_id=instrument.instrument_id,
                    ticker="KLAC",
                    query="Assess the current setup",
                    horizon="3-5 days",
                    timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
                ),
                session,
                lambda _: "offline-current-task",
            )

        async with database.sessions() as session:
            persisted = await ResearchRunRepository(session).get(accepted.research_run_id)
            assert persisted is not None
            assert persisted.timestamp_mode is ResearchTimestampMode.CURRENT_RESEARCH
            assert persisted.analysis_timestamp is None
        await database.dispose()

    asyncio.run(scenario())


def test_current_research_save_persists_the_frozen_cutoff(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'frozen-cutoff.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        pending = ResearchState(
            instrument_id=instrument.instrument_id,
            ticker="KLAC",
            query="Assess the current setup",
            horizon="3-5 days",
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
        )
        frozen_cutoff = datetime.now(UTC)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            await repository.create(pending)
            await repository.save(pending.model_copy(update={"analysis_timestamp": frozen_cutoff}))

        async with database.sessions() as session:
            persisted = await ResearchRunRepository(session).get(pending.research_id)
            assert persisted is not None
            assert persisted.analysis_timestamp == frozen_cutoff
        await database.dispose()

    asyncio.run(scenario())


def test_set_status_rejects_complete_current_research_without_a_cutoff(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'invalid-complete.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        pending = ResearchState(
            instrument_id=instrument.instrument_id,
            ticker="KLAC",
            query="Assess the current setup",
            horizon="3-5 days",
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            await repository.create(pending)
            with pytest.raises(ValidationError, match="complete research requires"):
                await repository.set_status(
                    pending.research_id, ResearchStatus.COMPLETE
                )

            assert await repository.get(pending.research_id) == pending
        await database.dispose()

    asyncio.run(scenario())


def test_repository_backfills_requested_at_for_legacy_state_json(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'legacy-state.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        accepted_at = datetime(2020, 1, 1, tzinfo=UTC)
        state = ResearchState(
            instrument_id=instrument.instrument_id,
            ticker="KLAC",
            query="Current when submitted",
            requested_at=accepted_at,
            analysis_timestamp=accepted_at,
            horizon="3-5 days",
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            await repository.create(state)
            row = await session.get_one(ResearchRunRow, state.research_id)
            legacy_json = dict(row.state_json)
            legacy_json.pop("requested_at")
            row.state_json = legacy_json
            row.created_at = accepted_at
            await session.flush()

            loaded = await repository.get(state.research_id)
            assert loaded is not None
            assert loaded.requested_at == accepted_at
        await database.dispose()

    asyncio.run(scenario())


def test_repository_rejects_replacing_a_frozen_cutoff(tmp_path: Path) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'immutable-cutoff.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        first_cutoff = datetime.now(UTC)
        state = _state(instrument.instrument_id, first_cutoff)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            repository = ResearchRunRepository(session)
            await repository.create(state)
            with pytest.raises(ValueError, match="analysis_timestamp is immutable"):
                await repository.save(
                    state.model_copy(
                        update={"analysis_timestamp": first_cutoff + timedelta(seconds=1)}
                    )
                )
        await database.dispose()

    asyncio.run(scenario())


def test_leased_repository_rejects_replacing_a_cutoff_frozen_in_same_session(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'leased-cutoff.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = _instrument()
        pending = ResearchState(
            instrument_id=instrument.instrument_id,
            ticker="KLAC",
            query="Assess the current setup",
            horizon="3-5 days",
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(pending)

        first_cutoff = datetime.now(UTC)
        async with database.sessions() as session:
            repository = ResearchRunRepository(session)
            await repository.claim_execution(
                pending.research_id,
                execution_id="worker-one",
                lease_seconds=60,
            )
            await session.commit()
            frozen = pending.model_copy(update={"analysis_timestamp": first_cutoff})
            await repository.save(frozen, execution_id="worker-one")
            await session.commit()

            with pytest.raises(ValueError, match="analysis_timestamp is immutable"):
                await repository.save(
                    frozen.model_copy(
                        update={
                            "analysis_timestamp": first_cutoff + timedelta(seconds=1)
                        }
                    ),
                    execution_id="worker-one",
                )

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
                await second.claim_execution(uuid4(), execution_id="worker-two", lease_seconds=60)

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
            assert (
                await SecurityMasterRepository(session).get_instrument(instrument.instrument_id)
                is None
            )
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
                    timestamp_mode=ResearchTimestampMode.FIXED_CUTOFF,
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
                "timestamp_mode": "fixed_cutoff",
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
                        timestamp_mode=ResearchTimestampMode.FIXED_CUTOFF,
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
    monkeypatch.setattr(celery_module, "build_model_gateway", lambda _: ModelGateway([executor]))

    def eager_enqueue(research_run_id: str) -> str:
        result: dict[str, Any] = {}
        error: list[BaseException] = []

        def invoke() -> None:
            try:
                result["task"] = run_research.apply(args=[research_run_id], throw=True)
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
                "timestamp_mode": "fixed_cutoff",
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
