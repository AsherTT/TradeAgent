"""Exercise the Gate C mock-worker path through HTTP, Redis, and PostgreSQL."""

import asyncio
import json
from datetime import UTC, datetime
from time import monotonic
from urllib.request import Request, urlopen
from uuid import UUID

from backend.app.contracts.instrument import Instrument
from backend.app.jobs.celery_app import celery_app
from backend.app.persistence.repositories import ResearchRunRepository, SecurityMasterRepository
from backend.app.persistence.session import get_database

API = "http://api:8000"


def _http(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        API + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


async def main() -> None:
    database = get_database()
    instrument = Instrument(
        current_symbol="KLAC",
        exchange="NASDAQ",
        currency="USD",
        asset_type="equity",
        company_name="KLA Corporation Gate C fixture",
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

        synthesis = state["research_synthesis"]
        assert isinstance(synthesis, dict)
        citations = synthesis["evidence_ids"]
        assert isinstance(citations, list) and len(citations) == 1
        assert citations[0] == state["evidence"][0]["evidence_id"]
        transitions = state["runtime_metadata"]["transitions"]
        assert "synthesis" in transitions and transitions[-1] == "finish"

        async with database.sessions() as session:
            stored = await ResearchRunRepository(session).get(UUID(run_id))
            assert stored is not None and stored.research_synthesis is not None
            assert str(stored.research_synthesis.evidence_ids[0]) == citations[0]

        redelivery = celery_app.send_task("research.run", args=[run_id])
        redelivery.get(timeout=30)
        after = _http("GET", f"/research/{run_id}")
        assert after["status"] == "complete"
        assert after["research_synthesis"] == synthesis
        assert after["runtime_metadata"]["transitions"] == transitions
        print(
            json.dumps(
                {
                    "qualified_at": datetime.now(UTC).isoformat(),
                    "research_run_id": run_id,
                    "status": after["status"],
                    "citations": citations,
                    "transitions": transitions,
                    "redelivery": "idempotent",
                }
            )
        )
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
