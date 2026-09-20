from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .definition import FULL_REQUIRED_EXPERT_CONTEXT
from .state import DynamicMethodState
from .normalization import current_third_normal_form_evidence


DEFAULT_CONTEXT_CHAR_BUDGET = 50000

REQUIRED_EXPERT_CONTEXT: dict[str, tuple[tuple[str, str], ...]] = dict(
    FULL_REQUIRED_EXPERT_CONTEXT
)

VALID_CONTEXT_SOURCES = {
    "task",
    "budget",
    "readiness",
    "artifact",
    "turn",
    "failure_event",
    "tool_request_proposal",
    "tool_result",
    "repair_history",
    "open_assumptions",
    "warnings",
    "errors",
}

VALID_CONTEXT_VIEWS = {"summary", "full"}


@dataclass(frozen=True)
class ContextSelectionItem:
    source: str
    view: str = "summary"
    key: str = ""
    item_id: str = ""
    reason: str = ""
    max_chars: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextSelectionItem":
        source = str(data.get("source") or data.get("type") or "").strip()
        key = str(data.get("key") or data.get("artifact") or data.get("target_artifact") or "").strip()
        source, key = _normalize_context_source_key(source, key)
        view = str(data.get("view") or "summary").strip().lower()
        if view not in VALID_CONTEXT_VIEWS:
            view = "summary"
        raw_max_chars = data.get("max_chars") or 0
        try:
            max_chars = int(raw_max_chars)
        except (TypeError, ValueError):
            max_chars = 0
        return cls(
            source=source,
            view=view,
            key=key,
            item_id=str(data.get("id") or data.get("item_id") or ""),
            reason=str(data.get("reason") or ""),
            max_chars=max_chars,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "source": self.source,
            "view": self.view,
            "key": self.key,
            "id": self.item_id,
            "reason": self.reason,
        }
        if self.max_chars:
            payload["max_chars"] = self.max_chars
        return payload


@dataclass(frozen=True)
class ContextSelection:
    items: list[ContextSelectionItem] = field(default_factory=list)
    max_chars: int = DEFAULT_CONTEXT_CHAR_BUDGET
    reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ContextSelection":
        if not isinstance(data, dict):
            return cls()
        payload = _unwrap_selection_payload(data)
        raw_max_chars = payload.get("max_chars") or DEFAULT_CONTEXT_CHAR_BUDGET
        try:
            max_chars = int(raw_max_chars)
        except (TypeError, ValueError):
            max_chars = DEFAULT_CONTEXT_CHAR_BUDGET
        max_chars = max(0, max_chars)
        return cls(
            items=_selection_items_from_payload(payload),
            max_chars=max_chars,
            reason=str(payload.get("reason") or ""),
            raw=dict(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "max_chars": self.max_chars,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MaterializedContext:
    selection: dict[str, Any]
    items: list[dict[str, Any]]
    total_chars: int
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection": self.selection,
            "items": self.items,
            "total_chars": self.total_chars,
            "truncated": self.truncated,
            "warnings": self.warnings,
        }


def build_state_catalog(state: DynamicMethodState) -> dict[str, Any]:
    return {
        "task": {
            "ref": "task",
            "id": state.task.id,
            "target_dbms": state.task.target_dbms,
            "source": state.task.source,
            "requirement_chars": len(str(state.task.requirement or "")),
            "workload_count": len(state.task.workload),
            "metadata_keys": list((state.task.metadata or {}).keys())[:20],
        },
        "budget": {
            "ref": "budget",
            "max_turns": state.max_turns,
            "used_turns": state.normal_scheduler_steps_used(),
            "max_scheduler_steps": state.max_turns,
            "used_scheduler_steps": state.normal_scheduler_steps_used(),
            "remaining_scheduler_steps": state.remaining_scheduler_steps(),
            "total_scheduler_decisions": state.scheduler_steps,
            "trace_event_count": len(state.turns),
            "finalize_reserve_used": state.finalize_reserve_used,
            "max_repairs": state.max_repairs,
            "used_repairs": state.repair_budget_used(),
            "current_phase": state.current_phase,
            "final_ddl_ready": bool(str(state.final_ddl or "").strip()),
        },
        "readiness": _build_readiness_catalog(state),
        "artifact_keys": sorted(state.artifacts.keys()),
        "artifacts": {
            key: {
                "ref": key,
                "status": record.status,
                "version": record.version,
                "producer": record.producer,
                "declared_dependencies": list(
                    state.method_definition.artifact_dependencies.get(key, ())
                ),
                "depends_on_versions": record.depends_on_versions,
                "stale": record.stale,
                "stale_reasons": record.stale_reasons,
                "validation_keys": list((record.validation or {}).keys())[:20],
                "payload_type": type(record.payload).__name__,
                "payload_chars": _json_chars(record.payload),
                "summary": _shape_summary(record.payload),
            }
            for key, record in state.artifacts.items()
        },
        "turns": [
            {
                "ref": f"turn_{turn.index}",
                "index": turn.index,
                "speaker": turn.speaker,
                "kind": turn.kind,
                "status": turn.status,
                "action_type": turn.action.get("action_type", "") if isinstance(turn.action, dict) else "",
                "output_type": type(turn.output).__name__,
                "output_chars": _json_chars(turn.output),
                "metadata_keys": list(turn.metadata.keys())[:20],
                "warning_count": len(turn.warnings),
                "error_count": len(turn.errors),
            }
            for turn in state.turns
        ],
        "failure_events": [
            {
                "ref": event.event_id or f"failure_event_{index}",
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "source": event.source,
                "suspected_owner": event.suspected_owner,
                "affected_artifacts": event.affected_artifacts,
                "evidence_chars": _json_chars(event.evidence),
            }
            for index, event in enumerate(state.failure_events, start=1)
        ],
        "tool_results": [
            {
                "ref": f"tool_result_{index}",
                "tool_type": _nested_get(item, ["request", "tool_type"]),
                "target_artifact": _nested_get(item, ["request", "target_artifact"]),
                "result_type": type(item.get("result") if isinstance(item, dict) else item).__name__,
                "result_chars": _json_chars(item.get("result") if isinstance(item, dict) else item),
                "result_status": _tool_result_status(item.get("result") if isinstance(item, dict) else item),
            }
            for index, item in enumerate(state.tool_results, start=1)
        ],
        "tool_request_proposals": [
            {
                "ref": str(item.get("proposal_id") or f"tool_request_proposal_{index}") if isinstance(item, dict) else f"tool_request_proposal_{index}",
                "proposal_id": str(item.get("proposal_id") or "") if isinstance(item, dict) else "",
                "proposer_role": str(item.get("proposer_role") or "") if isinstance(item, dict) else "",
                "tool_type": str(item.get("tool_type") or "") if isinstance(item, dict) else "",
                "target_artifact": str(item.get("target_artifact") or "") if isinstance(item, dict) else "",
                "expected_interpreter": str(item.get("expected_interpreter") or "") if isinstance(item, dict) else "",
                "status": str(item.get("status") or "") if isinstance(item, dict) else "",
                "validation_errors": item.get("validation_errors") or [] if isinstance(item, dict) else [],
                "reason_chars": len(str(item.get("reason") or "")) if isinstance(item, dict) else 0,
            }
            for index, item in enumerate(state.tool_request_proposals, start=1)
        ],
        "repair_history": [
            {
                "ref": str(item.get("repair_id") or f"repair_{index}") if isinstance(item, dict) else f"repair_{index}",
                "repair_id": str(item.get("repair_id") or "") if isinstance(item, dict) else "",
                "status": str(item.get("status") or "") if isinstance(item, dict) else "",
                "event_type": str(item.get("event_type") or "") if isinstance(item, dict) else "",
                "repair_artifacts": item.get("repair_artifacts") or [] if isinstance(item, dict) else [],
                "keys": list(item.keys())[:20] if isinstance(item, dict) else [],
                "chars": _json_chars(item),
            }
            for index, item in enumerate(state.repair_history, start=1)
        ],
        "open_assumptions": {
            "ref": "open_assumptions",
            "count": len(state.open_assumptions),
            "chars": _json_chars(state.open_assumptions),
        },
        "warnings": {"ref": "warnings", "count": len(state.warnings), "chars": _json_chars(state.warnings)},
        "errors": {"ref": "errors", "count": len(state.errors), "chars": _json_chars(state.errors)},
        "selectable_sources": sorted(state.method_definition.scheduler_context_sources),
        "views": sorted(VALID_CONTEXT_VIEWS),
    }


def _normalize_context_source_key(source: str, key: str) -> tuple[str, str]:
    clean_source = source.strip().lower()
    clean_key = key.strip()
    key_alias = clean_key.lower().replace("-", "_").replace(" ", "_")

    source_aliases = {
        "artifacts": "artifact",
        "ready": "readiness",
        "readiness_summary": "readiness",
        "tool_results": "tool_result",
        "tool_request_proposals": "tool_request_proposal",
        "repairs": "repair_history",
        "repair": "repair_history",
        "warning": "warnings",
        "error": "errors",
        "assumptions": "open_assumptions",
    }
    clean_source = source_aliases.get(clean_source, clean_source)

    if clean_source == "artifact":
        if key_alias in {"task", "workload", "workloads", "requirement", "requirements", "task_metadata"}:
            return "task", ""
        if key_alias in {"budget", "run_budget", "turn_budget", "token_budget"}:
            return "budget", ""
        if key_alias in {"warning", "warnings"}:
            return "warnings", ""
        if key_alias in {"error", "errors"}:
            return "errors", ""
        if key_alias in {"open_assumptions", "assumptions"}:
            return "open_assumptions", ""
    return clean_source, clean_key


def _build_readiness_catalog(state: DynamicMethodState) -> dict[str, Any]:
    ddl = str(state.artifact_payload("ddl", "") or state.final_ddl or "")
    test_report_record = state.artifacts.get("test_report")
    test_report_produced = bool(
        test_report_record is not None and test_report_record.version > 0
    )
    test_report = state.artifact_payload("test_report", {}) or {}
    generated_tests = test_report.get("generated_tests") if isinstance(test_report, dict) else []
    generated_test_count = len(generated_tests) if isinstance(generated_tests, list) else 0
    test_report_passed = test_report.get("passed") if isinstance(test_report, dict) else None
    artifact_needs_revision = [
        key
        for key, record in state.artifacts.items()
        if record.status == "needs_revision"
    ]
    stale_artifacts = [
        key
        for key, record in state.artifacts.items()
        if record.stale and record.version > 0
    ]
    pending_proposals = [
        item
        for item in state.tool_request_proposals
        if isinstance(item, dict) and item.get("status") == "pending"
    ]
    pending_sql_proposals = [
        item
        for item in pending_proposals
        if item.get("tool_type") == "sql_test_runner"
        and item.get("target_artifact") == "test_report"
        and not item.get("validation_errors")
    ]
    latest_ddl = _latest_tool_result(state, "ddl_executor")
    latest_sql = _latest_tool_result(state, "sql_test_runner")
    latest_query_plan = _latest_tool_result(state, "query_plan_tool")
    ddl_real = bool((latest_ddl or {}).get("real_execution"))
    ddl_success = bool((latest_ddl or {}).get("success"))
    sql_real = bool((latest_sql or {}).get("real_execution"))
    sql_passed = bool((latest_sql or {}).get("passed"))
    sql_test_count = _int_from_keys(latest_sql or {}, "sql_test_count", "test_count")
    if state.method_definition.orchestration_mode == "fixed_pipeline":
        query_plan_required = latest_query_plan is not None
    else:
        query_plan_required = _query_plan_required_for_readiness(
            state,
            generated_tests,
            sql_real=sql_real,
            sql_passed=sql_passed,
            sql_test_count=sql_test_count,
        )
    query_plan_has_raw_evidence = _query_plan_has_executed_observation(latest_query_plan)
    logical_record = state.artifacts.get("logical_model")
    logical_version = int(logical_record.version if logical_record is not None else 0)
    normalization_evidence = (
        current_third_normal_form_evidence(state)
        if state.method_definition.normalization_validation_required
        else None
    )
    normalization_ref = normalization_evidence[0] if normalization_evidence else ""
    normalization_result = (
        normalization_evidence[1].get("result")
        if normalization_evidence and isinstance(normalization_evidence[1], dict)
        else None
    )
    if not isinstance(normalization_result, dict):
        normalization_result = None
    normalization_passed = (
        bool(normalization_result.get("passed"))
        if normalization_result is not None
        else None
    )
    ddl_execution_verified = bool(ddl.strip()) and (
        (ddl_success and ddl_real)
        or (sql_passed and sql_real and sql_test_count > 0)
    )
    design_completion = design_only_completion_status(state)
    if state.method_definition.runtime_verification_required:
        ready_evidence = bool(
            ddl_execution_verified
            and test_report_produced
            and generated_test_count > 0
            and sql_passed
            and sql_real
            and sql_test_count > 0
        )
        finalize_blockers: list[str] = []
        if not ddl.strip():
            finalize_blockers.append("ddl_missing")
        if artifact_needs_revision:
            finalize_blockers.append("artifact_needs_revision")
        if not test_report_produced:
            finalize_blockers.append("test_report_missing")
        elif generated_test_count <= 0:
            finalize_blockers.append("generated_tests_missing")
        if (
            test_report_record is not None
            and test_report_record.version > 0
            and test_report_record.stale
        ):
            finalize_blockers.append("stale_test_report")
        if test_report_passed is False:
            finalize_blockers.append("test_report_not_passed")
        if generated_test_count > 0 and not (sql_real and sql_test_count > 0):
            finalize_blockers.append("generated_tests_without_real_sql_runner")
        if latest_sql and not sql_passed:
            finalize_blockers.append("latest_sql_test_runner_failed")
        if pending_sql_proposals:
            finalize_blockers.append("pending_sql_test_runner_proposal")
        if query_plan_required and not query_plan_has_raw_evidence:
            finalize_blockers.append("query_plan_without_raw_evidence")
        if ddl.strip() and not ddl_execution_verified:
            finalize_blockers.append("missing_real_execution_evidence")
        if (
            state.method_definition.normalization_validation_required
            and logical_version > 0
            and normalization_result is None
        ):
            finalize_blockers.append("normalization_validation_missing")
        elif (
            state.method_definition.normalization_validation_required
            and logical_version > 0
            and normalization_passed is False
        ):
            finalize_blockers.append("normalization_validation_failed")
    else:
        ready_evidence = bool(design_completion["ready"])
        finalize_blockers = list(design_completion["blockers"])

    readiness = {
        "ddl_present": bool(ddl.strip()),
        "ready_evidence": ready_evidence,
        "finalize_blockers": finalize_blockers,
        "verification_mode": state.method_definition.verification_mode,
        "runtime_verification_required": state.method_definition.runtime_verification_required,
        "missing_active_artifacts": design_completion["missing_active_artifacts"],
        "artifact_needs_revision": artifact_needs_revision,
        "stale_artifacts": stale_artifacts,
        "test_report_produced": test_report_produced,
        "generated_test_count": generated_test_count,
        "test_report_passed": test_report_passed if isinstance(test_report_passed, bool) else None,
        "query_plan_required": query_plan_required,
        "query_plan_has_raw_evidence": query_plan_has_raw_evidence,
        "normalization": {
            "required": bool(
                state.method_definition.normalization_validation_required
                and logical_version > 0
            ),
            "logical_model_version": logical_version,
            "current_evidence": normalization_result is not None,
            "passed": normalization_passed,
            "disabled_reason": (
                "disabled because third-normal-form validation belongs to the ablated scheduler"
                if not state.method_definition.normalization_validation_required
                else ""
            ),
            "tool_result_ref": normalization_ref,
            "violation_count": _int_from_keys(normalization_result or {}, "violation_count"),
        },
        "ddl_executor": {
            "attempted": latest_ddl is not None,
            "real_execution": ddl_real,
            "success": ddl_success if latest_ddl else None,
            "executor": (latest_ddl or {}).get("executor", ""),
        },
        "sql_test_runner": {
            "attempted": latest_sql is not None,
            "real_execution": sql_real,
            "passed": sql_passed if latest_sql else None,
            "test_count": sql_test_count,
            "executor": (latest_sql or {}).get("executor", ""),
        },
        "query_plan_tool": {
            "attempted": latest_query_plan is not None,
            "has_raw_evidence": query_plan_has_raw_evidence,
            "executor": (latest_query_plan or {}).get("executor", ""),
        },
        "pending_tool_request_count": len(pending_proposals),
        "pending_sql_test_request_count": len(pending_sql_proposals),
        "pending_tool_request_refs": [
            str(item.get("proposal_id") or "")
            for item in pending_proposals[:10]
        ],
    }
    if not state.method_definition.runtime_verification_required:
        for key in (
            "test_report_produced",
            "generated_test_count",
            "test_report_passed",
            "query_plan_required",
            "query_plan_has_raw_evidence",
            "ddl_executor",
            "sql_test_runner",
            "query_plan_tool",
            "pending_sql_test_request_count",
        ):
            readiness.pop(key, None)
    return readiness


def design_only_completion_status(state: DynamicMethodState) -> dict[str, Any]:
    active_artifacts = tuple(dict.fromkeys(state.method_definition.artifact_by_role.values()))
    relevant_artifacts = tuple(dict.fromkeys([*active_artifacts, "ddl"]))
    missing_active_artifacts = [
        key
        for key in active_artifacts
        if key not in state.artifacts or state.artifacts[key].version <= 0
    ]
    needs_revision = [
        key
        for key in relevant_artifacts
        if key in state.artifacts
        and state.artifacts[key].version > 0
        and state.artifacts[key].status == "needs_revision"
    ]
    stale_artifacts = [
        key
        for key in relevant_artifacts
        if key in state.artifacts
        and state.artifacts[key].version > 0
        and state.artifacts[key].stale
    ]
    ddl = str(state.artifact_payload("ddl", "") or state.final_ddl or "")
    logical_record = state.artifacts.get("logical_model")
    logical_version = int(logical_record.version if logical_record is not None else 0)
    normalization_evidence = current_third_normal_form_evidence(state)
    normalization_result = (
        normalization_evidence[1].get("result")
        if normalization_evidence and isinstance(normalization_evidence[1], dict)
        else None
    )
    if not isinstance(normalization_result, dict):
        normalization_result = None

    blockers: list[str] = []
    if missing_active_artifacts:
        blockers.append("active_artifacts_missing")
    if not ddl.strip():
        blockers.append("ddl_missing")
    if needs_revision:
        blockers.append("artifact_needs_revision")
    if stale_artifacts:
        blockers.append("stale_artifacts")
    if logical_version > 0 and normalization_result is None:
        blockers.append("normalization_validation_missing")
    elif logical_version > 0 and not normalization_result.get("passed"):
        blockers.append("normalization_validation_failed")

    return {
        "ready": not blockers,
        "blockers": blockers,
        "missing_active_artifacts": missing_active_artifacts,
        "artifact_needs_revision": needs_revision,
        "stale_artifacts": stale_artifacts,
    }


def materialize_context(
    state: DynamicMethodState,
    selection: ContextSelection | dict[str, Any] | None,
    *,
    allowed_sources: set[str] | frozenset[str] | None = None,
) -> MaterializedContext:
    parsed = selection if isinstance(selection, ContextSelection) else ContextSelection.from_dict(selection)
    effective_allowed_sources = (
        state.method_definition.scheduler_context_sources
        if allowed_sources is None
        else frozenset(allowed_sources)
    )
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    total_chars = 0

    for item in parsed.items:
        if item.source not in VALID_CONTEXT_SOURCES:
            warnings.append(f"unknown context source: {item.source}")
            continue
        if item.source not in effective_allowed_sources:
            warnings.append(
                f"context source not allowed for method variant "
                f"{state.method_definition.name}: {item.source}"
            )
            continue
        content, item_warnings = _lookup_context_content(state, item)
        warnings.extend(item_warnings)
        content = _view_content(content, item.view)
        materialized_content = content
        content_chars = _json_chars(content)
        item_truncated = False
        total_chars += content_chars
        items.append(
            {
                "source": item.source,
                "key": item.key,
                "id": item.item_id,
                "view": item.view,
                "reason": item.reason,
                "content": materialized_content,
                "content_chars": content_chars,
                "truncated": item_truncated,
            }
        )

    return MaterializedContext(
        selection=parsed.to_dict(),
        items=items,
        total_chars=total_chars,
        truncated=False,
        warnings=warnings,
    )


def materialize_expert_context(
    state: DynamicMethodState,
    role: str,
    selection: ContextSelection | dict[str, Any] | None,
) -> MaterializedContext:
    parsed = selection if isinstance(selection, ContextSelection) else ContextSelection.from_dict(selection)
    effective_items = list(parsed.items)
    required_warnings: list[str] = []

    required_context = state.method_definition.required_expert_context
    for source, key in required_context.get(role, ()):
        matching_indexes = [
            index
            for index, item in enumerate(effective_items)
            if _context_item_matches(item, source=source, key=key)
        ]
        if matching_indexes:
            first_index = matching_indexes[0]
            effective_items[first_index] = _full_context_item(effective_items[first_index])
            for duplicate_index in reversed(matching_indexes[1:]):
                del effective_items[duplicate_index]
        else:
            effective_items.append(
                ContextSelectionItem(
                    source=source,
                    key=key,
                    view="full",
                    reason=f"harness-required context for {role}",
                )
            )

        if source == "artifact":
            record = state.artifacts.get(key)
            if record is None or record.version <= 0:
                required_warnings.append(
                    f"required expert context unavailable for {role}: {key} has no produced version"
                )
            elif record.stale:
                required_warnings.append(
                    f"required expert context is stale for {role}: {key} version {record.version}"
                )

    effective_selection = ContextSelection(
        items=effective_items,
        max_chars=parsed.max_chars,
        reason=parsed.reason,
        raw=parsed.raw,
    )
    materialized = materialize_context(
        state,
        effective_selection,
        allowed_sources=state.method_definition.expert_context_sources(role),
    )
    if not required_warnings:
        return materialized
    return MaterializedContext(
        selection=materialized.selection,
        items=materialized.items,
        total_chars=materialized.total_chars,
        truncated=materialized.truncated,
        warnings=[*materialized.warnings, *required_warnings],
    )


def _context_item_matches(item: ContextSelectionItem, *, source: str, key: str) -> bool:
    if item.source != source:
        return False
    return source != "artifact" or item.key == key


def _full_context_item(item: ContextSelectionItem) -> ContextSelectionItem:
    if item.view == "full":
        return item
    return ContextSelectionItem(
        source=item.source,
        view="full",
        key=item.key,
        item_id=item.item_id,
        reason=item.reason,
        max_chars=item.max_chars,
    )


def _unwrap_selection_payload(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("decision_context_selection", "execution_context_selection", "context_selection"):
        nested = data.get(key)
        if isinstance(nested, dict):
            return nested
    return data


def _selection_items_from_payload(payload: dict[str, Any]) -> list[ContextSelectionItem]:
    raw_items = payload.get("items")
    if isinstance(raw_items, list):
        return [ContextSelectionItem.from_dict(item) for item in raw_items if isinstance(item, dict)]

    items: list[ContextSelectionItem] = []
    if payload.get("task"):
        task_payload = payload["task"] if isinstance(payload["task"], dict) else {}
        items.append(ContextSelectionItem.from_dict({"source": "task", **task_payload}))
    for key, source in (
        ("artifacts", "artifact"),
        ("turns", "turn"),
        ("failure_events", "failure_event"),
        ("tool_request_proposals", "tool_request_proposal"),
        ("tool_results", "tool_result"),
        ("repair_history", "repair_history"),
    ):
        values = payload.get(key)
        if isinstance(values, list):
            for value in values:
                if isinstance(value, dict):
                    items.append(ContextSelectionItem.from_dict({"source": source, **value}))
                else:
                    field = "key" if source == "artifact" else "id"
                    items.append(ContextSelectionItem.from_dict({"source": source, field: str(value)}))
    for source in ("budget", "open_assumptions", "warnings", "errors"):
        value = payload.get(source)
        if value:
            item_payload = value if isinstance(value, dict) else {}
            items.append(ContextSelectionItem.from_dict({"source": source, **item_payload}))
    return items


def _lookup_context_content(state: DynamicMethodState, item: ContextSelectionItem) -> tuple[Any, list[str]]:
    if item.source == "task":
        return state.task.to_dict(), []
    if item.source == "budget":
        return {
            "current_phase": state.current_phase,
            "max_turns": state.max_turns,
            "used_turns": state.normal_scheduler_steps_used(),
            "max_scheduler_steps": state.max_turns,
            "used_scheduler_steps": state.normal_scheduler_steps_used(),
            "remaining_scheduler_steps": state.remaining_scheduler_steps(),
            "total_scheduler_decisions": state.scheduler_steps,
            "trace_event_count": len(state.turns),
            "finalize_reserve_used": state.finalize_reserve_used,
            "max_repairs": state.max_repairs,
            "used_repairs": state.repair_budget_used(),
            "final_ddl_ready": bool(str(state.final_ddl or "").strip()),
        }, []
    if item.source == "readiness":
        return _build_readiness_catalog(state), []
    if item.source == "artifact":
        record = state.artifacts.get(item.key)
        if record is None:
            return None, [f"missing artifact: {item.key}"]
        return record.to_dict(), []
    if item.source == "turn":
        return _lookup_by_ref(
            [turn.to_dict() for turn in state.turns],
            item.item_id,
            lambda value, _index: f"turn_{value.get('index')}",
            "turn",
        )
    if item.source == "failure_event":
        return _lookup_by_ref(
            [event.to_dict() for event in state.failure_events],
            item.item_id,
            lambda value, index: str(value.get("event_id") or f"failure_event_{index}"),
            "failure_event",
        )
    if item.source == "tool_result":
        return _lookup_by_ref(
            list(state.tool_results),
            item.item_id,
            lambda _value, index: f"tool_result_{index}",
            "tool_result",
        )
    if item.source == "tool_request_proposal":
        return _lookup_by_ref(
            list(state.tool_request_proposals),
            item.item_id,
            lambda value, index: str(value.get("proposal_id") or f"tool_request_proposal_{index}") if isinstance(value, dict) else f"tool_request_proposal_{index}",
            "tool_request_proposal",
        )
    if item.source == "repair_history":
        return _lookup_by_ref(
            list(state.repair_history),
            item.item_id,
            lambda value, index: str(value.get("repair_id") or f"repair_{index}") if isinstance(value, dict) else f"repair_{index}",
            "repair_history",
        )
    if item.source == "open_assumptions":
        return state.open_assumptions, []
    if item.source == "warnings":
        return state.warnings, []
    if item.source == "errors":
        return state.errors, []
    return None, [f"unsupported context source: {item.source}"]


def _lookup_by_ref(
    values: list[Any],
    ref: str,
    ref_factory,
    source_name: str,
) -> tuple[Any, list[str]]:
    if not ref:
        return values, []
    for index, value in enumerate(values, start=1):
        generated_ref = ref_factory(value, index) if callable(ref_factory) else ""
        if generated_ref == ref:
            return value, []
        if isinstance(value, dict) and str(value.get("ref") or value.get("id") or "") == ref:
            return value, []
    return None, [f"missing {source_name}: {ref}"]


def _latest_tool_result(state: DynamicMethodState, tool_type: str) -> dict[str, Any] | None:
    for item in reversed(state.tool_results):
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        result = item.get("result")
        if (
            isinstance(request, dict)
            and request.get("tool_type") == tool_type
            and isinstance(result, dict)
        ):
            return result
    return None


def _int_from_keys(data: dict[str, Any], *keys: str) -> int:
    for key in keys:
        try:
            value = int(data.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    return 0


def _query_plan_required_for_readiness(
    state: DynamicMethodState,
    generated_tests: Any,
    *,
    sql_real: bool,
    sql_passed: bool,
    sql_test_count: int,
) -> bool:
    return (
        sql_real
        and sql_passed
        and sql_test_count > 0
        and _has_physical_access_paths(state.artifact_payload("physical_plan", {}) or {})
        and _has_workload_or_query_tests(generated_tests)
    )


def _has_physical_access_paths(physical_plan: Any) -> bool:
    if not isinstance(physical_plan, dict):
        return False
    plan = physical_plan.get("physical_plan")
    if not isinstance(plan, dict):
        plan = physical_plan
    indexes = plan.get("indexes")
    return isinstance(indexes, list) and any(isinstance(item, dict) for item in indexes)


def _has_workload_or_query_tests(generated_tests: Any) -> bool:
    if not isinstance(generated_tests, list):
        return False
    for test in generated_tests:
        if not isinstance(test, dict):
            continue
        kind = str(test.get("kind") or test.get("type") or "").strip().lower()
        if "workload" in kind or "query_plan" in kind:
            return True
        if any(key in test for key in ("expected_index", "require_index", "expect_index", "index_name")):
            return True
        if any(test.get(key) for key in ("explain_sql", "explain_query", "workload_sql")):
            return True
    return False


def _query_plan_has_executed_observation(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    observations = result.get("observations")
    if not isinstance(observations, list):
        return False
    return any(isinstance(item, dict) and item.get("status") == "executed" for item in observations)


def _view_content(content: Any, view: str) -> Any:
    if view == "full":
        return content
    return _shape_summary(content)


def _json_chars(value: Any) -> int:
    return len(_json_text(value))


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _shape_summary(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return {"type": "str", "chars": len(value), "preview": value[:160]}
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, list):
        return {
            "type": "list",
            "count": len(value),
            "sample": [_shape_summary(item) for item in value[:3]],
        }
    if isinstance(value, dict):
        summary: dict[str, Any] = {
            "type": "dict",
            "keys": list(value.keys())[:20],
            "chars": _json_chars(value),
        }
        samples: dict[str, Any] = {}
        for key, item in value.items():
            if len(samples) >= 6:
                break
            if isinstance(item, (str, int, float, bool)) or item is None:
                samples[str(key)] = _shape_summary(item)
            elif isinstance(item, list):
                samples[str(key)] = {"type": "list", "count": len(item)}
            elif isinstance(item, dict):
                samples[str(key)] = {"type": "dict", "keys": list(item.keys())[:10]}
        if samples:
            summary["samples"] = samples
        return summary
    return {"type": type(value).__name__, "chars": len(str(value))}


def _nested_get(value: Any, path: list[str]) -> Any:
    cursor = value
    for key in path:
        if not isinstance(cursor, dict):
            return ""
        cursor = cursor.get(key)
    return cursor if cursor is not None else ""


def _tool_result_status(result: Any) -> Any:
    if not isinstance(result, dict):
        return ""
    for key in ("passed", "success", "status", "mode"):
        if key in result:
            return result[key]
    return ""
