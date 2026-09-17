from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.contracts.evaluation import DataQualityStatus, ReplayIntegrityLevel
from backend.app.contracts.instrument import PriceAdjustmentMode, SymbolHistory
from backend.app.contracts.market import MarketBar
from backend.app.contracts.research import BudgetUsage, ResearchBudget, ResearchState
from backend.app.graph.budget_guard import BudgetGuard


def test_symbol_history_rejects_inverted_window() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="valid_to must be later"):
        SymbolHistory(
            instrument_id=uuid4(),
            symbol="KLAC",
            exchange="NASDAQ",
            valid_from=now,
            valid_to=now - timedelta(days=1),
        )


def test_market_bar_rejects_invalid_ohlc(now: datetime) -> None:
    with pytest.raises(ValidationError, match="high must be"):
        MarketBar(
            instrument_id=uuid4(),
            symbol="KLAC",
            timestamp=now,
            open=100,
            high=99,
            low=95,
            close=98,
            volume=1000,
            adjustment_mode=PriceAdjustmentMode.RAW,
            adjustment_factor=1,
            source="fixture",
            observed_at=now,
            available_at=now,
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="fixture-v1",
        )


def test_budget_guard_blocks_at_hard_limit() -> None:
    budget = ResearchBudget(max_llm_calls=2)
    usage = BudgetUsage(llm_calls=2)
    decision = BudgetGuard.evaluate(budget, usage)
    assert decision.allowed is False
    assert decision.exhausted_fields == ("llm_calls",)


def test_historical_replay_requires_parametric_risk_disclosure() -> None:
    with pytest.raises(ValidationError, match="parametric_lookahead_risk"):
        ResearchState(
            instrument_id=uuid4(),
            ticker="KLAC",
            query="historical analysis",
            analysis_timestamp=datetime(2020, 1, 1, tzinfo=UTC),
            horizon="3-5 days",
            replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        )


def test_historical_replay_accepts_explicit_risk() -> None:
    state = ResearchState(
        instrument_id=uuid4(),
        ticker="KLAC",
        query="historical analysis",
        analysis_timestamp=datetime(2020, 1, 1, tzinfo=UTC),
        horizon="3-5 days",
        replay_integrity_level=ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY,
        parametric_lookahead_risk=True,
    )
    assert state.parametric_lookahead_risk is True
