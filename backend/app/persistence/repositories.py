"""Domain repositories over the Phase 3 SQLAlchemy mappings."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.instrument import (
    CorporateAction,
    CorporateActionType,
    Instrument,
    InstrumentStatus,
    SymbolHistory,
)
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.persistence.models import (
    CorporateActionRow,
    InstrumentRow,
    ResearchBudgetRow,
    ResearchPlanRow,
    ResearchRunRow,
    SymbolHistoryRow,
)


class SecurityMasterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_instrument(self, instrument: Instrument) -> Instrument:
        self._session.add(
            InstrumentRow(
                instrument_id=instrument.instrument_id,
                current_symbol=instrument.current_symbol,
                exchange=instrument.exchange,
                currency=instrument.currency,
                asset_type=instrument.asset_type,
                listed_at=instrument.listed_at,
                delisted_at=instrument.delisted_at,
                company_name=instrument.company_name,
                status=instrument.status.value,
            )
        )
        await self._session.flush()
        return instrument

    async def get_instrument(self, instrument_id: UUID) -> Instrument | None:
        row = await self._session.get(InstrumentRow, instrument_id)
        return self._to_instrument(row) if row else None

    async def add_symbol_history(self, history: SymbolHistory) -> SymbolHistory:
        self._session.add(
            SymbolHistoryRow(
                instrument_id=history.instrument_id,
                symbol=history.symbol,
                exchange=history.exchange,
                valid_from=history.valid_from,
                valid_to=history.valid_to,
                available_at=history.available_at,
            )
        )
        await self._session.flush()
        return history

    async def resolve_symbol(
        self,
        symbol: str,
        exchange: str,
        as_of: datetime,
        *,
        analysis_timestamp: datetime | None = None,
    ) -> Instrument | None:
        knowledge_cutoff = analysis_timestamp or as_of
        statement = (
            select(InstrumentRow)
            .join(SymbolHistoryRow, SymbolHistoryRow.instrument_id == InstrumentRow.instrument_id)
            .where(
                SymbolHistoryRow.symbol == symbol,
                SymbolHistoryRow.exchange == exchange,
                SymbolHistoryRow.valid_from <= as_of,
                or_(SymbolHistoryRow.valid_to.is_(None), SymbolHistoryRow.valid_to > as_of),
                SymbolHistoryRow.available_at.is_not(None),
                SymbolHistoryRow.available_at <= knowledge_cutoff,
            )
            .limit(2)
        )
        rows = (await self._session.scalars(statement)).all()
        if len(rows) > 1:
            raise SecurityMasterIntegrityError(
                f"overlapping symbol history for {symbol}@{exchange} at {as_of.isoformat()}"
            )
        return self._to_instrument(rows[0]) if rows else None

    async def add_corporate_action(self, action: CorporateAction) -> CorporateAction:
        self._session.add(
            CorporateActionRow(
                action_id=action.action_id,
                instrument_id=action.instrument_id,
                action_type=action.action_type.value,
                announced_at=action.announced_at,
                ex_date=action.ex_date,
                effective_at=action.effective_at,
                available_at=action.available_at,
                ratio=action.ratio,
                cash_amount=action.cash_amount,
                currency=action.currency,
                source=action.source,
                provider_quality_version=action.provider_quality_version,
            )
        )
        await self._session.flush()
        return action

    async def list_corporate_actions(
        self,
        instrument_id: UUID,
        *,
        effective_from: datetime,
        effective_to: datetime,
        analysis_timestamp: datetime,
    ) -> tuple[CorporateAction, ...]:
        """Return actions effective in the interval and known at analysis time."""

        statement = (
            select(CorporateActionRow)
            .where(
                CorporateActionRow.instrument_id == instrument_id,
                CorporateActionRow.effective_at >= effective_from,
                CorporateActionRow.effective_at <= effective_to,
                CorporateActionRow.available_at <= analysis_timestamp,
            )
            .order_by(CorporateActionRow.effective_at, CorporateActionRow.action_id)
        )
        rows = (await self._session.scalars(statement)).all()
        return tuple(self._to_corporate_action(row) for row in rows)

    @staticmethod
    def _to_instrument(row: InstrumentRow) -> Instrument:
        return Instrument(
            instrument_id=row.instrument_id,
            current_symbol=row.current_symbol,
            exchange=row.exchange,
            currency=row.currency,
            asset_type=row.asset_type,
            listed_at=row.listed_at,
            delisted_at=row.delisted_at,
            company_name=row.company_name,
            status=InstrumentStatus(row.status),
        )

    @staticmethod
    def _to_corporate_action(row: CorporateActionRow) -> CorporateAction:
        return CorporateAction(
            action_id=row.action_id,
            instrument_id=row.instrument_id,
            action_type=CorporateActionType(row.action_type),
            announced_at=_as_utc(row.announced_at) if row.announced_at is not None else None,
            ex_date=row.ex_date,
            effective_at=_as_utc(row.effective_at),
            available_at=_as_utc(row.available_at),
            ratio=row.ratio,
            cash_amount=row.cash_amount,
            currency=row.currency,
            source=row.source,
            provider_quality_version=row.provider_quality_version or "legacy-unqualified",
        )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class SecurityMasterIntegrityError(RuntimeError):
    """Raised when temporal security-master records are ambiguous."""


class ResearchRunNotReadyError(LookupError):
    """Raised when a queued run is not yet visible to the worker."""


class ResearchRunBusyError(RuntimeError):
    """Raised when another worker owns the durable execution lease."""


_TERMINAL_RESEARCH_STATUSES = {
    ResearchStatus.COMPLETE,
    ResearchStatus.INSUFFICIENT_EVIDENCE,
    ResearchStatus.FAILED,
}


class ResearchRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, state: ResearchState) -> ResearchState:
        self._session.add(
            ResearchRunRow(
                research_run_id=state.research_id,
                instrument_id=state.instrument_id,
                query=state.query,
                analysis_timestamp=state.analysis_timestamp,
                horizon=state.horizon,
                status=state.status.value,
                state_json=state.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        await self._save_details(state)
        return state

    async def get(self, research_run_id: UUID) -> ResearchState | None:
        row = await self._session.get(ResearchRunRow, research_run_id)
        return ResearchState.model_validate_json(json.dumps(row.state_json)) if row else None

    async def claim_execution(
        self,
        research_run_id: UUID,
        *,
        execution_id: str,
        lease_seconds: int,
    ) -> ResearchState:
        now = datetime.now(UTC)
        statement = (
            update(ResearchRunRow)
            .where(
                ResearchRunRow.research_run_id == research_run_id,
                ResearchRunRow.status.in_(
                    (ResearchStatus.PENDING.value, ResearchStatus.RUNNING.value)
                ),
                or_(
                    ResearchRunRow.execution_id.is_(None),
                    ResearchRunRow.lease_expires_at.is_(None),
                    ResearchRunRow.lease_expires_at <= now,
                ),
            )
            .values(
                execution_id=execution_id,
                lease_expires_at=now + timedelta(seconds=lease_seconds),
            )
            .returning(ResearchRunRow.research_run_id)
        )
        claimed_id = await self._session.scalar(statement)
        if claimed_id is None:
            row = await self._session.get(ResearchRunRow, research_run_id)
            if row is None:
                raise ResearchRunNotReadyError(
                    f"research run {research_run_id} is not committed yet"
                )
            state = ResearchState.model_validate_json(json.dumps(row.state_json))
            if state.status in _TERMINAL_RESEARCH_STATUSES:
                return state
            raise ResearchRunBusyError(f"research run {research_run_id} has an active worker")
        claimed_state = await self.get(research_run_id)
        if claimed_state is None:  # pragma: no cover - guarded by the successful update
            raise ResearchRunNotReadyError(f"research run {research_run_id} disappeared")
        return claimed_state

    async def save(
        self,
        state: ResearchState,
        *,
        execution_id: str | None = None,
        failure_reason: str | None = None,
    ) -> ResearchState:
        if execution_id is not None:
            now = datetime.now(UTC)
            values: dict[str, object] = {
                "status": state.status.value,
                "state_json": state.model_dump(mode="json"),
                "updated_at": now,
            }
            if failure_reason is not None:
                values["failure_reason"] = failure_reason
            if state.status in _TERMINAL_RESEARCH_STATUSES:
                values["execution_id"] = None
                values["lease_expires_at"] = None
            statement = (
                update(ResearchRunRow)
                .where(
                    ResearchRunRow.research_run_id == state.research_id,
                    ResearchRunRow.execution_id == execution_id,
                    ResearchRunRow.lease_expires_at > now,
                )
                .values(**values)
                .returning(ResearchRunRow.research_run_id)
                .execution_options(synchronize_session=False)
            )
            saved_id = await self._session.scalar(statement)
            if saved_id is None:
                raise ResearchRunBusyError(
                    f"research run {state.research_id} is owned by another worker "
                    "or its execution lease expired"
                )
            await self._save_details(state)
            await self._session.flush()
            return state

        row = await self._session.get(ResearchRunRow, state.research_id)
        if row is None:
            raise LookupError(f"research run {state.research_id} does not exist")
        row.status = state.status.value
        row.state_json = state.model_dump(mode="json")
        if failure_reason is not None:
            row.failure_reason = failure_reason
        if state.status in _TERMINAL_RESEARCH_STATUSES:
            row.execution_id = None
            row.lease_expires_at = None
        row.updated_at = datetime.now(state.analysis_timestamp.tzinfo)
        await self._save_details(state)
        await self._session.flush()
        return state

    async def set_status(
        self,
        research_run_id: UUID,
        status: ResearchStatus,
        *,
        failure_reason: str | None = None,
    ) -> ResearchState:
        state = await self.get(research_run_id)
        if state is None:
            raise LookupError(f"research run {research_run_id} does not exist")
        row = await self._session.get_one(ResearchRunRow, research_run_id)
        updated = state.model_copy(update={"status": status})
        row.status = status.value
        row.state_json = updated.model_dump(mode="json")
        row.failure_reason = failure_reason
        row.updated_at = datetime.now(state.analysis_timestamp.tzinfo)
        await self._session.flush()
        return updated

    async def _save_details(self, state: ResearchState) -> None:
        plan_row = await self._session.get(ResearchPlanRow, state.research_id)
        if state.research_plan is None:
            if plan_row is not None:
                await self._session.delete(plan_row)
        elif plan_row is None:
            self._session.add(
                ResearchPlanRow(
                    research_run_id=state.research_id,
                    plan_json=state.research_plan.model_dump(mode="json"),
                )
            )
        else:
            plan_row.plan_json = state.research_plan.model_dump(mode="json")

        budget_json = state.research_budget.model_dump(mode="json")
        budget_row = await self._session.get(ResearchBudgetRow, state.research_id)
        if budget_row is None:
            self._session.add(
                ResearchBudgetRow(
                    research_run_id=state.research_id,
                    budget_json=budget_json,
                )
            )
        else:
            budget_row.budget_json = budget_json
