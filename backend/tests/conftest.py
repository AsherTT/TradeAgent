from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from backend.app.contracts.research import ResearchPlan


@pytest.fixture
def research_plan_payload() -> dict[str, Any]:
    return {
        "question": "Assess the 3-5 day setup",
        "instrument_symbol": "KLAC",
        "horizon": "3-5 days",
        "steps": (
            {
                "step_id": "market_snapshot",
                "objective": "Collect current market state",
                "capability": "market",
                "required": True,
            },
        ),
        "stop_conditions": ("required evidence collected",),
        "evidence_requirements": ("point-in-time market data",),
    }


@pytest.fixture
def research_plan_factory(
    research_plan_payload: dict[str, Any],
) -> Callable[[], ResearchPlan]:
    return lambda: ResearchPlan.model_validate(research_plan_payload)


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC)
