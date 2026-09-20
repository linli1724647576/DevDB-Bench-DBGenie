from __future__ import annotations

from typing import Any

from dbgenie.core.schema_ir import SchemaIR, TableIR
from benchmark.construction.reference_ddl import clean_identifier

from .state import DynamicMethodState


THIRD_NORMAL_FORM_TOOL = "third_normal_form_validator"


def validate_normalization_spec(logical_model: Any) -> dict[str, Any]:
    _schema, _specs, warnings, errors = _inspect_normalization_input(logical_model)
    return {
        "passed": not errors,
        "warnings": warnings,
        "errors": errors,
    }


def validate_third_normal_form(
    logical_model: Any,
    *,
    logical_model_version: int,
) -> dict[str, Any]:
    schema, specs, warnings, errors = _inspect_normalization_input(logical_model)
    table_results: list[dict[str, Any]] = []

    if schema is not None and not errors:
        for table in schema.tables:
            table_result, table_warnings, table_errors = _validate_table_third_normal_form(
                table,
                specs[_normalized_name(table.name)],
            )
            table_results.append(table_result)
            warnings.extend(table_warnings)
            errors.extend(table_errors)

    violation_count = sum(
        len(item.get("violations") or [])
        for item in table_results
        if isinstance(item, dict)
    )
    passed = not errors and violation_count == 0
    return {
        "tool_type": THIRD_NORMAL_FORM_TOOL,
        "mode": "deterministic_3nf",
        "passed": passed,
        "status": "passed" if passed else "failed",
        "logical_model_version": int(logical_model_version),
        "table_count": len(table_results),
        "violation_count": violation_count,
        "tables": table_results,
        "warnings": warnings,
        "errors": errors,
    }


def current_third_normal_form_evidence(
    state: DynamicMethodState,
) -> tuple[str, dict[str, Any]] | None:
    logical_record = state.artifacts.get("logical_model")
    logical_version = int(logical_record.version if logical_record is not None else 0)
    if logical_version <= 0:
        return None

    for index in range(len(state.tool_results), 0, -1):
        item = state.tool_results[index - 1]
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        result = item.get("result")
        if not isinstance(request, dict) or request.get("tool_type") != THIRD_NORMAL_FORM_TOOL:
            continue
        if not isinstance(result, dict):
            continue
        artifact_versions = item.get("artifact_versions")
        recorded_version = 0
        if isinstance(artifact_versions, dict):
            recorded_version = _int_value(artifact_versions.get("logical_model"))
        if recorded_version <= 0:
            recorded_version = _int_value(result.get("logical_model_version"))
        if recorded_version == logical_version:
            return f"tool_result_{index}", item
    return None


def _inspect_normalization_input(
    logical_model: Any,
) -> tuple[SchemaIR | None, dict[str, dict[str, Any]], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    specs: dict[str, dict[str, Any]] = {}

    if not isinstance(logical_model, dict):
        return None, specs, warnings, ["logical_model must be an object"]
    schema_payload = logical_model.get("schema_ir")
    if not isinstance(schema_payload, dict):
        return None, specs, warnings, ["logical_model missing schema_ir"]
    try:
        schema = SchemaIR.from_dict(schema_payload)
    except (KeyError, TypeError, ValueError) as exc:
        return None, specs, warnings, [f"invalid schema_ir: {exc}"]

    normalization_spec = logical_model.get("normalization_spec")
    if not isinstance(normalization_spec, dict):
        return schema, specs, warnings, ["logical_model missing normalization_spec"]
    raw_tables = normalization_spec.get("tables")
    if not isinstance(raw_tables, list):
        return schema, specs, warnings, ["normalization_spec.tables must be a list"]

    schema_tables = {_normalized_name(table.name): table for table in schema.tables}
    for index, item in enumerate(raw_tables, start=1):
        prefix = f"normalization_spec table #{index}"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        table_name = str(item.get("table") or "").strip()
        table_key = _normalized_name(table_name)
        if not table_key:
            errors.append(f"{prefix} missing table")
            continue
        if table_key not in schema_tables:
            errors.append(f"normalization_spec references unknown table: {table_name}")
            continue
        if table_key in specs:
            errors.append(f"normalization_spec has duplicate table: {table_name}")
            continue
        specs[table_key] = item
        _validate_functional_dependency_shapes(
            schema_tables[table_key],
            item,
            warnings,
            errors,
        )

    for table_key, table in schema_tables.items():
        if table_key not in specs:
            errors.append(f"normalization_spec missing table: {table.name}")
    return schema, specs, warnings, errors


def _validate_functional_dependency_shapes(
    table: TableIR,
    spec: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> None:
    raw_dependencies = spec.get("functional_dependencies")
    if not isinstance(raw_dependencies, list):
        errors.append(
            f"normalization_spec.{table.name}.functional_dependencies must be a list"
        )
        return
    columns = {_normalized_name(column.name) for column in table.columns}
    for index, dependency in enumerate(raw_dependencies, start=1):
        prefix = f"functional dependency {table.name}#{index}"
        if not isinstance(dependency, dict):
            errors.append(f"{prefix} must be an object")
            continue
        determinant = _strict_name_list(
            dependency.get("determinant"),
            field=f"{prefix}.determinant",
            allow_empty=True,
            errors=errors,
        )
        dependents = _strict_name_list(
            dependency.get("dependents"),
            field=f"{prefix}.dependents",
            allow_empty=False,
            errors=errors,
        )
        rationale = dependency.get("rationale")
        if rationale is not None and not isinstance(rationale, str):
            errors.append(f"{prefix}.rationale must be a string")
        for field_name, names in (("determinant", determinant), ("dependents", dependents)):
            for name in names or []:
                if _normalized_name(name) not in columns:
                    errors.append(
                        f"{prefix}.{field_name} references unknown column: {table.name}.{name}"
                    )
        if determinant is not None and dependents is not None:
            determinant_keys = {_normalized_name(name) for name in determinant}
            if dependents and all(_normalized_name(name) in determinant_keys for name in dependents):
                warnings.append(f"{prefix} is entirely trivial")


def _validate_table_third_normal_form(
    table: TableIR,
    spec: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    column_order = [_normalized_name(column.name) for column in table.columns]
    display_names = {
        _normalized_name(column.name): column.name
        for column in table.columns
    }
    nullable = {
        _normalized_name(column.name): bool(column.nullable)
        for column in table.columns
    }
    all_attributes = set(column_order)

    candidate_keys: list[tuple[str, ...]] = []
    primary_key = _normalized_tuple(table.primary_key)
    if primary_key:
        candidate_keys.append(primary_key)
    for constraint in table.unique_constraints:
        unique_key = _normalized_tuple(constraint.columns)
        if not unique_key:
            continue
        if any(nullable.get(column, True) for column in unique_key):
            warnings.append(
                "nullable UNIQUE constraint is not treated as a candidate key: "
                f"{table.name}({', '.join(_display_columns(unique_key, display_names))})"
            )
            continue
        if unique_key not in candidate_keys:
            candidate_keys.append(unique_key)
    if not candidate_keys:
        errors.append(f"table has no declared candidate key for 3NF validation: {table.name}")

    explicit_dependencies: list[tuple[frozenset[str], frozenset[str], str]] = []
    for dependency in spec.get("functional_dependencies") or []:
        determinant = frozenset(_normalized_name(name) for name in dependency.get("determinant") or [])
        dependents = frozenset(_normalized_name(name) for name in dependency.get("dependents") or [])
        explicit_dependencies.append(
            (determinant, dependents, str(dependency.get("rationale") or ""))
        )

    closure_dependencies = list(explicit_dependencies)
    for candidate_key in candidate_keys:
        closure_dependencies.append(
            (frozenset(candidate_key), frozenset(all_attributes), "declared candidate key")
        )

    prime_attributes = {column for key in candidate_keys for column in key}
    violations: list[dict[str, Any]] = []
    dependency_results: list[dict[str, Any]] = []
    for determinant, dependents, rationale in explicit_dependencies:
        closure = _attribute_closure(set(determinant), closure_dependencies)
        determinant_is_superkey = all_attributes.issubset(closure)
        nontrivial_dependents = [column for column in column_order if column in dependents - determinant]
        dependency_violations = []
        for dependent in nontrivial_dependents:
            if determinant_is_superkey or dependent in prime_attributes:
                continue
            violation = {
                "determinant": _display_columns(determinant, display_names, column_order),
                "dependent": display_names.get(dependent, dependent),
                "determinant_closure": _display_columns(closure, display_names, column_order),
                "reason": "determinant is not a superkey and dependent is non-prime",
            }
            violations.append(violation)
            dependency_violations.append(violation)
        dependency_results.append(
            {
                "determinant": _display_columns(determinant, display_names, column_order),
                "dependents": _display_columns(dependents, display_names, column_order),
                "determinant_closure": _display_columns(closure, display_names, column_order),
                "determinant_is_superkey": determinant_is_superkey,
                "rationale": rationale,
                "violations": dependency_violations,
            }
        )

    result = {
        "table": table.name,
        "passed": not errors and not violations,
        "candidate_keys": [
            _display_columns(key, display_names, column_order)
            for key in candidate_keys
        ],
        "prime_attributes": _display_columns(prime_attributes, display_names, column_order),
        "functional_dependency_count": len(explicit_dependencies),
        "functional_dependencies": dependency_results,
        "violations": violations,
        "warnings": warnings,
        "errors": errors,
    }
    return result, warnings, errors


def _attribute_closure(
    seed: set[str],
    dependencies: list[tuple[frozenset[str], frozenset[str], str]],
) -> set[str]:
    closure = set(seed)
    changed = True
    while changed:
        changed = False
        for determinant, dependents, _rationale in dependencies:
            if determinant.issubset(closure) and not dependents.issubset(closure):
                closure.update(dependents)
                changed = True
    return closure


def _strict_name_list(
    value: Any,
    *,
    field: str,
    allow_empty: bool,
    errors: list[str],
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return None
    names: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field} must contain non-empty strings")
            continue
        key = _normalized_name(item)
        if key in seen:
            errors.append(f"{field} contains duplicate column: {item}")
            continue
        seen.add(key)
        names.append(item.strip())
    if not allow_empty and not names:
        errors.append(f"{field} must not be empty")
    return names


def _normalized_name(value: Any) -> str:
    return clean_identifier(str(value or "")).strip().lower()


def _normalized_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(
        key
        for key in (_normalized_name(value) for value in values)
        if key
    )


def _display_columns(
    values: Any,
    display_names: dict[str, str],
    column_order: list[str] | None = None,
) -> list[str]:
    keys = set(values or [])
    ordered = column_order or sorted(keys)
    return [display_names.get(key, key) for key in ordered if key in keys]


def _int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
