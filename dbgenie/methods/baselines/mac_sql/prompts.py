from __future__ import annotations

import json
from typing import Any

from dbgenie.agents.types import AgentTaskInput
from dbgenie.llm.client import LLMMessage

from ..common import messages_to_dict, task_prompt_payload


PROMPT_VERSION = "mac-sql-adapted-v1"

DECOMPOSER_SYSTEM_PROMPT = """You are DecomposerAgent in a MAC-SQL adaptation for database schema design.

There is no existing database schema. Treat the empty schema in the input as the starting state and design a complete relational schema from the natural-language requirement and workload.

First decompose the task into the entities, relationships, integrity constraints, and workload-driven access paths that the design must support. Then end your response with exactly one fenced `sql` code block containing the complete executable DDL script.

Requirements:
- Target the specified DBMS and runtime.
- Include all required CREATE TABLE statements in dependency-safe form.
- Represent primary keys, foreign keys, uniqueness, nullability, checks, defaults, and indexes when justified by the input.
- Do not emit partial DDL blocks, query examples, data inserts, migrations, or explanatory text after the final DDL block.
"""

REFINER_SYSTEM_PROMPT = """You are RefinerAgent in a MAC-SQL adaptation for database schema design.

The candidate DDL failed when executed by the target DBMS. Repair the complete script using the exact execution error while preserving the requirement, relationships, constraints, and workload support.

Return exactly one fenced `sql` code block containing the complete corrected DDL script and no other text. Do not return a patch or only the failing statement.
"""


def selector_state() -> dict[str, Any]:
    return {
        "input_schema": {"tables": []},
        "selected_schema": {"tables": []},
        "reason": "No existing schema is available for this task; there is nothing to prune.",
        "llm_called": False,
    }


def decomposer_payload(task: AgentTaskInput) -> dict[str, Any]:
    payload = task_prompt_payload(task)
    payload["database_schema"] = {"tables": []}
    return payload


def build_decomposer_messages(task: AgentTaskInput) -> list[LLMMessage]:
    return [
        LLMMessage(role="system", content=DECOMPOSER_SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=json.dumps(decomposer_payload(task), ensure_ascii=False, indent=2),
        ),
    ]


def refiner_payload(
    task: AgentTaskInput,
    candidate_ddl: str,
    execution: dict[str, Any],
) -> dict[str, Any]:
    payload = task_prompt_payload(task)
    payload["database_schema"] = {"tables": []}
    payload["candidate_ddl"] = candidate_ddl
    payload["execution_error"] = execution
    return payload


def build_refiner_messages(
    task: AgentTaskInput,
    candidate_ddl: str,
    execution: dict[str, Any],
) -> list[LLMMessage]:
    return [
        LLMMessage(role="system", content=REFINER_SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=json.dumps(
                refiner_payload(task, candidate_ddl, execution),
                ensure_ascii=False,
                indent=2,
            ),
        ),
    ]


def prompt_catalog(task: AgentTaskInput) -> dict[str, Any]:
    execution_template = {
        "success": False,
        "error_type": "{{error_type}}",
        "error_message": "{{error_message}}",
        "executor": "{{executor}}",
        "real_execution": True,
        "dialect": str(task.target_dbms or ""),
        "runtime_version": "{{runtime_version}}",
    }
    return {
        "selector": selector_state(),
        "decomposer_messages": messages_to_dict(build_decomposer_messages(task)),
        "refiner_messages_template": messages_to_dict(
            build_refiner_messages(task, "{{candidate_ddl}}", execution_template)
        ),
        "limits": {
            "selector_llm_calls": 0,
            "decomposer_llm_calls": 1,
            "refiner_llm_calls": 1,
            "candidate_execution_attempts": 1,
            "reexecute_refined_ddl": False,
        },
    }
