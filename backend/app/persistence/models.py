"""Phase 3 relational mappings for ResearchRun and the security master."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.contracts.base import utc_now
from backend.app.persistence.base import Base


class InstrumentRow(Base):
    __tablename__ = "instrument"

    instrument_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    current_symbol: Mapped[str] = mapped_column(String(32), index=True)
    exchange: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3))
    asset_type: Mapped[str] = mapped_column(String(32))
    listed_at: Mapped[date | None] = mapped_column(Date)
    delisted_at: Mapped[date | None] = mapped_column(Date)
    company_name: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), index=True)

    __table_args__ = (
        Index("uq_instrument_symbol_exchange", "current_symbol", "exchange", unique=True),
    )


class SymbolHistoryRow(Base):
    __tablename__ = "symbol_history"

    symbol_history_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    exchange: Mapped[str] = mapped_column(String(32))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_symbol_history_lookup", "symbol", "exchange", "valid_from", "valid_to"),
        Index(
            "ix_symbol_history_pit_lookup",
            "symbol",
            "exchange",
            "valid_from",
            "valid_to",
            "available_at",
        ),
    )


class CorporateActionRow(Base):
    __tablename__ = "corporate_action"

    action_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(32))
    announced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ex_date: Mapped[date | None] = mapped_column(Date)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ratio: Mapped[float | None] = mapped_column(Float)
    cash_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(256))
    provider_quality_version: Mapped[str | None] = mapped_column(String(128))

    __table_args__ = (
        Index(
            "ix_corporate_action_pit_lookup",
            "instrument_id",
            "effective_at",
            "available_at",
        ),
        CheckConstraint(
            "action_type NOT IN ('split', 'reverse_split') OR "
            "(ratio IS NOT NULL AND ratio > 0)",
            name="split_ratio_required",
        ),
        CheckConstraint(
            "action_type != 'cash_dividend' OR "
            "(cash_amount IS NOT NULL AND cash_amount >= 0 AND currency IS NOT NULL)",
            name="cash_dividend_required",
        ),
    )


class ResearchRunRow(Base):
    __tablename__ = "research_run"

    research_run_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="RESTRICT"), index=True
    )
    query: Mapped[str] = mapped_column(Text)
    analysis_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    horizon: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    execution_id: Mapped[str | None] = mapped_column(String(64), index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ResearchPlanRow(Base):
    __tablename__ = "research_plan"

    research_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_run.research_run_id", ondelete="CASCADE"), primary_key=True
    )
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResearchBudgetRow(Base):
    __tablename__ = "research_budget"

    research_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_run.research_run_id", ondelete="CASCADE"), primary_key=True
    )
    budget_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EvidenceRow(Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    research_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_run.research_run_id", ondelete="CASCADE"), index=True
    )
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="RESTRICT"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index(
            "ix_evidence_pit_lookup",
            "instrument_id",
            "available_at",
            "observed_at",
            "published_at",
        ),
    )


class ThesisRow(Base):
    __tablename__ = "thesis"

    thesis_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="RESTRICT"), index=True
    )
    latest_version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ThesisVersionRow(Base):
    __tablename__ = "thesis_version"

    thesis_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    research_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_run.research_run_id", ondelete="RESTRICT"), index=True
    )
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))
    thesis_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        ForeignKeyConstraint(
            ["thesis_id"], ["thesis.thesis_id"], ondelete="RESTRICT"
        ),
        Index("ix_thesis_version_pit", "thesis_id", "recorded_at", "analysis_timestamp"),
    )


class ThesisTransitionRow(Base):
    __tablename__ = "thesis_transition"

    transition_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    thesis_id: Mapped[UUID] = mapped_column(
        ForeignKey("thesis.thesis_id", ondelete="RESTRICT"), index=True
    )
    from_version: Mapped[int | None] = mapped_column()
    to_version: Mapped[int] = mapped_column()
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ThesisEvidenceRow(Base):
    __tablename__ = "thesis_evidence"

    thesis_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence.evidence_id", ondelete="RESTRICT"), primary_key=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["thesis_id", "version"],
            ["thesis_version.thesis_id", "thesis_version.version"],
            ondelete="RESTRICT",
        ),
    )


class ForecastRecordRow(Base):
    __tablename__ = "forecast_record"

    forecast_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    research_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_run.research_run_id", ondelete="RESTRICT"), index=True
    )
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instrument.instrument_id", ondelete="RESTRICT"), index=True
    )
    thesis_id: Mapped[UUID] = mapped_column(Uuid)
    thesis_version: Mapped[int] = mapped_column()
    supersedes_forecast_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("forecast_record.forecast_id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    horizon: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(16))
    probability: Mapped[float] = mapped_column(Float)
    record_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    __table_args__ = (
        ForeignKeyConstraint(
            ["thesis_id", "thesis_version"],
            ["thesis_version.thesis_id", "thesis_version.version"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("research_run_id", "thesis_id", name="uq_forecast_run_thesis"),
        CheckConstraint("probability >= 0 AND probability <= 1", name="forecast_probability"),
    )
