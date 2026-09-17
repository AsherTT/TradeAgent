import json
from typing import Any

import pytest

from backend.app.ai.errors import StructuredOutputError
from backend.app.ai.structured_output import PydanticStructuredOutputAdapter
from backend.app.contracts.research import ResearchPlan


def test_validates_exact_json(research_plan_payload: dict[str, Any]) -> None:
    output = PydanticStructuredOutputAdapter.validate(
        json.dumps(research_plan_payload), ResearchPlan
    )
    assert output.instrument_symbol == "KLAC"


def test_rejects_markdown_wrapped_json(research_plan_payload: dict[str, Any]) -> None:
    raw = f"```json\n{json.dumps(research_plan_payload)}\n```"
    with pytest.raises(StructuredOutputError):
        PydanticStructuredOutputAdapter.validate(raw, ResearchPlan)


def test_schema_instruction_contains_json_schema() -> None:
    instruction = PydanticStructuredOutputAdapter.schema_instruction(ResearchPlan)
    assert "ResearchPlan" in instruction
    assert "Do not wrap it in Markdown" in instruction
