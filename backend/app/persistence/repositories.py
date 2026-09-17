"""Domain repositories over the Phase 3 SQLAlchemy mappings."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.instrument import (
    CorporateAction,
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
            )
        )
        await self._session.flush()
        return history

    async def resolve_symbol(
        self, symbol: str, exchange: str, as_of: datetime
    ) -> Instrument | None:
        statement = (
            select(InstrumentRow)
            .join(SymbolHistoryRow, SymbolHistoryRow.instrument_id == InstrumentRow.instrument_id)
            .where(
                SymbolHistoryRow.symbol == symbol,
                SymbolHistoryRow.exchange == exchange,
                SymbolHistoryRow.valid_from <= as_of,
                or_(SymbolHistoryRow.valid_to.is_(None), SymbolHistoryRow.valid_to > as_of),
            )
        )
        row = await self._session.scalar(statement)
        return self._to_instrument(row) if row else None

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
            )
        )
        await self._session.flush()
        return action

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

    async def save(self, state: ResearchState) -> ResearchState:
        row = await self._session.get(ResearchRunRow, state.research_id)
        if row is None:
            raise LookupError(f"research run {state.research_id} does not exist")
        row.status = state.status.value
        row.state_json = state.model_dump(mode="json")
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
