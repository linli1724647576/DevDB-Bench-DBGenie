from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dbgenie.core.io import read_json, write_text
from dbgenie.core.schema_ir import (
    CheckConstraintIR,
    ColumnIR,
    ForeignKeyIR,
    IndexIR,
    SchemaIR,
    TableIR,
)
from benchmark.construction.schema_extraction import (
    ExtractionInputFile,
    extract_sql_ddl,
)


SUPPORTED_DBMS = {"postgresql", "mysql", "mariadb", "sqlite", "sqlserver", "duckdb"}
PSEUDO_COLUMN_TYPES = {
    "dropcolumn",
    "dropforeign",
    "dropindex",
    "dropunique",
    "renamecolumn",
    "renameindex",
    "morphs",
    "nullablemorphs",
    "uuidmorphs",
    "manytomany",
}
RELATION_PSEUDO_TYPES = {
    "foreignkey",
    "foreignid",
    "foreignidfor",
    "onetoone",
    "belongsto",
}


@dataclass(frozen=True)
class ReferenceDDLGenerationResult:
    status: str
    canonical_dialect: str
    ddl_path: str | None = None
    roundtrip_validation: dict[str, Any] = field(default_factory=dict)
    sqlite_execution: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    preserved_source_ddl_dir: str | None = None
    preserved_source_ddl_combined_path: str | None = None
    preserved_source_ddl_files: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "canonical_dialect": self.canonical_dialect,
            "ddl_path": self.ddl_path,
            "roundtrip_validation": self.roundtrip_validation,
            "sqlite_execution": self.sqlite_execution,
            "warnings": self.warnings,
            "errors": self.errors,
            "preserved_source_ddl_dir": self.preserved_source_ddl_dir,
            "preserved_source_ddl_combined_path": self.preserved_source_ddl_combined_path,
            "preserved_source_ddl_files": self.preserved_source_ddl_files,
        }


@dataclass(frozen=True)
class RenderColumn:
    source: ColumnIR
    name: str
    sql_type: str
    nullable: bool
    identity: bool = False


@dataclass(frozen=True)
class RenderTable:
    source: TableIR
    name: str
    columns: list[RenderColumn]
    primary_key: list[str]
    unique_constraints: list[list[str]]
    check_constraints: list[str]
    foreign_keys: list[ForeignKeyIR]
    indexes: list[IndexIR]

    @property
    def column_names(self) -> set[str]:
        return {column.name for column in self.columns}


@dataclass(frozen=True)
class GeneratedDDL:
    ddl: str
    warnings: list[str]
    expected_stats: dict[str, int]


def generate_reference_ddl_for_candidate(
    candidate: dict[str, Any],
    output_dir: Path,
    dry_run: bool = False,
) -> ReferenceDDLGenerationResult:
    dbms = str(candidate.get("dbms_final") or "")
    dialect = normalize_dialect(dbms)
    if dialect not in SUPPORTED_DBMS:
        return ReferenceDDLGenerationResult(
            status="failed",
            canonical_dialect=dialect or dbms,
            errors=[f"unsupported target DBMS: {dbms}"],
        )

    ir_path = _candidate_schema_ir_path(candidate)
    if not ir_path or not ir_path.exists():
        return ReferenceDDLGenerationResult(
            status="failed",
            canonical_dialect=dialect,
            errors=[f"Schema IR file not found: {ir_path or ''}"],
        )

    try:
        schema_ir = SchemaIR.from_dict(read_json(ir_path))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return ReferenceDDLGenerationResult(
            status="failed",
            canonical_dialect=dialect,
            errors=[f"failed to load Schema IR: {exc}"],
        )

    generated = SchemaIRDDLGenerator(dialect).generate(schema_ir)
    if not generated.ddl.strip():
        return ReferenceDDLGenerationResult(
            status="failed",
            canonical_dialect=dialect,
            warnings=generated.warnings,
            errors=["generated DDL is empty"],
        )

    ddl_path = output_dir / _repo_slug(candidate) / f"{_dbms_file_label(dbms)}.sql"
    preserved = _preserve_original_direct_ddl(candidate, output_dir, dry_run=dry_run)
    if not dry_run:
        write_text(ddl_path, generated.ddl)
    roundtrip = _roundtrip_validate(generated.ddl, dialect, generated.expected_stats)
    sqlite_execution = _sqlite_execute_validate(generated.ddl) if dialect == "sqlite" else {
        "executed": False,
        "reason": "execution validation is only enabled for SQLite in this stage",
    }
    errors = []
    if not roundtrip.get("passed"):
        errors.append("roundtrip validation failed")
    if dialect == "sqlite" and not sqlite_execution.get("passed"):
        errors.append("SQLite execution validation failed")

    warnings = [*generated.warnings, *preserved.get("warnings", [])]
    status = "generated"
    if warnings or errors:
        status = "generated_with_warnings"
    if errors and not roundtrip.get("parsed"):
        status = "failed"

    return ReferenceDDLGenerationResult(
        status=status,
        canonical_dialect=dialect,
        ddl_path=None if dry_run else ddl_path.as_posix(),
        roundtrip_validation=roundtrip,
        sqlite_execution=sqlite_execution,
        warnings=warnings,
        errors=errors,
        preserved_source_ddl_dir=preserved.get("preserved_source_ddl_dir"),
        preserved_source_ddl_combined_path=preserved.get("preserved_source_ddl_combined_path"),
        preserved_source_ddl_files=preserved.get("preserved_source_ddl_files", []),
    )


def generate_reference_ddl_for_candidates(
    candidates: list[dict[str, Any]],
    output_dir: Path,
    dry_run: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected = candidates[:limit] if limit else candidates
    augmented = []
    for candidate in selected:
        result = generate_reference_ddl_for_candidate(candidate, output_dir, dry_run=dry_run)
        augmented.append({**candidate, "reference_ddl_generation": result.to_dict()})
    return augmented


def build_reference_ddl_report(
    candidates: list[dict[str, Any]],
    source_file: str,
    output_dir: str,
    dry_run: bool = False,
) -> str:
    results = [candidate.get("reference_ddl_generation", {}) for candidate in candidates]
    status_counts = Counter(str(result.get("status") or "missing") for result in results)
    dbms_counts = Counter(str(candidate.get("dbms_final") or "unknown") for candidate in candidates)
    roundtrip_counts = Counter(
        "passed" if result.get("roundtrip_validation", {}).get("passed") else "failed"
        for result in results
    )
    preserved_count = sum(1 for result in results if result.get("preserved_source_ddl_files"))
    warning_counts = Counter()
    review_candidates = []
    for candidate in candidates:
        result = candidate.get("reference_ddl_generation", {})
        warnings = list(result.get("warnings") or [])
        errors = list(result.get("errors") or [])
        for warning in warnings:
            warning_counts[_warning_kind(warning)] += 1
        if warnings or errors or result.get("status") != "generated":
            review_candidates.append(candidate)

    clean_lines = [
        "# Reference DDL 生成报告（2026-06-01）",
        "",
        f"- 输入文件：`{source_file}`",
        f"- 输出目录：`{output_dir}`",
        f"- dry run：{bool(dry_run)}",
        f"- 样本数：{len(candidates)}",
        f"- 保留原始 direct DDL 的样本数：{preserved_count}",
        "",
        "## 状态统计",
        "",
        _format_counts(status_counts),
        "",
        "## DBMS 分布",
        "",
        _format_counts(dbms_counts),
        "",
        "## Round-trip 校验",
        "",
        _format_counts(roundtrip_counts),
        "",
        "## Warning 类型统计",
        "",
        _format_counts(warning_counts),
        "",
        "## 需要人工复查的样本",
        "",
        _format_review_candidates(review_candidates),
        "",
        "## 说明",
        "",
        "- canonical reference DDL 由最终 SchemaIR 生成，路径为 `<repo>/<DBMS>.sql`。",
        "- 如果样本存在原始 `.sql` schema 文件，会额外保留到 `<repo>/source_direct_ddl/`，并生成 `original_direct_ddl.combined.sql` 合并副本。",
        "- `generated_with_warnings` 通常表示存在类型 fallback、重复列跳过、伪列跳过或 round-trip 计数差异。",
        "- 当前只对 SQLite 做真实执行校验；PostgreSQL / MySQL / MariaDB / SQL Server 后续可接入容器执行校验。",
    ]
    return "\n".join(clean_lines).rstrip() + "\n"

class SchemaIRDDLGenerator:
    def __init__(self, dialect: str) -> None:
        self.dialect = dialect
        self.warnings: list[str] = []

    def generate(self, schema_ir: SchemaIR) -> GeneratedDDL:
        render_tables = self._render_tables(schema_ir)
        if self.dialect in {"sqlite", "duckdb"}:
            render_tables = _order_tables_for_inline_foreign_keys(render_tables)
        statements: list[str] = []
        fk_statements: list[str] = []
        index_statements: list[str] = []
        used_index_names: set[str] = set()

        for table in render_tables:
            statements.append(self._create_table_statement(table, render_tables))
            index_statements.extend(self._index_statements(table, used_index_names))
        for table in render_tables:
            if self.dialect not in {"sqlite", "duckdb"}:
                fk_statements.extend(self._alter_foreign_key_statements(table, render_tables))

        ddl = "\n\n".join([*statements, *index_statements, *fk_statements]).strip()
        if ddl:
            ddl += "\n"
        expected_stats = {
            "table_count": len(render_tables),
            "column_count": sum(len(table.columns) for table in render_tables),
            "foreign_key_count": sum(
                len(self._valid_foreign_keys(table, render_tables)) for table in render_tables
            ),
            "unique_count": sum(len(table.unique_constraints) for table in render_tables),
            "index_count": sum(len(self._valid_indexes(table)) for table in render_tables),
        }
        return GeneratedDDL(ddl=ddl, warnings=_dedupe_warnings(self.warnings), expected_stats=expected_stats)

    def _render_tables(self, schema_ir: SchemaIR) -> list[RenderTable]:
        rendered = []
        table_names: set[str] = set()
        for table in schema_ir.tables:
            table_name = clean_identifier(table.name)
            if not table_name:
                self.warnings.append("skipped table with empty name")
                continue
            if table_name.lower() in table_names:
                self.warnings.append(f"skipped duplicate table after normalization: {table.name}")
                continue
            table_names.add(table_name.lower())
            columns = self._render_columns(table)
            if not columns:
                self.warnings.append(f"skipped table without renderable columns: {table.name}")
                continue
            column_names = {column.name.lower(): column.name for column in columns}
            primary_key = [
                column_names[clean_identifier(column).lower()]
                for column in table.primary_key
                if clean_identifier(column).lower() in column_names
            ]
            if len(primary_key) < len(table.primary_key):
                self.warnings.append(f"primary key references skipped or missing columns: {table.name}")
            unique_constraints = self._render_unique_constraints(table, column_names)
            check_constraints = self._render_check_constraints(table)
            rendered.append(
                RenderTable(
                    source=table,
                    name=table_name,
                    columns=columns,
                    primary_key=primary_key,
                    unique_constraints=unique_constraints,
                    check_constraints=check_constraints,
                    foreign_keys=table.foreign_keys,
                    indexes=table.indexes,
                )
            )
        return rendered

    def _render_columns(self, table: TableIR) -> list[RenderColumn]:
        rendered = []
        seen: set[str] = set()
        key_columns = _key_participating_columns(table)
        for column in table.columns:
            name = clean_identifier(column.name)
            if not name:
                self.warnings.append(f"skipped column with empty name: {table.name}")
                continue
            if name.lower() in seen:
                self.warnings.append(f"skipped duplicate column: {table.name}.{name}")
                continue
            sql_type = map_column_type(column.type, self.dialect)
            if sql_type is None:
                self.warnings.append(
                    f"skipped pseudo column: {table.name}.{name} type={column.type}"
                )
                continue
            if sql_type.endswith(" /* fallback */"):
                sql_type = sql_type.replace(" /* fallback */", "")
                self.warnings.append(
                    f"fallback type mapping: {table.name}.{name} type={column.type}"
                )
            if (
                self.dialect in {"mysql", "mariadb"}
                and name.lower() in key_columns
                and _is_unbounded_index_type(sql_type)
            ):
                sql_type = _varchar_type(self.dialect, 255)
                self.warnings.append(
                    f"narrowed MySQL/MariaDB key column type: {table.name}.{name}"
                )
            seen.add(name.lower())
            rendered.append(
                RenderColumn(
                    source=column,
                    name=name,
                    sql_type=sql_type,
                    nullable=column.nullable,
                    identity=_is_identity_column(column),
                )
            )
        return rendered

    def _render_unique_constraints(
        self,
        table: TableIR,
        column_names: dict[str, str],
    ) -> list[list[str]]:
        rendered = []
        seen: set[tuple[str, ...]] = set()
        for constraint in table.unique_constraints:
            columns = _resolve_columns(constraint.columns, column_names)
            if not columns:
                self.warnings.append(f"unique constraint has no renderable columns: {table.name}")
                continue
            if len(columns) < len(constraint.columns):
                self.warnings.append(f"unique constraint references missing columns: {table.name}")
                continue
            key = tuple(column.lower() for column in columns)
            if key in seen:
                continue
            seen.add(key)
            rendered.append(columns)
        return rendered

    def _render_check_constraints(self, table: TableIR) -> list[str]:
        checks = []
        for constraint in table.check_constraints:
            expression = _check_expression(constraint)
            if not expression:
                continue
            if _is_simple_check_expression(expression):
                checks.append(expression)
            else:
                self.warnings.append(f"skipped complex CHECK constraint: {table.name}")
        return checks

    def _create_table_statement(self, table: RenderTable, tables: list[RenderTable]) -> str:
        parts = []
        for column in table.columns:
            line = f"{self.q(column.name)} {column.sql_type}"
            identity_clause = self._identity_clause(column)
            if identity_clause:
                line += f" {identity_clause}"
            if not column.nullable or column.name in table.primary_key:
                line += " NOT NULL"
            parts.append(line)
        if table.primary_key:
            parts.append(f"PRIMARY KEY ({self._column_list(table.primary_key)})")
        for unique_columns in table.unique_constraints:
            parts.append(f"UNIQUE ({self._column_list(unique_columns)})")
        for check in table.check_constraints:
            parts.append(f"CHECK ({check})")
        if self.dialect in {"sqlite", "duckdb"}:
            for foreign_key in self._valid_foreign_keys(table, tables):
                parts.append(self._foreign_key_clause(foreign_key, tables))
        body = ",\n  ".join(parts)
        return f"CREATE TABLE {self.q(table.name)} (\n  {body}\n);"

    def _identity_clause(self, column: RenderColumn) -> str:
        if not column.identity:
            return ""
        if not _is_integer_identity_type(column.sql_type):
            self.warnings.append(
                f"skipped identity on non-integer column: {column.source.name}"
            )
            return ""
        if self.dialect == "sqlserver":
            return "IDENTITY(1,1)"
        if self.dialect in {"mysql", "mariadb"}:
            return "AUTO_INCREMENT"
        if self.dialect == "postgresql":
            return "GENERATED BY DEFAULT AS IDENTITY"
        return ""

    def _alter_foreign_key_statements(
        self,
        table: RenderTable,
        tables: list[RenderTable],
    ) -> list[str]:
        statements = []
        for index, foreign_key in enumerate(self._valid_foreign_keys(table, tables), start=1):
            ref_table = _resolve_table_name(foreign_key.ref_table, tables)
            if not ref_table:
                continue
            constraint_name = _short_name(
                f"fk_{table.name}_{'_'.join(clean_identifier(c) for c in foreign_key.columns)}_{index}"
            )
            statements.append(
                f"ALTER TABLE {self.q(table.name)} ADD CONSTRAINT {self.q(constraint_name)} "
                f"{self._foreign_key_clause(foreign_key, tables)};"
            )
        return statements

    def _foreign_key_clause(
        self,
        foreign_key: ForeignKeyIR,
        tables: list[RenderTable],
    ) -> str:
        ref_table = _resolve_table_name(foreign_key.ref_table, tables) or clean_identifier(
            foreign_key.ref_table
        )
        columns = [clean_identifier(column) for column in foreign_key.columns]
        ref_columns = [clean_identifier(column) for column in foreign_key.ref_columns]
        return (
            f"FOREIGN KEY ({self._column_list(columns)}) "
            f"REFERENCES {self.q(ref_table)} ({self._column_list(ref_columns)})"
        )

    def _valid_foreign_keys(
        self,
        table: RenderTable,
        tables: list[RenderTable],
    ) -> list[ForeignKeyIR]:
        table_lookup = {item.name.lower(): item for item in tables}
        valid = []
        for foreign_key in table.foreign_keys:
            columns = [clean_identifier(column) for column in foreign_key.columns]
            if not columns or any(column.lower() not in {c.lower() for c in table.column_names} for column in columns):
                self.warnings.append(f"foreign key references missing local columns: {table.name}")
                continue
            ref_table_name = clean_identifier(foreign_key.ref_table)
            ref_table = table_lookup.get(ref_table_name.lower())
            if not ref_table:
                self.warnings.append(
                    f"foreign key references missing table: {table.name}->{foreign_key.ref_table}"
                )
                continue
            ref_columns = [clean_identifier(column) for column in foreign_key.ref_columns]
            ref_column_names = {column.lower() for column in ref_table.column_names}
            if not ref_columns or any(column.lower() not in ref_column_names for column in ref_columns):
                self.warnings.append(
                    f"foreign key references missing target columns: {table.name}->{foreign_key.ref_table}"
                )
                continue
            if not self._foreign_key_types_compatible(
                table,
                columns,
                ref_table,
                ref_columns,
            ):
                self.warnings.append(
                    f"skipped incompatible foreign key types: {table.name}.{','.join(columns)}"
                    f"->{ref_table.name}.{','.join(ref_columns)}"
                )
                continue
            valid.append(foreign_key)
        return valid

    def _index_statements(self, table: RenderTable, used_names: set[str]) -> list[str]:
        statements = []
        for index, item in enumerate(self._valid_indexes(table), start=1):
            columns = [self._index_name_part(table, column) for column in item.columns]
            index_parts = [self._index_part_sql(table, column) for column in item.columns]
            using = self._index_using_clause(table, item)
            if using:
                using = f" USING {using}"
            unique = "UNIQUE " if item.unique else ""
            name = self._safe_index_name(table, columns, item, index, used_names)
            statements.append(
                f"CREATE {unique}INDEX {self.q(name)} ON {self.q(table.name)}{using} "
                f"({', '.join(index_parts)});"
            )
        return statements

    def _valid_indexes(self, table: RenderTable) -> list[IndexIR]:
        valid = []
        column_by_name = {column.name.lower(): column for column in table.columns}
        column_names = set(column_by_name)
        seen: set[tuple[str, ...]] = set()
        for index in table.indexes:
            columns = [self._index_name_part(table, column) for column in index.columns]
            if not columns or any(
                not self._index_part_is_supported(table, column)
                for column in index.columns
            ):
                self.warnings.append(f"index references missing columns: {table.name}")
                continue
            if self.dialect in {"mysql", "mariadb"} and any(
                _is_unbounded_index_type(column_by_name[column.lower()].sql_type)
                for column in columns
                if column.lower() in column_by_name
            ):
                self.warnings.append(
                    f"skipped MySQL/MariaDB index on unbounded text/blob column: "
                    f"{table.name}.{','.join(columns)}"
                )
                continue
            key = tuple(column.lower() for column in columns)
            if key in seen:
                continue
            seen.add(key)
            valid.append(index)
        return valid

    def _index_part_is_supported(self, table: RenderTable, value: str) -> bool:
        column_names = {column.name.lower() for column in table.columns}
        cleaned = clean_identifier(value)
        if cleaned.lower() in column_names:
            return True
        return bool(self._postgresql_index_expression(table, value))

    def _index_part_sql(self, table: RenderTable, value: str) -> str:
        expression = self._postgresql_index_expression(table, value)
        if expression:
            return expression
        return self.q(clean_identifier(value))

    def _index_name_part(self, table: RenderTable, value: str) -> str:
        expression = self._postgresql_index_expression(table, value)
        if expression:
            return clean_identifier(value)
        return clean_identifier(value)

    def _index_using_clause(self, table: RenderTable, index: IndexIR) -> str:
        if self.dialect != "postgresql":
            return ""
        column_by_name = {column.name.lower(): column for column in table.columns}
        for column in index.columns:
            column_name = clean_identifier(column)
            render_column = column_by_name.get(column_name.lower())
            if render_column and render_column.sql_type.upper() == "TSVECTOR":
                return "GIN"
        return ""

    def _postgresql_index_expression(self, table: RenderTable, value: str) -> str:
        if self.dialect != "postgresql":
            return ""
        raw = re.sub(r"\s+", " ", str(value or "").strip())
        match = re.fullmatch(
            r"lower\(\(([A-Za-z_][A-Za-z0-9_]*)\)::text\)\s+varchar_pattern_ops",
            raw,
            flags=re.IGNORECASE,
        )
        if not match:
            return ""
        column_by_name = {column.name.lower(): column.name for column in table.columns}
        column_name = column_by_name.get(match.group(1).lower())
        if not column_name:
            return ""
        return f"lower(({self.q(column_name)})::text) varchar_pattern_ops"

    def _safe_index_name(
        self,
        table: RenderTable,
        columns: list[str],
        item: IndexIR,
        index: int,
        used_names: set[str],
    ) -> str:
        prefix = "uidx" if item.unique else "idx"
        base = _short_name(f"{prefix}_{table.name}_{'_'.join(columns)}_{index}")
        name = base
        suffix = 2
        while name.lower() in used_names:
            name = _short_name(f"{base}_{suffix}")
            suffix += 1
        used_names.add(name.lower())
        return name

    def _foreign_key_types_compatible(
        self,
        table: RenderTable,
        columns: list[str],
        ref_table: RenderTable,
        ref_columns: list[str],
    ) -> bool:
        if len(columns) != len(ref_columns):
            return False
        local = {column.name.lower(): column for column in table.columns}
        remote = {column.name.lower(): column for column in ref_table.columns}
        for local_name, ref_name in zip(columns, ref_columns):
            local_column = local.get(local_name.lower())
            ref_column = remote.get(ref_name.lower())
            if not local_column or not ref_column:
                return False
            if _fk_type_family(local_column.sql_type, self.dialect) != _fk_type_family(
                ref_column.sql_type,
                self.dialect,
            ):
                return False
        return True

    def _column_list(self, columns: list[str]) -> str:
        return ", ".join(self.q(clean_identifier(column)) for column in columns)

    def q(self, value: str) -> str:
        return quote_identifier(value, self.dialect)


def map_column_type(raw_type: str, dialect: str) -> str | None:
    raw = str(raw_type or "").strip()
    normalized = _normalize_type(raw)
    lower = normalized.lower()
    if lower in PSEUDO_COLUMN_TYPES:
        return None
    if lower in RELATION_PSEUDO_TYPES:
        return _integer_type(dialect)
    if not lower or lower == "unknown":
        return _text_type(dialect) + " /* fallback */"
    native_type = _native_column_type(normalized, lower, dialect)
    if native_type:
        return native_type
    if lower in {"auto", "bigauto", "increments", "bigincrements", "primary_key", "id"}:
        return "BIGINT" if dialect != "sqlite" else "INTEGER"
    if lower in {"char", "string", "email", "url", "slug", "ipaddress", "uuidfield"}:
        return _varchar_type(dialect, 255)
    if lower in {"text", "longtext", "mediumtext"}:
        return _text_type(dialect)
    if lower in {"bool", "boolean", "bit"} or lower == "tinyint(1)":
        return _boolean_type(dialect)
    if lower in {"integer", "int", "positiveinteger", "unsignedinteger"}:
        return _unsigned_integer_type(dialect, "INTEGER", lower.startswith("unsigned"))
    if lower in {"biginteger", "bigint", "positivebiginteger", "unsignedbiginteger"}:
        return _unsigned_integer_type(dialect, "BIGINT", lower.startswith("unsigned"))
    if lower in {"smallinteger", "positivesmallinteger", "unsignedtinyinteger", "tinyinteger"}:
        return "SMALLINT"
    if lower in {"float", "real", "double"}:
        return _float_type(dialect, lower)
    if lower in {"decimal", "numeric"}:
        return "DECIMAL(18, 2)"
    if lower in {"date"}:
        return "DATE"
    if lower in {"datetime", "datetime2", "timestamp", "datetimetz"}:
        return _datetime_type(dialect)
    if lower in {"time"}:
        return "TIME"
    if lower in {"json", "jsonb"}:
        return _json_type(dialect)
    if lower in {"uuid", "ulid"}:
        return _uuid_type(dialect)
    if dialect == "postgresql" and lower == "tsvector":
        return "TSVECTOR"
    if dialect == "postgresql":
        native_pg_type = _postgresql_native_column_type(normalized, lower)
        if native_pg_type:
            return native_pg_type
    if "enum(" in lower:
        if dialect in {"mysql", "mariadb"}:
            return normalized
        return _varchar_type(dialect, 255) + " /* fallback */"
    if "varchar" in lower or "nvarchar" in lower or re.match(r"^(var)?char\(", lower):
        size = _type_size(lower) or (None if "max" in lower else 255)
        if "max" in lower:
            return _text_type(dialect)
        return _varchar_type(dialect, size or 255)
    if lower.startswith("int ") or lower.endswith(" unsigned"):
        if "big" in lower:
            return _unsigned_integer_type(dialect, "BIGINT", "unsigned" in lower)
        return _unsigned_integer_type(dialect, "INTEGER", "unsigned" in lower)
    if lower.startswith("bigint"):
        return _unsigned_integer_type(dialect, "BIGINT", "unsigned" in lower)
    if lower.startswith("tinyint"):
        return _boolean_type(dialect) if "(1)" in lower else "SMALLINT"
    if lower.startswith("smallint"):
        return "SMALLINT"
    if lower.startswith("int"):
        return _integer_type(dialect)
    if lower.startswith("decimal") or lower.startswith("numeric"):
        return _clean_native_type(normalized)
    if lower.startswith("double"):
        if dialect in {"mysql", "mariadb"} and re.fullmatch(r"double\(\d+\s*,\s*\d+\)", lower):
            return _clean_native_type(normalized)
        return _float_type(dialect, "double")
    if lower.startswith("float"):
        return _float_type(dialect, "float")
    if lower.startswith("datetime") or lower.startswith("timestamp"):
        return _datetime_type(dialect)
    if lower.startswith("date"):
        return "DATE"
    if lower.startswith("text") or lower.endswith("text"):
        return _text_type(dialect)
    if "binary" in lower or lower in {"blob", "bytea"}:
        return _binary_type(dialect)
    return _text_type(dialect) + " /* fallback */"


def normalize_dialect(dbms: str) -> str:
    normalized = str(dbms or "").strip().lower().replace("_", " ")
    if normalized in {"postgres", "postgresql"}:
        return "postgresql"
    if normalized in {"mysql"}:
        return "mysql"
    if normalized in {"mariadb", "maria db"}:
        return "mariadb"
    if normalized in {"sqlite", "sqlite3"}:
        return "sqlite"
    if normalized in {"duckdb", "duck db"}:
        return "duckdb"
    if normalized in {"sql server", "mssql", "sqlserver", "microsoft sql server"}:
        return "sqlserver"
    return normalized.replace(" ", "")


def quote_identifier(value: str, dialect: str) -> str:
    cleaned = clean_identifier(value) or "unnamed"
    if dialect in {"mysql", "mariadb"}:
        return f"`{cleaned.replace('`', '``')}`"
    if dialect == "sqlserver":
        return f"[{cleaned.replace(']', ']]')}]"
    escaped = cleaned.replace('"', '""')
    return f'"{escaped}"'


def clean_identifier(value: str) -> str:
    cleaned = str(value or "").strip().rstrip(",")
    cleaned = cleaned.replace("\\`", "`").replace("\\.", ".")
    cleaned = cleaned.replace("\\", "")
    cleaned = re.sub(r"\s+", "", cleaned)
    bracket_parts = re.findall(r"\[([^\]]+)\]", cleaned)
    if bracket_parts:
        cleaned = bracket_parts[-1]
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned.strip('"`[]')


def _preserve_original_direct_ddl(
    candidate: dict[str, Any],
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    source_files = _original_direct_ddl_files(candidate)
    if not source_files:
        return {"preserved_source_ddl_files": [], "warnings": []}

    source_dir = output_dir / _repo_slug(candidate) / "source_direct_ddl"
    combined_path = output_dir / _repo_slug(candidate) / "original_direct_ddl.combined.sql"
    preserved_files = []
    warnings = []
    combined_parts = []

    for index, item in enumerate(source_files, start=1):
        repo_path = str(item.get("repo_path") or "")
        local_path = Path(str(item.get("local_path") or ""))
        if not local_path.exists():
            warnings.append(f"original direct DDL file not found: {repo_path}")
            continue
        relative_path = _safe_relative_source_path(repo_path)
        target_path = source_dir / relative_path
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, target_path)
        preserved_files.append(
            {
                "repo_path": repo_path,
                "local_path": local_path.as_posix(),
                "preserved_path": target_path.as_posix(),
            }
        )
        try:
            source_text = local_path.read_text(encoding="utf-8", errors="replace").rstrip()
        except OSError as exc:
            warnings.append(f"failed to read original direct DDL file: {repo_path}: {exc}")
            continue
        combined_parts.append(
            "\n".join(
                [
                    f"-- source_file[{index}]: {repo_path}",
                    source_text,
                    "",
                ]
            )
        )

    if combined_parts and not dry_run:
        write_text(combined_path, "\n".join(combined_parts).rstrip() + "\n")

    return {
        "preserved_source_ddl_dir": None if dry_run else source_dir.as_posix(),
        "preserved_source_ddl_combined_path": None if dry_run or not combined_parts else combined_path.as_posix(),
        "preserved_source_ddl_files": preserved_files,
        "warnings": warnings,
    }


def _original_direct_ddl_files(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    materialization = candidate.get("schema_materialization") or {}
    strategy = str(materialization.get("strategy") or "")
    used_files = [
        str(item).split("#", 1)[0].replace("\\", "/")
        for item in materialization.get("used_files", [])
    ]
    used_lookup = {item.lower() for item in used_files}
    schema_artifact = str(candidate.get("schema_artifact_final") or "").lower()
    direct_strategy = strategy == "static_direct_ddl" or "sql ddl" in schema_artifact

    selected = []
    seen: set[str] = set()
    for item in (candidate.get("local_source_files") or {}).get("schema", []):
        repo_path = str(item.get("repo_path") or "").replace("\\", "/")
        if not repo_path.lower().endswith(".sql"):
            continue
        if used_lookup and repo_path.lower() not in used_lookup and not direct_strategy:
            continue
        if not direct_strategy and repo_path.lower() not in used_lookup:
            continue
        if repo_path.lower() in seen:
            continue
        seen.add(repo_path.lower())
        selected.append(item)

    if used_lookup:
        order = {path.lower(): index for index, path in enumerate(used_files)}
        selected.sort(key=lambda item: order.get(str(item.get("repo_path") or "").replace("\\", "/").lower(), 10**6))
    else:
        selected.sort(key=lambda item: str(item.get("repo_path") or "").lower())
    return selected


def _safe_relative_source_path(repo_path: str) -> Path:
    parts = []
    for raw_part in str(repo_path or "source.sql").replace("\\", "/").split("/"):
        part = re.sub(r"[^A-Za-z0-9_. -]+", "_", raw_part.strip())
        if part and part not in {".", ".."}:
            parts.append(part)
    return Path(*parts) if parts else Path("source.sql")


def _candidate_schema_ir_path(candidate: dict[str, Any]) -> Path | None:
    for key in ("final_schema_ir_path", "schema_ir_path"):
        path = candidate.get(key)
        if path:
            return Path(str(path))

    materialization = candidate.get("schema_materialization") or {}
    for key in ("final_ir_path", "introspection_ir_path"):
        path = materialization.get(key)
        if path:
            return Path(str(path))
    full_name = str(candidate.get("full_name") or "")
    if full_name:
        return Path("benchmark/schema_ir/final_validated") / (
            _repo_slug(candidate) + ".schema_ir.json"
        )
    return None


def _roundtrip_validate(ddl: str, dialect: str, expected: dict[str, int]) -> dict[str, Any]:
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / f"schema.{dialect}.sql"
        path.write_text(ddl, encoding="utf-8")
        result = extract_sql_ddl(
            [ExtractionInputFile(repo_path=path.name, local_path=path)],
            dbms=_dbms_label_from_dialect(dialect),
        )
    parsed = bool(result.schema_ir.tables)
    actual = {
        "table_count": result.schema_ir.table_count(),
        "column_count": sum(len(table.columns) for table in result.schema_ir.tables),
        "foreign_key_count": sum(len(table.foreign_keys) for table in result.schema_ir.tables),
        "unique_count": sum(len(table.unique_constraints) for table in result.schema_ir.tables),
        "index_count": sum(len(table.indexes) for table in result.schema_ir.tables),
    }
    mismatches = {}
    for key, value in expected.items():
        actual_value = actual.get(key)
        if key in {"table_count", "column_count"}:
            if actual_value != value:
                mismatches[key] = {"expected": value, "actual": actual_value}
        elif actual_value is None or actual_value < value:
            mismatches[key] = {"expected_at_least": value, "actual": actual_value}
    return {
        "parsed": parsed,
        "passed": parsed and not mismatches,
        "expected": expected,
        "actual": actual,
        "mismatches": mismatches,
        "parser_status": result.status,
        "parser_warnings": result.warnings,
        "parser_errors": result.errors,
    }


def _sqlite_execute_validate(ddl: str) -> dict[str, Any]:
    try:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.executescript(ddl)
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return {"executed": True, "passed": False, "error": str(exc)}
    return {"executed": True, "passed": True, "error": None}


def _normalize_type(raw: str) -> str:
    cleaned = str(raw or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\bNOT\s+NULL\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bNULL\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bAUTO_INCREMENT\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bIDENTITY\s*\([^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bCHARACTER\s+SET\s+\w+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bCOLLATE\s+\w+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'"([^"]+)"', r"\1", cleaned)
    return cleaned.strip()


def _is_identity_column(column: ColumnIR) -> bool:
    if column.identity:
        return True
    normalized = _normalize_type(column.type).lower()
    return normalized in {"auto", "bigauto", "increments", "bigincrements"}


def _is_integer_identity_type(sql_type: str) -> bool:
    normalized = str(sql_type or "").strip().upper()
    return normalized.startswith(("BIGINT", "INT", "INTEGER", "SMALLINT"))


def _native_column_type(normalized: str, lower: str, dialect: str) -> str:
    if dialect != "sqlserver":
        return ""
    if re.match(r"^(?:n?varchar|n?char|char)\((?:\d+|max)\)$", lower):
        return _clean_native_type(normalized)
    if re.match(r"^(?:varbinary|binary)\((?:\d+|max)\)$", lower):
        return _clean_native_type(normalized)
    if re.match(r"^(?:datetime2|datetimeoffset|time)(?:\(\d+\))?$", lower):
        return _clean_native_type(normalized)
    if re.match(r"^(?:decimal|numeric)\(\d+\s*,\s*\d+\)$", lower):
        return _clean_native_type(normalized)
    if lower in {
        "bit",
        "date",
        "datetime",
        "smalldatetime",
        "float",
        "real",
        "money",
        "smallmoney",
        "uniqueidentifier",
    }:
        return _clean_native_type(normalized)
    return ""


def _postgresql_native_column_type(normalized: str, lower: str) -> str:
    if lower in {"smallserial", "serial", "bigserial", "bm25vector"}:
        return normalized.upper() if lower.endswith("serial") else normalized
    if re.fullmatch(r"vector\(\d+\)(?:\[\])?", lower):
        return normalized.upper()
    if re.fullmatch(r"[a-z_][a-z0-9_]*(?:\([^)]*\))?\[\]", lower):
        return normalized.upper()
    return ""


def _clean_native_type(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().upper()


def _type_size(value: str) -> int | None:
    match = re.search(r"\((\d+)\)", value)
    return int(match.group(1)) if match else None


def _varchar_type(dialect: str, size: int) -> str:
    if dialect == "sqlserver":
        return f"NVARCHAR({size})"
    return f"VARCHAR({size})"


def _text_type(dialect: str) -> str:
    if dialect == "sqlserver":
        return "NVARCHAR(MAX)"
    return "TEXT"


def _integer_type(dialect: str) -> str:
    return "INTEGER" if dialect != "sqlserver" else "INT"


def _unsigned_integer_type(dialect: str, base: str, unsigned: bool) -> str:
    if dialect in {"mysql", "mariadb"} and unsigned:
        return f"{base} UNSIGNED"
    if dialect == "sqlserver" and base == "INTEGER":
        return "INT"
    return base


def _boolean_type(dialect: str) -> str:
    if dialect in {"mysql", "mariadb"}:
        return "TINYINT(1)"
    if dialect == "sqlserver":
        return "BIT"
    return "BOOLEAN"


def _float_type(dialect: str, lower: str) -> str:
    if dialect == "postgresql":
        return "DOUBLE PRECISION" if lower in {"double", "float"} else "REAL"
    if dialect in {"mysql", "mariadb"}:
        return "DOUBLE" if lower == "double" else "FLOAT"
    if dialect == "sqlserver":
        return "FLOAT"
    return "REAL"


def _datetime_type(dialect: str) -> str:
    if dialect in {"mysql", "mariadb", "sqlserver"}:
        return "DATETIME"
    return "TIMESTAMP"


def _json_type(dialect: str) -> str:
    if dialect == "postgresql":
        return "JSONB"
    if dialect in {"mysql", "mariadb"}:
        return "JSON"
    if dialect == "sqlserver":
        return "NVARCHAR(MAX)"
    if dialect == "duckdb":
        return "JSON"
    return "TEXT"


def _uuid_type(dialect: str) -> str:
    if dialect == "postgresql":
        return "UUID"
    if dialect == "duckdb":
        return "UUID"
    if dialect == "sqlserver":
        return "UNIQUEIDENTIFIER"
    return "CHAR(36)"


def _binary_type(dialect: str) -> str:
    if dialect == "postgresql":
        return "BYTEA"
    if dialect == "sqlserver":
        return "VARBINARY(MAX)"
    return "BLOB"


def _resolve_columns(columns: list[str], column_names: dict[str, str]) -> list[str]:
    resolved = []
    for column in columns:
        cleaned = clean_identifier(column)
        match = column_names.get(cleaned.lower())
        if match:
            resolved.append(match)
    return resolved


def _key_participating_columns(table: TableIR) -> set[str]:
    columns = {clean_identifier(column).lower() for column in table.primary_key}
    for constraint in table.unique_constraints:
        columns.update(clean_identifier(column).lower() for column in constraint.columns)
    for index in table.indexes:
        columns.update(clean_identifier(column).lower() for column in index.columns)
    for foreign_key in table.foreign_keys:
        columns.update(clean_identifier(column).lower() for column in foreign_key.columns)
    return {column for column in columns if column}


def _resolve_table_name(name: str, tables: list[RenderTable]) -> str | None:
    cleaned = clean_identifier(name)
    for table in tables:
        if table.name.lower() == cleaned.lower():
            return table.name
    return None


def _order_tables_for_inline_foreign_keys(tables: list[RenderTable]) -> list[RenderTable]:
    lookup = {table.name.lower(): table for table in tables}
    remaining = {table.name.lower(): table for table in tables}
    ordered: list[RenderTable] = []
    while remaining:
        progressed = False
        for key, table in list(remaining.items()):
            dependencies = {
                clean_identifier(foreign_key.ref_table).lower()
                for foreign_key in table.foreign_keys
                if clean_identifier(foreign_key.ref_table).lower() in lookup
            }
            if dependencies.isdisjoint(remaining.keys()):
                ordered.append(table)
                remaining.pop(key)
                progressed = True
        if not progressed:
            ordered.extend(remaining.values())
            break
    return ordered


def _check_expression(constraint: CheckConstraintIR) -> str:
    expression = constraint.expression.strip()
    match = re.search(r"CHECK\s*\((.*)\)", expression, re.IGNORECASE | re.S)
    if match:
        return match.group(1).strip()
    return expression


def _is_simple_check_expression(expression: str) -> bool:
    if not expression or len(expression) > 500:
        return False
    forbidden = (";", "--", "/*", "*/", "SELECT ", "INSERT ", "UPDATE ", "DELETE ")
    return not any(token in expression.upper() for token in forbidden)


def _is_unbounded_index_type(sql_type: str) -> bool:
    normalized = str(sql_type or "").strip().upper()
    return normalized in {
        "TEXT",
        "BLOB",
        "BYTEA",
        "JSON",
        "JSONB",
        "NVARCHAR(MAX)",
        "VARBINARY(MAX)",
        "LONGTEXT",
        "MEDIUMTEXT",
    }


def _fk_type_family(sql_type: str, dialect: str) -> str:
    normalized = str(sql_type or "").strip().upper()
    if dialect == "postgresql" and normalized == "UUID":
        return "uuid"
    if dialect == "sqlserver" and normalized == "UNIQUEIDENTIFIER":
        return "uuid"
    if dialect == "postgresql" and normalized in {"SMALLSERIAL", "SERIAL", "BIGSERIAL"}:
        return "integer"
    if normalized.startswith(("BIGINT", "INTEGER", "INT", "SMALLINT", "TINYINT")):
        return "integer"
    if normalized.startswith(("VARCHAR", "CHAR", "NVARCHAR", "NCHAR")):
        return "string"
    if normalized in {"TEXT", "UUID"}:
        return "string" if dialect in {"mysql", "mariadb", "sqlite"} else normalized.lower()
    return normalized.lower()


def _repo_slug(candidate: dict[str, Any]) -> str:
    return str(candidate.get("full_name", "unknown_repo")).replace("/", "__")


def _dbms_file_label(dbms: str) -> str:
    label = str(dbms or "unknown").strip() or "unknown"
    return re.sub(r"[^A-Za-z0-9_. -]+", "_", label)


def _dbms_label_from_dialect(dialect: str) -> str:
    return {
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mariadb": "MariaDB",
        "sqlite": "SQLite",
        "sqlserver": "SQL Server",
    }.get(dialect, dialect)


def _short_name(value: str, limit: int = 60) -> str:
    cleaned = clean_identifier(value) or "constraint"
    if len(cleaned) <= limit:
        return cleaned
    digest = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:8]
    return f"{cleaned[: limit - 9]}_{digest}"


def _warning_kind(warning: str) -> str:
    return warning.split(":", 1)[0]


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        result.append(warning)
    return result


def _format_counts(counter: Counter[str]) -> str:
    if not counter:
        return "- none"
    return "\n".join(f"- {key}: {value}" for key, value in sorted(counter.items()))


def _format_review_candidates(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "- 无"
    lines = []
    for candidate in candidates:
        result = candidate.get("reference_ddl_generation", {})
        warnings = result.get("warnings") or []
        errors = result.get("errors") or []
        lines.append(
            f"- `{candidate.get('full_name')}` | DBMS={candidate.get('dbms_final')} "
            f"| status={result.get('status')} | warnings={len(warnings)} | errors={len(errors)}"
        )
    return "\n".join(lines)
