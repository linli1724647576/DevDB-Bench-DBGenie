from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.construction.reference_ddl import normalize_dialect
from dbgenie.llm.client import LLMMessage

from .contracts import CANONICAL_FAILURE_TYPES, ROLE_DISPLAY_NAMES, ROLE_ORDER


SKILL_DIR = Path(__file__).with_name("skills")
DIALECT_CARD_DIR = Path(__file__).with_name("dialect_cards")


def build_role_messages(
    role: str,
    task_payload: dict[str, Any],
    artifacts: dict[str, Any],
    revision: dict[str, Any] | None = None,
    shared_messages: list[dict[str, Any]] | None = None,
    private_context: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    if role not in ROLE_ORDER:
        raise ValueError(f"unknown agent role: {role}")
    user_payload = {
        "task": task_payload,
        "shared_artifacts": artifacts,
        "group_chat_messages": shared_messages or [],
        "role_private_context": private_context or {},
    }
    if revision:
        user_payload["revision_request"] = revision
    return [
        LLMMessage(role="system", content=_role_system_prompt(role, task_payload)),
        LLMMessage(
            role="user",
            content=(
                "Return only valid JSON. Do not wrap the response in Markdown.\n"
                + json.dumps(user_payload, ensure_ascii=False, indent=2)
            ),
        ),
    ]


def messages_to_dict(messages: list[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]


def _role_system_prompt(role: str, task_payload: dict[str, Any]) -> str:
    sections = [
        _load_skill(role),
        _canonical_contract_prompt(),
    ]
    dialect_card = _load_dialect_card(role, task_payload)
    if dialect_card:
        sections.append(dialect_card)
    return "\n\n".join(sections)


def _load_skill(role: str) -> str:
    path = SKILL_DIR / f"{role}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return f"# {ROLE_DISPLAY_NAMES.get(role, role)}\n\nFollow the canonical contract."


def _load_dialect_card(role: str, task_payload: dict[str, Any]) -> str:
    if role not in {
        "logical_model_designer",
        "physical_design_specialist",
        "dialect_compiler",
        "test_expert",
    }:
        return ""
    dialect = normalize_dialect(str(task_payload.get("target_dbms") or ""))
    if not dialect:
        return ""
    path = DIALECT_CARD_DIR / f"{dialect}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _canonical_contract_prompt() -> str:
    return (
        "# Canonical Contract\n\n"
        "Use these exact canonical role ids when writing `owner` fields:\n"
        + json.dumps(ROLE_ORDER, ensure_ascii=False)
        + "\n\nUse these canonical failure_type values unless a more specific "
        "project-local value is unavoidable:\n"
        + json.dumps(CANONICAL_FAILURE_TYPES, ensure_ascii=False)
        + "\n\nFor SchemaIR, use these exact field names: "
        "`tables`, `name`, `columns`, `type`, `nullable`, `identity`, `primary_key`, "
        "`foreign_keys`, `ref_table`, `ref_columns`, `unique_constraints`, "
        "`check_constraints`, `indexes`. "
        "`identity` is an optional boolean column field for DB-managed surrogate "
        "integer keys. "
        "For `primary_key`, output a list of column names. "
        "For each foreign key, output `columns`, `ref_table`, and `ref_columns`. "
        "For PhysicalPlan indexes, use `table`, `name`, `columns`, `unique`, "
        "`include`, and `filter`. "
        "Do not use aliases such as `referenced_table`, `referenced_columns`, "
        "`logical_model`, or `physical_plan` in feedback owners."
    )
