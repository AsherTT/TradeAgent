"""Bounded browser research with ownership checked before every run operation."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select

from backend.app.accounts.sessions import require_browser_origin
from backend.app.api.accounts import AuthenticatedUser, BrowserSession
from backend.app.api.research import (
    ResearchEnqueuer,
    ResearchSubmission,
    create_research,
    get_research_enqueuer,
)
from backend.app.config import get_settings
from backend.app.contracts.evaluation import (
    DataQualityStatus,
    QualityAssessment,
    QualityGateDecision,
    ReplayIntegrityLevel,
    ResearchCompletion,
)
from backend.app.contracts.research import (
    BudgetUsage,
    ResearchBudget,
    ResearchState,
    ResearchStatus,
    ResearchTimestampMode,
)
from backend.app.graph.workflow import ResearchNode
from backend.app.persistence.accounts import UserResearchRow, UserRow
from backend.app.persistence.models import InstrumentRow, ResearchRunRow
from backend.app.persistence.repositories import ResearchRunRepository
from backend.app.reports.research import ResearchReport, build_research_report

router = APIRouter(prefix="/workspace/research", tags=["account research"])


class WorkspaceBudget(ResearchBudget):
    max_iterations: int = Field(default=4, ge=1, le=4)
    max_replans: int = Field(default=2, ge=0, le=2)
    max_tool_calls: int = Field(default=12, ge=0, le=12)
    max_llm_calls: int = Field(default=0, ge=0, le=10)
    max_wall_time_seconds: int = Field(default=120, ge=1, le=120)
    max_context_tokens: int = Field(default=100_000, ge=1, le=100_000)
    max_estimated_cost_usd: float = Field(default=0.1, ge=0, le=1)
    max_news_documents: int = Field(default=30, ge=0, le=30)
    max_rag_chunks: int = Field(default=12, ge=0, le=12)


class WorkspaceSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID
    instrument_id: UUID
    query: str = Field(min_length=1, max_length=2000)
    horizon: str = Field(min_length=1, max_length=64)
    collection_only: bool = True
    budget: WorkspaceBudget

    @field_validator("query", "horizon")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value

    @model_validator(mode="after")
    def model_budget(self) -> WorkspaceSubmission:
        if self.collection_only and self.budget.max_llm_calls != 0:
            raise ValueError("collection does not call models")
        if not self.collection_only and (
            self.budget.max_llm_calls == 0 or self.budget.max_estimated_cost_usd == 0
        ):
            raise ValueError("model research requires explicit nonzero budgets")
        return self


class ResearchReceipt(BaseModel):
    research_run_id: UUID
    status: ResearchStatus


class ResearchSummary(ResearchReceipt):
    instrument_id: UUID
    ticker: str
    query: str
    horizon: str
    requested_at: datetime
    research_completion: ResearchCompletion | None
    collection_only: bool


class ResearchDetail(ResearchSummary):
    analysis_timestamp: datetime | None
    research_budget: ResearchBudget
    budget_usage: BudgetUsage
    data_quality_status: DataQualityStatus
    quality_gate_decision: QualityGateDecision | None
    quality_assessment: QualityAssessment | None
    progress_steps: tuple[str, ...]
    failure_code: str | None
    # Supplier charges are not audited by this increment.
    actual_cost_usd: float | None = None


def summary(state: ResearchState) -> ResearchSummary:
    return ResearchSummary(
        research_run_id=state.research_id, status=state.status,
        instrument_id=state.instrument_id, ticker=state.ticker, query=state.query,
        horizon=state.horizon, requested_at=state.requested_at,
        research_completion=state.research_completion,
        collection_only=state.runtime_metadata.get("submission_mode") == "collection_only",
    )


async def owned_run(run_id: UUID, user_id: UUID, session: BrowserSession) -> ResearchState:
    owner = await session.scalar(select(UserResearchRow).where(
        UserResearchRow.research_run_id == run_id, UserResearchRow.user_id == user_id,
    ))
    if owner is None:
        raise HTTPException(404, detail="research_not_found")
    state = await ResearchRunRepository(session).get(run_id)
    if state is None:
        raise HTTPException(404, detail="research_not_found")
    return state


@router.get("/options")
async def research_options(user: AuthenticatedUser) -> dict[str, bool]:
    del user
    return {"models_enabled": get_settings().account_research_models_enabled}


@router.post("", response_model=ResearchReceipt, status_code=202,
             dependencies=[Depends(require_browser_origin)])
async def submit_owned_research(
    submission: WorkspaceSubmission, user: AuthenticatedUser, session: BrowserSession,
    enqueue: Annotated[ResearchEnqueuer, Depends(get_research_enqueuer)],
) -> ResearchReceipt:
    # PG row lock serializes owner submissions, protecting deduplication and active-run limit.
    await session.scalar(select(UserRow).where(UserRow.user_id == user.user_id).with_for_update())
    digest = sha256(submission.model_dump_json(exclude={"request_id"}).encode()).hexdigest()
    existing = await session.scalar(select(UserResearchRow).where(
        UserResearchRow.user_id == user.user_id,
        UserResearchRow.request_id == submission.request_id,
    ))
    if existing is not None:
        if existing.request_digest != digest:
            raise HTTPException(409, detail="submission_conflict")
        state = await owned_run(existing.research_run_id, user.user_id, session)
        return ResearchReceipt(research_run_id=state.research_id, status=state.status)
    instrument = await session.get(InstrumentRow, submission.instrument_id)
    if instrument is None or instrument.delisted_at is not None:
        raise HTTPException(404, detail="company_not_found")
    if not submission.collection_only and not get_settings().account_research_models_enabled:
        raise HTTPException(409, detail="model_research_disabled")
    active = await session.scalar(select(func.count()).select_from(ResearchRunRow).join(
        UserResearchRow,
    ).where(
        UserResearchRow.user_id == user.user_id,
        ResearchRunRow.status.in_((ResearchStatus.PENDING.value, ResearchStatus.RUNNING.value)),
    ))
    if active is not None and active >= 3:
        raise HTTPException(429, detail="active_research_limit")
    accepted = await create_research(
        ResearchSubmission(
            instrument_id=submission.instrument_id, ticker=instrument.current_symbol,
            query=submission.query, horizon=submission.horizon,
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            replay_integrity_level=ReplayIntegrityLevel.RESEARCH_REPLAY,
            collection_only=submission.collection_only, budget=submission.budget,
        ),
        session, enqueue,
        ownership=UserResearchRow(
            user_id=user.user_id, request_id=submission.request_id, request_digest=digest,
        ),
    )
    return ResearchReceipt(research_run_id=accepted.research_run_id, status=accepted.status)


@router.get("", response_model=list[ResearchSummary])
async def list_research(user: AuthenticatedUser, session: BrowserSession) -> list[ResearchSummary]:
    ids = await session.scalars(select(ResearchRunRow.research_run_id).join(UserResearchRow).where(
        UserResearchRow.user_id == user.user_id,
    ).order_by(ResearchRunRow.created_at.desc(), ResearchRunRow.research_run_id.desc()).limit(50))
    return [summary(await owned_run(run_id, user.user_id, session)) for run_id in ids]


@router.get("/{run_id}", response_model=ResearchDetail)
async def read_research(
    run_id: UUID, user: AuthenticatedUser, session: BrowserSession,
) -> ResearchDetail:
    state = await owned_run(run_id, user.user_id, session)
    row = await session.get(ResearchRunRow, run_id)
    allowed_steps = {node.value for node in ResearchNode} | {"cancelled"}
    return ResearchDetail(
        **summary(state).model_dump(), analysis_timestamp=state.analysis_timestamp,
        research_budget=state.research_budget, budget_usage=state.budget_usage,
        data_quality_status=state.data_quality_status,
        quality_gate_decision=state.quality_gate_decision,
        quality_assessment=state.quality_assessment,
        progress_steps=tuple(step for step in state.runtime_metadata.get("transitions", ())
                             if isinstance(step, str) and step in allowed_steps),
        failure_code=(
            "queue_unavailable" if row and row.failure_reason
            and row.failure_reason.startswith("queue dispatch failed:") else "research_failed"
        ) if state.status is ResearchStatus.FAILED else None,
    )


@router.post("/{run_id}/cancel", response_model=ResearchDetail,
             dependencies=[Depends(require_browser_origin)])
async def cancel_owned_research(
    run_id: UUID, user: AuthenticatedUser, session: BrowserSession,
) -> ResearchDetail:
    await owned_run(run_id, user.user_id, session)
    await ResearchRunRepository(session).cancel(run_id)
    await session.commit()
    return await read_research(run_id, user, session)


@router.get("/{run_id}/report", response_model=ResearchReport)
async def read_report(
    run_id: UUID, user: AuthenticatedUser, session: BrowserSession,
) -> ResearchReport:
    return build_research_report(await owned_run(run_id, user.user_id, session))
