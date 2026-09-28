"""Fail-closed evidence-constrained replay selection."""

import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.app.api.research import ResearchSubmission
from backend.app.config import Settings
from backend.app.contracts.evaluation import DataQualityStatus, ReplayIntegrityLevel
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.instrument import Instrument, PriceAdjustmentMode
from backend.app.contracts.market import MarketBar, MarketSnapshot, TechnicalSnapshot
from backend.app.contracts.research import ResearchState, ResearchTimestampMode
from backend.app.persistence.base import Base
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import Database
from backend.app.replay import PersistedReplayEvidence


def test_evidence_constrained_submission_requires_explicit_cutoff() -> None:
    with pytest.raises(ValidationError, match="explicit fixed cutoff"):
        ResearchSubmission(
            instrument_id=uuid4(),
            ticker="KLAC",
            query="historical setup",
            horizon="3-5 days",
            timestamp_mode=ResearchTimestampMode.FIXED_CUTOFF,
            replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        )


def test_persisted_replay_rejects_future_evidence_even_if_repository_is_wrong() -> None:
    cutoff = datetime(2020, 1, 1, tzinfo=UTC)
    instrument_id = uuid4()
    future = Evidence(
        instrument_id=instrument_id,
        evidence_type="news_document",
        source_name="fixture",
        observed_at=cutoff,
        retrieved_at=cutoff,
        available_at=cutoff + timedelta(seconds=1),
        content="future",
        confidence=1,
        freshness=1,
        source_type="news",
        content_hash="fixture",
        sanitization_status="html_cleaned_and_scanned",
        injection_risk=0,
    )

    class BrokenRepository:
        async def list_for_instrument(
            self, instrument_id: UUID, *, analysis_timestamp: datetime, limit: int
        ) -> tuple[Evidence, ...]:
            return (future,)

    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="historical setup",
        requested_at=cutoff + timedelta(days=1),
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        parametric_lookahead_risk=True,
    )
    with pytest.raises(ValueError, match="exceeds cutoff"):
        asyncio.run(PersistedReplayEvidence(BrokenRepository()).collect(state))  # type: ignore[arg-type]


def test_persisted_replay_restores_only_matching_market_snapshots() -> None:
    cutoff = datetime(2020, 1, 1, tzinfo=UTC)
    instrument_id = uuid4()
    bar = MarketBar(
        instrument_id=instrument_id,
        symbol="KLAC",
        timestamp=cutoff,
        open=100,
        high=100,
        low=100,
        close=100,
        volume=1000,
        adjustment_mode=PriceAdjustmentMode.RAW,
        adjustment_factor=1,
        source="fixture",
        observed_at=cutoff,
        available_at=cutoff,
        data_quality_status=DataQualityStatus.VERIFIED,
        provider_quality_version="fixture-v1",
    )
    market = MarketSnapshot(
        instrument_id=instrument_id,
        analysis_timestamp=cutoff,
        latest_bar=bar,
        currency="USD",
    )
    technical = TechnicalSnapshot(
        instrument_id=instrument_id,
        analysis_timestamp=cutoff,
        price_adjustment_mode=PriceAdjustmentMode.RAW,
        feature_version="fixture-v1",
    )
    item = Evidence(
        instrument_id=instrument_id,
        evidence_type="market_technical_snapshot",
        source_name="fixture",
        observed_at=cutoff,
        retrieved_at=cutoff,
        available_at=cutoff,
        content="market fixture",
        structured_data={
            "market_snapshot": market.model_dump(mode="json"),
            "technical_snapshot": technical.model_dump(mode="json"),
        },
        confidence=1,
        freshness=1,
        source_type="market_data_provider",
        content_hash="fixture",
        sanitization_status="deterministic_structured_data",
        injection_risk=0,
    )

    class Repository:
        async def list_for_instrument(
            self, instrument_id: UUID, *, analysis_timestamp: datetime, limit: int
        ) -> tuple[Evidence, ...]:
            return (item,)

    state = ResearchState(
        instrument_id=instrument_id,
        ticker="KLAC",
        query="historical setup",
        requested_at=cutoff + timedelta(days=1),
        analysis_timestamp=cutoff,
        horizon="3-5 days",
        replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        parametric_lookahead_risk=True,
    )
    adapter = PersistedReplayEvidence(Repository())  # type: ignore[arg-type]
    collection = asyncio.run(adapter.collect(state))
    assert collection.market_snapshot == market
    assert collection.technical_snapshot == technical
    assert collection.evidence == (item,)
    corrupted = item.model_copy(update={
        "structured_data": {
            **item.structured_data,
            "market_snapshot": market.model_copy(
                update={"analysis_timestamp": cutoff + timedelta(days=1)}
            ).model_dump(mode="json"),
        }
    })
    item = corrupted
    with pytest.raises(ValueError, match="violate replay cutoff"):
        asyncio.run(adapter.collect(state))


def test_worker_selects_persisted_replay_without_live_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    celery_module = importlib.import_module("backend.app.jobs.celery_app")

    async def scenario() -> None:
        database = Database(f"sqlite+aiosqlite:///{tmp_path / 'replay-worker.db'}")
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        instrument = Instrument(
            current_symbol="KLAC", exchange="NASDAQ", currency="USD",
            asset_type="equity", company_name="KLA Corporation",
        )
        cutoff = datetime(2020, 1, 1, tzinfo=UTC)
        state = ResearchState(
            instrument_id=instrument.instrument_id,
            ticker="KLAC", query="historical setup", horizon="3-5 days",
            requested_at=cutoff + timedelta(days=1), analysis_timestamp=cutoff,
            replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
            parametric_lookahead_risk=True,
        )
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
            await ResearchRunRepository(session).create(state)

        monkeypatch.setattr(celery_module, "get_database", lambda: database)
        monkeypatch.setattr(
            celery_module, "get_settings",
            lambda: Settings(_env_file=None, market_data_enabled=True, rag_enabled=True),
        )
        monkeypatch.setattr(
            celery_module, "build_market_data_loader",
            lambda *args, **kwargs: pytest.fail("live market loader was built"),
        )
        monkeypatch.setattr(
            celery_module, "build_rag_embedding_provider",
            lambda *args, **kwargs: pytest.fail("RAG embedding provider was built"),
        )

        class InspectWorkflow:
            def __init__(self, **kwargs: object) -> None:
                provider = kwargs["evidence_provider"]
                assert isinstance(provider, PersistedReplayEvidence)
                assert kwargs["rag_provider"] is None

            async def run(self, loaded: ResearchState) -> ResearchState:
                assert loaded.parametric_lookahead_risk is True
                return loaded

        monkeypatch.setattr(celery_module, "ResearchWorkflow", InspectWorkflow)
        try:
            result = await celery_module.execute_research_run(state.research_id)
            assert result.replay_integrity_level is ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY
        finally:
            await database.dispose()

    asyncio.run(scenario())
