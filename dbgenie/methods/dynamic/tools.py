from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from dbgenie.agents.tools import AgentToolbox
from dbgenie.core.schema_ir import SchemaIR
from benchmark.construction.reference_ddl import clean_identifier, normalize_dialect

from .contracts import ToolRequest
from .normalization import (
    THIRD_NORMAL_FORM_TOOL,
    validate_normalization_spec,
    validate_third_normal_form,
)
from .state import DynamicMethodState


@dataclass
class DynamicMethodToolbox:
    execution_mode: str = "docker"
    _agent_toolbox: AgentToolbox = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self._agent_toolbox is None:
            self._agent_toolbox = AgentToolbox(execution_mode=self.execution_mode)

    @property
    def validator(self):
        return self._agent_toolbox.validator

    def execute(self, state: DynamicMethodState, request: ToolRequest) -> dict[str, Any]:
        tool_type = request.tool_type
        if tool_type == "artifact_validator":
            return self._validate_state(state, request)
        if tool_type == THIRD_NORMAL_FORM_TOOL:
            logical_record = state.artifacts.get("logical_model")
            logical_model = state.artifact_payload("logical_model", {}) or {}
            return validate_third_normal_form(
                logical_model,
                logical_model_version=int(logical_record.version if logical_record is not None else 0),
            )
        if tool_type == "ddl_executor":
            ddl = str(state.artifact_payload("ddl", "") or "")
            return self._agent_toolbox.execute_ddl(ddl, state.task.target_dbms).to_dict()
        if tool_type == "dialect_linter":
            ddl = str(state.artifact_payload("ddl", "") or "")
            return self._agent_toolbox.lint_ddl(ddl, state.task.target_dbms)
        if tool_type == "sql_test_runner":
            report = state.artifact_payload("test_report", {}) or {}
            tests = report.get("generated_tests") if isinstance(report, dict) else []
            ddl = str(state.artifact_payload("ddl", "") or "")
            return self._agent_toolbox.run_generated_tests(list(tests or []), ddl=ddl, target_dbms=state.task.target_dbms)
        if tool_type == "query_plan_tool":
            report = state.artifact_payload("test_report", {}) or {}
            tests = report.get("generated_tests") if isinstance(report, dict) else []
            ddl = str(state.artifact_payload("ddl", "") or "")
            physical_plan = state.artifact_payload("physical_plan", {}) or {}
            return self._agent_toolbox.explain_generated_tests(
                list(tests or []),
                ddl=ddl,
                target_dbms=state.task.target_dbms,
                physical_plan=physical_plan if isinstance(physical_plan, dict) else None,
            )
        raise ValueError(f"unsupported tool_type: {tool_type}")

    def _validate_state(self, state: DynamicMethodState, request: ToolRequest) -> dict[str, Any]:
        artifact = request.target_artifact
        payload = _validation_payload(state, request)
        if artifact == "requirement_brief":
            return self.validator.validate_requirement_brief(payload or {}).to_dict()
        if artifact == "conceptual_model":
            return self.validator.validate_conceptual_model(payload or {}).to_dict()
        if artifact == "logical_model":
            schema_payload = payload.get("schema_ir") if isinstance(payload, dict) else None
            if not isinstance(schema_payload, dict):
                return {"passed": False, "warnings": [], "errors": ["logical_model missing schema_ir"]}
            schema_validation = self.validator.validate_schema_ir(schema_payload).to_dict()
            if not state.method_definition.normalization_validation_required:
                return schema_validation
            normalization_validation = validate_normalization_spec(payload)
            return {
                "passed": bool(schema_validation.get("passed"))
                and bool(normalization_validation.get("passed")),
                "warnings": [
                    *(schema_validation.get("warnings") or []),
                    *(normalization_validation.get("warnings") or []),
                ],
                "errors": [
                    *(schema_validation.get("errors") or []),
                    *(normalization_validation.get("errors") or []),
                ],
            }
        if artifact == "physical_plan":
            validation = self.validator.validate_physical_plan(payload or {}).to_dict()
            reference_validation = _validate_physical_plan_references(
                state,
                payload or {},
            )
            return {
                "passed": bool(validation.get("passed"))
                and bool(reference_validation.get("passed")),
                "warnings": [
                    *(validation.get("warnings") or []),
                    *(reference_validation.get("warnings") or []),
                ],
                "errors": [
                    *(validation.get("errors") or []),
                    *(reference_validation.get("errors") or []),
                ],
            }
        if artifact == "dialect_report":
            return self.validator.validate_dialect_report(payload or {}).to_dict()
        if artifact == "test_report":
            return self.validator.validate_test_report(payload or {}).to_dict()
        return {"passed": True, "warnings": [], "errors": []}


def _validation_payload(state: DynamicMethodState, request: ToolRequest) -> Any:
    payload = request.payload if isinstance(request.payload, dict) else {}
    metadata_keys = {"proposal_id", "value"}
    if payload and not set(payload.keys()).issubset(metadata_keys):
        return payload
    return state.artifact_payload(request.target_artifact, {})


def _validate_physical_plan_references(
    state: DynamicMethodState,
    payload: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    logical_model = state.artifact_payload("logical_model", {}) or {}
    schema_payload = logical_model.get("schema_ir") if isinstance(logical_model, dict) else None
    if not isinstance(schema_payload, dict):
        return {
            "passed": False,
            "warnings": warnings,
            "errors": ["physical_plan validation requires logical_model.schema_ir"],
        }
    try:
        schema = SchemaIR.from_dict(schema_payload)
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "passed": False,
            "warnings": warnings,
            "errors": [f"physical_plan validation found invalid logical schema_ir: {exc}"],
        }

    tables = {
        clean_identifier(table.name).casefold(): table
        for table in schema.tables
        if clean_identifier(table.name)
    }
    plan = payload.get("physical_plan")
    indexes = plan.get("indexes") if isinstance(plan, dict) else plan
    if not isinstance(indexes, list):
        return {"passed": not errors, "warnings": warnings, "errors": errors}
    dialect = normalize_dialect(state.task.target_dbms)
    unsupported_include = {"mysql", "mariadb", "duckdb", "sqlite"}
    unsupported_filter = {"mysql", "mariadb", "duckdb", "sqlite"}

    for position, item in enumerate(indexes, start=1):
        if not isinstance(item, dict):
            continue
        prefix = f"physical index #{position}"
        table_name = str(item.get("table") or "").strip()
        table = tables.get(clean_identifier(table_name).casefold())
        if table is None:
            errors.append(f"{prefix} references unknown table: {table_name or '<empty>'}")
            continue
        columns_by_name = {
            clean_identifier(column.name).casefold(): column
            for column in table.columns
            if clean_identifier(column.name)
        }
        key_columns = _physical_index_column_list(item.get("columns"), prefix, "columns", errors)
        include_columns = _physical_index_column_list(
            item.get("include", []), prefix, "include", errors, allow_empty=True
        )
        _validate_index_column_references(
            prefix,
            table.name,
            key_columns,
            columns_by_name,
            errors,
        )
        _validate_index_column_references(
            prefix,
            table.name,
            include_columns,
            columns_by_name,
            errors,
        )
        overlap = {
            clean_identifier(name).casefold() for name in key_columns
        } & {
            clean_identifier(name).casefold() for name in include_columns
        }
        if overlap:
            errors.append(
                f"{prefix} repeats key columns in include: {', '.join(sorted(overlap))}"
            )
        if include_columns and dialect in unsupported_include:
            errors.append(f"{prefix} uses include columns unsupported by {dialect}")
        if str(item.get("filter") or "").strip() and dialect in unsupported_filter:
            errors.append(f"{prefix} uses a filtered index unsupported by {dialect}")
        for name in key_columns:
            column = columns_by_name.get(clean_identifier(name).casefold())
            if column is not None and _unbounded_index_key_type(dialect, column.type):
                errors.append(
                    f"{prefix} key column {table.name}.{column.name} uses unsupported "
                    f"unbounded type {column.type} for {dialect}"
                )
    return {"passed": not errors, "warnings": warnings, "errors": errors}


def _physical_index_column_list(
    value: Any,
    prefix: str,
    field: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{prefix}.{field} must be a list")
        return []
    columns = [str(item).strip() for item in value if str(item).strip()]
    if not allow_empty and not columns:
        errors.append(f"{prefix}.{field} must contain at least one column")
    normalized = [clean_identifier(name).casefold() for name in columns]
    if len(normalized) != len(set(normalized)):
        errors.append(f"{prefix}.{field} contains duplicate columns")
    return columns


def _validate_index_column_references(
    prefix: str,
    table_name: str,
    columns: list[str],
    columns_by_name: dict[str, Any],
    errors: list[str],
) -> None:
    for name in columns:
        if clean_identifier(name).casefold() not in columns_by_name:
            errors.append(f"{prefix} references unknown column: {table_name}.{name}")


def _unbounded_index_key_type(dialect: str, column_type: str) -> bool:
    normalized = re.sub(r"\s+", "", str(column_type or "").casefold())
    if dialect in {"mysql", "mariadb"}:
        return any(token in normalized for token in ("text", "blob", "json"))
    if dialect == "sqlserver":
        return normalized in {"text", "ntext", "image", "xml"} or "(max)" in normalized
    return False
