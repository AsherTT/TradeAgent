import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest

from backend.app.contracts.evaluation import ProviderQualityReport
from backend.app.contracts.instrument import CorporateActionType, PriceAdjustmentMode
from backend.app.market_data.alpha_vantage import (
    AlphaVantageCorporateActionProvider,
    AlphaVantageMarketDataProvider,
    AlphaVantageProviderError,
)
from backend.app.market_data.instrument import ProviderInstrument
from backend.app.market_data.providers import InMemoryCorporateActionProvider
from backend.app.market_data.service import MarketDataRequest, MarketDataService

FIXTURES = Path(__file__).parent / "fixtures" / "alpha_vantage"
QUALITY_REPORTS = Path(__file__).parents[2] / "docs" / "provider_quality"
INSTRUMENT_ID = uuid4()
OBSERVED_AT = datetime(2024, 1, 11, 12, tzinfo=UTC)
ACTION_OBSERVED_AT = datetime(2024, 4, 1, 12, tzinfo=UTC)


class StaticSymbolResolver:
    async def resolve_instrument(
        self, instrument_id: UUID, *, at: datetime
    ) -> ProviderInstrument:
        assert instrument_id == INSTRUMENT_ID
        assert at.tzinfo is not None
        return ProviderInstrument(
            symbol="IBM",
            currency="USD",
            valid_from=datetime(2000, 1, 1, tzinfo=UTC),
        )


def _quality_report() -> ProviderQualityReport:
    return ProviderQualityReport.model_validate_json(
        (QUALITY_REPORTS / "alpha_vantage_daily_raw_v1.json").read_text(encoding="utf-8")
    )


def _action_quality_report() -> ProviderQualityReport:
    return ProviderQualityReport.model_validate_json(
        (QUALITY_REPORTS / "alpha_vantage_actions_observed_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _daily_payload() -> dict[str, object]:
    return json.loads((FIXTURES / "daily_raw_success.json").read_text(encoding="utf-8"))


def _market_provider(
    client: httpx.AsyncClient,
    *,
    api_key: str | None = "offline-test-key",
    observed_at: datetime = OBSERVED_AT,
    report: ProviderQualityReport | None = None,
) -> AlphaVantageMarketDataProvider:
    return AlphaVantageMarketDataProvider(
        api_key=api_key,
        instrument_resolver=StaticSymbolResolver(),
        quality_report=report or _quality_report(),
        client=client,
        observed_at=lambda: observed_at,
    )


@pytest.mark.asyncio
async def test_alpha_vantage_daily_raw_response_becomes_point_in_time_market_bars() -> None:
    payload = _daily_payload()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["function"] == "TIME_SERIES_DAILY"
        assert request.url.params["symbol"] == "IBM"
        assert request.url.params["outputsize"] == "compact"
        assert request.url.params["apikey"] == "offline-test-key"
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AlphaVantageMarketDataProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_quality_report(),
            client=client,
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
    assert all(bar.source == "alpha_vantage" for bar in bars)
    assert all(bar.provider_quality_version == "alpha-vantage-daily-raw-v1" for bar in bars)
    assert all(bar.available_at == OBSERVED_AT for bar in bars)
    assert await provider.get_quality_report() == _quality_report()


@pytest.mark.asyncio
async def test_alpha_vantage_bars_integrate_through_market_data_service() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_daily_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        report = _quality_report()
        service = MarketDataService(
            market_data_provider=_market_provider(client, report=report),
            corporate_action_provider=InMemoryCorporateActionProvider(
                actions=(), quality_report=report
            ),
        )
        bars = await service.load_bars(
            MarketDataRequest(
                instrument_id=INSTRUMENT_ID,
                start=datetime(2024, 1, 9, 21, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=OBSERVED_AT,
                adjustment_mode=PriceAdjustmentMode.RAW,
                strict_backtest=True,
            )
        )

    assert [bar.close for bar in bars] == [160.08, 163.55]


@pytest.mark.asyncio
async def test_alpha_vantage_partial_compact_history_fails_closed() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_daily_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AlphaVantageProviderError, match="does not cover"):
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2020, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=OBSERVED_AT,
            )


@pytest.mark.asyncio
async def test_alpha_vantage_allows_a_window_starting_on_a_weekend() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_daily_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        bars = await _market_provider(client).get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 7, tzinfo=UTC),
            end=datetime(2024, 1, 10, 21, tzinfo=UTC),
            analysis_timestamp=OBSERVED_AT,
        )

    assert [bar.timestamp.day for bar in bars] == [8, 9, 10]


@pytest.mark.asyncio
async def test_alpha_vantage_excludes_bars_after_analysis_timestamp() -> None:
    payload = _daily_payload()
    series = payload["Time Series (Daily)"]
    assert isinstance(series, dict)
    series["2024-01-11"] = {
        "1. open": "164",
        "2. high": "165",
        "3. low": "163",
        "4. close": "164.5",
        "5. volume": "1000",
    }
    metadata = payload["Meta Data"]
    assert isinstance(metadata, dict)
    metadata["3. Last Refreshed"] = "2024-01-11"

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        bars = await _market_provider(client).get_bars(
            INSTRUMENT_ID,
            start=datetime(2024, 1, 8, 21, tzinfo=UTC),
            end=datetime(2024, 1, 11, 12, tzinfo=UTC),
            analysis_timestamp=datetime(2024, 1, 11, 12, tzinfo=UTC),
        )

    assert [bar.timestamp.day for bar in bars] == [8, 9, 10]


@pytest.mark.asyncio
async def test_alpha_vantage_rejects_a_right_truncated_daily_response() -> None:
    payload = _daily_payload()
    series = payload["Time Series (Daily)"]
    assert isinstance(series, dict)
    del series["2024-01-10"]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AlphaVantageProviderError, match="last-refreshed"):
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 8, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=OBSERVED_AT,
            )


@pytest.mark.asyncio
async def test_alpha_vantage_rejects_a_self_consistent_stale_response() -> None:
    payload = _daily_payload()
    series = payload["Time Series (Daily)"]
    metadata = payload["Meta Data"]
    assert isinstance(series, dict)
    assert isinstance(metadata, dict)
    del series["2024-01-10"]
    del series["2024-01-09"]
    metadata["3. Last Refreshed"] = "2024-01-08"

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AlphaVantageProviderError, match="requested end"):
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 8, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=OBSERVED_AT,
            )


@pytest.mark.asyncio
async def test_alpha_vantage_rejects_windows_spanning_a_symbol_epoch() -> None:
    class RecentSymbolResolver:
        async def resolve_instrument(
            self, instrument_id: UUID, *, at: datetime
        ) -> ProviderInstrument:
            return ProviderInstrument(
                symbol="IBM",
                currency="USD",
                valid_from=datetime(2024, 1, 10, tzinfo=UTC),
            )

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: None)) as client:
        provider = AlphaVantageMarketDataProvider(
            api_key="offline-test-key",
            instrument_resolver=RecentSymbolResolver(),
            quality_report=_quality_report(),
            client=client,
            observed_at=lambda: OBSERVED_AT,
        )
        with pytest.raises(AlphaVantageProviderError, match="symbol epoch"):
            await provider.get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 9, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=OBSERVED_AT,
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("error_key", ["Error Message", "Note", "Information"])
async def test_alpha_vantage_provider_messages_fail_closed(error_key: str) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={error_key: "request rejected"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AlphaVantageProviderError, match=error_key):
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=datetime(2024, 1, 10, 21, tzinfo=UTC),
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "JSON object"),
        ({}, "missing metadata"),
        (
            {
                "Meta Data": {"2. Symbol": "WRONG", "5. Time Zone": "US/Eastern"},
                "Time Series (Daily)": {},
            },
            "does not match",
        ),
        (
            {
                "Meta Data": {"2. Symbol": "IBM", "5. Time Zone": "Mars/Olympus"},
                "Time Series (Daily)": {},
            },
            "unsupported time zone",
        ),
        (
            {
                "Meta Data": {
                    "2. Symbol": "IBM",
                    "3. Last Refreshed": "2024-01-10",
                    "5. Time Zone": "US/Eastern",
                },
                "Time Series (Daily)": {
                    "2024-01-10": {"1. open": "1"},
                },
            },
            "invalid bar",
        ),
    ],
)
async def test_alpha_vantage_malformed_daily_responses_fail_closed(
    payload: object, message: str
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AlphaVantageProviderError, match=message):
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=datetime(2024, 1, 10, 21, tzinfo=UTC),
            )


@pytest.mark.asyncio
async def test_alpha_vantage_http_failure_and_missing_key_fail_closed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        caplog.set_level(logging.INFO, logger="httpx")
        with pytest.raises(AlphaVantageProviderError, match="request failed") as exc_info:
            await _market_provider(client).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=datetime(2024, 1, 10, 21, tzinfo=UTC),
            )
        assert "offline-test-key" not in str(exc_info.value)
        assert "offline-test-key" not in caplog.text
        with pytest.raises(AlphaVantageProviderError, match="not configured"):
            await _market_provider(client, api_key=None).get_bars(
                INSTRUMENT_ID,
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 10, 21, tzinfo=UTC),
                analysis_timestamp=datetime(2024, 1, 10, 21, tzinfo=UTC),
            )


def test_alpha_vantage_provider_configuration_fails_closed() -> None:
    with pytest.raises(ValueError, match="provider must be"):
        AlphaVantageMarketDataProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_quality_report().model_copy(update={"provider": "other"}),
            observed_at=lambda: OBSERVED_AT,
        )
    with pytest.raises(ValueError, match="outputsize"):
        AlphaVantageMarketDataProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_quality_report(),
            observed_at=lambda: OBSERVED_AT,
            outputsize="unbounded",
        )
    with pytest.raises(ValueError, match="must remain unverified"):
        AlphaVantageCorporateActionProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_quality_report(),
            observed_at=lambda: ACTION_OBSERVED_AT,
        )


@pytest.mark.asyncio
async def test_alpha_vantage_actions_preserve_declared_and_observed_availability() -> None:
    dividends = json.loads((FIXTURES / "dividends_success.json").read_text(encoding="utf-8"))
    splits = json.loads((FIXTURES / "splits_success.json").read_text(encoding="utf-8"))

    async def handler(request: httpx.Request) -> httpx.Response:
        function = request.url.params["function"]
        payload = dividends if function == "DIVIDENDS" else splits
        return httpx.Response(200, json=payload)

    report = _action_quality_report()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AlphaVantageCorporateActionProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=report,
            client=client,
            observed_at=lambda: ACTION_OBSERVED_AT,
        )
        actions = await provider.get_actions(
            INSTRUMENT_ID,
            start=datetime(2021, 1, 1, tzinfo=UTC),
            end=datetime(2024, 12, 31, tzinfo=UTC),
            analysis_timestamp=datetime(2024, 4, 2, tzinfo=UTC),
        )

    assert len(actions) == 2
    split, dividend = actions
    assert split.action_type is CorporateActionType.SPLIT
    assert split.effective_at == datetime(2021, 11, 4, tzinfo=UTC)
    assert split.available_at == ACTION_OBSERVED_AT
    assert split.ratio == 1.046
    assert dividend.action_type is CorporateActionType.CASH_DIVIDEND
    assert dividend.announced_at == datetime(2024, 1, 30, tzinfo=UTC)
    assert dividend.effective_at == datetime(2024, 2, 8, tzinfo=UTC)
    assert dividend.available_at == ACTION_OBSERVED_AT
    assert dividend.cash_amount == 1.66
    assert dividend.currency == "USD"
    assert dividend.provider_quality_version == "alpha-vantage-actions-observed-v1"
    assert await provider.get_quality_report() == report


@pytest.mark.asyncio
async def test_alpha_vantage_actions_exclude_events_not_known_at_analysis_time() -> None:
    dividends = json.loads((FIXTURES / "dividends_success.json").read_text(encoding="utf-8"))
    splits = json.loads((FIXTURES / "splits_success.json").read_text(encoding="utf-8"))

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=dividends if request.url.params["function"] == "DIVIDENDS" else splits,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AlphaVantageCorporateActionProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_action_quality_report(),
            client=client,
            observed_at=lambda: ACTION_OBSERVED_AT,
        )
        actions = await provider.get_actions(
            INSTRUMENT_ID,
            start=datetime(2021, 1, 1, tzinfo=UTC),
            end=datetime(2024, 12, 31, tzinfo=UTC),
            analysis_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )

    assert actions == ()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("bad_payload", "message"),
    [
        ({"Note": "throttled"}, "returned Note"),
        ({"symbol": "WRONG", "data": []}, "invalid symbol or data"),
        ({"symbol": "IBM", "data": ["not-an-object"]}, "malformed rows"),
        (
            {"symbol": "IBM", "data": [{"ex_dividend_date": "2024-02-08"}]},
            "invalid action",
        ),
    ],
)
async def test_alpha_vantage_action_errors_fail_closed(
    bad_payload: dict[str, object], message: str
) -> None:
    splits = json.loads((FIXTURES / "splits_success.json").read_text(encoding="utf-8"))

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=bad_payload
            if request.url.params["function"] == "DIVIDENDS"
            else splits,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AlphaVantageCorporateActionProvider(
            api_key="offline-test-key",
            instrument_resolver=StaticSymbolResolver(),
            quality_report=_action_quality_report(),
            client=client,
            observed_at=lambda: ACTION_OBSERVED_AT,
        )
        with pytest.raises(AlphaVantageProviderError, match=message):
            await provider.get_actions(
                INSTRUMENT_ID,
                start=datetime(2021, 1, 1, tzinfo=UTC),
                end=datetime(2024, 12, 31, tzinfo=UTC),
                analysis_timestamp=datetime(2024, 4, 1, tzinfo=UTC),
            )
