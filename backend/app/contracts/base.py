"""Shared contract primitives."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


class ContractModel(BaseModel):
    """Strict immutable base for data crossing architectural boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, validate_assignment=True)


class IdentifiedContract(ContractModel):
    """Contract with an application-generated identifier."""

    id: UUID = Field(default_factory=uuid4)


class TemporalWindow(ContractModel):
    """A half-open validity interval."""

    valid_from: datetime
    valid_to: datetime | None = None

    @model_validator(mode="after")
    def validate_window(self) -> TemporalWindow:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be later than valid_from")
        return self
