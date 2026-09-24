import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pandas as pd
import pytest
from curl_cffi.requests.exceptions import ConnectionError as CurlConnectionError
from curl_cffi.requests.exceptions import HTTPError
from yfinance.exceptions import YFRateLimitError

from backend.app.config import Settings
from backend.app.contracts.evaluation import DataQualityStatus, ProviderQualityReport
from backend.app.contracts.instrument import (
    CorporateActionType,
    Instrument,
    PriceAdjustmentMode,
    SymbolHistory,
)
from backend.app.market_data.errors import (
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.instrument import ProviderInstrument
from backend.app.market_data.runtime import (
    RuntimeMarketDataLoader,
    SecurityMasterInstrumentResolver,
    build_market_data_loader,
)
from backend.app.market_data.service import (
    CurrentMarketDataLoader,
    CurrentMarketDataRequest,
    MarketDataRequest,
    ProviderAttemptOutcome,
)
from backend.app.market_data.yfinance import (
    YFinanceCorporateActionProvider,
    YFinanceLibraryClient,
    YFinanceMarketDataProvider,
    YFinanceProviderError,
)

FIXTURES = Path(__file__).parent / "fixtures" / "yfinance"
QUALITY_REPORTS = Path(__file__).parents[2] / "docs" / "provider_quality"
INSTRUMENT_ID = uuid4()
OBSERVED_AT = datetime(2024, 1, 11, 12, tzinfo=UTC)


class StaticSymbolResolver:
    async def resolve_instrument(
        self, instrument_id: UUID, *, at: datetime
    ) -> ProviderInstrument:
        assert instrument_id == INSTRUMENT_ID
        return ProviderInstrument(
            symbol="IBM",
            currency="USD",
            valid_from=datetime(2000, 1, 1, tzinfo=UTC),
        )


class StaticHistoryClient:
    async def history(
        self, symbol: str, *, start: datetime, end: datetime
    ) -> pd.DataFrame:
        assert symbol == "IBM"
        return _fixture_frame("daily_raw_success.json")


def _fixture_frame(name: str) -> pd.DataFrame:
    rows = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if not rows:
        return pd.DataFrame(
            columns=["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"],
            index=pd.DatetimeIndex([], tz="America/New_York"),
        )
    return pd.DataFrame(rows).set_index(pd.to_datetime([row["Date"] for row in rows]))


def _quality_report() -> ProviderQualityReport:
    return ProviderQualityReport.model_validate_json(
        (QUALITY_REPORTS / "yfinance_daily_raw_v1.json").read_text(encoding="utf-8")
    )


def _action_quality_report() -> ProviderQualityReport:
    return ProviderQualityReport.model_validate_json(
        (QUALITY_REPORTS / "yfinance_actions_observed_v1.json").read_text(
            encoding="utf-8"
        )
    )


@pytest.mark.asyncio
async def test_yfinance_daily_raw_response_becomes_point_in_time_market_bars() -> None:
    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=StaticHistoryClient(),
        observed_at=lambda: OBSERVED_AT,
    )

    bars = await provider.get_bars(
        INSTRUMENT_ID,
        start=datetime(2024, 1, 9, 21, tzinfo=UTC),
        end=datetime(2024, 1, 10, 21, tzinfo=UTC),
        analysis_timestamp=OBSERVED_AT,
    )

    assert [(bar.timestamp, bar.close) for bar in bars] == [
        (datetime(2024, 1, 9, 21, tzinfo=UTC), 160.08),
        (datetime(2024, 1, 10, 21, tzinfo=UTC), 163.55),
    ]
    assert all(bar.instrument_id == INSTRUMENT_ID for bar in bars)
    assert all(bar.symbol == "IBM" for bar in bars)
    assert all(bar.adjustment_mode is PriceAdjustmentMode.RAW for bar in bars)
    assert all(bar.source == "yfinance" for bar in bars)
    assert all(bar.provider_quality_version == "yfinance-daily-raw-v1" for bar in bars)
    assert all(bar.available_at == OBSERVED_AT for bar in bars)


@pytest.mark.asyncio
async def test_yfinance_library_requests_unadjusted_unrepaired_daily_history() -> None:
    frame = _fixture_frame("daily_raw_success.json")
    captured: dict[str, object] = {}

    class FakeTicker:
        def history(self, **kwargs: object) -> pd.DataFrame:
            captured.update(kwargs)
            return frame

    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=YFinanceLibraryClient(lambda symbol: FakeTicker()),
        observed_at=lambda: OBSERVED_AT,
    )

    await provider.get_bars(
        INSTRUMENT_ID,
        start=datetime(2024, 1, 9, 21, tzinfo=UTC),
        end=datetime(2024, 1, 10, 21, tzinfo=UTC),
        analysis_timestamp=OBSERVED_AT,
    )

    assert captured == {
        "start": "2024-01-09",
        "end": "2024-01-11",
        "interval": "1d",
        "auto_adjust": False,
        "back_adjust": False,
        "repair": False,
        "actions": True,
        "raise_errors": True,
    }


@pytest.mark.asyncio
async def test_yfinance_actions_remain_observed_and_unverified() -> None:
    provider = YFinanceCorporateActionProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_action_quality_report(),
        client=StaticHistoryClient(),
        observed_at=lambda: OBSERVED_AT,
    )

    actions = await provider.get_actions(
        INSTRUMENT_ID,
        start=datetime(2024, 1, 1, tzinfo=UTC),
        end=datetime(2024, 1, 31, tzinfo=UTC),
        analysis_timestamp=OBSERVED_AT,
    )

    assert len(actions) == 1
    action = actions[0]
    assert action.action_type is CorporateActionType.CASH_DIVIDEND
    assert action.cash_amount == 1.66
    assert action.currency == "USD"
    assert action.available_at == OBSERVED_AT
    assert action.source == "yfinance"
    assert action.provider_quality_version == "yfinance-actions-observed-v1"
    assert (await provider.get_quality_report()).quality_status is DataQualityStatus.UNVERIFIED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fixture_name", "make_naive", "message"),
    [
        ("empty.json", False, "no bars"),
        ("malformed.json", False, "OHLCV"),
        ("daily_raw_success.json", True, "timezone-aware"),
        ("stale.json", False, "requested end"),
        ("partial.json", False, "requested start"),
    ],
)
async def test_yfinance_invalid_or_incomplete_history_fails_closed(
    fixture_name: str, make_naive: bool, message: str
) -> None:
    frame = _fixture_frame(fixture_name)
    if make_naive:
        frame.index = frame.index.tz_localize(None)

    class Client:
        async def history(
            self, symbol: str, *, start: datetime, end: datetime
        ) -> pd.DataFrame:
            return frame

    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=Client(),
        observed_at=lambda: OBSERVED_AT,
    )
    with pytest.raises(YFinanceProviderError, match=message):
        await provider.get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 8, 21, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fixture_name", "reason"),
    [("throttled.json", "rate_limited"), ("upstream_error.json", "network")],
)
async def test_yfinance_upstream_failure_is_typed_as_operational(
    fixture_name: str, reason: str
) -> None:
    error_fixture = json.loads((FIXTURES / fixture_name).read_text(encoding="utf-8"))

    class FailingTicker:
        def history(self, **kwargs: object) -> pd.DataFrame:
            if reason == "rate_limited":
                raise YFRateLimitError
            raise CurlConnectionError(error_fixture["error"])

    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=YFinanceLibraryClient(lambda symbol: FailingTicker()),
        observed_at=lambda: OBSERVED_AT,
    )
    with pytest.raises(MarketDataOperationalError) as error:
        await provider.get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 8, 21, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )
    assert error.value.reason.value == reason


@pytest.mark.asyncio
async def test_yfinance_unknown_library_failures_are_not_mislabeled_as_network() -> None:
    class BrokenTicker:
        def history(self, **kwargs: object) -> pd.DataFrame:
            raise RuntimeError("unexpected parser bug")

    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=YFinanceLibraryClient(lambda symbol: BrokenTicker()),
        observed_at=lambda: OBSERVED_AT,
    )

    with pytest.raises(RuntimeError, match="parser bug"):
        await provider.get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 8, 21, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )


@pytest.mark.asyncio
async def test_yfinance_terminal_http_4xx_does_not_trigger_operational_fallback() -> None:
    class Response:
        status_code = 404

    class MissingTicker:
        def history(self, **kwargs: object) -> pd.DataFrame:
            raise HTTPError("not found", response=Response())

    provider = YFinanceMarketDataProvider(
        instrument_resolver=StaticSymbolResolver(),
        quality_report=_quality_report(),
        client=YFinanceLibraryClient(lambda symbol: MissingTicker()),
        observed_at=lambda: OBSERVED_AT,
    )

    with pytest.raises(YFinanceProviderError, match="terminal HTTP"):
        await provider.get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 8, 21, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )


@pytest.mark.asyncio
async def test_yfinance_rejects_a_window_spanning_a_symbol_epoch() -> None:
    epoch = json.loads(
        (FIXTURES / "renamed_symbol_epoch.json").read_text(encoding="utf-8")
    )

    class RecentSymbolResolver:
        async def resolve_instrument(
            self, instrument_id: UUID, *, at: datetime
        ) -> ProviderInstrument:
            return ProviderInstrument(
                symbol=epoch["symbol"],
                currency="USD",
                valid_from=datetime.fromisoformat(epoch["valid_from"]),
            )

    provider = YFinanceMarketDataProvider(
        instrument_resolver=RecentSymbolResolver(),
        quality_report=_quality_report(),
        client=StaticHistoryClient(),
        observed_at=lambda: OBSERVED_AT,
    )
    with pytest.raises(YFinanceProviderError, match="symbol epoch"):
        await provider.get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 9, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )


@pytest.mark.asyncio
async def test_free_runtime_route_falls_back_offline_when_alpha_key_is_missing() -> None:
    class CountingHistoryClient(StaticHistoryClient):
        def __init__(self) -> None:
            self.calls = 0

        async def history(
            self, symbol: str, *, start: datetime, end: datetime
        ) -> pd.DataFrame:
            self.calls += 1
            return await super().history(symbol, start=start, end=end)

    class Repository:
        async def resolve_instrument_epoch(
            self,
            instrument_id: UUID,
            *,
            at: datetime,
            analysis_timestamp: datetime,
        ) -> tuple[Instrument, SymbolHistory] | None:
            return (
                Instrument(
                    instrument_id=instrument_id,
                    current_symbol="IBM",
                    exchange="XNYS",
                    currency="USD",
                    asset_type="equity",
                    company_name="Fixture Corp",
                ),
                SymbolHistory(
                    instrument_id=instrument_id,
                    symbol="IBM",
                    exchange="XNYS",
                    valid_from=datetime(2000, 1, 1, tzinfo=UTC),
                    available_at=datetime(2000, 1, 1, tzinfo=UTC),
                ),
            )

    client = CountingHistoryClient()
    loader = build_market_data_loader(
        Settings(alpha_vantage_api_key=None),
        instrument_resolver=SecurityMasterInstrumentResolver(Repository()),
        yfinance_client=client,
        observed_at=lambda: OBSERVED_AT,
    )

    bars = await loader.load_bars(
        MarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            start=datetime(2024, 1, 9, 21, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
            adjustment_mode=PriceAdjustmentMode.RAW,
        )
    )

    assert [bar.source for bar in bars] == ["yfinance", "yfinance"]
    assert client.calls == 1


@pytest.mark.asyncio
async def test_runtime_current_research_acquires_one_offline_yfinance_snapshot() -> None:
    class Repository:
        async def resolve_instrument_epoch(
            self,
            instrument_id: UUID,
            *,
            at: datetime,
            analysis_timestamp: datetime,
        ) -> tuple[Instrument, SymbolHistory] | None:
            return (
                Instrument(
                    instrument_id=instrument_id,
                    current_symbol="IBM",
                    exchange="XNYS",
                    currency="USD",
                    asset_type="equity",
                    company_name="Fixture Corp",
                ),
                SymbolHistory(
                    instrument_id=instrument_id,
                    symbol="IBM",
                    exchange="XNYS",
                    valid_from=datetime(2000, 1, 1, tzinfo=UTC),
                    available_at=datetime(2000, 1, 1, tzinfo=UTC),
                ),
            )

    class CountingHistoryClient(StaticHistoryClient):
        def __init__(self) -> None:
            self.calls = 0

        async def history(
            self, symbol: str, *, start: datetime, end: datetime
        ) -> pd.DataFrame:
            self.calls += 1
            return await super().history(symbol, start=start, end=end)

    client = CountingHistoryClient()
    loader = build_market_data_loader(
        Settings(alpha_vantage_api_key=None),
        instrument_resolver=SecurityMasterInstrumentResolver(Repository()),
        yfinance_client=client,
        observed_at=lambda: OBSERVED_AT,
    )

    assert isinstance(loader, CurrentMarketDataLoader)
    result = await loader.load_current_bars(
        CurrentMarketDataRequest(
            instrument_id=INSTRUMENT_ID,
            requested_at=OBSERVED_AT - timedelta(hours=1),
            lookback_days=2,
        )
    )

    assert [bar.source for bar in result.bars] == ["yfinance", "yfinance"]
    assert all(
        bar.data_quality_status is DataQualityStatus.UNVERIFIED
        for bar in result.bars
    )
    assert client.calls == 1
    assert isinstance(loader, RuntimeMarketDataLoader)
    assert loader.last_attempts[0].outcome is ProviderAttemptOutcome.SELECTED


@pytest.mark.asyncio
async def test_runtime_current_research_records_terminal_provider_failure() -> None:
    class Repository:
        async def resolve_instrument_epoch(
            self,
            instrument_id: UUID,
            *,
            at: datetime,
            analysis_timestamp: datetime,
        ) -> tuple[Instrument, SymbolHistory] | None:
            return (
                Instrument(
                    instrument_id=instrument_id,
                    current_symbol="IBM",
                    exchange="XNYS",
                    currency="USD",
                    asset_type="equity",
                    company_name="Fixture Corp",
                ),
                SymbolHistory(
                    instrument_id=instrument_id,
                    symbol="IBM",
                    exchange="XNYS",
                    valid_from=datetime(2000, 1, 1, tzinfo=UTC),
                    available_at=datetime(2000, 1, 1, tzinfo=UTC),
                ),
            )

    class RateLimitedHistoryClient:
        async def history(
            self, symbol: str, *, start: datetime, end: datetime
        ) -> pd.DataFrame:
            raise MarketDataOperationalError(
                "rate limited",
                reason=OperationalFailureReason.RATE_LIMITED,
            )

    loader = build_market_data_loader(
        Settings(alpha_vantage_api_key=None),
        instrument_resolver=SecurityMasterInstrumentResolver(Repository()),
        yfinance_client=RateLimitedHistoryClient(),
        observed_at=lambda: OBSERVED_AT,
    )

    assert isinstance(loader, RuntimeMarketDataLoader)
    with pytest.raises(MarketDataOperationalError):
        await loader.load_current_bars(
            CurrentMarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                requested_at=OBSERVED_AT - timedelta(hours=1),
                lookback_days=2,
            )
        )

    assert loader.last_attempts[0].outcome is (
        ProviderAttemptOutcome.TERMINAL_OPERATIONAL_FAILURE
    )
    assert loader.last_attempts[0].reason == OperationalFailureReason.RATE_LIMITED.value


@pytest.mark.asyncio
async def test_runtime_current_research_fails_closed_when_yfinance_is_not_configured() -> None:
    class Repository:
        async def resolve_instrument_epoch(
            self,
            instrument_id: UUID,
            *,
            at: datetime,
            analysis_timestamp: datetime,
        ) -> tuple[Instrument, SymbolHistory] | None:
            raise AssertionError("current acquisition must not resolve an instrument")

    loader = build_market_data_loader(
        Settings(
            alpha_vantage_api_key=None,
            market_data_provider_order=("alpha_vantage",),
        ),
        instrument_resolver=SecurityMasterInstrumentResolver(Repository()),
        yfinance_client=StaticHistoryClient(),
        observed_at=lambda: OBSERVED_AT,
    )

    assert isinstance(loader, CurrentMarketDataLoader)
    with pytest.raises(MarketDataOperationalError) as exc_info:
        await loader.load_current_bars(
            CurrentMarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                requested_at=OBSERVED_AT - timedelta(hours=1),
                lookback_days=2,
            )
        )

    assert exc_info.value.reason is OperationalFailureReason.UPSTREAM_UNAVAILABLE
