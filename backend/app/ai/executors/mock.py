"""Deterministic executor for tests and local development."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from backend.app.ai.executors.base import ModelExecutor
from backend.app.contracts.base import utc_now
from backend.app.contracts.model import (
    Capability,
    CostTier,
    ExecutorMetadata,
    LatencyTier,
    ModelCapabilityProfile,
    ModelRequest,
    ModelResponse,
    ProviderName,
)


class MockExecutor(ModelExecutor):
    provider = ProviderName.MOCK
    model = "deterministic-mock"
    capabilities = frozenset(Capability)
    profile = ModelCapabilityProfile(
        structured_output=True,
        tool_calling=True,
        reasoning=True,
        streaming=True,
        vision=True,
        context_length=1_000_000,
        max_output=1_000_000,
        latency_tier=LatencyTier.LOW,
        cost_tier=CostTier.LOW,
    )

    def __init__(self, output_factory: Callable[[ModelRequest[BaseModel]], Any]) -> None:
        self._output_factory = output_factory
        self.call_count = 0

    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        started = perf_counter()
        self.call_count += 1
        raw = self._output_factory(request)
        output = request.output_schema.model_validate(raw)
        metadata = ExecutorMetadata(
            request_id=request.request_id,
            provider=self.provider,
            model=self.model,
            reasoning_level=request.reasoning_level,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - started) * 1000,
            status="success",
        )
        return ModelResponse(output=output, metadata=metadata)
