"""Point-in-time and immutability checks for the Phase 6 evidence repository."""

import asyncio
import importlib.util
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from backend.app.contracts.evidence import Evidence, TrustLevel
from backend.app.contracts.instrument import Instrument
from backend.app.contracts.research import ResearchState
from backend.app.persistence.base import Base
from backend.app.persistence.evidence import EvidenceIntegrityError, EvidenceRepository
from backend.app.persistence.models import ResearchRunRow
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database


def _evidence(instrument_id: UUID, observed_at: datetime, *, content: str) -> Evidence:
    return Evidence(
        instrument_id=instrument_id,
        evidence_type="news_document",
        source_name="fixture",
        observed_at=observed_at,
        retrieved_at=observed_at,
        available_at=observed_at,
        published_at=observed_at,
        content=content,
        confidence=0.8,
        freshness=0.8,
        trust_level=TrustLevel.PUBLIC_SOURCE,
        source_type="news",
        content_hash=content,
        sanitization_status="html_cleaned_and_scanned",
        injection_risk=0,
    )


def test_research_checkpoint_persists_append_only_evidence_with_pit_reads(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase6-evidence.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = Instrument(
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        cutoff = datetime(2026, 9, 28, tzinfo=UTC)
        known = _evidence(instrument.instrument_id, cutoff - timedelta(days=1), content="known")
        future = _evidence(instrument.instrument_id, cutoff + timedelta(days=1), content="future")
        offset = _evidence(
            instrument.instrument_id,
            (cutoff - timedelta(hours=1)).astimezone(timezone(timedelta(hours=8))),
            content="offset",
        )
        state = ResearchState(
            instrument_id=instrument.instrument_id, ticker="KLAC", query="Assess setup",
            analysis_timestamp=cutoff, requested_at=cutoff,
            horizon="3-5 days", evidence=(known, future, offset),
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(state)

        async with database.sessions() as session:
            repository = EvidenceRepository(session)
            persisted = await ResearchRunRepository(session).get(state.research_id)
            assert persisted is not None
            assert persisted.evidence == (known, offset)
            assert await repository.list_for_instrument(
                instrument.instrument_id, analysis_timestamp=cutoff
            ) == (known, offset)
            assert await repository.list_for_instrument(
                instrument.instrument_id, analysis_timestamp=cutoff + timedelta(days=2)
            ) == (known, offset)
            with pytest.raises(ValueError, match="timezone-aware"):
                await repository.list_for_instrument(
                    instrument.instrument_id,
                    analysis_timestamp=cutoff.replace(tzinfo=None),
                )

        async with database.sessions() as session, session.begin():
            repository = EvidenceRepository(session)
            await repository.add_from_run(state)
            changed = known.model_copy(update={"content": "silently changed"})
            with pytest.raises(EvidenceIntegrityError, match="reused"):
                await repository.add_from_run(state.model_copy(update={"evidence": (changed,)}))
            future_mutation = known.model_copy(update={
                "content": "changed later",
                "available_at": cutoff + timedelta(days=1),
            })
            with pytest.raises(EvidenceIntegrityError, match="reused"):
                await ResearchRunRepository(session).save(
                    state.model_copy(update={"evidence": (future_mutation,)})
                )
            duplicate = known.model_copy(update={"content": "different in same checkpoint"})
            with pytest.raises(EvidenceIntegrityError, match="reused"):
                await ResearchRunRepository(session).save(
                    state.model_copy(update={"evidence": (known, duplicate)})
                )
            wrong_instrument = _evidence(uuid4(), cutoff, content="wrong instrument")
            with pytest.raises(EvidenceIntegrityError, match="instrument"):
                await repository.add_from_run(
                    state.model_copy(update={"evidence": (wrong_instrument,)})
                )
            naive = known.model_copy(update={"observed_at": cutoff.replace(tzinfo=None)})
            with pytest.raises(EvidenceIntegrityError, match="timezone-aware"):
                await repository.add_from_run(state.model_copy(update={"evidence": (naive,)}))
        await database.dispose()

    asyncio.run(scenario())


def test_migration_backfills_only_pit_eligible_historical_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration_path = (
        Path(__file__).parents[2] / "alembic" / "versions"
        / "0007_phase6_evidence_repository.py"
    )
    spec = importlib.util.spec_from_file_location("phase6_evidence_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase6-backfill.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = Instrument(
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        cutoff = datetime(2026, 9, 28, tzinfo=UTC)
        known = _evidence(
            instrument.instrument_id,
            (cutoff - timedelta(hours=1)).astimezone(timezone(timedelta(hours=8))),
            content="historical known",
        )
        future = _evidence(instrument.instrument_id, cutoff + timedelta(hours=1), content="later")
        state = ResearchState(
            instrument_id=instrument.instrument_id, ticker="KLAC", query="Assess setup",
            analysis_timestamp=cutoff, requested_at=cutoff,
            horizon="3-5 days", evidence=(known, future),
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            session.add(ResearchRunRow(
                research_run_id=state.research_id,
                instrument_id=state.instrument_id,
                query=state.query,
                analysis_timestamp=state.analysis_timestamp,
                horizon=state.horizon,
                status=state.status.value,
                state_json=state.model_dump(mode="json"),
            ))
        async with database.engine.begin() as connection:
            await connection.run_sync(
                lambda sync_connection: (
                    monkeypatch.setattr(migration.op, "get_bind", lambda: sync_connection),
                    migration._backfill_research_evidence(),
                )
            )
        async with database.sessions() as session:
            assert await EvidenceRepository(session).list_for_instrument(
                instrument.instrument_id, analysis_timestamp=cutoff
            ) == (known,)
            persisted = await ResearchRunRepository(session).get(state.research_id)
            assert persisted is not None and persisted.evidence == (known,)
        await database.dispose()

    asyncio.run(scenario())
