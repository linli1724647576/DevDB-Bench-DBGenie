from __future__ import annotations

import re
from typing import Any

from dbgenie.agents.types import AgentTaskInput
from dbgenie.llm.client import LLMClient, LLMMessage

from .contracts import BaselineMethod, BaselineRunResult
from .runtime import runtime_description


def task_prompt_payload(task: AgentTaskInput) -> dict[str, Any]:
    return {
        "requirement": task.requirement,
        "workload": [item.description for item in task.workload],
        "target_dbms": task.target_dbms,
        "runtime": runtime_description(task.target_dbms).to_prompt_dict(),
    }


def generate_once(
    method: BaselineMethod,
    task: AgentTaskInput,
    llm_client: LLMClient,
    *,
    on_attempt_error=None,
) -> BaselineRunResult:
    raw_output = llm_client.complete(
        method.build_messages(task),
        stage=f"baseline:{method.name}",
        on_attempt_error=on_attempt_error,
    )
    final_ddl = normalize_ddl_output(raw_output)
    return BaselineRunResult(
        task_id=task.id,
        status="generated" if final_ddl else "failed",
        final_ddl=final_ddl,
    )


def normalize_ddl_output(raw_output: str) -> str:
    text = str(raw_output or "").strip()
    if not text:
        return ""
    fenced = re.fullmatch(
        r"```(?:sql|ddl|postgresql|postgres|mysql|mariadb|sqlite|duckdb|tsql)?\s*\n?"
        r"(.*?)\n?```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return fenced.group(1).strip() if fenced else text


def messages_to_dict(messages: list[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]
