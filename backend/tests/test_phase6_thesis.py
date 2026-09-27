"""Version, transition, and citation safety for Phase 6 Thesis memory."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from backend.app.contracts.evidence import Evidence, ResearchSynthesis, TrustLevel
from backend.app.contracts.instrument import Instrument
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.contracts.thesis import Direction, Thesis, ThesisStatus
from backend.app.persistence.base import Base
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database
from backend.app.persistence.thesis import ThesisLifecycleError, ThesisRepository


def _complete_run(instrument_id: UUID, cutoff: datetime) -> ResearchState:
    evidence = Evidence(
        instrument_id=instrument_id,
        evidence_type="market_technical_snapshot",
        source_name="fixture",
        observed_at=cutoff - timedelta(hours=1),
        retrieved_at=cutoff - timedelta(hours=1),
        available_at=cutoff - timedelta(hours=1),
        content="PIT market evidence",
        confidence=1,
        freshness=1,
        trust_level=TrustLevel.TRUSTED_PROVIDER,
        source_type="market_data",
        content_hash="fixture",
        sanitization_status="structured_verified",
        injection_risk=0,
    )
    return ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="Assess setup",
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        parametric_lookahead_risk=True,
        status=ResearchStatus.COMPLETE,
        evidence=(evidence,),
        research_synthesis=ResearchSynthesis(
            summary="Cautious view",
            bull_case="Trend persists",
            bear_case="Trend weakens",
            limitations=("Fixture only",),
            evidence_ids=(evidence.evidence_id,),
            confidence=0.5,
        ),
    )


def _thesis(run: ResearchState, *, thesis_id: UUID | None = None,
            status: ThesisStatus = ThesisStatus.CREATED) -> Thesis:
    return Thesis(
        thesis_id=thesis_id or uuid4(),
        instrument_id=run.instrument_id,
        analysis_timestamp=run.analysis_timestamp,
        horizon=run.horizon,
        direction=Direction.BULLISH,
        direction_probability=0.6,
        summary="Cautious bullish thesis",
        bull_case="Trend persists",
        bear_case="Trend weakens",
        invalidation_conditions=("close below 90",),
        confidence=0.5,
        evidence_ids=(run.evidence[0].evidence_id,),
        status=status,
    )


def test_thesis_versions_preserve_history_and_require_cited_completed_research(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase6-thesis.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = Instrument(
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        first_run = _complete_run(instrument.instrument_id, datetime(2026, 9, 20, tzinfo=UTC))
        second_run = _complete_run(instrument.instrument_id, datetime(2026, 9, 21, tzinfo=UTC))
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(first_run)
            await ResearchRunRepository(session).create(second_run)

        created = _thesis(first_run)
        async with database.sessions() as session, session.begin():
            repository = ThesisRepository(session)
            first = await repository.create(created, research_run_id=first_run.research_id)
            assert first.version == 1
            with pytest.raises(ThesisLifecycleError, match="already exists"):
                await repository.create(created, research_run_id=first_run.research_id)

        updated = _thesis(second_run, thesis_id=created.thesis_id,
                          status=ThesisStatus.STRENGTHENED)
        async with database.sessions() as session, session.begin():
            repository = ThesisRepository(session)
            with pytest.raises(ThesisLifecycleError, match="version changed"):
                await repository.transition(
                    updated, research_run_id=second_run.research_id, expected_version=0
                )
            with pytest.raises(ThesisLifecycleError, match="new research run"):
                await repository.transition(
                    updated, research_run_id=first_run.research_id, expected_version=1
                )
            second = await repository.transition(
                updated, research_run_id=second_run.research_id, expected_version=1
            )
            assert second.version == 2

        async with database.sessions() as session:
            repository = ThesisRepository(session)
            before = await repository.get_as_of(created.thesis_id, at=first.recorded_at)
            latest = await repository.get_as_of(created.thesis_id, at=second.recorded_at)
            assert before == first
            assert latest == second
            transitions = await repository.list_transitions(created.thesis_id)
            assert [(item.from_status, item.to_status) for item in transitions] == [
                (None, ThesisStatus.CREATED),
                (ThesisStatus.CREATED, ThesisStatus.STRENGTHENED),
            ]
            with pytest.raises(ValueError, match="timezone-aware"):
                await repository.get_as_of(
                    created.thesis_id, at=second.recorded_at.replace(tzinfo=None)
                )

        async with database.sessions() as session, session.begin():
            repository = ThesisRepository(session)
            invented = updated.model_copy(update={"evidence_ids": (uuid4(),)})
            with pytest.raises(ThesisLifecycleError, match="citations"):
                await repository.create(invented.model_copy(update={"thesis_id": uuid4(),
                                                               "status": ThesisStatus.CREATED}),
                                        research_run_id=second_run.research_id)
            with pytest.raises(ThesisLifecycleError, match="not allowed"):
                await repository.transition(
                    updated.model_copy(update={"status": ThesisStatus.CREATED}),
                    research_run_id=second_run.research_id,
                    expected_version=2,
                )
        await database.dispose()

    asyncio.run(scenario())
