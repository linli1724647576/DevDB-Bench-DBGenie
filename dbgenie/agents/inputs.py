from __future__ import annotations

from pathlib import Path
from typing import Any

from dbgenie.core.io import read_json

from .types import AgentTaskInput, WorkloadDescription


def load_agent_tasks(
    path: str | Path,
    input_format: str = "auto",
    limit: int | None = None,
) -> list[AgentTaskInput]:
    payload = read_json(path)
    tasks = agent_tasks_from_payload(payload, input_format=input_format)
    return tasks[:limit] if limit else tasks


def agent_tasks_from_payload(
    payload: dict[str, Any],
    input_format: str = "auto",
) -> list[AgentTaskInput]:
    clean_format = input_format.lower()
    if clean_format not in {"auto", "candidate", "task"}:
        raise ValueError(f"unsupported input format: {input_format}")
    if clean_format == "candidate":
        return [_task_from_candidate(item) for item in _candidate_items(payload)]
    if clean_format == "task":
        return [_task_from_task(item) for item in _task_items(payload)]

    if "candidates" in payload:
        return [_task_from_candidate(item) for item in _candidate_items(payload)]
    if "tasks" in payload:
        return [_task_from_task(item) for item in _task_items(payload)]
    return [_task_from_task(payload)]


def _candidate_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        return [item for item in candidates if isinstance(item, dict)]
    if payload.get("requirement") or payload.get("workload"):
        return [payload]
    return []


def _task_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = payload.get("tasks")
    if isinstance(tasks, list):
        return [item for item in tasks if isinstance(item, dict)]
    return [payload]


def _task_from_candidate(candidate: dict[str, Any]) -> AgentTaskInput:
    task_id = str(
        candidate.get("id")
        or candidate.get("full_name")
        or candidate.get("name")
        or "candidate"
    )
    return AgentTaskInput(
        id=_safe_task_id(task_id),
        requirement=str(candidate.get("requirement") or ""),
        workload=_workload_from_any(candidate.get("workload") or []),
        target_dbms=str(candidate.get("target_dbms") or candidate.get("dbms_final") or ""),
        source=str(candidate.get("full_name") or candidate.get("url") or ""),
        metadata={
            "input_kind": "candidate",
            "full_name": candidate.get("full_name"),
            "domain": (
                candidate.get("application_domain_final")
                or candidate.get("domain_final")
                or candidate.get("domain")
            ),
            "ecosystem": candidate.get("ecosystem_final") or candidate.get("ecosystem"),
            "ignored_fields": [
                key for key in ("business_rules", "tests") if key in candidate
            ],
        },
    )


def _task_from_task(task: dict[str, Any]) -> AgentTaskInput:
    task_id = str(task.get("id") or task.get("name") or "task")
    return AgentTaskInput(
        id=_safe_task_id(task_id),
        requirement=str(task.get("requirement") or ""),
        workload=_workload_from_any(task.get("workload") or []),
        target_dbms=str(task.get("target_dbms") or task.get("dbms") or ""),
        source=str(task.get("source") or ""),
        metadata={"input_kind": "task", **dict(task.get("metadata") or {})},
    )


def _workload_from_any(value: Any) -> list[WorkloadDescription]:
    if isinstance(value, str):
        return [WorkloadDescription.from_any(value, 1)] if value.strip() else []
    if isinstance(value, list):
        return [
            WorkloadDescription.from_any(item, index)
            for index, item in enumerate(value, start=1)
        ]
    if isinstance(value, dict):
        return [WorkloadDescription.from_any(value, 1)]
    return []


def _safe_task_id(value: str) -> str:
    cleaned = value.strip().replace("\\", "/").replace("/", "__")
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in cleaned)
    return cleaned or "task"
