"""Strict features require historical membership and point-in-time price inputs."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.contracts.evaluation import (
    DataQualityStatus,
    ProviderQualityReport,
    ReplayIntegrityLevel,
)
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.quality import ProviderQualityError
from backend.app.strategy import StrictBacktestInput, StrictInputError, build_strict_features

START = datetime(2020, 1, 1, tzinfo=UTC)


def _quality(name: str, status: DataQualityStatus = DataQualityStatus.VERIFIED
             ) -> ProviderQualityReport:
    return ProviderQualityReport(
        provider=name, provider_version="fixture-v1", evaluated_at=START,
        golden_case_count=1, passed_case_count=1, coverage=1, quality_status=status,
    )


def _input() -> StrictBacktestInput:
    instrument_id = uuid4()
    closes = (100.0, 102.0, 104.0, 53.0, 55.0)
    bars = tuple(
        MarketBar(
            instrument_id=instrument_id, symbol="TEST",
            timestamp=START + timedelta(days=index),
            open=close, high=close, low=close, close=close, volume=1000,
            adjustment_mode=PriceAdjustmentMode.RAW, adjustment_factor=1,
            source="fixture-market", observed_at=START + timedelta(days=index),
            available_at=START + timedelta(days=index, hours=1),
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="fixture-v1",
        )
        for index, close in enumerate(closes)
    )
    split = CorporateAction(
        instrument_id=instrument_id, action_type=CorporateActionType.SPLIT,
        effective_at=START + timedelta(days=3),
        available_at=START + timedelta(days=2), ratio=2,
        source="fixture-actions", provider_quality_version="fixture-v1",
    )
    return StrictBacktestInput(
        instrument_id=instrument_id, universe_as_of=START,
        universe_instrument_ids=(instrument_id,), bars=bars,
        corporate_actions=(split,), market_quality=_quality("fixture-market"),
        corporate_action_quality=_quality("fixture-actions"),
    )


def test_features_use_only_actions_visible_at_each_bar() -> None:
    data = _input()
    features = build_strict_features(data)
    assert len(features) == 3
    assert features[0].bar_timestamp == data.bars[2].timestamp
    assert features[0].close == 104
    assert features[0].price_adjustment_mode is PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED
    assert features[1].close == 53
    assert features[1].slow_mean == pytest.approx((51 + 52 + 53) / 3)


def test_strict_input_rejects_unqualified_and_late_information() -> None:
    data = _input()
    with pytest.raises(ProviderQualityError):
        build_strict_features(data.model_copy(update={
            "market_quality": _quality("fixture-market", DataQualityStatus.DEGRADED),
        }))
    with pytest.raises(ValueError, match="historical universe"):
        StrictBacktestInput.model_validate(data.model_dump() | {
            "universe_as_of": START + timedelta(days=1),
            "universe_instrument_ids": (uuid4(),),
        })
    with pytest.raises(StrictInputError, match="historical universe"):
        build_strict_features(data.model_copy(update={
            "universe_as_of": START + timedelta(days=1),
        }))
    with pytest.raises(StrictInputError, match="effective time"):
        build_strict_features(data.model_copy(update={
            "corporate_actions": (
                data.corporate_actions[0].model_copy(update={
                    "available_at": START + timedelta(days=4),
                }),
            ),
        }))
    with pytest.raises(ValueError, match="strict quant"):
        StrictBacktestInput.model_validate(data.model_dump() | {
            "replay_integrity_level": ReplayIntegrityLevel.RESEARCH_REPLAY,
        })
