"""Exercise the Phase 6 command and immutable forecast on PostgreSQL."""

import asyncio
import json
import os
from datetime import UTC, datetime
from time import monotonic
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError

from backend.app.contracts.instrument import Instrument
from backend.app.contracts.thesis import ForecastRecord
from backend.app.persistence.models import (
    ForecastRecordRow,
    ModelExecutionRow,
    ThesisEvidenceRow,
    ThesisVersionRow,
)
from backend.app.persistence.repositories import SecurityMasterRepository
from backend.app.persistence.session import get_database

API = "http://api:8000"
TOKEN = os.environ["PHASE6_WRITE_TOKEN"]


def _http(
    method: str, path: str, payload: dict[str, object] | None = None, *, guarded: bool = False
) -> dict[str, object]:
    request = Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Content-Type": "application/json",
            **({"X-Phase6-Write-Token": TOKEN} if guarded else {}),
        },
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


async def _reject_mutation(database: object, forecast_id: UUID, *, remove: bool) -> None:
    async with database.sessions() as session, session.begin():
        try:
            statement = (
                delete(ForecastRecordRow).where(ForecastRecordRow.forecast_id == forecast_id)
                if remove
                else update(ForecastRecordRow)
                .where(ForecastRecordRow.forecast_id == forecast_id)
                .values(probability=0.1)
            )
            await session.execute(statement)
        except DBAPIError as exc:
            assert "forecast records are immutable" in str(exc.orig)
            await session.rollback()
        else:
            raise AssertionError("PostgreSQL accepted a ForecastRecord mutation")


async def _reject_thesis_mutation(database: object, thesis_id: UUID, *, remove: bool) -> None:
    async with database.sessions() as session, session.begin():
        try:
            statement = (
                delete(ThesisVersionRow).where(ThesisVersionRow.thesis_id == thesis_id)
                if remove
                else update(ThesisVersionRow)
                .where(ThesisVersionRow.thesis_id == thesis_id)
                .values(status="invalidated")
            )
            await session.execute(statement)
        except DBAPIError as exc:
            assert "phase 6 history is immutable" in str(exc.orig)
            await session.rollback()
        else:
            raise AssertionError("PostgreSQL accepted a ThesisVersion mutation")


async def main() -> None:
    database = get_database()
    instrument = Instrument(
        current_symbol="P6" + uuid4().hex[:8].upper(),
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="Phase 6 fixture",
    )
    try:
        async with database.sessions() as session, session.begin():
            await SecurityMasterRepository(session).add_instrument(instrument)
        accepted = _http(
            "POST",
            "/research",
            {
                "instrument_id": str(instrument.instrument_id),
                "ticker": "KLAC",
                "query": "Assess the setup",
                "horizon": "3-5 days",
                "timestamp_mode": "fixed_cutoff",
                "replay_integrity_level": "research_replay",
            },
        )
        run_id = str(accepted["research_run_id"])
        deadline = monotonic() + 45
        while monotonic() < deadline:
            state = _http("GET", f"/research/{run_id}")
            if state["status"] == "complete":
                break
            if state["status"] in {"failed", "insufficient_evidence", "cancelled"}:
                raise AssertionError(f"unexpected terminal status: {state['status']}")
            await asyncio.sleep(0.5)
        else:
            raise AssertionError("research run did not complete in 45 seconds")
        thesis_id = uuid4()
        response = _http(
            "POST",
            f"/research/{run_id}/theses",
            {
                "thesis_id": str(thesis_id),
                "direction": "bullish",
                "direction_probability": 0.6,
                "summary": "Qualified fixture bullish thesis",
                "bull_case": "Trend persists",
                "bear_case": "Trend weakens",
                "invalidation_conditions": ["close below 90"],
                "confidence": 0.5,
            },
            guarded=True,
        )
        revision = response["revision"]
        forecast = response["forecast"]
        assert revision["version"] == 1
        assert forecast["frozen"] is True
        assert forecast["evidence_ids"] == revision["thesis"]["evidence_ids"]
        assert forecast["model_execution_ids"]
        forecast_id = UUID(forecast["forecast_id"])
        async with database.sessions() as session:
            stored = await session.get(ForecastRecordRow, forecast_id)
            assert stored is not None
            execution_id = UUID(forecast["model_execution_ids"][0])
            execution = await session.get(ModelExecutionRow, execution_id)
            assert execution is not None
            assert execution.output_json["forecast_direction"] == forecast["direction"]
            assert execution.output_json["forecast_probability"] == forecast["probability"]
            assert ForecastRecord.model_validate_json(
                json.dumps(stored.record_json)
            ) == ForecastRecord.model_validate_json(json.dumps(forecast))
            version = await session.get(ThesisVersionRow, (thesis_id, 1))
            assert version is not None
            evidence_id = UUID(forecast["evidence_ids"][0])
            assert await session.get(ThesisEvidenceRow, (thesis_id, 1, evidence_id))
        await _reject_mutation(database, forecast_id, remove=False)
        await _reject_mutation(database, forecast_id, remove=True)
        await _reject_thesis_mutation(database, thesis_id, remove=False)
        await _reject_thesis_mutation(database, thesis_id, remove=True)
        print(
            json.dumps(
                {
                    "qualified_at": datetime.now(UTC).isoformat(),
                    "research_run_id": run_id,
                    "thesis_id": str(thesis_id),
                    "forecast_id": str(forecast_id),
                    "status": state["status"],
                    "citations": forecast["evidence_ids"],
                    "immutability": "UPDATE and DELETE rejected",
                }
            )
        )
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
