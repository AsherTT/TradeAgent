"""Celery application configured with Redis transport and JSON-only messages."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

from celery import Celery

from backend.app.ai.runtime import build_model_gateway
from backend.app.config import Settings, get_settings
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.graph import ResearchWorkflow, failed_research_state
from backend.app.persistence.repositories import (
    ResearchRunBusyError,
    ResearchRunNotReadyError,
    ResearchRunRepository,
)
from backend.app.persistence.session import get_database


def create_celery(settings: Settings | None = None) -> Celery:
    runtime = settings or get_settings()
    app = Celery(
        "tradeagent",
        broker=runtime.redis_broker_url,
        backend=runtime.redis_result_url,
    )
    app.conf.update(
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
        task_track_started=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        result_expires=3600,
        broker_transport_options={"global_keyprefix": "tradeagent:broker:"},
        result_backend_transport_options={"global_keyprefix": "tradeagent:result:"},
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = create_celery()


@celery_app.task(bind=True, max_retries=None, name="research.run")  # type: ignore[untyped-decorator]
def run_research(task: Any, research_run_id: str) -> dict[str, Any]:
    """Execute one durable research graph from the synchronous Celery boundary."""

    execution_id = str(task.request.id or uuid4())
    try:
        state = asyncio.run(
            execute_research_run(UUID(research_run_id), execution_id=execution_id)
        )
    except (ResearchRunBusyError, ResearchRunNotReadyError) as exc:
        raise task.retry(exc=exc, countdown=5) from exc
    return {"research_run_id": research_run_id, "state": state.status.value}


async def execute_research_run(
    research_run_id: UUID, *, execution_id: str | None = None
) -> ResearchState:
    """Load, execute, and durably finish a run; terminal redeliveries are no-ops."""

    database = get_database()
    async with database.sessions() as session:
        repository = ResearchRunRepository(session)
        state = await repository.get(research_run_id)
        if state is None:
            raise ResearchRunNotReadyError(
                f"research run {research_run_id} is not committed yet"
            )
        if state.status in {
            ResearchStatus.COMPLETE,
            ResearchStatus.INSUFFICIENT_EVIDENCE,
            ResearchStatus.FAILED,
        }:
            return state
        owner = execution_id or str(uuid4())
        lease_seconds = max(120, state.research_budget.max_wall_time_seconds) + 60
        state = await repository.claim_execution(
            research_run_id,
            execution_id=owner,
            lease_seconds=lease_seconds,
        )
        await session.commit()

        async def save(updated: ResearchState) -> None:
            await repository.save(updated, execution_id=owner)
            await session.commit()

        workflow = ResearchWorkflow(
            model_gateway=build_model_gateway(get_settings()),
            save=save,
        )
        try:
            return await workflow.run(state)
        except Exception as exc:
            latest = await repository.get(research_run_id) or state
            failed = failed_research_state(latest, exc)
            await repository.save(
                failed,
                execution_id=owner,
                failure_reason=f"{type(exc).__name__}: {exc}",
            )
            await session.commit()
            return failed


def enqueue_research_run(research_run_id: str) -> str:
    result = celery_app.send_task("research.run", args=[research_run_id])
    return str(result.id)
