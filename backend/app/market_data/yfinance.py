"""yfinance adapters for personal, non-strict research workflows."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pandas as pd
from curl_cffi.requests.exceptions import (
    ConnectionError as CurlConnectionError,
)
from curl_cffi.requests.exceptions import (
    DNSError,
    HTTPError,
    ProxyError,
    RequestException,
    Timeout,
)
from yfinance.exceptions import YFException, YFRateLimitError

from backend.app.contracts.evaluation import ProviderQualityReport
from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    PriceAdjustmentMode,
)
from backend.app.contracts.market import MarketBar
from backend.app.market_data.errors import (
    MarketDataIntegrityError,
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.instrument import InstrumentMetadataResolver
from backend.app.market_data.normalization import normalize_prices
from backend.app.market_data.quality import worse_quality
from backend.app.market_data.service import CurrentMarketDataRequest, CurrentMarketDataResult

YFINANCE_SOURCE = "yfinance"


class YFinanceHistoryClient(Protocol):
    async def history(
        self, symbol: str, *, start: datetime, end: datetime
    ) -> pd.DataFrame: ...


class YFinanceLibraryClient:
    """Run the synchronous yfinance library behind an asynchronous port."""

    def __init__(self, ticker_factory: Callable[[str], Any] | None = None) -> None:
        self._ticker_factory = ticker_factory

    async def history(
        self, symbol: str, *, start: datetime, end: datetime
    ) -> pd.DataFrame:
        return await asyncio.to_thread(self._history, symbol, start, end)

    def _history(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        factory = self._ticker_factory
        if factory is None:
            import yfinance as yf

            factory = yf.Ticker
        try:
            result = factory(symbol).history(
                start=start.date().isoformat(),
                end=(end.date() + timedelta(days=1)).isoformat(),
                interval="1d",
                auto_adjust=False,
                back_adjust=False,
                repair=False,
                actions=True,
                raise_errors=True,
            )
        except YFRateLimitError as exc:
            raise MarketDataOperationalError(
                f"yfinance request failed: {exc}",
                reason=OperationalFailureReason.RATE_LIMITED,
            ) from exc
        except (CurlConnectionError, DNSError, ProxyError, Timeout, TimeoutError) as exc:
            raise MarketDataOperationalError(
                f"yfinance request failed: {exc}",
                reason=OperationalFailureReason.NETWORK,
            ) from exc
        except HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                raise MarketDataOperationalError(
                    f"yfinance request failed: {exc}",
                    reason=OperationalFailureReason.RATE_LIMITED,
                ) from exc
            if isinstance(status, int) and status >= 500:
                raise MarketDataOperationalError(
                    f"yfinance request failed: {exc}",
                    reason=OperationalFailureReason.UPSTREAM_UNAVAILABLE,
                ) from exc
            raise YFinanceProviderError(
                f"yfinance returned a terminal HTTP failure: {exc}"
            ) from exc
        except RequestException as exc:
            raise YFinanceProviderError(
                f"yfinance returned an unclassified request failure: {exc}"
            ) from exc
        except YFException as exc:
            raise YFinanceProviderError(f"yfinance rejected the request: {exc}") from exc
        if not isinstance(result, pd.DataFrame):
            raise YFinanceProviderError("yfinance history did not return a DataFrame")
        return result


class YFinanceRequestSession:
    """Share one exact history snapshot only inside one market-data request."""

    def __init__(self, client: YFinanceHistoryClient) -> None:
        self._client = client
        self._frames: ContextVar[
            dict[tuple[str, datetime, datetime], pd.DataFrame] | None
        ] = ContextVar(f"yfinance_request_frames_{id(self)}", default=None)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        token = self._frames.set({})
        try:
            yield
        finally:
            self._frames.reset(token)

    async def history(
        self, symbol: str, *, start: datetime, end: datetime
    ) -> pd.DataFrame:
        frames = self._frames.get()
        if frames is None:
            return await self._client.history(symbol, start=start, end=end)
        key = (symbol, start, end)
        frame = frames.get(key)
        if frame is None:
            frame = await self._client.history(symbol, start=start, end=end)
            frames[key] = frame
        return frame


class YFinanceCurrentMarketDataLoader:
    """Acquire and qualify one current yfinance snapshot without a pre-frozen cutoff."""

    def __init__(
        self,
        *,
        instrument_resolver: InstrumentMetadataResolver,
        bar_quality_report: ProviderQualityReport,
        action_quality_report: ProviderQualityReport,
        client: YFinanceHistoryClient,
        clock: Callable[[], datetime],
    ) -> None:
        if bar_quality_report.provider != YFINANCE_SOURCE:
            raise ValueError("bar quality report provider must be yfinance")
        if action_quality_report.provider != YFINANCE_SOURCE:
            raise ValueError("action quality report provider must be yfinance")
        if action_quality_report.quality_status.value != "unverified":
            raise ValueError("yfinance current actions must remain unverified")
        self._instrument_resolver = instrument_resolver
        self._bar_quality_report = bar_quality_report
        self._action_quality_report = action_quality_report
        self._client = client
        self._clock = clock

    async def load_current_bars(
        self, request: CurrentMarketDataRequest
    ) -> CurrentMarketDataResult:
        acquisition_started_at = self._clock()
        if acquisition_started_at.tzinfo is None:
            raise YFinanceProviderError("acquisition clock must be timezone-aware")
        acquisition_started_at = acquisition_started_at.astimezone(UTC)
        if acquisition_started_at < request.requested_at:
            raise YFinanceProviderError("acquisition cannot start before requested_at")
        start = acquisition_started_at - timedelta(days=request.lookback_days)
        resolved = await self._instrument_resolver.resolve_instrument(
            request.instrument_id, at=acquisition_started_at
        )
        _require_single_symbol_epoch(
            valid_from=resolved.valid_from,
            valid_to=resolved.valid_to,
            start=start,
            end=acquisition_started_at,
        )
        frame = await self._client.history(
            resolved.symbol, start=start, end=acquisition_started_at
        )
        observed_at = self._clock()
        if observed_at.tzinfo is None:
            raise YFinanceProviderError("observed_at must be timezone-aware")
        observed_at = observed_at.astimezone(UTC)
        if observed_at < acquisition_started_at:
            raise YFinanceProviderError("observation cannot precede acquisition start")
        bars = _parse_bars(
            frame,
            instrument_id=request.instrument_id,
            symbol=resolved.symbol,
            observed_at=observed_at,
            quality_report=self._bar_quality_report,
        )
        actions = _parse_actions(
            frame,
            instrument_id=request.instrument_id,
            symbol=resolved.symbol,
            currency=resolved.currency,
            observed_at=observed_at,
            quality_report=self._action_quality_report,
        )
        _require_daily_coverage(frame, start=start, end=acquisition_started_at)
        qualified = tuple(
            bar.model_copy(
                update={
                    "data_quality_status": worse_quality(
                        worse_quality(
                            bar.data_quality_status,
                            self._bar_quality_report.quality_status,
                        ),
                        self._action_quality_report.quality_status,
                    )
                }
            )
            for bar in bars
        )
        normalized = normalize_prices(
            qualified,
            actions,
            mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            analysis_timestamp=observed_at,
        )
        return CurrentMarketDataResult(
            bars=tuple(
                bar
                for bar in normalized
                if start <= bar.timestamp <= acquisition_started_at
                and bar.available_at <= observed_at
            )
        )


class YFinanceProviderError(MarketDataIntegrityError):
    """Raised when yfinance returns invalid or ambiguous data."""


class YFinanceMarketDataProvider:
    def __init__(
        self,
        *,
        instrument_resolver: InstrumentMetadataResolver,
        quality_report: ProviderQualityReport,
        client: YFinanceHistoryClient,
        observed_at: Callable[[], datetime],
    ) -> None:
        if quality_report.provider != YFINANCE_SOURCE:
            raise ValueError("quality report provider must be yfinance")
        self._instrument_resolver = instrument_resolver
        self._quality_report = quality_report
        self._client = client
        self._observed_at = observed_at

    async def get_bars(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[MarketBar, ...]:
        resolved = await self._instrument_resolver.resolve_instrument(
            instrument_id, at=analysis_timestamp
        )
        _require_single_symbol_epoch(
            valid_from=resolved.valid_from,
            valid_to=resolved.valid_to,
            start=start,
            end=end,
        )
        try:
            frame = await self._client.history(resolved.symbol, start=start, end=end)
        except MarketDataOperationalError:
            raise
        observed_at = self._observed_at()
        if observed_at.tzinfo is None:
            raise YFinanceProviderError("observed_at must be timezone-aware")
        bars = _parse_bars(
            frame,
            instrument_id=instrument_id,
            symbol=resolved.symbol,
            observed_at=observed_at.astimezone(UTC),
            quality_report=self._quality_report,
        )
        timezone = cast(pd.DatetimeIndex, frame.index).tz
        if timezone is None:
            raise YFinanceProviderError("yfinance history has no time zone")
        first_date = cast(pd.DatetimeIndex, frame.index)[0].date()
        last_date = cast(pd.DatetimeIndex, frame.index)[-1].date()
        if _contains_weekday(
            start.astimezone(timezone).date(), first_date, include_end=False
        ):
            raise YFinanceProviderError("yfinance response does not cover the requested start")
        requested_through = _completed_daily_date(end, timezone)
        if _contains_weekday(
            last_date + timedelta(days=1),
            requested_through,
            include_end=True,
        ):
            raise YFinanceProviderError("yfinance response does not cover the requested end")
        return tuple(
            bar
            for bar in bars
            if start <= bar.timestamp <= end
            and bar.timestamp <= analysis_timestamp
            and bar.available_at <= analysis_timestamp
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report


class YFinanceCorporateActionProvider:
    def __init__(
        self,
        *,
        instrument_resolver: InstrumentMetadataResolver,
        quality_report: ProviderQualityReport,
        client: YFinanceHistoryClient,
        observed_at: Callable[[], datetime],
    ) -> None:
        if quality_report.provider != YFINANCE_SOURCE:
            raise ValueError("quality report provider must be yfinance")
        if quality_report.quality_status.value != "unverified":
            raise ValueError(
                "yfinance corporate actions must remain unverified until historical "
                "publication timestamps are qualified"
            )
        self._instrument_resolver = instrument_resolver
        self._quality_report = quality_report
        self._client = client
        self._observed_at = observed_at

    async def get_actions(
        self,
        instrument_id: UUID,
        *,
        start: datetime,
        end: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[CorporateAction, ...]:
        resolved = await self._instrument_resolver.resolve_instrument(
            instrument_id, at=analysis_timestamp
        )
        _require_single_symbol_epoch(
            valid_from=resolved.valid_from,
            valid_to=resolved.valid_to,
            start=start,
            end=end,
        )
        try:
            frame = await self._client.history(resolved.symbol, start=start, end=end)
        except MarketDataOperationalError:
            raise
        observed_at = self._observed_at()
        if observed_at.tzinfo is None:
            raise YFinanceProviderError("observed_at must be timezone-aware")
        actions = _parse_actions(
            frame,
            instrument_id=instrument_id,
            symbol=resolved.symbol,
            currency=resolved.currency,
            observed_at=observed_at.astimezone(UTC),
            quality_report=self._quality_report,
        )
        return tuple(
            action
            for action in actions
            if start <= action.effective_at <= end
            and action.available_at <= analysis_timestamp
        )

    async def get_quality_report(self) -> ProviderQualityReport:
        return self._quality_report


def _parse_bars(
    frame: pd.DataFrame,
    *,
    instrument_id: UUID,
    symbol: str,
    observed_at: datetime,
    quality_report: ProviderQualityReport,
) -> tuple[MarketBar, ...]:
    if frame.empty:
        raise YFinanceProviderError("yfinance response contains no bars")
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(frame.columns):
        raise YFinanceProviderError("yfinance response is missing required OHLCV columns")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise YFinanceProviderError("yfinance history index must be timezone-aware")
    try:
        bars = tuple(
            MarketBar(
                instrument_id=instrument_id,
                symbol=symbol,
                timestamp=_daily_timestamp(cast(pd.Timestamp, index)),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                adjustment_mode=PriceAdjustmentMode.RAW,
                adjustment_factor=1,
                source=YFINANCE_SOURCE,
                observed_at=observed_at,
                available_at=max(
                    _daily_timestamp(cast(pd.Timestamp, index)),
                    observed_at,
                ),
                data_quality_status=quality_report.quality_status,
                provider_quality_version=quality_report.provider_version,
            )
            for index, row in frame.iterrows()
        )
    except (TypeError, ValueError) as exc:
        raise YFinanceProviderError(f"yfinance response contains an invalid bar: {exc}") from exc
    return tuple(sorted(bars, key=lambda bar: bar.timestamp))


def _parse_actions(
    frame: pd.DataFrame,
    *,
    instrument_id: UUID,
    symbol: str,
    currency: str,
    observed_at: datetime,
    quality_report: ProviderQualityReport,
) -> tuple[CorporateAction, ...]:
    required = {"Dividends", "Stock Splits"}
    if not required.issubset(frame.columns):
        raise YFinanceProviderError("yfinance response is missing corporate-action columns")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise YFinanceProviderError("yfinance history index must be timezone-aware")
    actions: list[CorporateAction] = []
    try:
        for index, row in frame.iterrows():
            timestamp = cast(pd.Timestamp, index)
            effective_at = datetime.combine(
                timestamp.date(), time(), tzinfo=timestamp.tzinfo
            ).astimezone(UTC)
            dividend = float(row["Dividends"])
            split = float(row["Stock Splits"])
            if dividend < 0 or split < 0:
                raise ValueError("corporate-action values must not be negative")
            if dividend:
                actions.append(
                    CorporateAction(
                        action_id=_action_id(
                            instrument_id, "dividend", effective_at, dividend
                        ),
                        instrument_id=instrument_id,
                        action_type=CorporateActionType.CASH_DIVIDEND,
                        ex_date=timestamp.date(),
                        effective_at=effective_at,
                        available_at=observed_at,
                        cash_amount=dividend,
                        currency=currency,
                        source=YFINANCE_SOURCE,
                        provider_quality_version=quality_report.provider_version,
                    )
                )
            if split:
                actions.append(
                    CorporateAction(
                        action_id=_action_id(instrument_id, "split", effective_at, split),
                        instrument_id=instrument_id,
                        action_type=CorporateActionType.SPLIT,
                        effective_at=effective_at,
                        available_at=observed_at,
                        ratio=split,
                        source=YFINANCE_SOURCE,
                        provider_quality_version=quality_report.provider_version,
                    )
                )
    except (TypeError, ValueError) as exc:
        raise YFinanceProviderError(
            f"yfinance response contains an invalid corporate action: {exc}"
        ) from exc
    return tuple(sorted(actions, key=lambda action: (action.effective_at, action.action_id)))


def _daily_timestamp(index: pd.Timestamp) -> datetime:
    return datetime.combine(index.date(), time(16), tzinfo=index.tzinfo).astimezone(UTC)


def _require_daily_coverage(
    frame: pd.DataFrame, *, start: datetime, end: datetime
) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise YFinanceProviderError("yfinance history has no time zone")
    timezone = frame.index.tz
    first_date = frame.index[0].date()
    last_date = frame.index[-1].date()
    if _contains_weekday(start.astimezone(timezone).date(), first_date, include_end=False):
        raise YFinanceProviderError("yfinance response does not cover the requested start")
    requested_through = _completed_daily_date(end, timezone)
    if _contains_weekday(
        last_date + timedelta(days=1), requested_through, include_end=True
    ):
        raise YFinanceProviderError("yfinance response does not cover the requested end")


def _action_id(
    instrument_id: UUID, action_type: str, effective_at: datetime, value: float
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"yfinance:{instrument_id}:{action_type}:{effective_at.isoformat()}:{value}",
    )


def _require_single_symbol_epoch(
    *,
    valid_from: datetime,
    valid_to: datetime | None,
    start: datetime,
    end: datetime,
) -> None:
    if start < valid_from or (valid_to is not None and end >= valid_to):
        raise YFinanceProviderError(
            "requested window spans time outside the resolved symbol epoch"
        )


def _completed_daily_date(end: datetime, timezone: Any) -> date:
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
