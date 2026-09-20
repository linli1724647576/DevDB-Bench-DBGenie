from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

from dbgenie.agents.types import AgentTaskInput
from dbgenie.llm.client import LLMMessage

from ..common import task_prompt_payload
from ..runtime import runtime_description


PROMPT_VERSION = "few-shot-v1"
EXAMPLE_IDS = (
    "koel_mysql",
    "swirl_postgresql",
    "equipment_sqlite",
)


@dataclass(frozen=True)
class FewShotExample:
    id: str
    source_kind: str
    source_id: str
    input_payload: dict[str, Any]
    output_ddl: str


def build_few_shot_messages(task: AgentTaskInput) -> list[LLMMessage]:
    messages = [LLMMessage(role="system", content=_system_prompt())]
    for example in load_few_shot_examples():
        messages.append(
            LLMMessage(role="user", content=_input_json(_example_prompt_payload(example)))
        )
        messages.append(LLMMessage(role="assistant", content=example.output_ddl))
    messages.append(LLMMessage(role="user", content=_input_json(task_prompt_payload(task))))
    return messages


@lru_cache(maxsize=1)
def load_few_shot_examples() -> tuple[FewShotExample, ...]:
    example_dir = files(__package__).joinpath("examples")
    manifest = json.loads(example_dir.joinpath("manifest.json").read_text(encoding="utf-8"))
    rows = manifest.get("examples") or []
    examples: list[FewShotExample] = []
    for row in rows:
        input_payload = json.loads(
            example_dir.joinpath(str(row["input_file"])).read_text(encoding="utf-8")
        )
        output_ddl = example_dir.joinpath(str(row["output_file"])).read_text(
            encoding="utf-8"
        ).strip()
        examples.append(
            FewShotExample(
                id=str(row["id"]),
                source_kind=str(row["source_kind"]),
                source_id=str(row["source_id"]),
                input_payload=input_payload,
                output_ddl=output_ddl,
            )
        )
    ids = tuple(example.id for example in examples)
    if ids != EXAMPLE_IDS:
        raise ValueError(f"few-shot example order must be {EXAMPLE_IDS}, got {ids}")
    return tuple(examples)


def _example_prompt_payload(example: FewShotExample) -> dict[str, Any]:
    payload = example.input_payload
    target_dbms = str(payload.get("target_dbms") or "")
    return {
        "requirement": str(payload.get("requirement") or ""),
        "workload": [str(item) for item in payload.get("workload") or []],
        "target_dbms": target_dbms,
        "runtime": runtime_description(target_dbms).to_prompt_dict(),
    }


def _input_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _system_prompt() -> str:
    return """
You are a database DDL generator.

For each JSON input, generate one complete database schema as executable DDL for the specified target DBMS and runtime. The requirement describes the data the schema must preserve. The workload contains only natural-language access patterns; use it to infer appropriate relationships, constraints, and indexes.

Return only SQL DDL statements. Do not return Markdown fences, JSON, explanations, tests, sample data, alternative designs, or migration rollback statements. Do not assume access to any reference schema or information beyond the JSON input.
""".strip()
