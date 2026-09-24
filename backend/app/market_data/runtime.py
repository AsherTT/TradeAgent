"""Production composition for the qualified free market-data route."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from backend.app.config import Settings
from backend.app.contracts.base import utc_now
from backend.app.contracts.evaluation import ProviderQualityReport
from backend.app.contracts.instrument import Instrument, SymbolHistory
from backend.app.contracts.market import MarketBar
from backend.app.market_data.alpha_vantage import (
    AlphaVantageCorporateActionProvider,
    AlphaVantageMarketDataProvider,
)
from backend.app.market_data.cache import (
    CachedMarketDataLoader,
    InMemoryQualifiedMarketDataCache,
    ProviderQualificationVersions,
)
from backend.app.market_data.errors import (
    MarketDataIntegrityError,
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.instrument import ProviderInstrument
from backend.app.market_data.service import (
    CurrentMarketDataRequest,
    CurrentMarketDataResult,
    FallbackMarketDataService,
    MarketDataAttemptSource,
    MarketDataCandidate,
    MarketDataFallbackPolicy,
    MarketDataLoader,
    MarketDataRequest,
    MarketDataService,
    ProviderAttempt,
    ProviderAttemptOutcome,
)
from backend.app.market_data.yfinance import (
    YFinanceCorporateActionProvider,
    YFinanceCurrentMarketDataLoader,
    YFinanceHistoryClient,
    YFinanceLibraryClient,
    YFinanceMarketDataProvider,
    YFinanceRequestSession,
)

_QUALITY_REPORTS = Path(__file__).parents[3] / "docs" / "provider_quality"


class InstrumentEpochRepository(Protocol):
    async def resolve_instrument_epoch(
        self,
        instrument_id: UUID,
        *,
        at: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[Instrument, SymbolHistory] | None: ...


class SecurityMasterInstrumentResolver:
    def __init__(self, repository: InstrumentEpochRepository) -> None:
        self._repository = repository

    async def resolve_instrument(
        self, instrument_id: UUID, *, at: datetime
    ) -> ProviderInstrument:
        resolved = await self._repository.resolve_instrument_epoch(
            instrument_id, at=at, analysis_timestamp=at
        )
        if resolved is None:
            raise MarketDataIntegrityError(
                f"no unambiguous point-in-time symbol epoch for instrument {instrument_id}"
            )
        instrument, epoch = resolved
        return ProviderInstrument(
            symbol=epoch.symbol,
            currency=instrument.currency,
            valid_from=epoch.valid_from,
            valid_to=epoch.valid_to,
        )


class RuntimeMarketDataLoader:
    """Expose fixed and current acquisition behind one worker-facing seam."""

    def __init__(
        self,
        *,
        fixed: MarketDataLoader,
        current: YFinanceCurrentMarketDataLoader | None,
    ) -> None:
        self._fixed = fixed
        self._current = current
        self._attempts: ContextVar[tuple[ProviderAttempt, ...]] = ContextVar(
            f"runtime_market_data_attempts_{id(self)}", default=()
        )

    @property
    def last_attempts(self) -> tuple[ProviderAttempt, ...]:
        return self._attempts.get()

    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        self._attempts.set(())
        try:
            return await self._fixed.load_bars(request)
        finally:
            self._attempts.set(
                self._fixed.last_attempts
                if isinstance(self._fixed, MarketDataAttemptSource)
                else ()
            )

    async def load_current_bars(
        self, request: CurrentMarketDataRequest
    ) -> CurrentMarketDataResult:
        self._attempts.set(())
        if self._current is None:
            raise MarketDataOperationalError(
                "current-research provider is not configured",
                reason=OperationalFailureReason.UPSTREAM_UNAVAILABLE,
            )
        try:
            result = await self._current.load_current_bars(request)
        except MarketDataOperationalError as exc:
            self._attempts.set(
                (
                    ProviderAttempt(
                        provider="yfinance",
                        outcome=ProviderAttemptOutcome.TERMINAL_OPERATIONAL_FAILURE,
                        reason=exc.reason.value,
                    ),
                )
            )
            raise
        except Exception as exc:
            self._attempts.set(
                (
                    ProviderAttempt(
                        provider="yfinance",
                        outcome=ProviderAttemptOutcome.INTEGRITY_FAILURE,
                        reason=type(exc).__name__,
                    ),
                )
            )
            raise
        self._attempts.set(
            (
                ProviderAttempt(
                    provider="yfinance",
                    outcome=ProviderAttemptOutcome.SELECTED,
                ),
            )
        )
        return result


def build_market_data_loader(
    settings: Settings,
    *,
    instrument_resolver: SecurityMasterInstrumentResolver,
    cache: InMemoryQualifiedMarketDataCache | None = None,
    yfinance_client: YFinanceHistoryClient | None = None,
    observed_at: Callable[[], datetime] = utc_now,
    quality_report_directory: Path = _QUALITY_REPORTS,
) -> MarketDataLoader:
    reports = {
        "alpha_vantage": (
            _load_report(quality_report_directory / "alpha_vantage_daily_raw_v1.json"),
            _load_report(
                quality_report_directory / "alpha_vantage_actions_observed_v1.json"
            ),
        ),
        "yfinance": (
            _load_report(quality_report_directory / "yfinance_daily_raw_v1.json"),
            _load_report(quality_report_directory / "yfinance_actions_observed_v1.json"),
        ),
    }
    unknown = set(settings.market_data_provider_order) - reports.keys()
    if unknown:
        raise ValueError(f"unknown market-data providers: {', '.join(sorted(unknown))}")
    if len(set(settings.market_data_provider_order)) != len(
        settings.market_data_provider_order
    ):
        raise ValueError("market-data provider order must not contain duplicates")
    try:
        configured_reasons = frozenset(
            OperationalFailureReason(reason)
            for reason in settings.market_data_fallback_reasons
        )
    except ValueError as exc:
        raise ValueError(f"unknown market-data fallback reason: {exc}") from exc
    fallback_policy = MarketDataFallbackPolicy(
        allowed_reasons=(
            configured_reasons
            if settings.market_data_fallback_enabled
            else frozenset()
        )
    )

    alpha_bars, alpha_actions = reports["alpha_vantage"]
    yahoo_bars, yahoo_actions = reports["yfinance"]
    yahoo_session = YFinanceRequestSession(
        yfinance_client or YFinanceLibraryClient()
    )
    services: dict[str, MarketDataService] = {
        "alpha_vantage": MarketDataService(
            market_data_provider=AlphaVantageMarketDataProvider(
                api_key=settings.alpha_vantage_api_key,
                instrument_resolver=instrument_resolver,
                quality_report=alpha_bars,
                observed_at=observed_at,
                base_url=settings.alpha_vantage_base_url,
            ),
            corporate_action_provider=AlphaVantageCorporateActionProvider(
                api_key=settings.alpha_vantage_api_key,
                instrument_resolver=instrument_resolver,
                quality_report=alpha_actions,
                observed_at=observed_at,
                base_url=settings.alpha_vantage_base_url,
            ),
        ),
        "yfinance": MarketDataService(
            market_data_provider=YFinanceMarketDataProvider(
                instrument_resolver=instrument_resolver,
                quality_report=yahoo_bars,
                client=yahoo_session,
                observed_at=observed_at,
            ),
            corporate_action_provider=YFinanceCorporateActionProvider(
                instrument_resolver=instrument_resolver,
                quality_report=yahoo_actions,
                client=yahoo_session,
                observed_at=observed_at,
            ),
            request_context=yahoo_session.acquire,
        ),
    }
    fallback = FallbackMarketDataService(
        tuple(
            MarketDataCandidate(provider, services[provider])
            for provider in settings.market_data_provider_order
        ),
        policy=fallback_policy,
    )
    fixed: MarketDataLoader = fallback
    if settings.market_data_cache_enabled:
        versions = {
            provider: ProviderQualificationVersions(
                bar_version=reports[provider][0].provider_version,
                action_version=reports[provider][1].provider_version,
            )
            for provider in settings.market_data_provider_order
        }
        fixed = CachedMarketDataLoader(
            loader=fallback,
            cache=cache
            or InMemoryQualifiedMarketDataCache(
                max_entries=settings.market_data_cache_max_entries
            ),
            provider_order=settings.market_data_provider_order,
            qualified_versions=versions,
        )
    current = (
        YFinanceCurrentMarketDataLoader(
            instrument_resolver=instrument_resolver,
            bar_quality_report=yahoo_bars,
            action_quality_report=yahoo_actions,
            client=yahoo_session,
            clock=observed_at,
        )
        if "yfinance" in settings.market_data_provider_order
        else None
    )
    return RuntimeMarketDataLoader(
        fixed=fixed,
        current=current,
    )


def _load_report(path: Path) -> ProviderQualityReport:
    return ProviderQualityReport.model_validate_json(path.read_text(encoding="utf-8"))
