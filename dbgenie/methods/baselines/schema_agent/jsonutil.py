from __future__ import annotations

import json
import re
from typing import Any


class SchemaAgentJSONError(ValueError):
    pass


def parse_json_object(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    candidates = [raw]
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidates.append(raw[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise SchemaAgentJSONError("LLM output is not a valid JSON object")


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)
