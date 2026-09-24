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
from backend.app.market_data.cache import (
    CachedMarketDataLoader,
    InMemoryQualifiedMarketDataCache,
    ProviderQualificationVersions,
)
from backend.app.market_data.errors import (
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.normalization import PriceNormalizationError, normalize_prices
from backend.app.market_data.providers import (
    InMemoryCorporateActionProvider,
    InMemoryMarketDataProvider,
)
from backend.app.market_data.quality import ProviderQualityError, require_strict_backtest_eligible
from backend.app.market_data.service import (
    FallbackMarketDataService,
    MarketDataCandidate,
    MarketDataFallbackPolicy,
    MarketDataRequest,
    MarketDataService,
    ProviderAttempt,
    ProviderAttemptOutcome,
)

NOW = datetime(2024, 1, 10, 21, tzinfo=UTC)
INSTRUMENT_ID = uuid4()
FALLBACK_POLICY = MarketDataFallbackPolicy(
    allowed_reasons=frozenset(OperationalFailureReason)
)


def test_provider_attempt_contract_rejects_invalid_outcome_reason_combinations() -> None:
    with pytest.raises(ValidationError, match="typed operational reason"):
        ProviderAttempt(
            provider="alpha_vantage",
            outcome=ProviderAttemptOutcome.OPERATIONAL_FAILURE,
        )
    with pytest.raises(ValidationError, match="cannot have a failure reason"):
        ProviderAttempt(
            provider="yfinance",
            outcome=ProviderAttemptOutcome.SELECTED,
            reason="unexpected",
        )


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
async def test_action_provider_quality_propagates_to_adjusted_bars() -> None:
    bars = (_bar(1, 100), _bar(2, 50))
    split = _action(
        CorporateActionType.SPLIT,
        effective_at=datetime(2024, 1, 2, tzinfo=UTC),
        ratio=2,
    )
    service = MarketDataService(
        market_data_provider=InMemoryMarketDataProvider(
            bars=bars, quality_report=_report(DataQualityStatus.ACCEPTABLE)
        ),
        corporate_action_provider=InMemoryCorporateActionProvider(
            actions=(split,), quality_report=_report(DataQualityStatus.UNVERIFIED)
        ),
    )

    result = await service.load_bars(
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=bars[0].timestamp,
            end=bars[-1].timestamp,
            analysis_timestamp=NOW,
            adjustment_mode=PriceAdjustmentMode.SPLIT_ADJUSTED,
        )
    )

    assert all(
        bar.data_quality_status is DataQualityStatus.UNVERIFIED for bar in result
    )


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


@pytest.mark.asyncio
async def test_fallback_retries_the_complete_request_after_an_operational_failure() -> None:
    class UnavailableLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            raise MarketDataOperationalError(
                "free quota exhausted",
                reason=OperationalFailureReason.QUOTA_EXHAUSTED,
            )

    class YFinanceLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            return (
                _bar(1, 100).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    loader = FallbackMarketDataService(
        (
            MarketDataCandidate("alpha_vantage", UnavailableLoader()),
            MarketDataCandidate("yfinance", YFinanceLoader()),
        ),
        policy=FALLBACK_POLICY,
    )
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )

    result = await loader.load_bars(request)

    assert [bar.source for bar in result] == ["yfinance"]
    attempts = [
        (attempt.provider, attempt.outcome, attempt.reason)
        for attempt in loader.last_attempts
    ]
    assert attempts == [
        ("alpha_vantage", "operational_failure", "quota_exhausted"),
        ("yfinance", "selected", None),
    ]


@pytest.mark.asyncio
async def test_fallback_does_not_hide_provider_integrity_failures() -> None:
    class InvalidLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            raise ProviderQualityError("provider qualification provenance mismatch")

    class UnexpectedFallbackLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            raise AssertionError("integrity failure must not fall back")

    loader = FallbackMarketDataService(
        (
            MarketDataCandidate("alpha_vantage", InvalidLoader()),
            MarketDataCandidate("yfinance", UnexpectedFallbackLoader()),
        ),
        policy=FALLBACK_POLICY,
    )
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )

    with pytest.raises(ProviderQualityError, match="provenance"):
        await loader.load_bars(request)

    assert [(attempt.provider, attempt.outcome) for attempt in loader.last_attempts] == [
        ("alpha_vantage", "integrity_failure")
    ]


@pytest.mark.asyncio
async def test_fallback_policy_rejects_an_operational_reason_not_on_its_allowlist() -> None:
    class UnavailableLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            raise MarketDataOperationalError(
                "credential missing",
                reason=OperationalFailureReason.MISSING_CREDENTIAL,
            )

    loader = FallbackMarketDataService(
        (MarketDataCandidate("alpha_vantage", UnavailableLoader()),),
        policy=MarketDataFallbackPolicy(
            allowed_reasons=frozenset({OperationalFailureReason.RATE_LIMITED})
        ),
    )
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )

    with pytest.raises(MarketDataOperationalError, match="credential missing"):
        await loader.load_bars(request)

    assert loader.last_attempts[0].outcome == "terminal_operational_failure"


@pytest.mark.asyncio
async def test_qualified_cache_serves_a_validated_result_before_external_loading() -> None:
    class Loader:
        unavailable = False

        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            if self.unavailable:
                raise MarketDataOperationalError(
                    "provider is offline", reason=OperationalFailureReason.NETWORK
                )
            return (
                _bar(1, 100).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    underlying = Loader()
    loader = CachedMarketDataLoader(
        loader=underlying,
        cache=InMemoryQualifiedMarketDataCache(),
        provider_order=("alpha_vantage", "yfinance"),
        qualified_versions={
            "alpha_vantage": ProviderQualificationVersions(
                "alpha-vantage-daily-raw-v1", "alpha-vantage-actions-observed-v1"
            ),
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v1", "yfinance-actions-observed-v1"
            ),
        },
    )
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )

    first = await loader.load_bars(request)
    underlying.unavailable = True
    second = await loader.load_bars(request)

    assert second == first
    assert second[0].observed_at == first[0].observed_at
    assert second[0].available_at == first[0].available_at
    assert [(attempt.provider, attempt.outcome) for attempt in loader.last_attempts] == [
        ("yfinance", "cache_hit")
    ]


@pytest.mark.asyncio
async def test_qualified_cache_clears_attempts_before_an_untraced_miss() -> None:
    class Loader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            return (
                _bar(1, 100).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    loader = CachedMarketDataLoader(
        loader=Loader(),
        cache=InMemoryQualifiedMarketDataCache(),
        provider_order=("yfinance",),
        qualified_versions={
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v1", "yfinance-actions-observed-v1"
            )
        },
    )
    first = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )
    await loader.load_bars(first)
    await loader.load_bars(first)
    assert loader.last_attempts[0].outcome is ProviderAttemptOutcome.CACHE_HIT

    await loader.load_bars(
        first.model_copy(update={"start": datetime(2024, 1, 1, 20, tzinfo=UTC)})
    )

    assert loader.last_attempts == ()


@pytest.mark.asyncio
async def test_qualified_cache_preserves_attempts_from_any_traced_loader() -> None:
    class TracedLoader:
        @property
        def last_attempts(self) -> tuple[ProviderAttempt, ...]:
            return (
                ProviderAttempt(
                    provider="yfinance",
                    outcome=ProviderAttemptOutcome.SELECTED,
                ),
            )

        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            return (
                _bar(1, 100).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    loader = CachedMarketDataLoader(
        loader=TracedLoader(),
        cache=InMemoryQualifiedMarketDataCache(),
        provider_order=("yfinance",),
        qualified_versions={
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v1", "yfinance-actions-observed-v1"
            )
        },
    )
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )

    await loader.load_bars(request)

    assert [(attempt.provider, attempt.outcome) for attempt in loader.last_attempts] == [
        ("yfinance", "selected")
    ]


@pytest.mark.asyncio
async def test_qualified_cache_never_reuses_an_old_provider_quality_version() -> None:
    class VersionTwoLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            return (
                _bar(1, 101).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v2",
                    }
                ),
            )

    cache = InMemoryQualifiedMarketDataCache()
    request = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )
    class VersionOneLoader:
        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            return (
                _bar(1, 100).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    version_one = CachedMarketDataLoader(
        loader=VersionOneLoader(),
        cache=cache,
        provider_order=("yfinance",),
        qualified_versions={
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v1", "yfinance-actions-observed-v1"
            )
        },
    )
    assert (await version_one.load_bars(request))[0].close == 100

    version_two = CachedMarketDataLoader(
        loader=VersionTwoLoader(),
        cache=cache,
        provider_order=("yfinance",),
        qualified_versions={
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v2", "yfinance-actions-observed-v2"
            )
        },
    )
    result = await version_two.load_bars(request)

    assert result[0].close == 101
    assert result[0].provider_quality_version == "yfinance-daily-raw-v2"


@pytest.mark.asyncio
async def test_qualified_cache_evicts_the_least_recently_used_entry_at_its_bound() -> None:
    class CountingLoader:
        calls = 0

        async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
            self.calls += 1
            return (
                _bar(1, 100 + self.calls).model_copy(
                    update={
                        "source": "yfinance",
                        "provider_quality_version": "yfinance-daily-raw-v1",
                    }
                ),
            )

    underlying = CountingLoader()
    loader = CachedMarketDataLoader(
        loader=underlying,
        cache=InMemoryQualifiedMarketDataCache(max_entries=2),
        provider_order=("yfinance",),
        qualified_versions={
            "yfinance": ProviderQualificationVersions(
                "yfinance-daily-raw-v1", "yfinance-actions-observed-v1"
            )
        },
    )
    base = MarketDataRequest(
        instrument_id=INSTRUMENT_ID,
        start=datetime(2024, 1, 1, 21, tzinfo=UTC),
        end=datetime(2024, 1, 1, 21, tzinfo=UTC),
        analysis_timestamp=NOW,
        adjustment_mode=PriceAdjustmentMode.RAW,
    )
    first = base
    second = base.model_copy(
        update={"start": datetime(2024, 1, 1, 20, tzinfo=UTC)}
    )
    third = base.model_copy(
        update={"start": datetime(2024, 1, 1, 19, tzinfo=UTC)}
    )

    await loader.load_bars(first)
    await loader.load_bars(second)
    await loader.load_bars(first)  # refresh first; second becomes least recently used
    await loader.load_bars(third)
    await loader.load_bars(second)

    assert underlying.calls == 4
