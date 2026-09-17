"""Pydantic-based structured output validation."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from backend.app.ai.errors import StructuredOutputError

OutputT = TypeVar("OutputT", bound=BaseModel)


class PydanticStructuredOutputAdapter:
    """Create JSON-schema instructions and validate exact JSON responses."""

    @staticmethod
    def schema_instruction(schema: type[BaseModel]) -> str:
        serialized = json.dumps(schema.model_json_schema(), separators=(",", ":"))
        return (
            "Return exactly one JSON value matching this JSON Schema. "
            "Do not wrap it in Markdown or add commentary. Schema: "
            f"{serialized}"
        )

    @staticmethod
    def validate(raw: str | bytes | dict[str, Any], schema: type[OutputT]) -> OutputT:
        try:
            if isinstance(raw, dict):
                return schema.model_validate(raw)
            return schema.model_validate_json(raw)
        except (ValidationError, ValueError, TypeError) as exc:
            raise StructuredOutputError(f"output does not match {schema.__name__}: {exc}") from exc
