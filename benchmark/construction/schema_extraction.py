from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbgenie.core.schema_ir import (
    ColumnIR,
    ForeignKeyIR,
    IndexIR,
    SchemaIR,
    TableIR,
    UniqueConstraintIR,
)


@dataclass(frozen=True)
class ExtractionInputFile:
    repo_path: str
    local_path: Path


@dataclass
class StaticExtractionResult:
    schema_ir: SchemaIR
    status: str
    strategy: str
    used_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    unsupported_constructs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DDLDialect:
    name: str


DIALECT_GENERIC = DDLDialect("generic")
DIALECT_POSTGRESQL = DDLDialect("postgresql")
DIALECT_MYSQL = DDLDialect("mysql")
DIALECT_SQLITE = DDLDialect("sqlite")
DIALECT_SQLSERVER = DDLDialect("sqlserver")
DIALECT_DUCKDB = DDLDialect("duckdb")


def extract_schema_static(
    candidate: dict[str, Any],
    schema_files: list[ExtractionInputFile],
) -> StaticExtractionResult:
    sql_files = [item for item in schema_files if _is_sql_file(item.repo_path)]
    if sql_files:
        return extract_sql_ddl(sql_files, dbms=str(candidate.get("dbms_final") or ""))

    prisma_files = [
        item for item in schema_files if item.repo_path.lower().replace("\\", "/").endswith("schema.prisma")
    ]
    if prisma_files:
        return extract_prisma_schema(prisma_files)

    embedded_sql_files = _embedded_sql_files(schema_files)
    if embedded_sql_files:
        result = extract_sql_ddl(embedded_sql_files, dbms=str(candidate.get("dbms_final") or ""))
        result.strategy = "static_embedded_sql"
        return result

    family = _detect_static_family(candidate, schema_files)
    if family == "django":
        return extract_django_schema(schema_files)
    if family == "laravel":
        return extract_laravel_schema(schema_files)
    if family == "rails":
        return extract_rails_schema(schema_files)
    if family == "alembic":
        return extract_alembic_schema(schema_files)
    if family == "typeorm":
        return extract_typeorm_schema(schema_files)
    if family == "sequelize":
        return extract_sequelize_schema(schema_files)
    if family == "ef_core":
        return extract_ef_core_schema(schema_files)
    if family == "csharp_entities":
        return extract_csharp_entity_schema(schema_files)
    if family == "python_models":
        return extract_python_sqlalchemy_schema(schema_files)
    if family in {"go_migrations", "php_migrations"}:
        return _generic_family_result(family, schema_files)

    return StaticExtractionResult(
        schema_ir=SchemaIR(),
        status="skipped",
        strategy="skipped",
        used_files=[item.repo_path for item in schema_files],
        errors=["no supported schema artifact for static extraction"],
    )


def extract_sql_ddl(sql_files: list[ExtractionInputFile], dbms: str = "") -> StaticExtractionResult:
    ordered_files = sorted(sql_files, key=lambda item: item.repo_path.lower())
    text_parts = []
    errors = []
    for item in ordered_files:
        try:
            text_parts.append(item.local_path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
    if errors:
        return StaticExtractionResult(
            schema_ir=SchemaIR(),
            status="failed",
            strategy="static_direct_ddl",
            used_files=[item.repo_path for item in ordered_files],
            errors=errors,
        )

    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    unsupported: list[str] = []
    dialect = _ddl_dialect(dbms, ordered_files, text_parts)
    ddl_text = _preprocess_ddl_text("\n".join(text_parts), dialect)

    for statement in _split_sql_statements(ddl_text):
        normalized = statement.strip()
        if not normalized:
            continue
        upper = normalized.lstrip().upper()
        if re.match(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+|TEMP\s+)?TABLE\b", normalized, re.IGNORECASE):
            table, statement_warnings = _parse_create_table(normalized, dialect)
            warnings.extend(statement_warnings)
            if table:
                tables[table.name] = table
            else:
                unsupported.append(_statement_head(normalized))
            continue
        if re.match(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b", normalized, re.IGNORECASE):
            index = _parse_create_index(normalized)
            if index and index[0] in tables:
                table = tables[index[0]]
                tables[index[0]] = TableIR(
                    name=table.name,
                    columns=table.columns,
                    primary_key=table.primary_key,
                    foreign_keys=table.foreign_keys,
                    unique_constraints=table.unique_constraints,
                    check_constraints=table.check_constraints,
                    indexes=[*table.indexes, index[1]],
                )
            else:
                unsupported.append(_statement_head(normalized))
            continue
        if upper.startswith("ALTER TABLE"):
            parsed = _parse_alter_table(normalized)
            if parsed and parsed[0] in tables:
                tables[parsed[0]] = _merge_alter_table(tables[parsed[0]], parsed[1])
            else:
                warnings.append(f"ALTER TABLE parsing is limited for {dialect.name}")
                unsupported.append(_statement_head(normalized))
            continue
        if any(token in upper for token in ("CREATE TYPE", "CREATE EXTENSION", "CREATE TRIGGER")):
            unsupported.append(_statement_head(normalized))

    schema_ir = SchemaIR(tables=sorted(tables.values(), key=lambda table: table.name.lower()))
    status = "static_extracted" if schema_ir.tables else "failed"
    if unsupported and schema_ir.tables:
        status = "partial"
    return StaticExtractionResult(
        schema_ir=schema_ir,
        status=status,
        strategy="static_direct_ddl",
        used_files=[item.repo_path for item in ordered_files],
        warnings=[f"direct DDL dialect layer: {dialect.name}", *warnings],
        errors=[] if schema_ir.tables else ["no CREATE TABLE statements could be parsed"],
        unsupported_constructs=unsupported[:50],
    )


def extract_prisma_schema(prisma_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: list[TableIR] = []
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in prisma_files:
        used_files.append(item.repo_path)
        try:
            text = item.local_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
            continue
        for model_name, body in _iter_prisma_blocks(text, "model"):
            table_name = _prisma_table_name(model_name, body)
            columns: list[ColumnIR] = []
            primary_key: list[str] = []
            unique_constraints: list[UniqueConstraintIR] = []
            foreign_keys: list[ForeignKeyIR] = []
            relation_fields: dict[str, str] = {}

            for raw_line in body.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("//"):
                    continue
                if line.startswith("@@id"):
                    primary_key = _prisma_attribute_columns(line)
                    continue
                if line.startswith("@@unique"):
                    columns_for_unique = _prisma_attribute_columns(line)
                    if columns_for_unique:
                        unique_constraints.append(UniqueConstraintIR(columns=columns_for_unique))
                    continue
                if line.startswith("@@"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                field_name, field_type = parts[0], parts[1]
                attrs = line[len(field_name) + len(field_type) + 2 :]
                if "@relation" in attrs and _is_prisma_relation_type(field_type):
                    relation_fields[field_name] = _clean_prisma_type(field_type)
                    continue
                if _is_prisma_relation_type(field_type):
                    continue
                columns.append(
                    ColumnIR(
                        name=_prisma_field_db_name(field_name, attrs),
                        type=_clean_prisma_type(field_type),
                        nullable=field_type.endswith("?"),
                    )
                )
                if "@id" in attrs:
                    primary_key.append(_prisma_field_db_name(field_name, attrs))
                if "@unique" in attrs:
                    unique_constraints.append(
                        UniqueConstraintIR(columns=[_prisma_field_db_name(field_name, attrs)])
                    )
                relation = _parse_prisma_relation(attrs)
                if relation:
                    ref_table = relation_fields.get(field_name) or relation.get("references_model", "")
                    foreign_keys.append(
                        ForeignKeyIR(
                            columns=relation["fields"],
                            ref_table=ref_table,
                            ref_columns=relation["references"],
                        )
                    )

            tables.append(
                TableIR(
                    name=table_name,
                    columns=columns,
                    primary_key=primary_key,
                    foreign_keys=foreign_keys,
                    unique_constraints=unique_constraints,
                    indexes=[],
                )
            )

    schema_ir = SchemaIR(tables=sorted(tables, key=lambda table: table.name.lower()))
    status = "static_extracted" if schema_ir.tables else "failed"
    return StaticExtractionResult(
        schema_ir=schema_ir,
        status=status,
        strategy="static_prisma",
        used_files=used_files,
        warnings=warnings,
        errors=errors if errors else ([] if schema_ir.tables else ["no Prisma model blocks could be parsed"]),
    )


def extract_django_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".py"):
            continue
        used_files.append(item.repo_path)
        try:
            text = item.local_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
            continue
        for match in re.finditer(r"migrations\.CreateModel\s*\(", text):
            block = _call_block(text, match.end() - 1)
            table = _parse_django_create_model(block)
            if table:
                tables[table.name] = table
        for match in re.finditer(r"migrations\.AddField\s*\(", text):
            block = _call_block(text, match.end() - 1)
            table_name, column, fk = _parse_django_add_field(block)
            if table_name and column:
                table = tables.get(table_name, TableIR(name=table_name))
                tables[table_name] = _table_with(
                    table,
                    columns=[*table.columns, column],
                    foreign_keys=[*table.foreign_keys, *([fk] if fk else [])],
                )
    return _schema_result("static_django", tables, used_files, warnings, errors)


def extract_laravel_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".php"):
            continue
        used_files.append(item.repo_path)
        try:
            text = item.local_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
            continue
        for match in re.finditer(r"Schema::create\s*\(\s*['\"]([^'\"]+)['\"]", text):
            table_name = match.group(1)
            block = _closure_block_after(text, match.end())
            table = _parse_laravel_table_block(table_name, block)
            if table:
                tables[table.name] = table
        for match in re.finditer(r"Schema::table\s*\(\s*['\"]([^'\"]+)['\"]", text):
            table_name = match.group(1)
            block = _closure_block_after(text, match.end())
            patch = _parse_laravel_table_block(table_name, block)
            if patch:
                old = tables.get(table_name, TableIR(name=table_name))
                tables[table_name] = _merge_table(old, patch)
    return _schema_result("static_laravel", tables, used_files, warnings, errors)


def extract_rails_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    schema_rb = [
        item for item in schema_files if item.repo_path.lower().replace("\\", "/").endswith("db/schema.rb")
    ]
    files = schema_rb or [item for item in schema_files if item.repo_path.lower().endswith(".rb")]
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(files, key=lambda file: file.repo_path.lower()):
        used_files.append(item.repo_path)
        try:
            text = item.local_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
            continue
        for match in re.finditer(r"create_table\s+[\"']([^\"']+)[\"'][^\n]*\s+do\s+\|t\|", text):
            table_name = match.group(1)
            block = _ruby_do_block(text, match.end())
            table = _parse_rails_table_block(table_name, match.group(0), block)
            tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
        for match in re.finditer(r"add_index\s+[\"']([^\"']+)[\"']\s*,\s*(.+)", text):
            table_name = match.group(1)
            table = tables.get(table_name, TableIR(name=table_name))
            index = _parse_rails_add_index(match.group(2))
            if index:
                tables[table_name] = _table_with(table, indexes=[*table.indexes, index])
    return _schema_result("static_rails", tables, used_files, warnings, errors)


def extract_alembic_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".py"):
            continue
        used_files.append(item.repo_path)
        try:
            text = item.local_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{item.repo_path}: {exc}")
            continue
        for match in re.finditer(r"op\.create_table\s*\(\s*['\"]([^'\"]+)['\"]", text):
            table_name = match.group(1)
            block = _call_block(text, match.end() - 1)
            table = _parse_sqlalchemy_table_call(table_name, block)
            tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
        for match in re.finditer(r"op\.add_column\s*\(\s*['\"]([^'\"]+)['\"]", text):
            table_name = match.group(1)
            block = _call_block(text, match.end() - 1)
            column = _parse_sqlalchemy_column(block)
            if column:
                old = tables.get(table_name, TableIR(name=table_name))
                tables[table_name] = _table_with(old, columns=[*old.columns, column])
        for match in re.finditer(r"op\.create_index\s*\(", text):
            block = _call_block(text, match.end() - 1)
            parsed = _parse_alembic_create_index(block)
            if parsed and parsed[0] in tables:
                old = tables[parsed[0]]
                tables[parsed[0]] = _table_with(old, indexes=[*old.indexes, parsed[1]])
    return _schema_result("static_alembic", tables, used_files, warnings, errors)


def extract_typeorm_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    sql_like = []
    entity_files = []
    for item in schema_files:
        text = _safe_read(item)
        if "queryRunner.query" in text and "CREATE TABLE" in text.upper():
            sql_like.append(item)
        elif "@Entity" in text or "@Column" in text:
            entity_files.append(item)
    if sql_like:
        return extract_sql_ddl(_typescript_sql_files(sql_like))
    return _extract_typeorm_entities(entity_files)


def extract_sequelize_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".js"):
            continue
        used_files.append(item.repo_path)
        text = _safe_read(item)
        for match in re.finditer(r"createTable\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*\{", text):
            table_name = match.group(1)
            body = _matching_brace_block(text, text.find("{", match.end() - 1))
            table = _parse_sequelize_columns(table_name, body)
            tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
        for match in re.finditer(r"addColumn(?:IfMissing)?\s*\([^,]+,\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*,\s*\{", text):
            table_name, column_name = match.group(1), match.group(2)
            body = _matching_brace_block(text, text.find("{", match.end() - 1))
            column = _sequelize_column_from_body(column_name, body)
            old = tables.get(table_name, TableIR(name=table_name))
            tables[table_name] = _table_with(old, columns=[*old.columns, column])
    return _schema_result("static_sequelize", tables, used_files, warnings, errors)


def extract_ef_core_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    warnings: list[str] = []
    errors: list[str] = []
    used_files: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".cs"):
            continue
        used_files.append(item.repo_path)
        text = _safe_read(item)
        migration_text = _ef_up_method_body(text) or text
        for match in re.finditer(r"migrationBuilder\.CreateTable\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            table_name = _ef_named_string(block, "name")
            if not table_name:
                continue
            table = _parse_ef_create_table(table_name, block)
            tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
        for match in re.finditer(r"modelBuilder\.Entity\s*\(\s*\"([^\"]+)\"\s*,\s*b\s*=>\s*\{", text):
            block = _matching_brace_block(text, text.find("{", match.end() - 1))
            table = _parse_ef_model_snapshot_entity(match.group(1), block)
            if table:
                tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
        for match in re.finditer(r"migrationBuilder\.DropColumn\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            table_name = _ef_named_string(block, "table")
            column_name = _ef_named_string(block, "name")
            if table_name and column_name and table_name in tables:
                tables[table_name] = _remove_column_from_table(tables[table_name], column_name)
        for match in re.finditer(r"migrationBuilder\.DropForeignKey\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            table_name = _ef_named_string(block, "table")
            if table_name and table_name in tables:
                tables[table_name] = _table_with(tables[table_name], foreign_keys=[])
        for match in re.finditer(r"migrationBuilder\.CreateIndex\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            parsed = _parse_ef_create_index(block)
            if parsed:
                table_name, index = parsed
                tables[table_name] = _merge_table(
                    tables.get(table_name, TableIR(name=table_name)),
                    TableIR(name=table_name, indexes=[index]),
                )
        for match in re.finditer(r"migrationBuilder\.AddForeignKey\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            parsed = _parse_ef_add_foreign_key(block)
            if parsed:
                table_name, fk = parsed
                tables[table_name] = _merge_table(
                    tables.get(table_name, TableIR(name=table_name)),
                    TableIR(name=table_name, foreign_keys=[fk]),
                )
    return _schema_result("static_ef_core", tables, used_files, warnings, errors)


def extract_csharp_entity_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    used_files: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".cs"):
            continue
        text = _safe_read(item)
        if "[Table(" not in text and "public class" not in text:
            continue
        table = _parse_csharp_entity(text)
        if table and table.columns:
            used_files.append(item.repo_path)
            tables[table.name] = _merge_table(tables.get(table.name, TableIR(name=table.name)), table)
    return _schema_result("static_csharp_entities", tables, used_files, warnings, errors)


def extract_python_sqlalchemy_schema(schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    used_files: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".py"):
            continue
        text = _safe_read(item)
        if "__tablename__" not in text or "Column(" not in text:
            continue
        used_files.append(item.repo_path)
        for class_match in re.finditer(r"class\s+(\w+)\s*\([^)]*\):", text):
            class_name = class_match.group(1)
            next_class = re.search(r"\nclass\s+\w+\s*\(", text[class_match.end() :])
            body_end = class_match.end() + next_class.start() if next_class else len(text)
            body = text[class_match.end() : body_end]
            table_name_match = re.search(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]", body)
            if not table_name_match:
                continue
            table_name = table_name_match.group(1) or class_name
            columns: list[ColumnIR] = []
            primary_key: list[str] = []
            foreign_keys: list[ForeignKeyIR] = []
            unique_constraints: list[UniqueConstraintIR] = []
            indexes: list[IndexIR] = []
            for line in body.splitlines():
                if "Column(" not in line and "db.Column(" not in line:
                    continue
                parsed = _parse_python_sqlalchemy_column(line)
                if not parsed:
                    continue
                column, fk = parsed
                columns.append(column)
                if "primary_key=True" in line:
                    primary_key.append(column.name)
                if "unique=True" in line:
                    unique_constraints.append(UniqueConstraintIR(columns=[column.name]))
                if "index=True" in line:
                    indexes.append(IndexIR(columns=[column.name]))
                if fk:
                    foreign_keys.append(fk)
            if columns:
                tables[table_name] = TableIR(
                    name=table_name,
                    columns=columns,
                    primary_key=primary_key,
                    foreign_keys=foreign_keys,
                    unique_constraints=unique_constraints,
                    indexes=indexes,
                )
    return _schema_result("static_python_sqlalchemy", tables, used_files, warnings, errors)


def _parse_create_table(
    statement: str,
    dialect: DDLDialect = DIALECT_GENERIC,
) -> tuple[TableIR | None, list[str]]:
    match = re.search(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+|TEMP\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)\s*\(",
        statement,
        re.IGNORECASE,
    )
    if not match:
        return None, []
    table_name = _clean_identifier(match.group(1))
    start = statement.find("(", match.end() - 1)
    end = _matching_paren(statement, start)
    if start < 0 or end < 0:
        return None, [f"cannot find column block for {table_name}"]
    body = statement[start + 1 : end]
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    unique_constraints: list[UniqueConstraintIR] = []
    warnings: list[str] = []

    for item in _split_top_level_commas(body):
        part = item.strip()
        if not part:
            continue
        upper = part.upper()
        is_mysql_index = dialect.name in {"mysql", "mariadb"} and upper.startswith(("KEY ", "INDEX "))
        if upper.startswith(("CONSTRAINT ", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")) or is_mysql_index:
            if "PRIMARY KEY" in upper:
                primary_key = _columns_inside_keyword(part, "PRIMARY KEY") or primary_key
            elif "FOREIGN KEY" in upper:
                fk = _parse_table_foreign_key(part)
                if fk:
                    foreign_keys.append(fk)
            elif "UNIQUE" in upper:
                unique_columns = _columns_inside_keyword(part, "UNIQUE") or _columns_inside_first_parens(part)
                if unique_columns:
                    unique_constraints.append(UniqueConstraintIR(columns=unique_columns))
            elif is_mysql_index:
                # MySQL inline KEY definitions are parsed as indexes by table-level post-processing later.
                warnings.append(f"MySQL table-level index kept for human review on {table_name}: {part[:80]}")
            elif "CHECK" in upper:
                warnings.append(f"CHECK constraint kept for human review on {table_name}")
            continue

        column = _parse_column_definition(part)
        if not column:
            warnings.append(f"unsupported column definition in {table_name}: {part[:80]}")
            continue
        columns.append(column)
        if "PRIMARY KEY" in upper:
            primary_key.append(column.name)
        if "UNIQUE" in upper:
            unique_constraints.append(UniqueConstraintIR(columns=[column.name]))
        inline_fk = _parse_inline_foreign_key(column.name, part)
        if inline_fk:
            foreign_keys.append(inline_fk)

    return (
        TableIR(
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            unique_constraints=unique_constraints,
            indexes=[],
        ),
        warnings,
    )


def _parse_django_create_model(block: str) -> TableIR | None:
    name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", block)
    if not name_match:
        return None
    table_name = name_match.group(1)
    db_table_match = re.search(r"['\"]db_table['\"]\s*:\s*['\"]([^'\"]+)['\"]", block)
    if db_table_match:
        table_name = db_table_match.group(1)
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    fields_block_match = re.search(r"fields\s*=\s*\[", block)
    if not fields_block_match:
        return TableIR(name=table_name)
    start = block.find("[", fields_block_match.end() - 1)
    end = _matching_square(block, start)
    if end < 0:
        return TableIR(name=table_name)
    for field_expr in _django_field_tuples(block[start + 1 : end]):
        parsed = _parse_django_field_tuple(field_expr)
        if not parsed:
            continue
        column, fk = parsed
        columns.append(column)
        if "primary_key=True" in field_expr:
            primary_key.append(column.name)
        if fk:
            foreign_keys.append(fk)
    return TableIR(name=table_name, columns=columns, primary_key=primary_key, foreign_keys=foreign_keys)


def _parse_django_add_field(block: str) -> tuple[str | None, ColumnIR | None, ForeignKeyIR | None]:
    model_match = re.search(r"model_name\s*=\s*['\"]([^'\"]+)['\"]", block)
    name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", block)
    field_match = re.search(r"field\s*=\s*(models\.[\s\S]+)", block)
    if not model_match or not name_match or not field_match:
        return None, None, None
    parsed = _parse_django_field_tuple(f"('{name_match.group(1)}', {field_match.group(1)})")
    if not parsed:
        return model_match.group(1), None, None
    return model_match.group(1), parsed[0], parsed[1]


def _django_field_tuples(fields_text: str) -> list[str]:
    tuples = []
    for index, char in enumerate(fields_text):
        if char != "(":
            continue
        end = _matching_paren(fields_text, index)
        if end < 0:
            continue
        segment = fields_text[index : end + 1]
        if re.match(r"\(\s*['\"][^'\"]+['\"]\s*,\s*models\.", segment):
            tuples.append(segment)
    return tuples


def _parse_django_field_tuple(field_expr: str) -> tuple[ColumnIR, ForeignKeyIR | None] | None:
    name_match = re.match(r"\(\s*['\"]([^'\"]+)['\"]\s*,\s*models\.([A-Za-z0-9_]+)Field?\s*\(", field_expr.strip())
    if not name_match:
        name_match = re.match(r"\(\s*['\"]([^'\"]+)['\"]\s*,\s*models\.([A-Za-z0-9_]+)\s*\(", field_expr.strip())
    if not name_match:
        return None
    name, field_type = name_match.group(1), name_match.group(2)
    db_column = _kw_string(field_expr, "db_column") or name
    nullable = "null=True" in field_expr or "blank=True" in field_expr
    column = ColumnIR(name=db_column, type=field_type, nullable=nullable)
    fk = None
    if field_type in {"ForeignKey", "OneToOneField"}:
        to_match = re.search(r"models\.[A-Za-z0-9_]+\s*\(\s*(?:to=)?['\"]([^'\"]+)['\"]", field_expr)
        ref = to_match.group(1).split(".")[-1] if to_match else ""
        fk_column = db_column if db_column.endswith("_id") else f"{db_column}_id"
        column = ColumnIR(name=fk_column, type="ForeignKey", nullable=nullable)
        fk = ForeignKeyIR(columns=[fk_column], ref_table=ref, ref_columns=["id"])
    return column, fk


def _parse_laravel_table_block(table_name: str, block: str) -> TableIR | None:
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    unique_constraints: list[UniqueConstraintIR] = []
    indexes: list[IndexIR] = []
    for stmt in re.findall(r"\$table->[^;]+;", block):
        method_match = re.match(r"\$table->([A-Za-z0-9_]+)\s*\((.*?)\)", stmt, re.S)
        if not method_match:
            continue
        method = method_match.group(1)
        args = method_match.group(2)
        column_name = _first_quoted(args)
        nullable = "->nullable(" in stmt or "->nullable()" in stmt
        if method in {"id", "increments", "bigIncrements"}:
            name = column_name or "id"
            columns.append(ColumnIR(name=name, type=method, nullable=False))
            primary_key.append(name)
        elif method == "timestamps":
            columns.append(ColumnIR(name="created_at", type="timestamp", nullable=True))
            columns.append(ColumnIR(name="updated_at", type="timestamp", nullable=True))
        elif method in {"foreignId", "foreignUuid", "foreignIdFor"}:
            name = column_name or _laravel_foreign_id_for(args)
            columns.append(ColumnIR(name=name, type=method, nullable=nullable))
            ref_table = _laravel_constrained_table(stmt, name)
            if ref_table:
                foreign_keys.append(ForeignKeyIR(columns=[name], ref_table=ref_table, ref_columns=["id"]))
        elif method in {"unique", "index"}:
            cols = _laravel_column_list_arg(args)
            if method == "unique" and cols:
                unique_constraints.append(UniqueConstraintIR(columns=cols))
            elif cols:
                indexes.append(IndexIR(columns=cols))
        elif column_name:
            columns.append(ColumnIR(name=column_name, type=method, nullable=nullable))
            if "->primary(" in stmt or "->primary()" in stmt:
                primary_key.append(column_name)
            if "->unique(" in stmt or "->unique()" in stmt:
                unique_constraints.append(UniqueConstraintIR(columns=[column_name]))
            if "->index(" in stmt or "->index()" in stmt:
                indexes.append(IndexIR(columns=[column_name]))
    if not columns and not indexes and not foreign_keys:
        return None
    return TableIR(
        name=table_name,
        columns=columns,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        unique_constraints=unique_constraints,
        indexes=indexes,
    )


def _parse_rails_table_block(table_name: str, header: str, block: str) -> TableIR:
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    indexes: list[IndexIR] = []
    unique_constraints: list[UniqueConstraintIR] = []
    if "id: false" not in header:
        columns.append(ColumnIR(name="id", type="primary_key", nullable=False))
        primary_key.append("id")
    for line in block.splitlines():
        stripped = line.strip()
        col_match = re.match(r"t\.([a-zA-Z_][\w]*)\s+[\"']([^\"']+)[\"'](.*)", stripped)
        if col_match:
            col_type, col_name, opts = col_match.group(1), col_match.group(2), col_match.group(3)
            columns.append(ColumnIR(name=col_name, type=col_type, nullable="null: false" not in opts))
            continue
        idx_match = re.match(r"t\.index\s+\[([^\]]+)\](.*)", stripped)
        if idx_match:
            cols = re.findall(r"[\"']([^\"']+)[\"']", idx_match.group(1))
            unique = "unique: true" in idx_match.group(2)
            name = _ruby_option_string(idx_match.group(2), "name")
            index = IndexIR(columns=cols, name=name, unique=unique)
            indexes.append(index)
            if unique:
                unique_constraints.append(UniqueConstraintIR(columns=cols, name=name))
    return TableIR(
        name=table_name,
        columns=columns,
        primary_key=primary_key,
        unique_constraints=unique_constraints,
        indexes=indexes,
    )


def _parse_rails_add_index(args: str) -> IndexIR | None:
    columns = re.findall(r"[\"']([^\"']+)[\"']", args)
    if not columns:
        return None
    # First quoted value can be a single column when no array is used.
    unique = "unique: true" in args
    name = _ruby_option_string(args, "name")
    return IndexIR(columns=columns, name=name, unique=unique)


def _parse_sqlalchemy_table_call(table_name: str, block: str) -> TableIR:
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    unique_constraints: list[UniqueConstraintIR] = []
    for col_match in re.finditer(r"sa\.Column\s*\(", block):
        col = _parse_sqlalchemy_column(_call_block(block, col_match.end() - 1))
        if col:
            columns.append(col)
            col_block = _call_block(block, col_match.end() - 1)
            if "primary_key=True" in col_block:
                primary_key.append(col.name)
            fk_match = re.search(r"sa\.ForeignKey\s*\(\s*['\"]([^'\"]+)['\"]", col_block)
            if fk_match:
                ref = fk_match.group(1)
                if "." in ref:
                    ref_table, ref_col = ref.rsplit(".", 1)
                    foreign_keys.append(ForeignKeyIR(columns=[col.name], ref_table=ref_table, ref_columns=[ref_col]))
        else:
            continue
    for uq_match in re.finditer(r"sa\.UniqueConstraint\s*\(([^)]*)\)", block):
        cols = re.findall(r"['\"]([^'\"]+)['\"]", uq_match.group(1))
        if cols:
            unique_constraints.append(UniqueConstraintIR(columns=cols))
    return TableIR(
        name=table_name,
        columns=columns,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        unique_constraints=unique_constraints,
    )


def _parse_sqlalchemy_column(block: str) -> ColumnIR | None:
    name = _first_quoted(block)
    if not name:
        return None
    type_match = re.search(r"sa\.([A-Za-z0-9_]+)\s*\(", block)
    data_type = type_match.group(1) if type_match else "unknown"
    nullable = "nullable=False" not in block and "primary_key=True" not in block
    return ColumnIR(name=name, type=data_type, nullable=nullable)


def _parse_alembic_create_index(block: str) -> tuple[str, IndexIR] | None:
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", block)
    if len(quoted) < 2:
        return None
    name, table = quoted[0], quoted[1]
    cols = re.findall(r"\[([^\]]+)\]", block)
    col_names = re.findall(r"['\"]([^'\"]+)['\"]", cols[0]) if cols else quoted[2:]
    return table, IndexIR(name=name, columns=col_names, unique="unique=True" in block)


def _typescript_sql_files(files: list[ExtractionInputFile]) -> list[ExtractionInputFile]:
    converted = []
    for item in files:
        text = _safe_read(item)
        sql_chunks = re.findall(r"queryRunner\.query\s*\(\s*`([\s\S]*?)`\s*[,)]", text)
        if not sql_chunks:
            continue
        pseudo = item.local_path.with_suffix(item.local_path.suffix + ".extracted.sql")
        pseudo.write_text("\n;\n".join(sql_chunks) + "\n", encoding="utf-8")
        converted.append(ExtractionInputFile(repo_path=item.repo_path + "#queryRunner.sql", local_path=pseudo))
    return converted


def _embedded_sql_files(files: list[ExtractionInputFile]) -> list[ExtractionInputFile]:
    converted = []
    for item in files:
        lower = item.repo_path.lower().replace("\\", "/")
        if not lower.endswith((".py", ".ts", ".js", ".cs", ".go", ".java", ".php", ".rb")):
            continue
        text = _safe_read(item)
        if "CREATE TABLE" not in text.upper():
            continue
        chunks = _extract_create_table_statements(text)
        if not chunks:
            continue
        pseudo = item.local_path.with_suffix(item.local_path.suffix + ".embedded.sql")
        pseudo.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
        converted.append(ExtractionInputFile(repo_path=item.repo_path + "#embedded.sql", local_path=pseudo))
    return converted


def _extract_create_table_statements(text: str) -> list[str]:
    statements = []
    pattern = re.compile(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+|TEMP\s+)?TABLE[\s\S]{0,12000}?;",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        statement = _unescape_embedded_sql(match.group(0))
        if "(" in statement and ")" in statement:
            statements.append(statement)
    return statements


def _unescape_embedded_sql(value: str) -> str:
    cleaned = value.replace("\\n", "\n").replace("\\t", "\t")
    cleaned = cleaned.replace('\\"', '"').replace("\\'", "'")
    return cleaned


def _extract_typeorm_entities(entity_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    tables: dict[str, TableIR] = {}
    used_files: list[str] = []
    for item in sorted(entity_files, key=lambda file: file.repo_path.lower()):
        used_files.append(item.repo_path)
        text = _safe_read(item)
        entity_match = re.search(r"@Entity\s*\(([^)]*)\)\s*export\s+class\s+(\w+)", text)
        if not entity_match:
            entity_match = re.search(r"@Entity\s*\(\s*\)\s*export\s+class\s+(\w+)", text)
            if not entity_match:
                continue
            table_name = entity_match.group(1)
        else:
            table_name = _first_quoted(entity_match.group(1)) or entity_match.group(2)
        columns: list[ColumnIR] = []
        primary_key: list[str] = []
        unique_constraints: list[UniqueConstraintIR] = []
        for match in re.finditer(r"@(PrimaryGeneratedColumn|PrimaryColumn|Column)\s*(?:\(([^)]*)\))?\s*(?:\n\s*@\w+[^\n]*)*\s*\n\s*(?:public\s+)?(\w+)\??\s*:", text):
            decorator, args, prop = match.group(1), match.group(2) or "", match.group(3)
            name = _object_option_string(args, "name") or prop
            typ = _object_option_string(args, "type") or "unknown"
            nullable = "nullable: true" in args or "?" in match.group(0)
            columns.append(ColumnIR(name=name, type=typ, nullable=nullable))
            if decorator in {"PrimaryGeneratedColumn", "PrimaryColumn"}:
                primary_key.append(name)
            if "unique: true" in args:
                unique_constraints.append(UniqueConstraintIR(columns=[name]))
        if columns:
            tables[table_name] = TableIR(
                name=table_name,
                columns=columns,
                primary_key=primary_key,
                unique_constraints=unique_constraints,
            )
    return _schema_result("static_typeorm", tables, used_files, [], [])


def _parse_sequelize_columns(table_name: str, body: str) -> TableIR:
    columns = []
    primary_key = []
    unique_constraints = []
    for match in re.finditer(r"(\w+)\s*:\s*\{", body):
        col_name = match.group(1)
        col_body = _matching_brace_block(body, match.end() - 1)
        column = _sequelize_column_from_body(col_name, col_body)
        columns.append(column)
        if "primaryKey: true" in col_body:
            primary_key.append(col_name)
        if "unique: true" in col_body:
            unique_constraints.append(UniqueConstraintIR(columns=[col_name]))
    return TableIR(name=table_name, columns=columns, primary_key=primary_key, unique_constraints=unique_constraints)


def _sequelize_column_from_body(column_name: str, body: str) -> ColumnIR:
    type_match = re.search(r"type\s*:\s*Sequelize\.([A-Za-z0-9_]+)", body)
    return ColumnIR(
        name=column_name,
        type=type_match.group(1) if type_match else "unknown",
        nullable="allowNull: false" not in body,
    )


def _parse_ef_create_table(table_name: str, block: str) -> TableIR:
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    columns_match = re.search(r"columns:\s*table\s*=>\s*new\s*\{", block)
    if columns_match:
        body = _matching_brace_block(block, block.find("{", columns_match.end() - 1))
        for line in body.splitlines():
            match = re.search(r"(\w+)\s*=\s*table\.Column<([^>]+)>\(([^)]*)\)", line)
            if match:
                columns.append(
                    ColumnIR(
                        name=match.group(1),
                        type=match.group(2),
                        nullable="nullable: true" in match.group(3),
                    )
                )
    pk_match = re.search(r"table\.PrimaryKey\s*\(", block)
    if pk_match:
        pk_block = _call_block(block, pk_match.end() - 1)
        primary_key = _ef_lambda_columns(pk_block)
    for fk_match in re.finditer(r"table\.ForeignKey\s*\(", block):
        fk_block = _call_block(block, fk_match.end() - 1)
        fk = _parse_ef_foreign_key_call(fk_block)
        if fk:
            foreign_keys.append(fk)
    return TableIR(
        name=table_name,
        columns=columns,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
    )


def _parse_ef_model_snapshot_entity(entity_name: str, block: str) -> TableIR | None:
    table_match = re.search(r"\.ToTable\(\s*\"([^\"]+)\"", block)
    table_name = table_match.group(1) if table_match else entity_name.split(".")[-1]
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    indexes: list[IndexIR] = []
    for prop_match in re.finditer(r"b\.Property<([^>]+)>\(\s*\"([^\"]+)\"\s*\)", block):
        prop_type, name = prop_match.group(1), prop_match.group(2)
        line_start = prop_match.start()
        next_prop = re.search(r"\n\s*b\.(?:Property|HasKey|HasIndex|ToTable)\(", block[prop_match.end() :])
        prop_block = block[line_start : prop_match.end() + (next_prop.start() if next_prop else 250)]
        type_match = re.search(r"\.HasColumnType\(\s*\"([^\"]+)\"", prop_block)
        columns.append(
            ColumnIR(
                name=name,
                type=type_match.group(1) if type_match else prop_type,
                nullable=prop_type.endswith("?") or ".IsRequired()" not in prop_block,
            )
        )
    for key_match in re.finditer(r"b\.HasKey\s*\(", block):
        key_block = _call_block(block, key_match.end() - 1)
        primary_key.extend(_ef_quoted_args(key_block))
    for idx_match in re.finditer(r"b\.HasIndex\s*\(", block):
        idx_block = _call_block(block, idx_match.end() - 1)
        index_columns = _ef_quoted_args(idx_block)
        if index_columns:
            indexes.append(IndexIR(columns=index_columns, unique=".IsUnique()" in idx_block))
    if not columns:
        return None
    return TableIR(name=table_name, columns=columns, primary_key=primary_key, indexes=indexes)


def _ef_up_method_body(text: str) -> str:
    match = re.search(r"\bvoid\s+Up\s*\(\s*MigrationBuilder\s+\w+\s*\)\s*\{", text)
    if not match:
        return ""
    open_brace = text.find("{", match.end() - 1)
    return _matching_brace_block(text, open_brace)


def _parse_ef_create_index(block: str) -> tuple[str, IndexIR] | None:
    table_name = _ef_named_string(block, "table")
    if not table_name:
        return None
    name = _ef_named_string(block, "name")
    columns = _ef_named_columns(block, "column", "columns")
    if not columns:
        return None
    return table_name, IndexIR(columns=columns, name=name, unique=_ef_named_bool(block, "unique"))


def _parse_ef_add_foreign_key(block: str) -> tuple[str, ForeignKeyIR] | None:
    table_name = _ef_named_string(block, "table")
    fk = _parse_ef_foreign_key_call(block)
    if not table_name or not fk:
        return None
    return table_name, fk


def _parse_ef_foreign_key_call(block: str) -> ForeignKeyIR | None:
    columns = _ef_named_columns(block, "column", "columns") or _ef_lambda_columns(block)
    ref_table = _ef_named_string(block, "principalTable")
    ref_columns = _ef_named_columns(block, "principalColumn", "principalColumns")
    if not columns or not ref_table:
        return None
    if not ref_columns:
        ref_columns = ["Id"]
    return ForeignKeyIR(columns=columns, ref_table=ref_table, ref_columns=ref_columns)


def _ef_named_string(block: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*\"([^\"]+)\"", block)
    return match.group(1) if match else None


def _ef_named_bool(block: str, name: str) -> bool:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*(true|false)", block, re.IGNORECASE)
    return bool(match and match.group(1).lower() == "true")


def _ef_named_columns(block: str, singular: str, plural: str) -> list[str]:
    singular_match = re.search(rf"\b{re.escape(singular)}\s*:\s*\"([^\"]+)\"", block)
    if singular_match:
        return [singular_match.group(1)]
    plural_match = re.search(rf"\b{re.escape(plural)}\s*:\s*new\s*\[\]\s*\{{([^}}]+)\}}", block)
    if plural_match:
        return re.findall(r"\"([^\"]+)\"", plural_match.group(1))
    return []


def _ef_lambda_columns(block: str) -> list[str]:
    lambda_match = re.search(r"=>\s*x\.(\w+)", block)
    if lambda_match:
        return [lambda_match.group(1)]
    object_match = re.search(r"=>\s*new\s*\{([^}]+)\}", block)
    if object_match:
        return re.findall(r"\bx\.(\w+)", object_match.group(1))
    return []


def _ef_quoted_args(block: str) -> list[str]:
    return re.findall(r"\"([^\"]+)\"", block)


def _parse_csharp_entity(text: str) -> TableIR | None:
    table_match = re.search(r"\[Table\(\s*\"([^\"]+)\"\s*\)\]", text)
    class_match = re.search(r"public\s+class\s+(\w+)", text)
    if not class_match:
        return None
    table_name = table_match.group(1) if table_match else class_match.group(1)
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    pending_key = False
    pending_column_name: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[Key]"):
            pending_key = True
            continue
        col_attr = re.search(r"\[Column\(\s*\"([^\"]+)\"", stripped)
        if col_attr:
            pending_column_name = col_attr.group(1)
            continue
        prop = re.search(r"public\s+([A-Za-z0-9_<>?]+)\s+(\w+)\s*\{\s*get;\s*set;\s*\}", stripped)
        if not prop:
            continue
        typ, name = prop.group(1), prop.group(2)
        col_name = pending_column_name or name
        columns.append(ColumnIR(name=col_name, type=typ.rstrip("?"), nullable=typ.endswith("?")))
        if pending_key or name.lower() in {"id", f"{class_match.group(1).lower()}id"}:
            primary_key.append(col_name)
        pending_key = False
        pending_column_name = None
    return TableIR(name=table_name, columns=columns, primary_key=primary_key)


def _parse_python_sqlalchemy_column(line: str) -> tuple[ColumnIR, ForeignKeyIR | None] | None:
    assign_match = re.match(r"\s*(\w+)\s*=\s*(?:db\.)?Column\s*\((.*)", line)
    if not assign_match:
        return None
    attr_name, args = assign_match.group(1), assign_match.group(2)
    explicit_name = _first_quoted(args)
    if explicit_name and "." not in explicit_name:
        column_name = explicit_name
    else:
        column_name = attr_name
    type_match = re.search(
        r"(?:db\.)?(Integer|BigInteger|SmallInteger|String|Text|DateTime|Date|Boolean|Float|Numeric|JSON|LargeBinary)",
        args,
    )
    data_type = type_match.group(1) if type_match else "unknown"
    nullable = "nullable=False" not in args and "primary_key=True" not in args
    fk = None
    fk_match = re.search(r"(?:db\.)?ForeignKey\s*\(\s*['\"]([^'\"]+)['\"]", args)
    if fk_match:
        ref = fk_match.group(1)
        if "." in ref:
            ref_table, ref_col = ref.rsplit(".", 1)
            fk = ForeignKeyIR(columns=[column_name], ref_table=ref_table, ref_columns=[ref_col])
    return ColumnIR(name=column_name, type=data_type, nullable=nullable), fk
    if not match:
        return None, []
    table_name = _clean_identifier(match.group(1))
    start = statement.find("(", match.end() - 1)
    end = _matching_paren(statement, start)
    if start < 0 or end < 0:
        return None, [f"cannot find column block for {table_name}"]
    body = statement[start + 1 : end]
    columns: list[ColumnIR] = []
    primary_key: list[str] = []
    foreign_keys: list[ForeignKeyIR] = []
    unique_constraints: list[UniqueConstraintIR] = []
    warnings: list[str] = []

    for item in _split_top_level_commas(body):
        part = item.strip()
        if not part:
            continue
        upper = part.upper()
        if upper.startswith(("CONSTRAINT ", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")):
            if "PRIMARY KEY" in upper:
                primary_key = _columns_inside_keyword(part, "PRIMARY KEY") or primary_key
            elif "FOREIGN KEY" in upper:
                fk = _parse_table_foreign_key(part)
                if fk:
                    foreign_keys.append(fk)
            elif "UNIQUE" in upper:
                unique_columns = _columns_inside_keyword(part, "UNIQUE")
                if unique_columns:
                    unique_constraints.append(UniqueConstraintIR(columns=unique_columns))
            elif "CHECK" in upper:
                warnings.append(f"CHECK constraint kept for human review on {table_name}")
            continue

        column = _parse_column_definition(part)
        if not column:
            warnings.append(f"unsupported column definition in {table_name}: {part[:80]}")
            continue
        columns.append(column)
        if "PRIMARY KEY" in upper:
            primary_key.append(column.name)
        if "UNIQUE" in upper:
            unique_constraints.append(UniqueConstraintIR(columns=[column.name]))
        inline_fk = _parse_inline_foreign_key(column.name, part)
        if inline_fk:
            foreign_keys.append(inline_fk)

    return (
        TableIR(
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            unique_constraints=unique_constraints,
            indexes=[],
        ),
        warnings,
    )


def _parse_column_definition(part: str) -> ColumnIR | None:
    part = _strip_column_tail_options(part)
    tokens = part.split()
    if len(tokens) < 2:
        return None
    name = _clean_identifier(tokens[0])
    type_tokens = []
    for token in tokens[1:]:
        if token.upper() in {
            "PRIMARY",
            "NOT",
            "NULL",
            "DEFAULT",
            "UNIQUE",
            "CHECK",
            "REFERENCES",
            "COLLATE",
            "CONSTRAINT",
            "GENERATED",
            "IDENTITY",
            "COMMENT",
            "AUTO_INCREMENT",
            "AUTOINCREMENT",
            "UNSIGNED",
            "CHARACTER",
            "ENCODE",
        }:
            break
        type_tokens.append(token)
    data_type = " ".join(type_tokens) or tokens[1]
    upper = part.upper()
    nullable = "NOT NULL" not in upper and "PRIMARY KEY" not in upper
    return ColumnIR(name=name, type=data_type.strip(), nullable=nullable)


def _schema_result(
    strategy: str,
    tables: dict[str, TableIR],
    used_files: list[str],
    warnings: list[str],
    errors: list[str],
) -> StaticExtractionResult:
    schema_ir = SchemaIR(tables=sorted(tables.values(), key=lambda table: table.name.lower()))
    if schema_ir.tables:
        status = "static_extracted"
    elif used_files:
        status = "needs_human_review"
        warnings = [*warnings, "parser found relevant files but no tables could be extracted"]
    else:
        status = "skipped"
    return StaticExtractionResult(
        schema_ir=schema_ir,
        status=status,
        strategy=strategy,
        used_files=used_files,
        warnings=warnings,
        errors=errors,
    )


def _generic_family_result(family: str, schema_files: list[ExtractionInputFile]) -> StaticExtractionResult:
    return StaticExtractionResult(
        schema_ir=SchemaIR(),
        status="needs_human_review",
        strategy=f"static_{family}_candidate",
        used_files=[item.repo_path for item in schema_files],
        warnings=[f"{family} parser is not implemented yet"],
        unsupported_constructs=[family],
    )


def _table_with(
    table: TableIR,
    columns: list[ColumnIR] | None = None,
    primary_key: list[str] | None = None,
    foreign_keys: list[ForeignKeyIR] | None = None,
    unique_constraints: list[UniqueConstraintIR] | None = None,
    indexes: list[IndexIR] | None = None,
) -> TableIR:
    return TableIR(
        name=table.name,
        columns=columns if columns is not None else table.columns,
        primary_key=primary_key if primary_key is not None else table.primary_key,
        foreign_keys=foreign_keys if foreign_keys is not None else table.foreign_keys,
        unique_constraints=(
            unique_constraints if unique_constraints is not None else table.unique_constraints
        ),
        check_constraints=table.check_constraints,
        indexes=indexes if indexes is not None else table.indexes,
    )


def _merge_table(base: TableIR, patch: TableIR) -> TableIR:
    column_names = {column.name for column in base.columns}
    columns = [*base.columns, *[column for column in patch.columns if column.name not in column_names]]
    return TableIR(
        name=base.name,
        columns=columns,
        primary_key=base.primary_key or patch.primary_key,
        foreign_keys=_dedupe_foreign_keys([*base.foreign_keys, *patch.foreign_keys]),
        unique_constraints=_dedupe_unique_constraints(
            [*base.unique_constraints, *patch.unique_constraints]
        ),
        check_constraints=[*base.check_constraints, *patch.check_constraints],
        indexes=_dedupe_indexes([*base.indexes, *patch.indexes]),
    )


def _remove_column_from_table(table: TableIR, column_name: str) -> TableIR:
    return TableIR(
        name=table.name,
        columns=[column for column in table.columns if column.name != column_name],
        primary_key=[column for column in table.primary_key if column != column_name],
        foreign_keys=[
            fk
            for fk in table.foreign_keys
            if column_name not in fk.columns and column_name not in fk.ref_columns
        ],
        unique_constraints=[
            constraint
            for constraint in table.unique_constraints
            if column_name not in constraint.columns
        ],
        check_constraints=table.check_constraints,
        indexes=[index for index in table.indexes if column_name not in index.columns],
    )


def _dedupe_foreign_keys(items: list[ForeignKeyIR]) -> list[ForeignKeyIR]:
    seen: set[tuple[tuple[str, ...], str, tuple[str, ...]]] = set()
    result: list[ForeignKeyIR] = []
    for item in items:
        key = (tuple(item.columns), item.ref_table, tuple(item.ref_columns))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_unique_constraints(items: list[UniqueConstraintIR]) -> list[UniqueConstraintIR]:
    seen: set[tuple[tuple[str, ...], str | None]] = set()
    result: list[UniqueConstraintIR] = []
    for item in items:
        key = (tuple(item.columns), item.name)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_indexes(items: list[IndexIR]) -> list[IndexIR]:
    positions: dict[tuple[str, ...], int] = {}
    result: list[IndexIR] = []
    for item in items:
        key = tuple(item.columns)
        if key in positions:
            existing_index = positions[key]
            existing = result[existing_index]
            if item.unique and not existing.unique:
                result[existing_index] = IndexIR(
                    columns=existing.columns,
                    name=existing.name or item.name,
                    unique=True,
                )
            continue
        positions[key] = len(result)
        result.append(item)
    return result


def _safe_read(item: ExtractionInputFile) -> str:
    try:
        return item.local_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _call_block(text: str, open_paren_index: int) -> str:
    end = _matching_paren(text, open_paren_index)
    if open_paren_index < 0 or end < 0:
        return ""
    return text[open_paren_index : end + 1]


def _closure_block_after(text: str, start: int) -> str:
    brace = text.find("{", start)
    if brace < 0:
        return ""
    return _matching_brace_block(text, brace)


def _matching_brace_block(text: str, start: int) -> str:
    end = _matching_brace(text, start)
    if start < 0 or end < 0:
        return ""
    return text[start + 1 : end]


def _ruby_do_block(text: str, start: int) -> str:
    end_match = re.search(r"^\s*end\s*$", text[start:], re.MULTILINE)
    if not end_match:
        return ""
    return text[start : start + end_match.start()]


def _matching_square(text: str, start: int) -> int:
    if start < 0:
        return -1
    depth = 0
    quote: str | None = None
    for index in range(start, len(text)):
        char = text[index]
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif quote is None:
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return index
    return -1


def _kw_string(text: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1) if match else None


def _first_quoted(text: str) -> str | None:
    match = re.search(r"['\"]([^'\"]+)['\"]", text)
    return match.group(1) if match else None


def _quoted_list_or_first(text: str) -> list[str]:
    return re.findall(r"['\"]([^'\"]+)['\"]", text)


def _laravel_column_list_arg(text: str) -> list[str]:
    stripped = text.strip()
    if stripped.startswith("["):
        end = _matching_square(stripped, 0)
        if end > 0:
            return _quoted_list_or_first(stripped[: end + 1])
    first = _first_quoted(stripped)
    return [first] if first else []


def _laravel_foreign_id_for(args: str) -> str:
    class_match = re.search(r"([A-Za-z0-9_]+)::class", args)
    if not class_match:
        return "user_id"
    name = class_match.group(1)
    return _camel_to_snake(name) + "_id"


def _laravel_constrained_table(stmt: str, column_name: str) -> str | None:
    constrained = re.search(r"->constrained\s*\(([^)]*)\)", stmt)
    if constrained:
        quoted = _first_quoted(constrained.group(1))
        if quoted:
            return quoted
    if column_name.endswith("_id"):
        return column_name[:-3] + "s"
    return None


def _ruby_option_string(text: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}:\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def _object_option_string(text: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}\s*:\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def _camel_to_snake(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()


def _parse_table_foreign_key(part: str) -> ForeignKeyIR | None:
    columns = _columns_inside_keyword(part, "FOREIGN KEY")
    ref_match = re.search(r"REFERENCES\s+([^\s(]+)\s*\(([^)]+)\)", part, re.IGNORECASE)
    if not columns or not ref_match:
        return None
    return ForeignKeyIR(
        columns=columns,
        ref_table=_clean_identifier(ref_match.group(1)),
        ref_columns=_parse_column_list(ref_match.group(2)),
    )


def _parse_alter_table(statement: str) -> tuple[str, TableIR] | None:
    match = re.search(r"ALTER\s+TABLE\s+(?:ONLY\s+)?([^\s]+)\s+(.+)", statement, re.IGNORECASE | re.S)
    if not match:
        return None
    table_name = _clean_identifier(match.group(1))
    action = match.group(2).strip()
    action_upper = action.upper()
    patch = TableIR(name=table_name)

    if action_upper.startswith("ADD CONSTRAINT") or action_upper.startswith("ADD "):
        body = re.sub(r"^ADD\s+(?:CONSTRAINT\s+[^\s]+\s+)?", "", action, flags=re.IGNORECASE).strip()
        body_upper = body.upper()
        if body_upper.startswith("FOREIGN KEY"):
            fk = _parse_table_foreign_key(body)
            if fk:
                patch = _table_with(patch, foreign_keys=[fk])
                return table_name, patch
        if body_upper.startswith("UNIQUE"):
            cols = _columns_inside_keyword(body, "UNIQUE") or _columns_inside_first_parens(body)
            if cols:
                patch = _table_with(patch, unique_constraints=[UniqueConstraintIR(columns=cols)])
                return table_name, patch
        if body_upper.startswith("PRIMARY KEY"):
            cols = _columns_inside_keyword(body, "PRIMARY KEY")
            if cols:
                patch = _table_with(patch, primary_key=cols)
                return table_name, patch
        if body_upper.startswith("CHECK"):
            return table_name, patch
        column_body = re.sub(r"^COLUMN\s+", "", body, flags=re.IGNORECASE).strip()
        column = _parse_column_definition(column_body)
        if column:
            patch = _table_with(patch, columns=[column])
            if "PRIMARY KEY" in body_upper:
                patch = _table_with(patch, primary_key=[column.name])
            if "UNIQUE" in body_upper:
                patch = _table_with(patch, unique_constraints=[UniqueConstraintIR(columns=[column.name])])
            inline_fk = _parse_inline_foreign_key(column.name, body)
            if inline_fk:
                patch = _table_with(patch, foreign_keys=[inline_fk])
            return table_name, patch

    return None


def _merge_alter_table(base: TableIR, patch: TableIR) -> TableIR:
    existing_columns = {column.name.lower() for column in base.columns}
    added_columns = [
        column for column in patch.columns if column.name.lower() not in existing_columns
    ]
    return _table_with(
        base,
        columns=[*base.columns, *added_columns],
        primary_key=patch.primary_key or base.primary_key,
        foreign_keys=[*base.foreign_keys, *patch.foreign_keys],
        unique_constraints=[*base.unique_constraints, *patch.unique_constraints],
    )


def _parse_inline_foreign_key(column_name: str, part: str) -> ForeignKeyIR | None:
    ref_match = re.search(r"REFERENCES\s+([^\s(]+)\s*(?:\(([^)]+)\))?", part, re.IGNORECASE)
    if not ref_match:
        return None
    ref_columns = _parse_column_list(ref_match.group(2) or "id")
    return ForeignKeyIR(
        columns=[column_name],
        ref_table=_clean_identifier(ref_match.group(1)),
        ref_columns=ref_columns,
    )


def _parse_create_index(statement: str) -> tuple[str, IndexIR] | None:
    match = re.search(
        r"CREATE\s+(UNIQUE\s+)?(?:CLUSTERED\s+|NONCLUSTERED\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s]+)\s+ON\s+([^\s(]+)(?:\s+USING\s+\w+)?\s*\(([^)]+)\)",
        statement,
        re.IGNORECASE,
    )
    if not match:
        return None
    return (
        _clean_identifier(match.group(3)),
        IndexIR(
            name=_clean_identifier(match.group(2)),
            columns=_parse_column_list(match.group(4)),
            unique=bool(match.group(1)),
        ),
    )


def _iter_prisma_blocks(text: str, block_type: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"\b{re.escape(block_type)}\s+(\w+)\s*\{{", re.IGNORECASE)
    blocks = []
    for match in pattern.finditer(text):
        start = match.end() - 1
        end = _matching_brace(text, start)
        if end > start:
            blocks.append((match.group(1), text[start + 1 : end]))
    return blocks


def _prisma_table_name(model_name: str, body: str) -> str:
    match = re.search(r"@@map\(\s*[\"']([^\"']+)[\"']\s*\)", body)
    return match.group(1) if match else model_name


def _prisma_field_db_name(field_name: str, attrs: str) -> str:
    match = re.search(r"@map\(\s*[\"']([^\"']+)[\"']\s*\)", attrs)
    return match.group(1) if match else field_name


def _parse_prisma_relation(attrs: str) -> dict[str, list[str]] | None:
    if "@relation" not in attrs:
        return None
    fields_match = re.search(r"fields\s*:\s*\[([^\]]+)\]", attrs)
    refs_match = re.search(r"references\s*:\s*\[([^\]]+)\]", attrs)
    if not fields_match or not refs_match:
        return None
    return {
        "fields": _parse_column_list(fields_match.group(1)),
        "references": _parse_column_list(refs_match.group(1)),
    }


def _prisma_attribute_columns(line: str) -> list[str]:
    match = re.search(r"\[([^\]]+)\]", line)
    if not match:
        return []
    return _parse_column_list(match.group(1))


def _is_prisma_relation_type(field_type: str) -> bool:
    cleaned = _clean_prisma_type(field_type)
    return cleaned[:1].isupper()


def _clean_prisma_type(field_type: str) -> str:
    return field_type.rstrip("?[]")


def _split_sql_statements(text: str) -> list[str]:
    statements = []
    current = []
    quote: str | None = None
    depth = 0
    i = 0
    while i < len(text):
        char = text[i]
        next_two = text[i : i + 2]
        if quote is None and next_two == "--":
            end = text.find("\n", i)
            if end == -1:
                break
            i = end + 1
            continue
        if quote is None and next_two == "/*":
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        current.append(char)
        if char in {"'", '"', "`"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif quote is None:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif char == ";" and depth == 0:
                statements.append("".join(current[:-1]).strip())
                current = []
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _ddl_dialect(
    dbms: str,
    sql_files: list[ExtractionInputFile],
    text_parts: list[str],
) -> DDLDialect:
    value = dbms.lower()
    if "postgres" in value:
        return DIALECT_POSTGRESQL
    if "mariadb" in value:
        return DDLDialect("mariadb")
    if "mysql" in value:
        return DIALECT_MYSQL
    if "sqlite" in value:
        return DIALECT_SQLITE
    if "sql server" in value or "sqlserver" in value or "mssql" in value:
        return DIALECT_SQLSERVER
    if "duckdb" in value:
        return DIALECT_DUCKDB

    combined = "\n".join(text_parts).lower()
    paths = " ".join(item.repo_path.lower() for item in sql_files)
    if "go\n" in combined or "\ngo\n" in combined or "sqlserver" in paths or "mssql" in paths:
        return DIALECT_SQLSERVER
    if "engine=innodb" in combined or "auto_increment" in combined:
        return DIALECT_MYSQL
    if "create extension" in combined or "::" in combined or "serial" in combined:
        return DIALECT_POSTGRESQL
    if "without rowid" in combined or "sqlite" in paths:
        return DIALECT_SQLITE
    if "duckdb" in paths:
        return DIALECT_DUCKDB
    return DIALECT_GENERIC


def _preprocess_ddl_text(text: str, dialect: DDLDialect) -> str:
    normalized = text.replace("\r\n", "\n")
    if dialect.name == "sqlserver":
        normalized = re.sub(r"(?im)^\s*GO\s*$", ";\n", normalized)
    if dialect.name in {"mysql", "mariadb"}:
        normalized = re.sub(r"(?im)^\s*DELIMITER\s+\S+\s*$", "", normalized)
        normalized = re.sub(r"\)\s*ENGINE\s*=\s*\w+[^;]*;", ");", normalized)
        normalized = re.sub(r"\)\s*DEFAULT\s+CHARSET\s*=\s*\w+[^;]*;", ");", normalized)
    if dialect.name == "postgresql":
        normalized = re.sub(r"(?i)\bCREATE\s+UNLOGGED\s+TABLE\b", "CREATE TABLE", normalized)
    return normalized


def _strip_column_tail_options(part: str) -> str:
    cleaned = part.strip()
    cleaned = re.sub(r"\s+COMMENT\s+['\"][\s\S]*?['\"]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+COLLATE\s+[\w.\"`\[\]-]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+CHARACTER\s+SET\s+[\w-]+", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _split_top_level_commas(text: str) -> list[str]:
    parts = []
    current = []
    quote: str | None = None
    depth = 0
    for char in text:
        current.append(char)
        if char in {"'", '"', "`"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif quote is None:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                parts.append("".join(current[:-1]))
                current = []
    if current:
        parts.append("".join(current))
    return parts


def _columns_inside_keyword(part: str, keyword: str) -> list[str]:
    index = part.upper().find(keyword)
    if index < 0:
        return []
    start = part.find("(", index)
    end = _matching_paren(part, start)
    if start < 0 or end < 0:
        return []
    return _parse_column_list(part[start + 1 : end])


def _columns_inside_first_parens(part: str) -> list[str]:
    start = part.find("(")
    end = _matching_paren(part, start)
    if start < 0 or end < 0:
        return []
    return _parse_column_list(part[start + 1 : end])


def _parse_column_list(text: str) -> list[str]:
    return [_clean_identifier(part.strip().split()[0]) for part in text.split(",") if part.strip()]


def _matching_paren(text: str, start: int) -> int:
    if start < 0:
        return -1
    depth = 0
    quote: str | None = None
    for index in range(start, len(text)):
        char = text[index]
        if char in {"'", '"', "`"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif quote is None:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return index
    return -1


def _matching_brace(text: str, start: int) -> int:
    if start < 0:
        return -1
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _clean_identifier(value: str) -> str:
    cleaned = value.strip().rstrip(",")
    cleaned = re.sub(r"\s+", "", cleaned)
    bracket_parts = re.findall(r"\[([^\]]+)\]", cleaned)
    if bracket_parts:
        return bracket_parts[-1]
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned.strip('"`[]')


def _statement_head(statement: str) -> str:
    return " ".join(statement.strip().split()[:6])


def _is_sql_file(repo_path: str) -> bool:
    return repo_path.lower().replace("\\", "/").endswith(".sql")


def _detect_static_family(
    candidate: dict[str, Any],
    schema_files: list[ExtractionInputFile],
) -> str | None:
    artifact = str(candidate.get("schema_artifact_final") or "").lower()
    repo_paths = [item.repo_path.lower().replace("\\", "/") for item in schema_files]
    if any(path.endswith(".cs") and "/migrations/" in path for path in repo_paths) or "ef core" in artifact:
        return "ef_core"
    if any(path.endswith(".cs") and ("/models/" in path or "entity.cs" in path) for path in repo_paths):
        return "csharp_entities"
    if any("db/schema.rb" in path or "db/migrate/" in path for path in repo_paths) or "rails" in artifact:
        return "rails"
    if any("database/migrations/" in path for path in repo_paths) or "laravel" in artifact:
        return "laravel"
    if any("alembic/versions/" in path for path in repo_paths) or "alembic" in artifact:
        return "alembic"
    if any("migrations/" in path and path.endswith(".py") for path in repo_paths) or "django" in artifact:
        return "django"
    if any(path.endswith(".entity.ts") or "typeorm" in path for path in repo_paths) or "typeorm" in artifact:
        return "typeorm"
    if any(path.endswith(".js") and "migration" in path for path in repo_paths) or "sequelize" in artifact:
        return "sequelize"
    if any(path.endswith("models.py") for path in repo_paths):
        return "python_models"
    if any(path.endswith(".go") and "migration" in path for path in repo_paths):
        return "go_migrations"
    if any(path.endswith(".php") and "migration" in path for path in repo_paths):
        return "php_migrations"
    return None
