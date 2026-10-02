"""Opt-in current KLAC HTTP/queue probe with a maximum of two model nodes.

Requires local API, PostgreSQL, Redis and a worker with market/news enabled.
Financial acquisition remains disabled unless separately configured/qualified.
"""

import asyncio
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

import httpx
from sqlalchemy import select

from backend.app.contracts.instrument import Instrument, SymbolHistory
from backend.app.persistence.models import InstrumentRow, SymbolHistoryRow
from backend.app.persistence.repositories import SecurityMasterRepository
from backend.app.persistence.session import get_database


async def main() -> None:
    database = get_database()
    try:
        async with database.sessions() as session, session.begin():
            existing = await session.scalar(
                select(InstrumentRow).where(
                    InstrumentRow.current_symbol == "KLAC", InstrumentRow.exchange == "NASDAQ"
                )
            )
            if existing is None:
                instrument = Instrument(
                    current_symbol="KLAC",
                    exchange="NASDAQ",
                    currency="USD",
                    asset_type="equity",
                    company_name="KLA Corporation",
                )
                await SecurityMasterRepository(session).add_instrument(instrument)
                instrument_id = instrument.instrument_id
            else:
                instrument_id = existing.instrument_id
            history = await session.scalar(
                select(SymbolHistoryRow).where(
                    SymbolHistoryRow.instrument_id == instrument_id,
                    SymbolHistoryRow.valid_to.is_(None),
                )
            )
            if history is None:
                observed = datetime.now(UTC)
                await SecurityMasterRepository(session).add_symbol_history(
                    SymbolHistory(
                        instrument_id=instrument_id,
                        symbol="KLAC",
                        exchange="NASDAQ",
                        valid_from=observed,
                        available_at=observed,
                    )
                )
        url = os.environ.get("KLAC_PROBE_API_URL", "http://127.0.0.1:8002")
        async with httpx.AsyncClient(base_url=url, timeout=10, trust_env=False) as client:
            response = await client.post(
                "/research",
                json={
                    "instrument_id": str(instrument_id),
                    "ticker": "KLAC",
                    "query": (
                        "Assess KLAC current market and news observations "
                        "and identify evidence gaps"
                    ),
                    "horizon": "3-5 days",
                    "timestamp_mode": "current_research",
                    "replay_integrity_level": "research_replay",
                    "collection_only": False,
                    "budget": {
                        "max_llm_calls": 2,
                        "max_tool_calls": (
                            6 if os.environ.get("KLAC_PROBE_RAG_LEXICAL") == "true" else 4
                        ),
                        "max_replans": 0,
                        "max_news_documents": 8,
                        "max_wall_time_seconds": 90,
                    },
                },
            )
            response.raise_for_status()
            run_id = response.json()["research_run_id"]
            deadline = monotonic() + 120
            for _ in range(60):
                response = await client.get(f"/research/{run_id}")
                response.raise_for_status()
                state = response.json()
                if state["status"] in {"complete", "failed", "insufficient_evidence", "cancelled"}:
                    break
                if monotonic() >= deadline:
                    raise TimeoutError("current model queue probe exceeded wait deadline")
                await asyncio.sleep(2)
            else:
                raise TimeoutError("current model queue probe exceeded wait deadline")
            response = await client.get(f"/research/{run_id}/report")
            response.raise_for_status()
            report = response.json()
        acquisition = state.get("market_acquisition") or {}
        diagnostic = {
            "research_run_id": run_id,
            "status": state["status"],
            "has_intent": state.get("research_intent") is not None,
            "has_plan": state.get("research_plan") is not None,
            "has_synthesis": state.get("research_synthesis") is not None,
            "budget_usage": state.get("budget_usage"),
            "acquisition_bars": acquisition.get("bar_count"),
            "acquisition_quality": acquisition.get("data_quality_status"),
            "news_count": sum(
                item["evidence_type"] == "news_document" for item in state["evidence"]
            ),
            "financial_count": sum(
                item["evidence_type"] == "financial_fact" for item in state["evidence"]
            ),
            "rag_count": sum(item["evidence_type"] == "rag_document" for item in state["evidence"]),
            "rag_modes": sorted({
                item["structured_data"].get("retrieval_mode", "unknown")
                for item in state["evidence"] if item["evidence_type"] == "rag_document"
            }),
            "report_citations": len(report["citations"]),
            "complete_analysis": report["complete_analysis"],
            "gaps": report["gaps"],
        }
        path = Path(tempfile.gettempdir()) / "tradeagent-klac-current-model-durable.json"
        path.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
        print(json.dumps(diagnostic))
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
