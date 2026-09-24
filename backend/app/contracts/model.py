"""Provider-neutral model execution contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.app.contracts.base import ContractModel, utc_now


class ReasoningLevel(StrEnum):
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"
    ULTRA = "ultra"


class RuntimeProfile(StrEnum):
    PERSONAL_PREMIUM = "personal_premium"
    ECONOMY = "economy"
    CLOUD_API = "cloud_api"


class ProviderName(StrEnum):
    CODEX_SUBSCRIPTION = "codex_subscription"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    MOCK = "mock"


class Capability(StrEnum):
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_CALLING = "tool_calling"
    REASONING = "reasoning"
    STREAMING = "streaming"
    VISION = "vision"


class LatencyTier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostTier(StrEnum):
    SUBSCRIPTION = "subscription"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelCapabilityProfile(ContractModel):
    """Declared limits and runtime characteristics for one configured model."""

    structured_output: bool
    tool_calling: bool
    reasoning: bool
    streaming: bool
    vision: bool
    context_length: int = Field(gt=0)
    max_output: int = Field(gt=0)
    latency_tier: LatencyTier
    cost_tier: CostTier


class TaskKind(StrEnum):
    GENERIC = "generic"
    INTENT = "intent"
    CLASSIFICATION = "classification"
    NEWS_EXTRACTION = "news_extraction"
    RESEARCH_PLANNING = "research_planning"
    SYNTHESIS = "synthesis"


OutputT = TypeVar("OutputT", bound=BaseModel)


class ModelRequest(BaseModel, Generic[OutputT]):
    """Runtime request; output_schema is a trusted in-process type, not user data."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, arbitrary_types_allowed=True
    )

    request_id: UUID = Field(default_factory=uuid4)
    task: str = Field(min_length=1)
    task_kind: TaskKind = TaskKind.GENERIC
    context: dict[str, Any]
    output_schema: type[OutputT]
    reasoning_level: ReasoningLevel = ReasoningLevel.MEDIUM
    runtime_profile: RuntimeProfile = RuntimeProfile.PERSONAL_PREMIUM
    required_capabilities: frozenset[Capability] = frozenset({Capability.STRUCTURED_OUTPUT})
    timeout_seconds: float = Field(default=60, gt=0)


class ExecutorMetadata(ContractModel):
    execution_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    provider: ProviderName
    model: str
    reasoning_level: ReasoningLevel
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime
    latency_ms: float = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)
    fallback_reason: str | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    status: str


class ModelResponse(ContractModel, Generic[OutputT]):
    output: OutputT
    metadata: ExecutorMetadata
