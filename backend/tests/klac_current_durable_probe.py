"""Opt-in live KLAC queue-path probe; run only with provider flags and a Finnhub key."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from time import monotonic

import httpx
from sqlalchemy import select

from backend.app.contracts.instrument import Instrument, SymbolHistory
from backend.app.contracts.research import (
    ResearchBudget,
    ResearchPlan,
    ResearchState,
    ResearchStep,
    ResearchTimestampMode,
)
from backend.app.jobs.celery_app import enqueue_research_run
from backend.app.persistence.models import InstrumentRow, SymbolHistoryRow
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import get_database


async def main() -> None:
    database = get_database()
    instrument = Instrument(
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA Corporation live qualification",
    )
    try:
        async with database.sessions() as session, session.begin():
            existing = await session.scalar(
                select(InstrumentRow).where(
                    InstrumentRow.current_symbol == "KLAC", InstrumentRow.exchange == "NASDAQ"
                )
            )
            if existing is None:
                await SecurityMasterRepository(session).add_instrument(instrument)
                instrument_id = instrument.instrument_id
            else:
                instrument_id = existing.instrument_id
            history = await session.scalar(
                select(SymbolHistoryRow).where(SymbolHistoryRow.instrument_id == instrument_id)
            )
            if history is None:
                await SecurityMasterRepository(session).add_symbol_history(
                    SymbolHistory(
                        instrument_id=instrument_id,
                        symbol="KLAC",
                        exchange="NASDAQ",
                        valid_from=datetime(1990, 1, 1, tzinfo=UTC),
                        valid_to=None,
                        available_at=datetime(1990, 1, 1, tzinfo=UTC),
                    )
                )
        state = ResearchState(
            instrument_id=instrument_id,
            ticker="KLAC",
            query="Assess the current KLAC setup and evidence gaps",
            timestamp_mode=ResearchTimestampMode.CURRENT_RESEARCH,
            analysis_timestamp=None,
            horizon="3-5 days",
            research_plan=ResearchPlan(
                question="Assess the current KLAC setup and evidence gaps",
                instrument_symbol="KLAC",
                horizon="3-5 days",
                steps=(
                    ResearchStep(
                        step_id="market_snapshot",
                        objective="Collect current market state",
                        capability="market",
                    ),
                ),
                stop_conditions=("evidence collected",),
                evidence_requirements=("market data",),
            ),
            research_budget=ResearchBudget(max_llm_calls=0, max_replans=0),
        )
        async with database.sessions() as session, session.begin():
            await ResearchRunRepository(session).create(state)
        enqueue_research_run(str(state.research_id))
        deadline = monotonic() + 180
        api_base_url = os.environ.get("KLAC_PROBE_API_URL", "http://api:8000")
        async with httpx.AsyncClient(
            base_url=api_base_url, timeout=10, trust_env=False
        ) as client:
            while monotonic() < deadline:
                response = await client.get(f"/research/{state.research_id}")
                response.raise_for_status()
                result = response.json()
                if result["status"] in {"complete", "insufficient_evidence", "failed", "cancelled"}:
                    break
                await asyncio.sleep(2)
            else:
                raise TimeoutError(f"research run {state.research_id} did not finish")
            response = await client.get(f"/research/{state.research_id}/report")
            response.raise_for_status()
            report = response.json()
        acquisition = result.get("market_acquisition") or {}
        print(
            json.dumps(
                {
                    "research_run_id": str(state.research_id),
                    "status": result["status"],
                    "analysis_timestamp": result.get("analysis_timestamp"),
                "market_acquisition": {
                    "bar_count": acquisition.get("bar_count"),
                    "quality": acquisition.get("data_quality_status"),
                    "sources": acquisition.get("source_names"),
                    },
                    "market_snapshot": result.get("market_snapshot") is not None,
                    "technical_snapshot": result.get("technical_snapshot") is not None,
                    "news_evidence_count": sum(
                        item["evidence_type"] == "news_document" for item in result["evidence"]
                    ),
                    "report_status": report.get("status"),
                "report_gaps": report.get("gaps"),
                },
                default=str,
            )
        )
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
