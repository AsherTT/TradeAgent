"""Forward-only, immutable ForecastRecord qualification."""

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
from backend.app.persistence.forecast import ForecastIntegrityError, ForecastRepository
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database
from backend.app.persistence.thesis import ThesisRepository


def _run(instrument_id: UUID, cutoff: datetime, *, model_execution: bool = True) -> ResearchState:
    evidence = Evidence(
        instrument_id=instrument_id,
        evidence_type="market_technical_snapshot",
        source_name="fixture",
        observed_at=cutoff - timedelta(minutes=1),
        retrieved_at=cutoff - timedelta(minutes=1),
        available_at=cutoff - timedelta(minutes=1),
        content="Qualified market evidence",
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
        requested_at=cutoff,
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        status=ResearchStatus.COMPLETE,
        evidence=(evidence,),
        model_history=(
            ({"execution_id": str(uuid4()), "status": "success"},)
            if model_execution else ()
        ),
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
    assert run.analysis_timestamp is not None
    return Thesis(
        thesis_id=thesis_id or uuid4(),
        instrument_id=run.instrument_id,
        analysis_timestamp=run.analysis_timestamp,
        horizon=run.horizon,
        direction=Direction.BULLISH,
        direction_probability=0.6,
        summary="Cautious bullish view",
        bull_case="Trend persists",
        bear_case="Trend weakens",
        invalidation_conditions=("close below 90",),
        confidence=0.5,
        evidence_ids=(run.evidence[0].evidence_id,),
        status=status,
    )


def test_forward_forecasts_freeze_provenance_and_supersede_without_mutation(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'phase6-forecast.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = Instrument(
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        now = datetime.now(UTC)
        first_run = _run(instrument.instrument_id, now - timedelta(minutes=2))
        second_run = _run(instrument.instrument_id, now - timedelta(minutes=1))
        old_run = _run(instrument.instrument_id, now - timedelta(days=2))
        no_model_run = _run(instrument.instrument_id, now, model_execution=False)
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            for run in (first_run, second_run, old_run, no_model_run):
                await ResearchRunRepository(session).create(run)
            thesis_repo = ThesisRepository(session)
            first_revision = await thesis_repo.create(
                _thesis(first_run), research_run_id=first_run.research_id
            )
            second_revision = await thesis_repo.transition(
                _thesis(second_run, thesis_id=first_revision.thesis.thesis_id,
                        status=ThesisStatus.STRENGTHENED),
                research_run_id=second_run.research_id,
                expected_version=1,
            )
            old_revision = await thesis_repo.create(
                _thesis(old_run), research_run_id=old_run.research_id
            )
            no_model_revision = await thesis_repo.create(
                _thesis(no_model_run), research_run_id=no_model_run.research_id
            )

        async with database.sessions() as session, session.begin():
            repository = ForecastRepository(session)
            first = await repository.freeze(first_revision)
            assert first.frozen is True
            assert first.probability == first_revision.thesis.direction_probability
            assert first.evidence_ids == first_revision.thesis.evidence_ids
            assert len(first.model_execution_ids) == 1
            assert await repository.freeze(first_revision) == first
            later = ForecastRepository(
                session, clock=lambda: first.created_at + timedelta(minutes=30)
            )
            assert await later.freeze(first_revision) == first
            with pytest.raises(ForecastIntegrityError, match="historical or stale"):
                await repository.freeze(old_revision)
            with pytest.raises(ForecastIntegrityError, match="model execution"):
                await repository.freeze(no_model_revision)

        async with database.sessions() as session, session.begin():
            repository = ForecastRepository(session)
            second = await repository.freeze(
                second_revision, supersedes_forecast_id=first.forecast_id
            )
            assert second.supersedes_forecast_id == first.forecast_id
            assert second.forecast_id != first.forecast_id
            assert await repository.get_as_of(
                first.forecast_id, at=first.created_at - timedelta(microseconds=1)
            ) is None
            assert await repository.get_as_of(
                first.forecast_id, at=second.created_at
            ) == first
            with pytest.raises(ForecastIntegrityError, match="already differs"):
                await repository.freeze(second_revision)
        await database.dispose()

    asyncio.run(scenario())
