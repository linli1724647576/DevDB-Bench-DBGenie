from __future__ import annotations

import re
from typing import Any, Callable, Protocol

from dbgenie.agents.tools import AgentToolbox
from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig
from dbgenie.llm.client import LLMClient, LLMMessage

from ..common import messages_to_dict, normalize_ddl_output, task_prompt_payload
from ..contracts import BaselineRunOutcome, BaselineRunResult
from .prompts import (
    PROMPT_VERSION,
    build_decomposer_messages,
    build_refiner_messages,
    selector_state,
)


ProgressCallback = Callable[[str], None]


class DDLExecutor(Protocol):
    def execute_ddl(self, ddl: str, target_dbms: str) -> Any: ...


_FENCED_DDL = re.compile(
    r"```(?:sql|ddl|postgresql|postgres|mysql|mariadb|sqlite|duckdb|tsql|mssql|sqlserver)?"
    r"[ \t]*\r?\n(?P<body>.*?)```",
    flags=re.IGNORECASE | re.DOTALL,
)


def extract_final_ddl(raw_output: str) -> str:
    text = str(raw_output or "").strip()
    if not text:
        return ""
    matching_blocks = [
        match.group("body").strip()
        for match in _FENCED_DDL.finditer(text)
        if "create table" in match.group("body").lower()
    ]
    if matching_blocks:
        return matching_blocks[-1]
    normalized = normalize_ddl_output(text)
    return normalized if "create table" in normalized.lower() else ""


def execute_mac_sql(
    task: AgentTaskInput,
    llm_config: LLMConfig,
    *,
    llm_client_factory: Callable[[LLMConfig], LLMClient] = LLMClient,
    executor: DDLExecutor | None = None,
    progress: ProgressCallback | None = None,
) -> BaselineRunOutcome:
    emit = progress or (lambda _message: None)
    trace: dict[str, Any] = {
        "task_id": task.id,
        "method": "mac-sql",
        "prompt_version": PROMPT_VERSION,
        "input": task_prompt_payload(task),
        "selector": selector_state(),
        "decomposer": {},
        "candidate_execution": None,
        "refiner": {"status": "not_needed"},
        "final_source": None,
        "final_execution_verified": False,
        "model_call_count": 0,
        "llm_attempt_errors": [],
        "warnings": [],
        "errors": [],
    }
    emit("mac_sql selector no-op")
    client = llm_client_factory(llm_config)

    decomposer_messages = build_decomposer_messages(task)
    emit("mac_sql decomposer")
    try:
        raw_candidate = _complete(
            client,
            decomposer_messages,
            stage="baseline:mac-sql:decomposer",
            trace=trace,
        )
    except Exception as exc:
        trace["decomposer"] = {
            "status": "failed",
            "messages": messages_to_dict(decomposer_messages),
            "raw_output": "",
            "candidate_ddl": "",
        }
        trace["errors"].append(_error_text(exc))
        return _outcome(task.id, "", trace)

    candidate_ddl = extract_final_ddl(raw_candidate)
    trace["decomposer"] = {
        "status": "generated" if candidate_ddl else "failed",
        "messages": messages_to_dict(decomposer_messages),
        "raw_output": raw_candidate,
        "candidate_ddl": candidate_ddl,
    }
    if not candidate_ddl:
        trace["errors"].append("DecomposerAgent did not produce a usable DDL script")
        return _outcome(task.id, "", trace)

    ddl_executor = executor or AgentToolbox(execution_mode="docker")
    emit("mac_sql executing candidate")
    try:
        execution = _execution_dict(
            ddl_executor.execute_ddl(candidate_ddl, task.target_dbms)
        )
    except Exception as exc:
        execution = {
            "success": False,
            "error_type": "executor_exception",
            "error_message": str(exc),
            "executor": type(ddl_executor).__name__,
            "real_execution": False,
            "stub": True,
        }
    trace["candidate_execution"] = execution

    execution_verified = bool(execution.get("success")) and bool(
        execution.get("real_execution")
    )
    if execution_verified:
        trace["final_source"] = "decomposer"
        trace["final_execution_verified"] = True
        return _outcome(task.id, candidate_ddl, trace)

    if execution.get("success") and not execution.get("real_execution"):
        trace["warnings"].append(
            "candidate execution returned only a stub; real execution is required"
        )
    else:
        trace["warnings"].append("candidate DDL failed real execution")

    refiner_messages = build_refiner_messages(task, candidate_ddl, execution)
    emit("mac_sql refiner")
    trace["refiner"] = {
        "status": "running",
        "messages": messages_to_dict(refiner_messages),
        "raw_output": "",
        "refined_ddl": "",
        "reexecuted": False,
    }
    try:
        raw_refined = _complete(
            client,
            refiner_messages,
            stage="baseline:mac-sql:refiner",
            trace=trace,
        )
        refined_ddl = extract_final_ddl(raw_refined)
        trace["refiner"].update(
            {
                "status": "generated" if refined_ddl else "failed",
                "raw_output": raw_refined,
                "refined_ddl": refined_ddl,
            }
        )
    except Exception as exc:
        refined_ddl = ""
        trace["refiner"]["status"] = "failed"
        trace["errors"].append(_error_text(exc))

    if refined_ddl:
        trace["final_source"] = "refiner"
        trace["warnings"].append(
            "RefinerAgent output was not re-executed, matching the source workflow"
        )
        return _outcome(task.id, refined_ddl, trace)

    trace["final_source"] = "decomposer_fallback"
    trace["warnings"].append(
        "RefinerAgent did not produce usable DDL; preserving the candidate DDL"
    )
    return _outcome(task.id, candidate_ddl, trace)


def _complete(
    client: LLMClient,
    messages: list[LLMMessage],
    *,
    stage: str,
    trace: dict[str, Any],
) -> str:
    trace["model_call_count"] += 1

    def record_attempt(_error, record: dict[str, Any], total: int) -> None:
        trace["llm_attempt_errors"].append(
            {"stage": stage, "total_attempts": total, **record}
        )

    return client.complete(
        messages,
        stage=stage,
        on_attempt_error=record_attempt,
    )


def _execution_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
    elif isinstance(value, dict):
        payload = dict(value)
    else:
        raise TypeError("DDL executor returned an unsupported result type")
    return payload


def _error_text(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _outcome(task_id: str, final_ddl: str, trace: dict[str, Any]) -> BaselineRunOutcome:
    status = "generated" if final_ddl else "failed"
    trace["status"] = status
    return BaselineRunOutcome(
        result=BaselineRunResult(
            task_id=task_id,
            status=status,
            final_ddl=final_ddl,
        ),
        trace=trace,
    )
