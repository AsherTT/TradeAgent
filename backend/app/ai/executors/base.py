"""Executor interface implemented by every provider adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from backend.app.contracts.model import (
    Capability,
    ModelCapabilityProfile,
    ModelRequest,
    ModelResponse,
    ProviderName,
)


class ModelExecutor(ABC):
    provider: ProviderName
    model: str
    capabilities: frozenset[Capability]
    profile: ModelCapabilityProfile

    @abstractmethod
    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        """Execute and validate a provider-neutral model request."""
