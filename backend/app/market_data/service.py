"""Orchestration behind the provider-neutral market-data seam."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar
from backend.app.market_data.errors import (
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.normalization import normalize_prices
from backend.app.market_data.providers import CorporateActionProvider, MarketDataProvider
from backend.app.market_data.quality import (
    require_report_matches_actions,
    require_report_matches_bars,
    require_strict_backtest_eligible,
    require_strict_bars_eligible,
    worse_quality,
)


class MarketDataRequest(ContractModel):
    instrument_id: UUID
    start: datetime
    end: datetime
    analysis_timestamp: datetime
    adjustment_mode: PriceAdjustmentMode
    strict_backtest: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> MarketDataRequest:
        if self.end < self.start:
            raise ValueError("end must not be earlier than start")
        if self.end > self.analysis_timestamp:
            raise ValueError("end must not be later than analysis_timestamp")
        return self


class CurrentMarketDataRequest(ContractModel):
    instrument_id: UUID
    requested_at: datetime
    lookback_days: int = Field(ge=1)


class CurrentMarketDataResult(ContractModel):
    bars: tuple[MarketBar, ...]


@runtime_checkable
class MarketDataLoader(Protocol):
    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]: ...


@runtime_checkable
class CurrentMarketDataLoader(Protocol):
    async def load_current_bars(
        self, request: CurrentMarketDataRequest
    ) -> CurrentMarketDataResult: ...


@dataclass(frozen=True)
class MarketDataCandidate:
    name: str
    loader: MarketDataLoader


class ProviderAttemptOutcome(StrEnum):
    OPERATIONAL_FAILURE = "operational_failure"
    TERMINAL_OPERATIONAL_FAILURE = "terminal_operational_failure"
    INTEGRITY_FAILURE = "integrity_failure"
    SELECTED = "selected"
    CACHE_HIT = "cache_hit"


class ProviderAttempt(ContractModel):
    provider: str = Field(min_length=1)
    outcome: ProviderAttemptOutcome
    reason: str | None = None

    @model_validator(mode="after")
    def validate_outcome_reason(self) -> ProviderAttempt:
        operational_outcomes = {
            ProviderAttemptOutcome.OPERATIONAL_FAILURE,
            ProviderAttemptOutcome.TERMINAL_OPERATIONAL_FAILURE,
        }
        terminal_successes = {
            ProviderAttemptOutcome.SELECTED,
            ProviderAttemptOutcome.CACHE_HIT,
        }
        if self.outcome in operational_outcomes:
            valid_reasons = {reason.value for reason in OperationalFailureReason}
            if self.reason not in valid_reasons:
                raise ValueError("operational attempts require a typed operational reason")
        elif self.outcome is ProviderAttemptOutcome.INTEGRITY_FAILURE:
            if not self.reason:
                raise ValueError("integrity failures require a reason")
        elif self.outcome in terminal_successes and self.reason is not None:
            raise ValueError("selected and cache-hit attempts cannot have a failure reason")
        return self


@runtime_checkable
class MarketDataAttemptSource(Protocol):
    @property
    def last_attempts(self) -> tuple[ProviderAttempt, ...]: ...


@dataclass(frozen=True)
class MarketDataFallbackPolicy:
    allowed_reasons: frozenset[OperationalFailureReason]

    def allows(self, reason: OperationalFailureReason) -> bool:
        return reason in self.allowed_reasons


class AllMarketDataProvidersUnavailable(MarketDataOperationalError):
    def __init__(self, attempts: tuple[ProviderAttempt, ...]) -> None:
        reason = attempts[-1].reason if attempts else None
        summary = ", ".join(
            f"{attempt.provider}({attempt.reason or attempt.outcome})"
            for attempt in attempts
        )
        super().__init__(
            f"all market-data providers were operationally unavailable: {summary}",
            reason=OperationalFailureReason(
                reason or OperationalFailureReason.UPSTREAM_UNAVAILABLE
            ),
        )
        self.attempts = attempts


_EMPTY_ATTEMPTS: tuple[ProviderAttempt, ...] = ()


class FallbackMarketDataService:
    """Try complete qualified loaders in order, but only after operational failures."""

    def __init__(
        self,
        candidates: tuple[MarketDataCandidate, ...],
        *,
        policy: MarketDataFallbackPolicy,
    ) -> None:
        if not candidates:
            raise ValueError("at least one market-data candidate is required")
        if len({candidate.name for candidate in candidates}) != len(candidates):
            raise ValueError("market-data candidate names must be unique")
        self._candidates = candidates
        self._policy = policy
        self._attempts: ContextVar[tuple[ProviderAttempt, ...]] = ContextVar(
            f"market_data_attempts_{id(self)}", default=_EMPTY_ATTEMPTS
        )

    @property
    def last_attempts(self) -> tuple[ProviderAttempt, ...]:
        return self._attempts.get()

    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        attempts: list[ProviderAttempt] = []
        self._attempts.set(())
        for candidate in self._candidates:
            try:
                bars = await candidate.loader.load_bars(request)
            except MarketDataOperationalError as exc:
                outcome = (
                    "operational_failure"
                    if self._policy.allows(exc.reason)
                    else "terminal_operational_failure"
                )
                attempts.append(
                    ProviderAttempt(
                        provider=candidate.name,
                        outcome=ProviderAttemptOutcome(outcome),
                        reason=exc.reason.value,
                    )
                )
                self._attempts.set(tuple(attempts))
                if not self._policy.allows(exc.reason):
                    raise
                continue
            except Exception as exc:
                attempts.append(
                    ProviderAttempt(
                        provider=candidate.name,
                        outcome=ProviderAttemptOutcome.INTEGRITY_FAILURE,
                        reason=type(exc).__name__,
                    )
                )
                self._attempts.set(tuple(attempts))
                raise
            attempts.append(
                ProviderAttempt(
                    provider=candidate.name,
                    outcome=ProviderAttemptOutcome.SELECTED,
                )
            )
            self._attempts.set(tuple(attempts))
            return bars
        raise AllMarketDataProvidersUnavailable(tuple(attempts))


class MarketDataService:
    def __init__(
        self,
        *,
        market_data_provider: MarketDataProvider,
        corporate_action_provider: CorporateActionProvider,
        request_context: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    ) -> None:
        self._market_data_provider = market_data_provider
        self._corporate_action_provider = corporate_action_provider
        self._request_context = request_context

    async def load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        if self._request_context is None:
            return await self._load_bars(request)
        async with self._request_context():
            return await self._load_bars(request)

    async def _load_bars(self, request: MarketDataRequest) -> tuple[MarketBar, ...]:
        quality_report = await self._market_data_provider.get_quality_report()
        action_quality_report = await self._corporate_action_provider.get_quality_report()
        if request.strict_backtest:
            require_strict_backtest_eligible(quality_report)
            require_strict_backtest_eligible(action_quality_report)
        bars = await self._market_data_provider.get_bars(
            request.instrument_id,
            start=request.start,
            end=request.analysis_timestamp,
            analysis_timestamp=request.analysis_timestamp,
        )
        require_report_matches_bars(quality_report, bars)
        actions = await self._corporate_action_provider.get_actions(
            request.instrument_id,
            start=request.start,
            end=request.analysis_timestamp,
            analysis_timestamp=request.analysis_timestamp,
        )
        require_report_matches_actions(action_quality_report, actions)
        qualified_bars = tuple(
            bar.model_copy(
                update={
                    "data_quality_status": worse_quality(
                        worse_quality(
                            bar.data_quality_status, quality_report.quality_status
                        ),
                        action_quality_report.quality_status,
                    ),
                }
            )
            for bar in bars
        )
        if request.strict_backtest:
            require_strict_bars_eligible(qualified_bars)
        normalized = normalize_prices(
            qualified_bars,
            actions,
            mode=request.adjustment_mode,
            analysis_timestamp=request.analysis_timestamp,
        )
        return tuple(bar for bar in normalized if bar.timestamp <= request.end)
