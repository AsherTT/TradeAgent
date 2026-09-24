"""Alpha Vantage adapters behind the provider-neutral market-data boundary."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from backend.app.contracts.evaluation import DataQualityStatus, ProviderQualityReport
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.errors import (
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.instrument import (
    InstrumentMetadataResolver,
    ProviderInstrument,
)

ALPHA_VANTAGE_SOURCE = "alpha_vantage"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


class _ApiKeyRedactionFilter(logging.Filter):
    _pattern = re.compile(r"([?&]apikey=)[^&\s]+", flags=re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = self._pattern.sub(r"\1[REDACTED]", message)
        record.args = ()
        return True


_httpx_logger = logging.getLogger("httpx")
if not any(isinstance(item, _ApiKeyRedactionFilter) for item in _httpx_logger.filters):
    _httpx_logger.addFilter(_ApiKeyRedactionFilter())


class AlphaVantageProviderError(RuntimeError):
    """Raised when Alpha Vantage cannot provide a valid, unambiguous response."""


class AlphaVantageOperationalError(
    AlphaVantageProviderError, MarketDataOperationalError
):
    """Raised when Alpha Vantage is operationally unavailable for this request."""

    def __init__(self, message: str, *, reason: OperationalFailureReason) -> None:
        RuntimeError.__init__(self, message)
        self.reason = reason


class AlphaVantageMarketDataProvider:
    """Translate Alpha Vantage raw daily responses into strict market-bar contracts."""

    def __init__(
        self,
        *,
        api_key: str | None,
        instrument_resolver: InstrumentMetadataResolver,
        quality_report: ProviderQualityReport,
        client: httpx.AsyncClient | None = None,
        observed_at: Callable[[], datetime],
        base_url: str = ALPHA_VANTAGE_URL,
        outputsize: str = "compact",
    ) -> None:
        if quality_report.provider != ALPHA_VANTAGE_SOURCE:
            raise ValueError("quality report provider must be alpha_vantage")
        if outputsize not in {"compact", "full"}:
            raise ValueError("outputsize must be compact or full")
        self._api_key = api_key
        self._instrument_resolver = instrument_resolver
        self._quality_report = quality_report
        self._client = client
        self._observed_at = observed_at
        self._base_url = base_url
        self._outputsize = outputsize

    async def get_bars(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[MarketBar, ...]:
        if not self._api_key:
            raise AlphaVantageOperationalError(
                "Alpha Vantage API key is not configured",
                reason=OperationalFailureReason.MISSING_CREDENTIAL,
            )
        resolved = await self._instrument_resolver.resolve_instrument(
            instrument_id, at=analysis_timestamp
        )
        _require_single_symbol_epoch(resolved, start=start, end=end)
        symbol = resolved.symbol
        payload = await _request_json(
            client=self._client,
            base_url=self._base_url,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": self._outputsize,
                "datatype": "json",
                "apikey": self._api_key,
            },
        )
        bars = self._parse_daily_bars(payload, instrument_id=instrument_id, symbol=symbol)
        timezone = _provider_timezone(cast(str, payload["Meta Data"]["5. Time Zone"]))
        if _contains_weekday(
            start.date(), bars[0].timestamp.astimezone(timezone).date(), include_end=False
        ):
            raise AlphaVantageProviderError(
                "Alpha Vantage response does not cover the requested start; "
                "use outputsize=full or a shorter window"
            )
        requested_through = _completed_daily_date(end, timezone)
        if _contains_weekday(
            bars[-1].timestamp.astimezone(timezone).date() + timedelta(days=1),
            requested_through,
            include_end=True,
        ):
            raise AlphaVantageProviderError(
                "Alpha Vantage response does not cover the requested end"
            )
        return tuple(
            bar
            for bar in bars
            if start <= bar.timestamp <= end
            and bar.timestamp <= analysis_timestamp
            and bar.available_at <= analysis_timestamp
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report

    def _parse_daily_bars(
        self,
        payload: Mapping[str, Any],
        *,
        instrument_id: UUID,
        symbol: str,
    ) -> tuple[MarketBar, ...]:
        metadata = payload.get("Meta Data")
        series = payload.get("Time Series (Daily)")
        if not isinstance(metadata, Mapping) or not isinstance(series, Mapping):
            raise AlphaVantageProviderError(
                "Alpha Vantage daily response is missing metadata or time series"
            )
        response_symbol = metadata.get("2. Symbol")
        if response_symbol != symbol:
            raise AlphaVantageProviderError(
                f"Alpha Vantage response symbol {response_symbol!r} does not match {symbol!r}"
            )
        timezone_name = metadata.get("5. Time Zone")
        if not isinstance(timezone_name, str):
            raise AlphaVantageProviderError("Alpha Vantage response has no time zone")
        timezone = _provider_timezone(timezone_name)
        last_refreshed = metadata.get("3. Last Refreshed")
        if not isinstance(last_refreshed, str):
            raise AlphaVantageProviderError("Alpha Vantage response has no last-refreshed date")
        observed_at = self._observed_at()
        if observed_at.tzinfo is None:
            raise AlphaVantageProviderError("observed_at must be timezone-aware")

        try:
            bars = tuple(
                MarketBar(
                    instrument_id=instrument_id,
                    symbol=symbol,
                    timestamp=_daily_close_timestamp(day, timezone),
                    open=float(_required_string(values, "1. open")),
                    high=float(_required_string(values, "2. high")),
                    low=float(_required_string(values, "3. low")),
                    close=float(_required_string(values, "4. close")),
                    volume=float(_required_string(values, "5. volume")),
                    adjustment_mode=PriceAdjustmentMode.RAW,
                    adjustment_factor=1,
                    source=ALPHA_VANTAGE_SOURCE,
                    observed_at=observed_at.astimezone(UTC),
                    available_at=max(
                        _daily_close_timestamp(day, timezone), observed_at.astimezone(UTC)
                    ),
                    data_quality_status=self._quality_report.quality_status,
                    provider_quality_version=self._quality_report.provider_version,
                )
                for day, values in series.items()
                if isinstance(day, str) and isinstance(values, Mapping)
            )
        except (TypeError, ValueError) as exc:
            raise AlphaVantageProviderError(
                f"Alpha Vantage daily response contains an invalid bar: {exc}"
            ) from exc
        if len(bars) != len(series):
            raise AlphaVantageProviderError("Alpha Vantage daily response contains malformed rows")
        if not bars:
            raise AlphaVantageProviderError("Alpha Vantage daily response contains no bars")
        sorted_bars = tuple(sorted(bars, key=lambda bar: bar.timestamp))
        try:
            refreshed_date = date.fromisoformat(last_refreshed[:10])
        except ValueError as exc:
            raise AlphaVantageProviderError(
                "Alpha Vantage response has an invalid last-refreshed date"
            ) from exc
        if sorted_bars[-1].timestamp.astimezone(timezone).date() != refreshed_date:
            raise AlphaVantageProviderError(
                "Alpha Vantage time series does not reach its last-refreshed date"
            )
        return sorted_bars


class AlphaVantageCorporateActionProvider:
    """Map dividend and split feeds without overstating historical availability."""

    def __init__(
        self,
        *,
        api_key: str | None,
        instrument_resolver: InstrumentMetadataResolver,
        quality_report: ProviderQualityReport,
        client: httpx.AsyncClient | None = None,
        observed_at: Callable[[], datetime],
        base_url: str = ALPHA_VANTAGE_URL,
    ) -> None:
        if quality_report.provider != ALPHA_VANTAGE_SOURCE:
            raise ValueError("quality report provider must be alpha_vantage")
        if quality_report.quality_status is not DataQualityStatus.UNVERIFIED:
            raise ValueError(
                "Alpha Vantage corporate actions must remain unverified until "
                "historical publication timestamps are qualified"
            )
        self._api_key = api_key
        self._instrument_resolver = instrument_resolver
        self._quality_report = quality_report
        self._client = client
        self._observed_at = observed_at
        self._base_url = base_url

    async def get_actions(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[CorporateAction, ...]:
        if not self._api_key:
            raise AlphaVantageOperationalError(
                "Alpha Vantage API key is not configured",
                reason=OperationalFailureReason.MISSING_CREDENTIAL,
            )
        resolved = await self._instrument_resolver.resolve_instrument(
            instrument_id, at=analysis_timestamp
        )
        _require_single_symbol_epoch(resolved, start=start, end=end)
        observed_at = self._observed_at()
        if observed_at.tzinfo is None:
            raise AlphaVantageProviderError("observed_at must be timezone-aware")
        dividends = await self._request("DIVIDENDS", resolved.symbol)
        splits = await self._request("SPLITS", resolved.symbol)
        actions = (
            *self._parse_dividends(
                dividends,
                instrument_id=instrument_id,
                resolved=resolved,
                observed_at=observed_at.astimezone(UTC),
            ),
            *self._parse_splits(
                splits,
                instrument_id=instrument_id,
                symbol=resolved.symbol,
                observed_at=observed_at.astimezone(UTC),
            ),
        )
        return tuple(
            sorted(
                (
                    action
                    for action in actions
                    if start <= action.effective_at <= end
                    and action.available_at <= analysis_timestamp
                ),
                key=lambda action: (action.effective_at, action.action_id),
            )
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report

    async def _request(self, function: str, symbol: str) -> Mapping[str, Any]:
        payload = await _request_json(
            client=self._client,
            base_url=self._base_url,
            params={
                "function": function,
                "symbol": symbol,
                "datatype": "json",
                "apikey": cast(str, self._api_key),
            },
        )
        if payload.get("symbol") != symbol or not isinstance(payload.get("data"), list):
            raise AlphaVantageProviderError(
                f"Alpha Vantage {function} response has invalid symbol or data"
            )
        return payload

    def _parse_dividends(
        self,
        payload: Mapping[str, Any],
        *,
        instrument_id: UUID,
        resolved: ProviderInstrument,
        observed_at: datetime,
    ) -> tuple[CorporateAction, ...]:
        rows = _action_rows(payload)
        try:
            return tuple(
                CorporateAction(
                    action_id=_action_id(
                        instrument_id,
                        "dividend",
                        _required_string(row, "ex_dividend_date"),
                        _required_string(row, "amount"),
                    ),
                    instrument_id=instrument_id,
                    action_type=CorporateActionType.CASH_DIVIDEND,
                    announced_at=_midnight(_required_string(row, "declaration_date")),
                    ex_date=date.fromisoformat(_required_string(row, "ex_dividend_date")),
                    effective_at=_midnight(_required_string(row, "ex_dividend_date")),
                    available_at=max(
                        _midnight(_required_string(row, "declaration_date")),
                        observed_at,
                    ),
                    cash_amount=float(_required_string(row, "amount")),
                    currency=resolved.currency,
                    source=ALPHA_VANTAGE_SOURCE,
                    provider_quality_version=self._quality_report.provider_version,
                )
                for row in rows
            )
        except (TypeError, ValueError) as exc:
            raise AlphaVantageProviderError(
                f"Alpha Vantage dividend response contains an invalid action: {exc}"
            ) from exc

    def _parse_splits(
        self,
        payload: Mapping[str, Any],
        *,
        instrument_id: UUID,
        symbol: str,
        observed_at: datetime,
    ) -> tuple[CorporateAction, ...]:
        rows = _action_rows(payload)
        try:
            return tuple(
                CorporateAction(
                    action_id=_action_id(
                        instrument_id,
                        "split",
                        _required_string(row, "effective_date"),
                        _required_string(row, "split_factor"),
                    ),
                    instrument_id=instrument_id,
                    action_type=CorporateActionType.SPLIT,
                    effective_at=_midnight(_required_string(row, "effective_date")),
                    available_at=observed_at,
                    ratio=float(_required_string(row, "split_factor")),
                    source=ALPHA_VANTAGE_SOURCE,
                    provider_quality_version=self._quality_report.provider_version,
                )
                for row in rows
            )
        except (TypeError, ValueError) as exc:
            raise AlphaVantageProviderError(
                f"Alpha Vantage split response contains an invalid action: {exc}"
            ) from exc


def _provider_timezone(name: str) -> ZoneInfo:
    aliases = {"US/Eastern": "America/New_York"}
    try:
        return ZoneInfo(aliases.get(name, name))
    except ZoneInfoNotFoundError as exc:
        raise AlphaVantageProviderError(
            f"Alpha Vantage returned unsupported time zone {name!r}"
        ) from exc


async def _request_json(
    *,
    client: httpx.AsyncClient | None,
    base_url: str,
    params: dict[str, str],
) -> Mapping[str, Any]:
    owns_client = client is None
    request_client = client or httpx.AsyncClient(timeout=30)
    try:
        response = await request_client.get(base_url, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            reason = OperationalFailureReason.RATE_LIMITED
        elif status >= 500:
            reason = OperationalFailureReason.UPSTREAM_UNAVAILABLE
        elif status in {402, 403}:
            reason = OperationalFailureReason.FREE_ENTITLEMENT_UNAVAILABLE
        else:
            raise AlphaVantageProviderError(
                f"Alpha Vantage request failed with HTTP {status}"
            ) from None
        raise AlphaVantageOperationalError(
            f"Alpha Vantage request failed with HTTP {status}", reason=reason
        ) from None
    except httpx.RequestError:
        raise AlphaVantageOperationalError(
            "Alpha Vantage request failed due to a network error",
            reason=OperationalFailureReason.NETWORK,
        ) from None
    except ValueError as exc:
        raise AlphaVantageProviderError(f"Alpha Vantage request failed: {exc}") from exc
    finally:
        if owns_client:
            await request_client.aclose()
    if not isinstance(payload, Mapping):
        raise AlphaVantageProviderError("Alpha Vantage response must be a JSON object")
    error_message = payload.get("Error Message")
    if error_message:
        raise AlphaVantageProviderError("Alpha Vantage returned Error Message response")
    note = payload.get("Note")
    if note:
        reason = (
            OperationalFailureReason.QUOTA_EXHAUSTED
            if "frequency" in str(note).lower() or "limit" in str(note).lower()
            else OperationalFailureReason.RATE_LIMITED
        )
        raise AlphaVantageOperationalError(
            "Alpha Vantage returned Note response", reason=reason
        )
    information = payload.get("Information")
    if information:
        raise AlphaVantageOperationalError(
            "Alpha Vantage returned Information response",
            reason=OperationalFailureReason.FREE_ENTITLEMENT_UNAVAILABLE,
        )
    return cast(Mapping[str, Any], payload)


def _daily_close_timestamp(day: str, timezone: ZoneInfo) -> datetime:
    parsed = date.fromisoformat(day)
    return datetime.combine(parsed, time(16), tzinfo=timezone).astimezone(UTC)


def _required_field(values: Mapping[object, object], key: str) -> object:
    if key not in values:
        raise ValueError(f"missing {key}")
    return values[key]


def _required_string(values: Mapping[object, object], key: str) -> str:
    value = _required_field(values, key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _midnight(day: str) -> datetime:
    return datetime.combine(date.fromisoformat(day), time(), tzinfo=UTC)


def _action_id(instrument_id: UUID, action_type: str, day: str, value: str) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"alpha-vantage:{instrument_id}:{action_type}:{day}:{value}",
    )


def _action_rows(payload: Mapping[str, Any]) -> tuple[Mapping[object, object], ...]:
    rows = cast(list[object], payload["data"])
    if any(not isinstance(row, Mapping) for row in rows):
        raise AlphaVantageProviderError(
            "Alpha Vantage corporate-action response contains malformed rows"
        )
    return tuple(cast(Mapping[object, object], row) for row in rows)


def _require_single_symbol_epoch(
    resolved: ProviderInstrument, *, start: datetime, end: datetime
) -> None:
    if start < resolved.valid_from or (
        resolved.valid_to is not None and end >= resolved.valid_to
    ):
        raise AlphaVantageProviderError(
            "requested window spans time outside the resolved symbol epoch"
        )


def _completed_daily_date(end: datetime, timezone: ZoneInfo) -> date:
    local_end = end.astimezone(timezone)
    if local_end.time() < time(16):
        return local_end.date() - timedelta(days=1)
    return local_end.date()


def _contains_weekday(start: date, end: date, *, include_end: bool) -> bool:
    current = start
    boundary = end + timedelta(days=1) if include_end else end
    while current < boundary:
        if current.weekday() < 5:
            return True
        current += timedelta(days=1)
    return False
