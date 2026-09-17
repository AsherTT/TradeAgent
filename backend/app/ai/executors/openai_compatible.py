"""OpenAI-compatible HTTP executors for Qwen, DeepSeek, and OpenAI API."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

import httpx
from pydantic import BaseModel

from backend.app.ai.errors import ProviderUnavailableError
from backend.app.ai.executors.base import ModelExecutor
from backend.app.ai.structured_output import PydanticStructuredOutputAdapter
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
    ReasoningLevel,
)


class OpenAICompatibleExecutor(ModelExecutor):
    """Provider adapter using the OpenAI-compatible chat-completions contract."""

    capabilities = frozenset({Capability.STRUCTURED_OUTPUT, Capability.REASONING})

    def __init__(
        self,
        *,
        provider: ProviderName,
        model: str,
        api_key: str | None,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        if not self._api_key:
            raise ProviderUnavailableError(f"{self.provider.value} API key is not configured")

        started = perf_counter()
        adapter = PydanticStructuredOutputAdapter()
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": adapter.schema_instruction(request.output_schema),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"task": request.task, "context": request.context},
                        default=str,
                        separators=(",", ":"),
                    ),
                },
            ],
            "response_format": self._response_format(request.output_schema),
            **self._reasoning_payload(request.reasoning_level),
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=request.timeout_seconds,
        )
        try:
            response = await client.post(f"{self._base_url}/chat/completions", json=body)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderUnavailableError(f"{self.provider.value} request failed: {exc}") from exc
        finally:
            if owns_client:
                await client.aclose()

        try:
            raw_output = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailableError(
                f"{self.provider.value} response did not contain message content"
            ) from exc

        output = adapter.validate(raw_output, request.output_schema)
        usage = payload.get("usage", {})
        metadata = ExecutorMetadata(
            request_id=request.request_id,
            provider=self.provider,
            model=str(payload.get("model", self.model)),
            reasoning_level=request.reasoning_level,
            completed_at=utc_now(),
            latency_ms=(perf_counter() - started) * 1000,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            status="success",
        )
        return ModelResponse(output=output, metadata=metadata)

    def _reasoning_payload(self, level: ReasoningLevel) -> dict[str, str]:
        if level is ReasoningLevel.NONE:
            return {}
        mappings = {
            ReasoningLevel.MINIMAL: "minimal",
            ReasoningLevel.LOW: "low",
            ReasoningLevel.MEDIUM: "medium",
            ReasoningLevel.HIGH: "high",
            ReasoningLevel.XHIGH: "high",
            ReasoningLevel.MAX: "high",
            ReasoningLevel.ULTRA: "high",
        }
        return {"reasoning_effort": mappings[level]}

    @staticmethod
    def _response_format(schema: type[BaseModel]) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "strict": True,
                "schema": schema.model_json_schema(),
            },
        }


class QwenExecutor(OpenAICompatibleExecutor):
    profile = ModelCapabilityProfile(
        structured_output=True,
        tool_calling=True,
        reasoning=True,
        streaming=True,
        vision=True,
        context_length=1_000_000,
        max_output=131_072,
        latency_tier=LatencyTier.LOW,
        cost_tier=CostTier.LOW,
    )

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            provider=ProviderName.QWEN,
            model=model,
            api_key=api_key,
            base_url=base_url,
            client=client,
        )

    def _reasoning_payload(self, level: ReasoningLevel) -> dict[str, Any]:
        return {"extra_body": {"enable_thinking": level is not ReasoningLevel.NONE}}


class DeepSeekExecutor(OpenAICompatibleExecutor):
    profile = ModelCapabilityProfile(
        structured_output=True,
        tool_calling=True,
        reasoning=True,
        streaming=True,
        vision=False,
        context_length=1_000_000,
        max_output=393_216,
        latency_tier=LatencyTier.MEDIUM,
        cost_tier=CostTier.LOW,
    )

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            provider=ProviderName.DEEPSEEK,
            model=model,
            api_key=api_key,
            base_url=base_url,
            client=client,
        )

    @staticmethod
    def _response_format(schema: type[BaseModel]) -> dict[str, str]:
        return {"type": "json_object"}

class OpenAIAPIExecutor(OpenAICompatibleExecutor):
    profile = ModelCapabilityProfile(
        structured_output=True,
        tool_calling=False,
        reasoning=True,
        streaming=False,
        vision=False,
        context_length=128_000,
        max_output=16_384,
        latency_tier=LatencyTier.MEDIUM,
        cost_tier=CostTier.MEDIUM,
    )

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            provider=ProviderName.OPENAI,
            model=model,
            api_key=api_key,
            base_url=base_url,
            client=client,
        )
