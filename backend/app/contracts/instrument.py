"""Security master and corporate-action contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from backend.app.contracts.base import ContractModel, TemporalWindow


class InstrumentStatus(StrEnum):
    ACTIVE = "active"
    DELISTED = "delisted"
    INACTIVE = "inactive"


class CorporateActionType(StrEnum):
    SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    CASH_DIVIDEND = "cash_dividend"
    STOCK_DIVIDEND = "stock_dividend"
    MERGER = "merger"
    SPINOFF = "spinoff"
    SYMBOL_CHANGE = "symbol_change"
    DELISTING = "delisting"


class PriceAdjustmentMode(StrEnum):
    RAW = "raw"
    SPLIT_ADJUSTED = "split_adjusted"
    TOTAL_RETURN = "total_return"
    POINT_IN_TIME_ADJUSTED = "point_in_time_adjusted"


class Instrument(ContractModel):
    instrument_id: UUID = Field(default_factory=uuid4)
    current_symbol: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=32)
    currency: str = Field(min_length=3, max_length=3)
    asset_type: str = Field(min_length=1, max_length=32)
    listed_at: date | None = None
    delisted_at: date | None = None
    company_name: str = Field(min_length=1, max_length=256)
    status: InstrumentStatus = InstrumentStatus.ACTIVE


class SymbolHistory(TemporalWindow):
    instrument_id: UUID
    symbol: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=32)


class CorporateAction(ContractModel):
    action_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    action_type: CorporateActionType
    announced_at: datetime | None = None
    ex_date: date | None = None
    effective_at: datetime
    available_at: datetime
    ratio: float | None = Field(default=None, gt=0)
    cash_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source: str = Field(min_length=1)
