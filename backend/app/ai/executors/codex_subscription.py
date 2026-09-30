"""ChatGPT subscription-backed Codex executor.

The official Python SDK controls a local Codex app-server. This adapter keeps
that SDK and its authentication/session behavior outside business nodes.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from functools import partial
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from backend.app.ai.errors import ProviderTimeoutError, ProviderUnavailableError
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

CodexRunner = Callable[[str, str | None, float, str], Awaitable[str]]


class CodexSubscriptionExecutor(ModelExecutor):
    provider = ProviderName.CODEX_SUBSCRIPTION
    capabilities = frozenset({Capability.STRUCTURED_OUTPUT, Capability.REASONING})
    profile = ModelCapabilityProfile(
        structured_output=True,
        tool_calling=True,
        reasoning=True,
        streaming=True,
        vision=True,
        context_length=1_050_000,
        max_output=131_072,
        latency_tier=LatencyTier.HIGH,
        cost_tier=CostTier.SUBSCRIPTION,
    )

    def __init__(
        self,
        *,
        model: str | None = None,
        runner: CodexRunner | None = None,
        proxy_url: str | None = None,
    ) -> None:
        self.model = model or "codex-account-default"
        self._configured_model = model
        self._runner = runner or partial(self._run_with_sdk, proxy_url=proxy_url)

    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        started = perf_counter()
        adapter = PydanticStructuredOutputAdapter()
        prompt = "\n\n".join(
            [
                (
                    "You are a reasoning executor inside a research system. "
                    "Do not modify files or call tools."
                ),
                adapter.schema_instruction(request.output_schema),
                f"Task: {request.task}",
                f"Context: {json.dumps(request.context, default=str, separators=(',', ':'))}",
            ]
        )
        raw_output = await self._runner(
            prompt,
            self._configured_model,
            request.timeout_seconds,
            self._map_reasoning(request.reasoning_level),
        )
        output = adapter.validate(raw_output, request.output_schema)
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

    @staticmethod
    def _map_reasoning(level: ReasoningLevel) -> str:
        mappings = {
            ReasoningLevel.NONE: "none",
            ReasoningLevel.MINIMAL: "minimal",
            ReasoningLevel.LOW: "low",
            ReasoningLevel.MEDIUM: "medium",
            ReasoningLevel.HIGH: "high",
            ReasoningLevel.XHIGH: "xhigh",
            ReasoningLevel.MAX: "xhigh",
            ReasoningLevel.ULTRA: "xhigh",
        }
        return mappings[level]

    @staticmethod
    async def _run_with_sdk(
        prompt: str,
        model: str | None,
        timeout_seconds: float,
        reasoning_effort: str,
        *,
        proxy_url: str | None = None,
    ) -> str:
        try:
            from openai_codex import AsyncCodex, Sandbox
        except ImportError as exc:
            raise ProviderUnavailableError(
                "openai-codex is not installed; install the 'codex' project extra"
            ) from exc

        try:
            sdk_options: dict[str, Any] = {}
            if proxy_url:
                from openai_codex import CodexConfig

                child_env = os.environ.copy()
                child_env["HTTPS_PROXY"] = child_env["HTTP_PROXY"] = proxy_url
                sdk_options["config"] = CodexConfig(env=child_env)
            async with asyncio.timeout(timeout_seconds):
                async with AsyncCodex(**sdk_options) as codex:
                    kwargs: dict[str, Any] = {
                        "sandbox": Sandbox.read_only,
                        "config": {"model_reasoning_effort": reasoning_effort},
                    }
                    if model:
                        kwargs["model"] = model
                    thread = await codex.thread_start(**kwargs)
                    result = await thread.run(prompt)
                    if result.status.value != "completed" or not isinstance(
                        result.final_response, str
                    ):
                        raise ProviderUnavailableError("Codex turn did not complete with text")
                    return result.final_response
        except TimeoutError as exc:
            raise ProviderTimeoutError("Codex app-server request timed out") from exc
        except Exception:
            raise ProviderUnavailableError("Codex app-server request failed") from None
