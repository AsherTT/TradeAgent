"""Celery application configured with Redis transport and JSON-only messages."""

from __future__ import annotations

from typing import Any

from celery import Celery

from backend.app.config import Settings, get_settings


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


@celery_app.task(name="research.run")  # type: ignore[untyped-decorator]
def run_research(research_run_id: str) -> dict[str, Any]:
    """Phase 3 queue boundary; the Phase 5 graph will replace this acknowledgement."""

    return {"research_run_id": research_run_id, "state": "accepted"}


def enqueue_research_run(research_run_id: str) -> str:
    result = celery_app.send_task("research.run", args=[research_run_id])
    return str(result.id)
