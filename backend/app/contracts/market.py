"""Market and deterministic-quant output contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel
from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.instrument import PriceAdjustmentMode


class MarketBar(ContractModel):
    instrument_id: UUID
    symbol: str
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    adjustment_mode: PriceAdjustmentMode
    adjustment_factor: float = Field(gt=0)
    source: str
    observed_at: datetime
    available_at: datetime
    data_quality_status: DataQualityStatus
    provider_quality_version: str

    @model_validator(mode="after")
    def validate_ohlc(self) -> MarketBar:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be the greatest OHLC value")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be the smallest OHLC value")
        return self


class MarketSnapshot(ContractModel):
    instrument_id: UUID
    analysis_timestamp: datetime
    latest_bar: MarketBar
    currency: str = Field(min_length=3, max_length=3)


class TechnicalSnapshot(ContractModel):
    instrument_id: UUID
    analysis_timestamp: datetime
    price_adjustment_mode: PriceAdjustmentMode
    feature_version: str
    indicators: dict[str, float | int | str | None] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarketAcquisitionSummary(ContractModel):
    """Provider acquisition metadata, without promoting bars to qualified evidence."""

    instrument_id: UUID
    analysis_timestamp: datetime
    first_bar_at: datetime
    latest_bar_at: datetime
    observed_at: datetime
    bar_count: int = Field(ge=1)
    source_names: tuple[str, ...] = Field(min_length=1, max_length=8)
    provider_quality_versions: tuple[str, ...] = Field(min_length=1, max_length=8)
    adjustment_mode: PriceAdjustmentMode
    data_quality_status: DataQualityStatus

    @model_validator(mode="after")
    def validate_times(self) -> MarketAcquisitionSummary:
        if (
            self.first_bar_at > self.latest_bar_at
            or self.latest_bar_at > self.analysis_timestamp
            or self.observed_at > self.analysis_timestamp
        ):
            raise ValueError("market acquisition timestamps exceed the analysis cutoff")
        return self
