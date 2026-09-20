from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.app.contracts.evaluation import DataQualityStatus, ProviderQualityReport
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.normalization import PriceNormalizationError, normalize_prices
from backend.app.market_data.providers import (
    InMemoryCorporateActionProvider,
    InMemoryMarketDataProvider,
)
from backend.app.market_data.quality import ProviderQualityError, require_strict_backtest_eligible
from backend.app.market_data.service import MarketDataRequest, MarketDataService

NOW = datetime(2024, 1, 10, 21, tzinfo=UTC)
INSTRUMENT_ID = uuid4()


def _bar(
    day: int,
    close: float,
    *,
    symbol: str = "ACME",
    quality: DataQualityStatus = DataQualityStatus.VERIFIED,
) -> MarketBar:
    timestamp = datetime(2024, 1, day, 21, tzinfo=UTC)
    return MarketBar(
        instrument_id=INSTRUMENT_ID,
        symbol=symbol,
        timestamp=timestamp,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=100,
        adjustment_mode=PriceAdjustmentMode.RAW,
        adjustment_factor=1,
        source="fixture",
        observed_at=timestamp,
        available_at=timestamp,
        data_quality_status=quality,
        provider_quality_version="fixture-v1",
    )


def _action(
    action_type: CorporateActionType,
    *,
    effective_at: datetime,
    available_at: datetime | None = None,
    ratio: float | None = None,
    cash_amount: float | None = None,
    currency: str | None = None,
    action_id: UUID | None = None,
) -> CorporateAction:
    values = {
        "instrument_id": INSTRUMENT_ID,
        "action_type": action_type,
        "effective_at": effective_at,
        "available_at": available_at or effective_at,
        "ratio": ratio,
        "cash_amount": cash_amount,
        "currency": currency,
        "source": "fixture",
        "provider_quality_version": "fixture-v1",
    }
    if action_id is not None:
        values["action_id"] = action_id
    return CorporateAction(**values)


def _report(
    status: DataQualityStatus = DataQualityStatus.ACCEPTABLE,
    *,
    provider: str = "fixture",
    version: str = "fixture-v1",
) -> ProviderQualityReport:
    return ProviderQualityReport(
        provider=provider,
        provider_version=version,
        evaluated_at=NOW,
        golden_case_count=6,
        passed_case_count=6,
        coverage=1,
        quality_status=status,
    )


def test_corporate_action_contract_requires_type_specific_values() -> None:
    with pytest.raises(ValidationError, match="ratio is required"):
        _action(CorporateActionType.SPLIT, effective_at=NOW)
    with pytest.raises(ValidationError, match="cash_amount and currency are required"):
        _action(CorporateActionType.CASH_DIVIDEND, effective_at=NOW, cash_amount=1)


def test_split_and_reverse_split_adjust_prices_and_volume() -> None:
    bars = (_bar(1, 100), _bar(2, 50), _bar(3, 100))
    actions = (
        _action(
            CorporateActionType.SPLIT,
            effective_at=datetime(2024, 1, 2, tzinfo=UTC),
            ratio=2,
        ),
        _action(
            CorporateActionType.REVERSE_SPLIT,
            effective_at=datetime(2024, 1, 3, tzinfo=UTC),
            ratio=0.5,
        ),
    )

    adjusted = normalize_prices(
        bars,
        actions,
        mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
        analysis_timestamp=NOW,
    )

    assert [bar.close for bar in adjusted] == [100, 100, 100]
    assert [bar.volume for bar in adjusted] == [100, 50, 100]
    assert [bar.adjustment_factor for bar in adjusted] == [1, 2, 1]


def test_total_return_reinvests_cash_dividend_with_known_factor() -> None:
    bars = (_bar(1, 100), _bar(2, 98))
    dividend = _action(
        CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        cash_amount=2,
        currency="USD",
    )

    adjusted = normalize_prices(
        bars,
        (dividend,),
        mode=PriceAdjustmentMode.TOTAL_RETURN,
        analysis_timestamp=NOW,
    )

    assert adjusted[0].close == pytest.approx(98)
    assert adjusted[0].adjustment_factor == pytest.approx(0.98)
    assert adjusted[1].close == 98


def test_point_in_time_mode_excludes_actions_not_yet_available_and_deduplicates_ids() -> None:
    action_id = uuid4()
    visible = _action(
        CorporateActionType.SPLIT,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        available_at=datetime(2024, 1, 2, tzinfo=UTC),
        ratio=2,
        action_id=action_id,
    )
    future_knowledge = _action(
        CorporateActionType.REVERSE_SPLIT,
        effective_at=datetime(2024, 1, 3, tzinfo=UTC),
        available_at=NOW + timedelta(days=1),
        ratio=0.5,
    )

    adjusted = normalize_prices(
        (_bar(1, 100), _bar(2, 50)),
        (visible, visible, future_knowledge),
        mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
        analysis_timestamp=NOW,
    )

    assert [bar.close for bar in adjusted] == [50, 50]


def test_semantically_duplicate_actions_with_different_ids_apply_once() -> None:
    first = _action(
        CorporateActionType.SPLIT,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        ratio=2,
    )
    duplicate = first.model_copy(
        update={
            "action_id": uuid4(),
            "available_at": first.available_at + timedelta(hours=1),
            "source": "second-feed",
        }
    )
    adjusted = normalize_prices(
        (_bar(1, 100), _bar(2, 50)),
        (first, duplicate),
        mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
        analysis_timestamp=NOW,
    )
    assert [bar.close for bar in adjusted] == [50, 50]


def test_same_time_split_and_dividend_use_post_split_reference_price() -> None:
    effective_at = datetime(2024, 1, 2, tzinfo=UTC)
    actions = (
        _action(CorporateActionType.SPLIT, effective_at=effective_at, ratio=2),
        _action(
            CorporateActionType.CASH_DIVIDEND,
            effective_at=effective_at,
            cash_amount=1,
            currency="USD",
        ),
    )
    adjusted = normalize_prices(
        (_bar(1, 100), _bar(2, 49)),
        actions,
        mode=PriceAdjustmentMode.TOTAL_RETURN,
        analysis_timestamp=NOW,
    )
    assert adjusted[0].close == pytest.approx(49)
    assert adjusted[1].close == 49


def test_symbol_change_is_non_numeric_and_delisting_rejects_later_bars() -> None:
    symbol_change = _action(
        CorporateActionType.SYMBOL_CHANGE,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
    )
    adjusted = normalize_prices(
        (_bar(1, 10, symbol="OLD"), _bar(2, 10, symbol="NEW")),
        (symbol_change,),
        mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
        analysis_timestamp=NOW,
    )
    assert [bar.symbol for bar in adjusted] == ["OLD", "NEW"]

    delisting = _action(
        CorporateActionType.DELISTING,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(PriceNormalizationError, match="after delisting"):
        normalize_prices(
            (_bar(1, 10), _bar(3, 10)),
            (delisting,),
            mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            analysis_timestamp=NOW,
        )


def test_invalid_or_unsupported_adjustment_events_fail_closed() -> None:
    unsupported = _action(
        CorporateActionType.MERGER,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(PriceNormalizationError, match="unsupported"):
        normalize_prices(
            (_bar(1, 10),),
            (unsupported,),
            mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            analysis_timestamp=NOW,
        )


def test_normalization_rejects_ambiguous_or_inconsistent_inputs() -> None:
    assert normalize_prices(
        (), (), mode=PriceAdjustmentMode.RAW, analysis_timestamp=NOW
    ) == ()
    adjusted = _bar(1, 10).model_copy(
        update={"adjustment_mode": PriceAdjustmentMode.SPLIT_ADJUSTED}
    )
    with pytest.raises(PriceNormalizationError, match="RAW"):
        normalize_prices(
            (adjusted,), (), mode=PriceAdjustmentMode.RAW, analysis_timestamp=NOW
        )
    with pytest.raises(PriceNormalizationError, match="one instrument"):
        normalize_prices(
            (_bar(1, 10), _bar(2, 10).model_copy(update={"instrument_id": uuid4()})),
            (),
            mode=PriceAdjustmentMode.RAW,
            analysis_timestamp=NOW,
        )
    with pytest.raises(PriceNormalizationError, match="duplicate market-bar"):
        normalize_prices(
            (_bar(1, 10), _bar(1, 10)),
            (),
            mode=PriceAdjustmentMode.RAW,
            analysis_timestamp=NOW,
        )
    assert normalize_prices(
        (_bar(1, 10),), (), mode=PriceAdjustmentMode.RAW, analysis_timestamp=NOW
    ) == (_bar(1, 10),)


def test_normalization_rejects_conflicting_or_incomplete_actions() -> None:
    action = _action(
        CorporateActionType.SPLIT,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        ratio=2,
    )
    conflicting = action.model_copy(update={"ratio": 3})
    with pytest.raises(PriceNormalizationError, match="conflicting duplicate"):
        normalize_prices(
            (_bar(1, 10),),
            (action, conflicting),
            mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
            analysis_timestamp=NOW,
        )

    missing_ratio = action.model_copy(update={"ratio": None})
    with pytest.raises(PriceNormalizationError, match="no split ratio"):
        normalize_prices(
            (_bar(1, 10),),
            (missing_ratio,),
            mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
            analysis_timestamp=NOW,
        )


def test_dividend_adjustment_requires_a_valid_prior_close() -> None:
    incomplete = _action(
        CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        cash_amount=1,
        currency="USD",
    ).model_copy(update={"cash_amount": None})
    with pytest.raises(PriceNormalizationError, match="no prior close"):
        normalize_prices(
            (_bar(1, 10),),
            (incomplete,),
            mode=PriceAdjustmentMode.TOTAL_RETURN,
            analysis_timestamp=NOW,
        )

    oversized = _action(
        CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        cash_amount=10,
        currency="USD",
    )
    with pytest.raises(PriceNormalizationError, match="not smaller"):
        normalize_prices(
            (_bar(1, 10),),
            (oversized,),
            mode=PriceAdjustmentMode.TOTAL_RETURN,
            analysis_timestamp=NOW,
        )


def test_strict_backtest_quality_gate_fails_closed() -> None:
    assert require_strict_backtest_eligible(_report()) is None
    with pytest.raises(ProviderQualityError, match="not eligible"):
        require_strict_backtest_eligible(_report(DataQualityStatus.DEGRADED))
    for incomplete in (
        _report().model_copy(update={"golden_case_count": 0, "passed_case_count": 0}),
        _report().model_copy(update={"passed_case_count": 5}),
        _report().model_copy(update={"coverage": 0.9}),
        _report().model_copy(update={"failed_cases": ("split",)}),
    ):
        with pytest.raises(ProviderQualityError, match="not eligible"):
            require_strict_backtest_eligible(incomplete)


def test_market_data_request_rejects_future_or_inverted_windows() -> None:
    with pytest.raises(ValidationError, match="end must not be earlier"):
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=NOW,
            end=NOW - timedelta(days=1),
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.RAW,
        )
    with pytest.raises(ValidationError, match="end must not be later"):
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=NOW,
            end=NOW + timedelta(days=1),
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.RAW,
        )


@pytest.mark.asyncio
async def test_market_data_service_uses_provider_neutral_interfaces() -> None:
    bars = (_bar(1, 100), _bar(2, 50))
    actions = (
        _action(
            CorporateActionType.SPLIT,
            effective_at=datetime(2024, 1, 2, tzinfo=UTC),
            ratio=2,
        ),
    )
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=bars, quality_report=_report()),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=actions, quality_report=_report()
        ),
    )

    result = await service.load_bars(
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=bars[0].timestamp,
            end=bars[-1].timestamp,
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
            strict_backtest=True,
        )
    )

    assert [bar.close for bar in result] == [50, 50]
    assert all(bar.data_quality_status is DataQualityStatus.ACCEPTABLE for bar in result)


@pytest.mark.asyncio
async def test_non_strict_market_data_load_preserves_degraded_status() -> None:
    bar = _bar(1, 100)
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(
            bars=(bar,), quality_report=_report(DataQualityStatus.DEGRADED)
        ),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=_report()
        ),
    )
    result = await service.load_bars(
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=bar.timestamp,
            end=bar.timestamp,
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.RAW,
        )
    )
    assert result[0].data_quality_status is DataQualityStatus.DEGRADED


@pytest.mark.asyncio
async def test_strict_market_data_load_cannot_upgrade_a_degraded_bar() -> None:
    bar = _bar(1, 100, quality=DataQualityStatus.DEGRADED)
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(
            bars=(bar,), quality_report=_report(DataQualityStatus.ACCEPTABLE)
        ),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=_report()
        ),
    )
    with pytest.raises(ProviderQualityError, match="market bars"):
        await service.load_bars(
            MarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                start=bar.timestamp,
                end=bar.timestamp,
                analysis_timestamp=NOW,
                adjustment_mode=PriceAdjustmentMode.RAW,
                strict_backtest=True,
            )
        )


@pytest.mark.asyncio
async def test_market_data_load_rejects_mismatched_qualification_provenance() -> None:
    bar = _bar(1, 100)
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(
            bars=(bar,), quality_report=_report(version="fixture-v2")
        ),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=_report()
        ),
    )
    with pytest.raises(ProviderQualityError, match="provenance"):
        await service.load_bars(
            MarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                start=bar.timestamp,
                end=bar.timestamp,
                analysis_timestamp=NOW,
                adjustment_mode=PriceAdjustmentMode.RAW,
            )
        )


@pytest.mark.asyncio
async def test_market_data_load_rejects_mismatched_action_provenance() -> None:
    bar = _bar(1, 100)
    action = _action(
        CorporateActionType.SPLIT,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        ratio=2,
    ).model_copy(update={"provider_quality_version": "fixture-v2"})
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=(bar,), quality_report=_report()),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(action,), quality_report=_report()
        ),
    )
    with pytest.raises(ProviderQualityError, match="corporate actions"):
        await service.load_bars(
            MarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                start=bar.timestamp,
                end=bar.timestamp,
                analysis_timestamp=NOW,
                adjustment_mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
            )
        )


@pytest.mark.asyncio
async def test_strict_load_qualifies_corporate_action_provider() -> None:
    bar = _bar(1, 100)
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=(bar,), quality_report=_report()),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(), quality_report=_report(DataQualityStatus.UNVERIFIED)
        ),
    )
    with pytest.raises(ProviderQualityError, match="not eligible"):
        await service.load_bars(
            MarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                start=bar.timestamp,
                end=bar.timestamp,
                analysis_timestamp=NOW,
                adjustment_mode=PriceAdjustmentMode.RAW,
                strict_backtest=True,
            )
        )


@pytest.mark.asyncio
async def test_adjustment_fetches_reference_bar_after_requested_output_window() -> None:
    bars = (_bar(1, 80), _bar(2, 100))
    dividend = _action(
        CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 3, tzinfo=UTC),
        cash_amount=2,
        currency="USD",
    )
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(bars=bars, quality_report=_report()),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(dividend,), quality_report=_report()
        ),
    )
    result = await service.load_bars(
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=bars[0].timestamp,
            end=bars[0].timestamp,
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.TOTAL_RETURN,
        )
    )
    assert len(result) == 1
    assert result[0].close == pytest.approx(78.4)
