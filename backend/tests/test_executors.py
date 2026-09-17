import asyncio
import json
from typing import Any

import httpx

from backend.app.ai.executors.codex_subscription import CodexSubscriptionExecutor
from backend.app.ai.executors.openai_compatible import DeepSeekExecutor, QwenExecutor
from backend.app.contracts.model import ModelRequest, ProviderName
from backend.app.contracts.research import ResearchPlan


def test_openai_compatible_executor_validates_response(
    research_plan_payload: dict[str, Any],
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["response_format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json={
                "model": "qwen-fixture",
                "choices": [{"message": {"content": json.dumps(research_plan_payload)}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    executor = QwenExecutor(
        model="qwen-fixture",
        api_key="test-only",
        base_url="https://provider.invalid/v1",
        client=client,
    )
    request = ModelRequest[ResearchPlan](
        task="Create a plan",
        context={"ticker": "KLAC"},
        output_schema=ResearchPlan,
    )
    response = asyncio.run(executor.execute(request))
    asyncio.run(client.aclose())

    assert response.output.instrument_symbol == "KLAC"
    assert response.metadata.provider is ProviderName.QWEN
    assert response.metadata.input_tokens == 10


def test_codex_executor_uses_injected_runner(
    research_plan_payload: dict[str, Any],
) -> None:
    async def runner(
        prompt: str, model: str | None, timeout_seconds: float, reasoning_effort: str
    ) -> str:
        assert "Do not modify files or call tools" in prompt
        assert model == "codex-fixture"
        assert timeout_seconds == 60
        assert reasoning_effort == "medium"
        return json.dumps(research_plan_payload)

    executor = CodexSubscriptionExecutor(model="codex-fixture", runner=runner)
    request = ModelRequest[ResearchPlan](
        task="Create a plan",
        context={"ticker": "KLAC"},
        output_schema=ResearchPlan,
    )
    response = asyncio.run(executor.execute(request))

    assert response.output.instrument_symbol == "KLAC"
    assert response.metadata.provider is ProviderName.CODEX_SUBSCRIPTION


def test_gate_a_adapters_return_same_research_plan(
    research_plan_payload: dict[str, Any],
) -> None:
    async def codex_runner(
        prompt: str, model: str | None, timeout_seconds: float, reasoning_effort: str
    ) -> str:
        return json.dumps(research_plan_payload)

    async def provider_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "fixture",
                "choices": [{"message": {"content": json.dumps(research_plan_payload)}}],
                "usage": {},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(provider_handler))
    request = ModelRequest[ResearchPlan](
        task="Create the same research plan",
        context={"ticker": "KLAC", "horizon": "3-5 days"},
        output_schema=ResearchPlan,
    )
    executors = (
        CodexSubscriptionExecutor(model="fixture", runner=codex_runner),
        QwenExecutor(
            model="fixture",
            api_key="test-only",
            base_url="https://qwen.invalid/v1",
            client=client,
        ),
        DeepSeekExecutor(
            model="fixture",
            api_key="test-only",
            base_url="https://deepseek.invalid/v1",
            client=client,
        ),
    )

    outputs = asyncio.run(_execute_all(executors, request))
    asyncio.run(client.aclose())

    assert outputs[0] == outputs[1] == outputs[2]
    assert all(isinstance(output, ResearchPlan) for output in outputs)


async def _execute_all(
    executors: tuple[CodexSubscriptionExecutor, QwenExecutor, DeepSeekExecutor],
    request: ModelRequest[ResearchPlan],
) -> tuple[ResearchPlan, ...]:
    responses = [await executor.execute(request) for executor in executors]
    return tuple(response.output for response in responses)
