import asyncio
from typing import Any

import pytest
from pydantic import BaseModel

from backend.app.ai.errors import AllProvidersFailedError, ProviderUnavailableError
from backend.app.ai.executors.base import ModelExecutor
from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import AttemptStatus, ModelGateway
from backend.app.contracts.model import (
    Capability,
    ModelRequest,
    ModelResponse,
    ProviderName,
)
from backend.app.contracts.research import ResearchPlan


class FailingExecutor(ModelExecutor):
    provider = ProviderName.CODEX_SUBSCRIPTION
    model = "failing"
    capabilities = frozenset({Capability.STRUCTURED_OUTPUT})

    def __init__(self) -> None:
        self.call_count = 0

    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        self.call_count += 1
        raise ProviderUnavailableError("temporary failure")


def test_gateway_falls_back_after_bounded_retries(
    research_plan_payload: dict[str, Any],
) -> None:
    failing = FailingExecutor()
    fallback = MockExecutor(lambda _: research_plan_payload)
    gateway = ModelGateway([failing, fallback], max_attempts_per_provider=2)
    request = ModelRequest[ResearchPlan](
        task="Create a research plan",
        context={"ticker": "KLAC"},
        output_schema=ResearchPlan,
    )

    response = asyncio.run(
        gateway.execute(
            request,
            provider_order=(ProviderName.CODEX_SUBSCRIPTION, ProviderName.MOCK),
        )
    )

    assert failing.call_count == 2
    assert fallback.call_count == 1
    assert response.output.instrument_symbol == "KLAC"
    assert response.metadata.provider is ProviderName.MOCK
    assert response.metadata.fallback_reason == "temporary failure"
    assert [item.status for item in gateway.tracer.attempts] == [
        AttemptStatus.FAILED,
        AttemptStatus.FAILED,
        AttemptStatus.SUCCEEDED,
    ]
    assert gateway.tracer.for_request(request.request_id) == gateway.tracer.attempts
    assert gateway.usage_meter.snapshot().executions == 1
    assert gateway.usage_meter.executions == (response.metadata,)


def test_gateway_reports_all_failures() -> None:
    gateway = ModelGateway([FailingExecutor()], max_attempts_per_provider=1)
    request = ModelRequest[ResearchPlan](
        task="Create a research plan",
        context={},
        output_schema=ResearchPlan,
    )
    with pytest.raises(AllProvidersFailedError, match="temporary failure"):
        asyncio.run(
            gateway.execute(
                request,
                provider_order=(ProviderName.CODEX_SUBSCRIPTION,),
            )
        )
    assert gateway.tracer.attempts[0].status is AttemptStatus.FAILED
    assert gateway.usage_meter.snapshot().executions == 0
