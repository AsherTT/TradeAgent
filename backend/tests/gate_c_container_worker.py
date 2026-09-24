"""Offline-only Celery worker for Gate C container qualification.

Run this module inside the rebuilt worker image. It replaces both external provider
boundaries before the worker accepts tasks; it is never imported by production code.
"""

from datetime import timedelta
from importlib import import_module
from uuid import UUID

from pydantic import BaseModel

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.evidence import Evidence, TrustLevel
from backend.app.contracts.instrument import PriceAdjustmentMode
from backend.app.contracts.market import MarketBar, MarketSnapshot, TechnicalSnapshot
from backend.app.contracts.model import ModelRequest, ProviderName, TaskKind
from backend.app.contracts.research import ResearchState
from backend.app.graph.workflow import EvidenceCollection


def _model_output(request: ModelRequest[BaseModel]) -> dict[str, object]:
    task_kind = request.task_kind
    if task_kind is TaskKind.INTENT:
        return {
            "research_goal": "Assess the short-term setup",
            "focus_areas": ("price trend",),
        }
    if task_kind is TaskKind.SYNTHESIS:
        selected = request.context["selected_evidence"]
        return {
            "summary": "Qualified fixture market evidence supports a cautious assessment.",
            "bull_case": "The trend may continue.",
            "bear_case": "The trend may weaken.",
            "limitations": ("Offline fixture only",),
            "evidence_ids": tuple(UUID(item["evidence_id"]) for item in selected),
            "confidence": 0.5,
        }
    return {
        "question": "Assess the setup",
        "instrument_symbol": "KLAC",
        "horizon": "3-5 days",
        "steps": (
            {
                "step_id": "market_snapshot",
                "objective": "Collect qualified market evidence",
                "capability": "market",
            },
        ),
        "stop_conditions": ("evidence collected",),
        "evidence_requirements": ("market data",),
    }


class _QualifiedMarketFixture:
    async def collect(self, state: ResearchState) -> EvidenceCollection:
        cutoff = state.analysis_timestamp
        if cutoff is None:
            raise ValueError("Gate C fixture requires a fixed cutoff")
        observed = cutoff - timedelta(days=1)
        bar = MarketBar(
            instrument_id=state.instrument_id,
            symbol="KLAC",
            timestamp=observed,
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1000,
            adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
            adjustment_factor=1,
            source="gate_c_fixture",
            observed_at=observed,
            available_at=observed,
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="gate-c-fixture-v1",
        )
        return EvidenceCollection(
            analysis_timestamp=cutoff,
            market_snapshot=MarketSnapshot(
                instrument_id=state.instrument_id,
                analysis_timestamp=cutoff,
                latest_bar=bar,
                currency="USD",
            ),
            technical_snapshot=TechnicalSnapshot(
                instrument_id=state.instrument_id,
                analysis_timestamp=cutoff,
                price_adjustment_mode=PriceAdjustmentMode.POINT_IN_TIME_ADJUSTED,
                feature_version="gate-c-fixture-v1",
            ),
            evidence=(
                Evidence(
                    instrument_id=state.instrument_id,
                    evidence_type="market_technical_snapshot",
                    source_name="gate_c_fixture",
                    observed_at=observed,
                    retrieved_at=cutoff,
                    available_at=observed,
                    content="Qualified fixture market snapshot",
                    confidence=1,
                    freshness=1,
                    trust_level=TrustLevel.TRUSTED_PROVIDER,
                    source_type="market_data",
                    content_hash="gate-c-fixture-hash",
                    sanitization_status="structured_verified",
                    injection_risk=0,
                ),
            ),
        )


def main() -> None:
    celery_module = import_module("backend.app.jobs.celery_app")
    executor = MockExecutor(_model_output)
    executor.provider = ProviderName.CODEX_SUBSCRIPTION
    celery_module.build_model_gateway = lambda settings: ModelGateway([executor])
    celery_module.build_market_data_loader = lambda *args, **kwargs: object()
    celery_module.MarketResearchEvidence = lambda *args, **kwargs: _QualifiedMarketFixture()
    celery_module.celery_app.worker_main(
        ["worker", "--loglevel=INFO", "--concurrency=1", "--pool=solo"]
    )


if __name__ == "__main__":
    main()
