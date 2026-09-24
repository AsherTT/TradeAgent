"""Celery application configured with Redis transport and JSON-only messages."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from celery import Celery

from backend.app.ai.runtime import build_model_gateway
from backend.app.config import Settings, get_settings
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.graph import MarketResearchEvidence, ResearchWorkflow, failed_research_state
from backend.app.market_data.cache import InMemoryQualifiedMarketDataCache
from backend.app.market_data.runtime import (
    SecurityMasterInstrumentResolver,
    build_market_data_loader,
)
from backend.app.persistence.repositories import (
    ResearchRunBusyError,
    ResearchRunNotReadyError,
    ResearchRunRepository,
    SecurityMasterRepository,
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
        beat_schedule={
            "reconcile-pending-research-runs": {
                "task": "research.reconcile_pending",
                "schedule": runtime.research_reconcile_interval_seconds,
            }
        },
    )
    return app


celery_app = create_celery()
_market_data_cache: InMemoryQualifiedMarketDataCache | None = None
logger = logging.getLogger(__name__)


def _get_market_data_cache(max_entries: int) -> InMemoryQualifiedMarketDataCache:
    global _market_data_cache
    if _market_data_cache is None or _market_data_cache.max_entries != max_entries:
        _market_data_cache = InMemoryQualifiedMarketDataCache(max_entries=max_entries)
    return _market_data_cache


@celery_app.task(bind=True, max_retries=None, name="research.run")  # type: ignore[untyped-decorator]
def run_research(task: Any, research_run_id: str) -> dict[str, Any]:
    """Execute one durable research graph from the synchronous Celery boundary."""

    execution_id = str(task.request.id or uuid4())
    try:
        state = asyncio.run(
            _execute_worker_task(UUID(research_run_id), execution_id=execution_id)
        )
    except (ResearchRunBusyError, ResearchRunNotReadyError) as exc:
        raise task.retry(exc=exc, countdown=5) from exc
    return {"research_run_id": research_run_id, "state": state.status.value}


async def _execute_worker_task(
    research_run_id: UUID, *, execution_id: str
) -> ResearchState:
    """Dispose loop-bound connections before the synchronous task loop closes."""

    database = get_database()
    try:
        return await execute_research_run(research_run_id, execution_id=execution_id)
    finally:
        await database.dispose()


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

        try:
            settings = get_settings()
            evidence_provider = None
            if settings.market_data_enabled:
                security_master = SecurityMasterRepository(session)
                instrument = await security_master.get_instrument(state.instrument_id)
                if instrument is None:
                    raise ValueError(
                        f"instrument {state.instrument_id} is not available in the security master"
                    )
                loader = build_market_data_loader(
                    settings,
                    instrument_resolver=SecurityMasterInstrumentResolver(security_master),
                    cache=_get_market_data_cache(
                        settings.market_data_cache_max_entries
                    ),
                )
                evidence_provider = MarketResearchEvidence(
                    loader, currency=instrument.currency
                )
            workflow = ResearchWorkflow(
                model_gateway=build_model_gateway(settings),
                save=save,
                evidence_provider=evidence_provider,
            )
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


@celery_app.task(name="research.reconcile_pending")  # type: ignore[untyped-decorator]
def reconcile_pending_research_runs() -> dict[str, int]:
    """Republish old pending runs while leaving worker claims authoritative."""

    return asyncio.run(_reconcile_pending_worker_task())


async def _reconcile_pending_worker_task() -> dict[str, int]:
    """Dispose loop-bound connections before the periodic task loop closes."""

    database = get_database()
    try:
        return await _reconcile_pending_runs()
    finally:
        await database.dispose()


async def _reconcile_pending_runs() -> dict[str, int]:
    settings = get_settings()
    database = get_database()
    cutoff = datetime.now(UTC) - timedelta(
        seconds=settings.research_reconcile_grace_seconds
    )
    async with database.sessions() as session:
        run_ids = await ResearchRunRepository(session).list_reconcilable_pending_ids(
            older_than=cutoff,
            limit=settings.research_reconcile_batch_size,
        )

    published = 0
    failed = 0
    for run_id in run_ids:
        try:
            enqueue_research_run(str(run_id))
        except Exception:  # broker errors are retried by a later reconciliation tick
            failed += 1
        else:
            published += 1

    result = {"eligible": len(run_ids), "published": published, "failed": failed}
    logger.info(
        "pending research reconciliation completed: eligible=%d published=%d failed=%d",
        result["eligible"],
        result["published"],
        result["failed"],
    )
    return result
