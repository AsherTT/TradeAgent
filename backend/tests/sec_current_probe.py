"""Opt-in two-request SEC diagnostic. Never imported by the ordinary test suite.

Set SEC_USER_AGENT to an identifying application/contact string, then run
python -m backend.tests.sec_current_probe. No key or model call is required.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

from backend.app.config import Settings
from backend.app.financials.sec import SecFinancialClient, SecFinancialError


async def main() -> None:
    agent = os.environ.get("SEC_USER_AGENT") or Settings().sec_user_agent or ""
    if not agent:
        print("SEC probe unavailable: SEC_USER_AGENT is not configured")
        return
    try:
        snapshot = await SecFinancialClient(user_agent=agent).load_current("KLAC")
    except (SecFinancialError, ValueError) as exc:
        print(f"SEC probe unavailable: {exc}")
        return
    path = Path(tempfile.gettempdir()) / "tradeagent-sec-klac-current.json"
    result = snapshot.model_dump(mode="json")
    result["complete_analysis"] = False
    result["historical_pit_qualified"] = False
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"SEC current diagnostic: {len(snapshot.facts)} facts, {len(snapshot.gaps)} gaps; {path}")


if __name__ == "__main__":
    asyncio.run(main())
