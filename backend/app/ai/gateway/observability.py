"""In-memory usage accounting and attempt-level execution tracing."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from backend.app.contracts.base import ContractModel
from backend.app.contracts.model import ExecutorMetadata, ProviderName


class AttemptStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionAttempt(ContractModel):
    request_id: UUID
    provider: ProviderName
    model: str | None = None
    attempt: int = Field(ge=0)
    status: AttemptStatus
    started_at: datetime
    completed_at: datetime
    latency_ms: float = Field(ge=0)
    error: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class UsageSnapshot(ContractModel):
    executions: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)


class UsageMeter:
    """Aggregate successful executor metadata without coupling business nodes to providers."""

    def __init__(self) -> None:
        self._executions: list[ExecutorMetadata] = []

    def record(self, metadata: ExecutorMetadata) -> None:
        self._executions.append(metadata)

    @property
    def executions(self) -> tuple[ExecutorMetadata, ...]:
        return tuple(self._executions)

    def snapshot(self) -> UsageSnapshot:
        return UsageSnapshot(
            executions=len(self._executions),
            input_tokens=sum(item.input_tokens or 0 for item in self._executions),
            output_tokens=sum(item.output_tokens or 0 for item in self._executions),
            estimated_cost_usd=sum(item.estimated_cost_usd or 0 for item in self._executions),
        )


class ExecutionTracer:
    """Retain every provider decision and attempt for audit and diagnostics."""

    def __init__(self) -> None:
        self._attempts: list[ExecutionAttempt] = []

    def record(self, attempt: ExecutionAttempt) -> None:
        self._attempts.append(attempt)

    @property
    def attempts(self) -> tuple[ExecutionAttempt, ...]:
        return tuple(self._attempts)

    def for_request(self, request_id: UUID) -> tuple[ExecutionAttempt, ...]:
        return tuple(item for item in self._attempts if item.request_id == request_id)
