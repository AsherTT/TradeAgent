"""Thesis, forecast, and outcome contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from backend.app.contracts.base import ContractModel


class Direction(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class ThesisStatus(StrEnum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    INVALIDATED = "invalidated"
    SUPERSEDED = "superseded"


class Thesis(ContractModel):
    thesis_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    analysis_timestamp: datetime
    horizon: str
    direction: Direction
    direction_probability: float = Field(ge=0, le=1)
    summary: str
    bull_case: str
    bear_case: str
    invalidation_conditions: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)
    evidence_ids: tuple[UUID, ...]
    status: ThesisStatus = ThesisStatus.CREATED


class ThesisRevision(ContractModel):
    thesis: Thesis
    version: int = Field(ge=1)
    research_run_id: UUID
    recorded_at: datetime


class ThesisTransition(ContractModel):
    thesis_id: UUID
    from_version: int | None = None
    to_version: int = Field(ge=1)
    from_status: ThesisStatus | None = None
    to_status: ThesisStatus
    recorded_at: datetime


class ForecastRecord(ContractModel):
    forecast_id: UUID = Field(default_factory=uuid4)
    research_run_id: UUID
    instrument_id: UUID
    created_at: datetime
    analysis_timestamp: datetime
    horizon: str
    direction: Direction
    probability: float = Field(ge=0, le=1)
    benchmark_id: UUID | None = None
    thesis_id: UUID
    thesis_version: int = Field(ge=1)
    model_execution_ids: tuple[UUID, ...]
    evidence_ids: tuple[UUID, ...]
    supersedes_forecast_id: UUID | None = None
    frozen: Literal[True] = True


class OutcomeRecord(ContractModel):
    forecast_id: UUID
    actual_return: float
    benchmark_return: float
    excess_return: float
    direction_correct: bool
    mfe: float
    mae: float
    invalidation_hit: bool
    evaluated_at: datetime
