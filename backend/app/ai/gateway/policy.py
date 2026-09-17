"""Provider-neutral routing and capability policy."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from backend.app.ai.errors import CapabilityError
from backend.app.ai.executors.base import ModelExecutor
from backend.app.contracts.model import (
    ModelRequest,
    ProviderName,
    RuntimeProfile,
    TaskKind,
)


class TaskPolicy:
    """Return an ordered provider route for a runtime profile and task."""

    _routes: ClassVar[dict[RuntimeProfile, tuple[ProviderName, ...]]] = {
        RuntimeProfile.PERSONAL_PREMIUM: (
            ProviderName.CODEX_SUBSCRIPTION,
            ProviderName.DEEPSEEK,
            ProviderName.QWEN,
            ProviderName.OPENAI,
        ),
        RuntimeProfile.ECONOMY: (ProviderName.QWEN, ProviderName.DEEPSEEK),
        RuntimeProfile.CLOUD_API: (
            ProviderName.OPENAI,
            ProviderName.QWEN,
            ProviderName.DEEPSEEK,
        ),
    }

    def route(self, request: ModelRequest[BaseModel]) -> tuple[ProviderName, ...]:
        route = self._routes[request.runtime_profile]
        cheap_task_kinds = {
            TaskKind.INTENT,
            TaskKind.CLASSIFICATION,
            TaskKind.NEWS_EXTRACTION,
        }
        if (
            request.runtime_profile is RuntimeProfile.PERSONAL_PREMIUM
            and request.task_kind in cheap_task_kinds
        ):
            return (ProviderName.QWEN, ProviderName.DEEPSEEK, ProviderName.CODEX_SUBSCRIPTION)
        return route


class CapabilityRegistry:
    @staticmethod
    def validate(executor: ModelExecutor, request: ModelRequest[BaseModel]) -> None:
        missing = request.required_capabilities - executor.capabilities
        if missing:
            values = ", ".join(sorted(capability.value for capability in missing))
            raise CapabilityError(
                f"{executor.provider.value} lacks required capabilities: {values}"
            )
