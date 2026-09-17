"""Multi-provider model gateway with bounded retry and fallback."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from backend.app.ai.errors import AllProvidersFailedError, ModelRuntimeError
from backend.app.ai.executors.base import ModelExecutor
from backend.app.ai.gateway.observability import (
    AttemptStatus,
    ExecutionAttempt,
    ExecutionTracer,
    UsageMeter,
)
from backend.app.ai.gateway.policy import CapabilityRegistry, TaskPolicy
from backend.app.contracts.base import utc_now
from backend.app.contracts.model import ModelRequest, ModelResponse, ProviderName


class ModelGateway:
    def __init__(
        self,
        executors: Iterable[ModelExecutor],
        *,
        task_policy: TaskPolicy | None = None,
        capability_registry: CapabilityRegistry | None = None,
        usage_meter: UsageMeter | None = None,
        tracer: ExecutionTracer | None = None,
        max_attempts_per_provider: int = 2,
        retry_backoff_seconds: float = 0,
    ) -> None:
        if max_attempts_per_provider < 1:
            raise ValueError("max_attempts_per_provider must be at least 1")
        self._executors = {executor.provider: executor for executor in executors}
        self._task_policy = task_policy or TaskPolicy()
        self._capabilities = capability_registry or CapabilityRegistry()
        self._usage_meter = usage_meter or UsageMeter()
        self._tracer = tracer or ExecutionTracer()
        self._max_attempts = max_attempts_per_provider
        self._retry_backoff_seconds = retry_backoff_seconds

    @property
    def usage_meter(self) -> UsageMeter:
        return self._usage_meter

    @property
    def tracer(self) -> ExecutionTracer:
        return self._tracer

    async def execute(
        self,
        request: ModelRequest[BaseModel],
        *,
        provider_order: tuple[ProviderName, ...] | None = None,
    ) -> ModelResponse[Any]:
        route = provider_order or self._task_policy.route(request)
        failures: dict[str, str] = {}
        prior_failure: str | None = None

        for provider in route:
            executor = self._executors.get(provider)
            if executor is None:
                failures[provider.value] = "executor is not registered"
                prior_failure = failures[provider.value]
                now = utc_now()
                self._tracer.record(
                    ExecutionAttempt(
                        request_id=request.request_id,
                        provider=provider,
                        attempt=0,
                        status=AttemptStatus.SKIPPED,
                        started_at=now,
                        completed_at=now,
                        latency_ms=0,
                        error=prior_failure,
                    )
                )
                continue
            try:
                self._capabilities.validate(executor, request)
            except ModelRuntimeError as exc:
                failures[provider.value] = str(exc)
                prior_failure = str(exc)
                now = utc_now()
                self._tracer.record(
                    ExecutionAttempt(
                        request_id=request.request_id,
                        provider=provider,
                        model=executor.model,
                        attempt=0,
                        status=AttemptStatus.SKIPPED,
                        started_at=now,
                        completed_at=now,
                        latency_ms=0,
                        error=prior_failure,
                    )
                )
                continue

            for attempt in range(self._max_attempts):
                started_at = utc_now()
                started = perf_counter()
                try:
                    response = await executor.execute(request)
                    metadata = response.metadata.model_copy(
                        update={
                            "retry_count": attempt,
                            "fallback_reason": prior_failure,
                        }
                    )
                    self._usage_meter.record(metadata)
                    self._tracer.record(
                        ExecutionAttempt(
                            request_id=request.request_id,
                            provider=provider,
                            model=executor.model,
                            attempt=attempt + 1,
                            status=AttemptStatus.SUCCEEDED,
                            started_at=started_at,
                            completed_at=utc_now(),
                            latency_ms=(perf_counter() - started) * 1000,
                            input_tokens=metadata.input_tokens,
                            output_tokens=metadata.output_tokens,
                        )
                    )
                    return response.model_copy(update={"metadata": metadata})
                except (ModelRuntimeError, TimeoutError, OSError) as exc:
                    failures[provider.value] = str(exc)
                    prior_failure = str(exc)
                    self._tracer.record(
                        ExecutionAttempt(
                            request_id=request.request_id,
                            provider=provider,
                            model=executor.model,
                            attempt=attempt + 1,
                            status=AttemptStatus.FAILED,
                            started_at=started_at,
                            completed_at=utc_now(),
                            latency_ms=(perf_counter() - started) * 1000,
                            error=prior_failure,
                        )
                    )
                    if attempt + 1 < self._max_attempts and self._retry_backoff_seconds:
                        await asyncio.sleep(self._retry_backoff_seconds * (attempt + 1))

        raise AllProvidersFailedError(failures)
