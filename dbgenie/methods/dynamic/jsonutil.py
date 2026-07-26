from __future__ import annotations

import json
import re
from typing import Any


class LLMJSONParseError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        raw_text: str = "",
        stage: str = "",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.stage = stage
        self.cause = cause


def parse_json_object(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise LLMJSONParseError(
                "LLM output is not a valid JSON object",
                raw_text=raw,
            )
        try:
            value = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMJSONParseError(
                f"LLM output contains an invalid JSON object: {exc}",
                raw_text=raw,
                cause=exc,
            ) from exc
    if not isinstance(value, dict):
        raise LLMJSONParseError(
            "LLM output must be exactly one JSON object",
            raw_text=raw,
        )
    return value
