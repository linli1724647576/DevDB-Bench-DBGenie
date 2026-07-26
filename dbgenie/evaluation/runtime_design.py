"""Evaluate generated DDL implementation consistency against runtime schema.

This implements the first part of benchmark/evaluation_7.14.md. The runtime
layer executes generated DDL against the target DBMS, introspects the resulting
schema, and then compares normalized design artifacts S/P with normalized
runtime Srt/Prt using exact set matching.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_DBMS = {"SQLite", "DuckDB", "PostgreSQL", "MySQL", "MariaDB", "SQL Server"}
DOCKER_DBMS = {"PostgreSQL", "MySQL", "MariaDB", "SQL Server"}
PASSWORD = "dbgenie_pass"
SQLSERVER_PASSWORD = "DBGenie_Strong_Pass_2026!"
PG_NAME = "dbgenie_eval_runtime_pg"
MY_NAME = "dbgenie_eval_runtime_mysql"
MA_NAME = "dbgenie_eval_runtime_mariadb"
SS_NAME = "dbgenie_eval_runtime_sqlserver"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def dig(payload: Any, *keys: str, default: Any = None) -> Any:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return string_list(
            value.get("columns")
            or value.get("column")
            or value.get("fields")
            or value.get("field")
        )
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("column") or item.get("field")
                if name:
                    out.append(str(name))
            else:
                out.append(str(item))
        return out
    return [str(value)]


def repo_slug_from_path(path: Path) -> str:
    return path.stem


def db_name(task_id: str) -> str:
    return ("t2d_" + re.sub(r"[^a-zA-Z0-9_]", "_", task_id).lower())[:48]


def run(
    cmd: list[str],
    input_text: str | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=timeout,
    )


def docker_rm(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_postgres() -> None:
    docker_rm(PG_NAME)
    cp = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            PG_NAME,
            "-e",
            f"POSTGRES_PASSWORD={PASSWORD}",
            "postgres:16-alpine",
        ],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout).strip())
    for _ in range(60):
        ok = run(["docker", "exec", PG_NAME, "pg_isready", "-U", "postgres"], timeout=10)
        if ok.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("PostgreSQL did not become ready")


def start_mysql_like(name: str, image: str, env_name: str, admin_bin: str = "mysqladmin") -> None:
    docker_rm(name)
    cp = run(
        ["docker", "run", "-d", "--name", name, "-e", f"{env_name}={PASSWORD}", image],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout).strip())
    for _ in range(90):
        ok = run(
            [
                "docker",
                "exec",
                name,
                admin_bin,
                "ping",
                "-h127.0.0.1",
                "--protocol=tcp",
                "-uroot",
                f"-p{PASSWORD}",
            ],
            timeout=10,
        )
        if ok.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"{image} did not become ready")


def start_sqlserver() -> None:
    docker_rm(SS_NAME)
    cp = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            SS_NAME,
            "-e",
            "ACCEPT_EULA=Y",
            "-e",
            f"MSSQL_SA_PASSWORD={SQLSERVER_PASSWORD}",
            "mcr.microsoft.com/mssql/server:2022-latest",
        ],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout).strip())
    try:
        for _ in range(120):
            try:
                ok = _sqlserver_query("master", "SELECT 1", timeout=30)
            except subprocess.TimeoutExpired:
                ok = None
            if ok is not None and ok.returncode == 0:
                return
            time.sleep(1)
    except Exception:
        docker_rm(SS_NAME)
        raise
    docker_rm(SS_NAME)
    raise RuntimeError("SQL Server did not become ready")


def prepare_runtime_services(dbms_set: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    availability = {dbms: {"available": True, "reason": ""} for dbms in SUPPORTED_DBMS}
    started: list[str] = []
    starters = [
        ("PostgreSQL", start_postgres),
        ("MySQL", lambda: start_mysql_like(MY_NAME, "mysql:8.4", "MYSQL_ROOT_PASSWORD")),
        ("MariaDB", lambda: start_mysql_like(MA_NAME, "mariadb:11.4", "MARIADB_ROOT_PASSWORD", admin_bin="mariadb-admin")),
        ("SQL Server", start_sqlserver),
    ]
    for dbms, starter in starters:
        if dbms not in dbms_set:
            continue
        try:
            starter()
            started.append(dbms)
        except Exception as exc:
            availability[dbms] = {
                "available": False,
                "reason": f"{exc.__class__.__name__}: {exc}",
            }
    return availability, started


def cleanup_runtime_services(started: list[str]) -> None:
    for dbms in reversed(started):
        if dbms == "PostgreSQL":
            docker_rm(PG_NAME)
        elif dbms == "MySQL":
            docker_rm(MY_NAME)
        elif dbms == "MariaDB":
            docker_rm(MA_NAME)
        elif dbms == "SQL Server":
            docker_rm(SS_NAME)


def quote_sqlite_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def execute_and_introspect_sqlite(ddl: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        con.executescript(ddl)
        runtime_ir = introspect_sqlite(con)
        table_count = len(runtime_ir.get("tables") or [])
        if table_count == 0:
            return None, {
                "status": "failed",
                "executed": True,
                "introspected": True,
                "error_type": "empty_runtime_schema",
                "error": "DDL executed but produced no user tables.",
            }
        return runtime_ir, {
            "status": "passed",
            "executed": True,
            "introspected": True,
            "table_count_runtime": table_count,
            "error": None,
        }
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    finally:
        con.close()


def introspect_sqlite(con: sqlite3.Connection) -> dict[str, Any]:
    table_rows = con.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    tables = []
    for row in table_rows:
        table_name = str(row["name"])
        create_sql = str(row["sql"] or "")
        table = {
            "name": table_name,
            "columns": sqlite_columns(con, table_name),
            "primary_key": [],
            "foreign_keys": sqlite_foreign_keys(con, table_name),
            "unique_constraints": [],
            "check_constraints": [
                {"expression": expression}
                for expression in extract_check_expressions(create_sql)
            ],
            "indexes": [],
        }
        pk_columns = [
            column["name"]
            for column in sorted(table["columns"], key=lambda item: item.get("_pk_order", 0))
            if item_pk_order(column) > 0
        ]
        for column in table["columns"]:
            column.pop("_pk_order", None)
        table["primary_key"] = pk_columns

        unique_constraints, indexes = sqlite_indexes(con, table_name)
        table["unique_constraints"] = unique_constraints
        table["indexes"] = indexes
        tables.append(table)
    return {"tables": tables}


def item_pk_order(column: dict[str, Any]) -> int:
    value = column.get("_pk_order")
    return int(value) if isinstance(value, int) else 0


def sqlite_columns(con: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    rows = con.execute(f"PRAGMA table_info({quote_sqlite_identifier(table_name)})").fetchall()
    columns = []
    for row in rows:
        pk_order = int(row["pk"] or 0)
        raw_type = str(row["type"] or "")
        column = {
            "name": str(row["name"]),
            "type": raw_type,
            "nullable": not bool(row["notnull"]) and pk_order == 0,
            "identity": bool(pk_order == 1 and canonical_type(raw_type, "SQLite") == "integer"),
            "_pk_order": pk_order,
        }
        if row["dflt_value"] is not None:
            column["default"] = str(row["dflt_value"])
        columns.append(column)
    return columns


def sqlite_foreign_keys(con: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    rows = con.execute(f"PRAGMA foreign_key_list({quote_sqlite_identifier(table_name)})").fetchall()
    grouped: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        grouped.setdefault(int(row["id"]), []).append(row)
    foreign_keys = []
    for _fk_id, fk_rows in sorted(grouped.items()):
        ordered = sorted(fk_rows, key=lambda item: int(item["seq"]))
        foreign_keys.append(
            {
                "columns": [str(item["from"]) for item in ordered],
                "ref_table": str(ordered[0]["table"]),
                "ref_columns": [str(item["to"] or "") for item in ordered if item["to"]],
            }
        )
    return foreign_keys


def sqlite_indexes(
    con: sqlite3.Connection,
    table_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = con.execute(f"PRAGMA index_list({quote_sqlite_identifier(table_name)})").fetchall()
    unique_constraints = []
    indexes = []
    seen_uniques: set[tuple[str, ...]] = set()
    for row in rows:
        name = str(row["name"])
        unique = bool(row["unique"])
        origin = str(row["origin"])
        columns = sqlite_index_columns(con, name)
        if not columns:
            continue
        if unique and origin != "pk":
            key = tuple(columns)
            if key not in seen_uniques:
                seen_uniques.add(key)
                unique_constraints.append({"name": name, "columns": columns})
        if origin == "pk":
            continue
        indexes.append(
            {
                "name": name,
                "columns": columns,
                "unique": unique,
                "origin": "unique_constraint" if origin == "u" else "explicit_index",
            }
        )
    unique_constraints.sort(key=lambda item: (tuple(item["columns"]), item.get("name") or ""))
    indexes.sort(key=lambda item: (tuple(item["columns"]), bool(item["unique"]), item.get("name") or ""))
    return unique_constraints, indexes


def sqlite_index_columns(con: sqlite3.Connection, index_name: str) -> list[str]:
    rows = con.execute(f"PRAGMA index_info({quote_sqlite_identifier(index_name)})").fetchall()
    ordered = sorted(rows, key=lambda item: int(item["seqno"]))
    columns = []
    for row in ordered:
        name = row["name"]
        if name is not None:
            columns.append(str(name))
    return columns


def execution_passed(runtime_ir: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    table_count = len(runtime_ir.get("tables") or [])
    if table_count == 0:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": True,
            "error_type": "empty_runtime_schema",
            "error": "DDL executed but produced no user tables.",
        }
    return runtime_ir, {
        "status": "passed",
        "executed": True,
        "introspected": True,
        "table_count_runtime": table_count,
        "error": None,
    }


def execute_and_introspect_runtime(
    target_dbms: str,
    task_id: str,
    ddl: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if target_dbms == "SQLite":
        return execute_and_introspect_sqlite(ddl)
    if target_dbms == "DuckDB":
        return execute_and_introspect_duckdb(ddl)
    if target_dbms == "PostgreSQL":
        return execute_and_introspect_postgres(task_id, ddl)
    if target_dbms == "MySQL":
        return execute_and_introspect_mysql_like(MY_NAME, "mysql", task_id, ddl)
    if target_dbms == "MariaDB":
        return execute_and_introspect_mysql_like(MA_NAME, "mariadb", task_id, ddl)
    if target_dbms == "SQL Server":
        return execute_and_introspect_sqlserver(task_id, ddl)
    return None, {
        "status": "skipped",
        "executed": False,
        "introspected": False,
        "reason": f"unsupported_dbms:{target_dbms}",
    }


def query_dicts_duckdb(con: Any, sql: str) -> list[dict[str, Any]]:
    cursor = con.execute(sql)
    names = [item[0] for item in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def execute_and_introspect_duckdb(ddl: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not importlib.util.find_spec("duckdb"):
        return None, {
            "status": "skipped",
            "executed": False,
            "introspected": False,
            "reason": "duckdb Python package is not installed",
        }
    import duckdb  # type: ignore[import-not-found]

    con = duckdb.connect(database=":memory:")
    try:
        con.execute(ddl)
        return execution_passed(introspect_duckdb(con))
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    finally:
        con.close()


def introspect_duckdb(con: Any) -> dict[str, Any]:
    table_rows = query_dicts_duckdb(
        con,
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_name
        """,
    )
    tables = {
        str(row["table_name"]): {
            "name": str(row["table_name"]),
            "columns": [],
            "primary_key": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": [],
        }
        for row in table_rows
    }
    for row in query_dicts_duckdb(
        con,
        """
        SELECT table_name, column_name, data_type, is_nullable, column_default, ordinal_position
        FROM information_schema.columns
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_name, ordinal_position
        """,
    ):
        table = tables.get(str(row["table_name"]))
        if not table:
            continue
        column = {
            "name": str(row["column_name"]),
            "type": str(row.get("data_type") or ""),
            "nullable": str(row.get("is_nullable") or "").upper() == "YES",
            "identity": False,
        }
        if row.get("column_default") is not None:
            column["default"] = str(row["column_default"])
        table["columns"].append(column)
    duckdb_constraints(con, tables)
    duckdb_indexes(con, tables)
    return {"tables": list(tables.values())}


def duckdb_constraints(con: Any, tables: dict[str, dict[str, Any]]) -> None:
    try:
        rows = query_dicts_duckdb(
            con,
            """
            SELECT table_name, constraint_name, constraint_type, constraint_text,
                   constraint_column_names
            FROM duckdb_constraints()
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_name, constraint_index
            """,
        )
    except Exception:
        rows = []
    for row in rows:
        table = tables.get(str(row.get("table_name") or ""))
        if not table:
            continue
        constraint_type = str(row.get("constraint_type") or "").casefold()
        columns = string_list(row.get("constraint_column_names"))
        text = str(row.get("constraint_text") or "")
        if "primary" in constraint_type:
            table["primary_key"] = columns
        elif "unique" in constraint_type:
            table["unique_constraints"].append({"columns": columns})
        elif "foreign" in constraint_type:
            ref_table, ref_columns = parse_reference_from_constraint(text)
            table["foreign_keys"].append(
                {"columns": columns, "ref_table": ref_table, "ref_columns": ref_columns}
            )
        elif "check" in constraint_type:
            expression = normalize_expression(text)
            if expression:
                table["check_constraints"].append({"expression": expression})


def duckdb_indexes(con: Any, tables: dict[str, dict[str, Any]]) -> None:
    try:
        rows = query_dicts_duckdb(
            con,
            """
            SELECT table_name, index_name, is_unique, expressions, sql
            FROM duckdb_indexes()
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_name, index_name
            """,
        )
    except Exception:
        rows = []
    for row in rows:
        table = tables.get(str(row.get("table_name") or ""))
        if not table:
            continue
        columns = string_list(row.get("expressions"))
        if not columns:
            columns = parse_index_columns_from_sql(str(row.get("sql") or ""))
        if columns:
            table["indexes"].append(
                {
                    "name": str(row.get("index_name") or ""),
                    "columns": columns,
                    "unique": bool(row.get("is_unique")),
                    "origin": "explicit_index",
                }
            )


def parse_reference_from_constraint(text: str) -> tuple[str, list[str]]:
    match = re.search(
        r"references\s+([`\"\[\]\w.]+)\s*\(([^)]+)\)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return "", []
    return match.group(1), split_sql_identifier_list(match.group(2))


def parse_index_columns_from_sql(sql: str) -> list[str]:
    match = re.search(r"\bon\b\s+[`\"\[\]\w.]+\s*\(([^)]+)\)", sql, flags=re.IGNORECASE)
    if not match:
        return []
    return split_sql_identifier_list(match.group(1))


def split_sql_identifier_list(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote: str | None = None
    for ch in text:
        if in_quote:
            current.append(ch)
            if ch == in_quote:
                in_quote = None
            continue
        if ch in ("'", '"', "`"):
            in_quote = ch
            current.append(ch)
        elif ch == "[":
            in_quote = "]"
            current.append(ch)
        elif ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
        else:
            current.append(ch)
    item = "".join(current).strip()
    if item:
        items.append(item)
    return items


def pg_query_json(database: str, sql: str, timeout: int = 60) -> list[dict[str, Any]]:
    cp = run(
        ["docker", "exec", PG_NAME, "psql", "-U", "postgres", "-d", database, "-tA", "-c", sql],
        timeout=timeout,
    )
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout)[-4000:])
    text = (cp.stdout or "").strip()
    return json.loads(text or "[]")


def pg_json_array(select_sql: str) -> str:
    return f"SELECT COALESCE(json_agg(row_to_json(q)), '[]'::json) FROM ({select_sql}) q"


def execute_and_introspect_postgres(
    task_id: str,
    ddl: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    database = db_name(task_id)
    run(
        [
            "docker",
            "exec",
            PG_NAME,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-c",
            f"DROP DATABASE IF EXISTS {database};",
        ],
        timeout=30,
    )
    create = run(
        [
            "docker",
            "exec",
            PG_NAME,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-c",
            f"CREATE DATABASE {database};",
        ],
        timeout=30,
    )
    if create.returncode != 0:
        return None, {
            "status": "failed",
            "executed": False,
            "introspected": False,
            "error_type": "create_database_failed",
            "error": (create.stderr or create.stdout)[-4000:],
        }
    cp = run(
        ["docker", "exec", "-i", PG_NAME, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", database],
        input_text=ddl,
        timeout=240,
    )
    if cp.returncode != 0:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": "ddl_execution_failed",
            "error": (cp.stderr or cp.stdout)[-4000:],
        }
    try:
        return execution_passed(introspect_postgres(database))
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


def introspect_postgres(database: str) -> dict[str, Any]:
    table_rows = pg_query_json(
        database,
        pg_json_array(
            """
            SELECT n.nspname AS table_schema, c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
            ORDER BY n.nspname, c.relname
            """
        ),
    )
    tables = {
        str(row["table_name"]): {
            "name": str(row["table_name"]),
            "columns": [],
            "primary_key": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": [],
        }
        for row in table_rows
    }
    for row in pg_query_json(
        database,
        pg_json_array(
            """
            SELECT cls.relname AS table_name,
                   att.attname AS column_name,
                   format_type(att.atttypid, att.atttypmod) AS data_type,
                   att.attnotnull AS not_null,
                   att.attidentity <> '' AS is_identity,
                   pg_get_expr(def.adbin, def.adrelid) AS column_default,
                   att.attnum AS ordinal_position
            FROM pg_attribute att
            JOIN pg_class cls ON cls.oid = att.attrelid
            JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
            LEFT JOIN pg_attrdef def ON def.adrelid = att.attrelid AND def.adnum = att.attnum
            WHERE cls.relkind IN ('r', 'p')
              AND att.attnum > 0
              AND NOT att.attisdropped
              AND nsp.nspname NOT IN ('pg_catalog', 'information_schema')
              AND nsp.nspname NOT LIKE 'pg_toast%'
            ORDER BY nsp.nspname, cls.relname, att.attnum
            """
        ),
    ):
        table = tables.get(str(row["table_name"]))
        if not table:
            continue
        column = {
            "name": str(row["column_name"]),
            "type": str(row.get("data_type") or ""),
            "nullable": not bool(row.get("not_null")),
            "identity": bool(row.get("is_identity")),
        }
        if row.get("column_default") is not None:
            column["default"] = str(row["column_default"])
        table["columns"].append(column)
    for row in pg_query_json(
        database,
        pg_json_array(
            """
            SELECT rel.relname AS table_name,
                   con.conname AS constraint_name,
                   con.contype,
                   COALESCE((
                     SELECT json_agg(att.attname ORDER BY key.ord)
                     FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, ord)
                     JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = key.attnum
                   ), '[]'::json) AS columns,
                   ref.relname AS ref_table,
                   COALESCE((
                     SELECT json_agg(att.attname ORDER BY key.ord)
                     FROM unnest(con.confkey) WITH ORDINALITY AS key(attnum, ord)
                     JOIN pg_attribute att ON att.attrelid = con.confrelid AND att.attnum = key.attnum
                   ), '[]'::json) AS ref_columns,
                   CASE WHEN con.contype = 'c' THEN pg_get_expr(con.conbin, con.conrelid) END AS expression
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            LEFT JOIN pg_class ref ON ref.oid = con.confrelid
            WHERE con.contype IN ('p', 'u', 'f', 'c')
              AND nsp.nspname NOT IN ('pg_catalog', 'information_schema')
              AND nsp.nspname NOT LIKE 'pg_toast%'
            ORDER BY rel.relname, con.conname
            """
        ),
    ):
        table = tables.get(str(row["table_name"]))
        if not table:
            continue
        contype = str(row.get("contype") or "")
        columns = string_list(row.get("columns"))
        if contype == "p":
            table["primary_key"] = columns
        elif contype == "u":
            table["unique_constraints"].append({"name": row.get("constraint_name"), "columns": columns})
        elif contype == "f":
            table["foreign_keys"].append(
                {
                    "columns": columns,
                    "ref_table": str(row.get("ref_table") or ""),
                    "ref_columns": string_list(row.get("ref_columns")),
                }
            )
        elif contype == "c":
            expression = normalize_expression(row.get("expression"))
            if expression:
                table["check_constraints"].append({"expression": expression})
    for row in pg_query_json(
        database,
        pg_json_array(
            """
            SELECT tab.relname AS table_name,
                   idx.relname AS index_name,
                   ind.indisunique AS is_unique,
                   ind.indisprimary AS is_primary,
                   EXISTS (SELECT 1 FROM pg_constraint con WHERE con.conindid = ind.indexrelid) AS is_constraint,
                   COALESCE((
                     SELECT json_agg(att.attname ORDER BY key.ord)
                     FROM unnest(ind.indkey) WITH ORDINALITY AS key(attnum, ord)
                     JOIN pg_attribute att ON att.attrelid = ind.indrelid AND att.attnum = key.attnum
                     WHERE key.ord <= ind.indnkeyatts AND key.attnum > 0
                   ), '[]'::json) AS columns
            FROM pg_index ind
            JOIN pg_class idx ON idx.oid = ind.indexrelid
            JOIN pg_class tab ON tab.oid = ind.indrelid
            JOIN pg_namespace nsp ON nsp.oid = tab.relnamespace
            WHERE ind.indisvalid
              AND nsp.nspname NOT IN ('pg_catalog', 'information_schema')
              AND nsp.nspname NOT LIKE 'pg_toast%'
            ORDER BY tab.relname, idx.relname
            """
        ),
    ):
        table = tables.get(str(row["table_name"]))
        columns = string_list(row.get("columns"))
        if not table or not columns or bool(row.get("is_primary")):
            continue
        origin = "unique_constraint" if bool(row.get("is_constraint")) else "explicit_index"
        table["indexes"].append(
            {
                "name": str(row.get("index_name") or ""),
                "columns": columns,
                "unique": bool(row.get("is_unique")),
                "origin": origin,
            }
        )
    return {"tables": list(tables.values())}


def mysql_connection_args(client_bin: str) -> list[str]:
    return [client_bin, "-h127.0.0.1", "--protocol=tcp", "-uroot", f"-p{PASSWORD}"]


def mysql_exec(
    container: str,
    client_bin: str,
    sql: str,
    *,
    database: str | None = None,
    input_text: str | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "exec", "-i", container, *mysql_connection_args(client_bin)]
    if database:
        cmd.append(database)
    if sql:
        cmd.extend(["-e", sql])
    return run(cmd, input_text=input_text, timeout=timeout)


def mysql_query_json(
    container: str,
    client_bin: str,
    database: str,
    sql: str,
    timeout: int = 60,
) -> list[dict[str, Any]]:
    cp = run(
        [
            "docker",
            "exec",
            "-i",
            container,
            *mysql_connection_args(client_bin),
            "-N",
            "-B",
            database,
            "-e",
            sql,
        ],
        timeout=timeout,
    )
    if cp.returncode != 0:
        raise RuntimeError((cp.stderr or cp.stdout)[-4000:])
    text = (cp.stdout or "").strip()
    if not text or text.upper() == "NULL":
        return []
    return json.loads(text.splitlines()[-1])


def mysql_json_array(object_args: str, from_sql: str) -> str:
    source = from_sql.strip()
    if source.casefold().startswith("select "):
        return f"SELECT COALESCE(JSON_ARRAYAGG(JSON_OBJECT({object_args})), JSON_ARRAY()) FROM ({source}) q"
    return f"SELECT COALESCE(JSON_ARRAYAGG(JSON_OBJECT({object_args})), JSON_ARRAY()) {source}"


def execute_and_introspect_mysql_like(
    container: str,
    client_bin: str,
    task_id: str,
    ddl: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    database = db_name(task_id)
    init = f"DROP DATABASE IF EXISTS `{database}`; CREATE DATABASE `{database}`;"
    cp = mysql_exec(container, client_bin, init, timeout=60)
    if cp.returncode != 0:
        return None, {
            "status": "failed",
            "executed": False,
            "introspected": False,
            "error_type": "create_database_failed",
            "error": (cp.stderr or cp.stdout)[-4000:],
        }
    cp = mysql_exec(container, client_bin, "", database=database, input_text=ddl, timeout=240)
    if cp.returncode != 0:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": "ddl_execution_failed",
            "error": (cp.stderr or cp.stdout)[-4000:],
        }
    try:
        return execution_passed(introspect_mysql_like(container, client_bin, database))
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


def introspect_mysql_like(container: str, client_bin: str, database: str) -> dict[str, Any]:
    table_rows = mysql_query_json(
        container,
        client_bin,
        database,
        mysql_json_array(
            """
            'table_name', TABLE_NAME
            """,
            """
              SELECT TABLE_NAME
              FROM information_schema.TABLES
              WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_TYPE = 'BASE TABLE'
              ORDER BY TABLE_NAME
            """
        ),
    )
    tables = {
        str(row["table_name"]): {
            "name": str(row["table_name"]),
            "columns": [],
            "primary_key": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": [],
        }
        for row in table_rows
    }
    for row in mysql_query_json(
        container,
        client_bin,
        database,
        mysql_json_array(
            """
            'table_name', TABLE_NAME,
            'column_name', COLUMN_NAME,
            'column_type', COLUMN_TYPE,
            'data_type', DATA_TYPE,
            'is_nullable', IS_NULLABLE,
            'column_default', COLUMN_DEFAULT,
            'extra', EXTRA,
            'ordinal_position', ORDINAL_POSITION
            """,
            """
              SELECT *
              FROM information_schema.COLUMNS
              WHERE TABLE_SCHEMA = DATABASE()
              ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
        ),
    ):
        table = tables.get(str(row["table_name"]))
        if not table:
            continue
        column = {
            "name": str(row["column_name"]),
            "type": str(row.get("column_type") or row.get("data_type") or ""),
            "nullable": str(row.get("is_nullable") or "").upper() == "YES",
            "identity": "auto_increment" in str(row.get("extra") or "").casefold(),
        }
        if row.get("column_default") is not None:
            column["default"] = str(row["column_default"])
        table["columns"].append(column)
    mysql_key_constraints(container, client_bin, database, tables)
    mysql_check_constraints(container, client_bin, database, tables)
    mysql_indexes(container, client_bin, database, tables)
    return {"tables": list(tables.values())}


def mysql_key_constraints(
    container: str,
    client_bin: str,
    database: str,
    tables: dict[str, dict[str, Any]],
) -> None:
    rows = mysql_query_json(
        container,
        client_bin,
        database,
        mysql_json_array(
            """
            'table_name', tc.TABLE_NAME,
            'constraint_name', tc.CONSTRAINT_NAME,
            'constraint_type', tc.CONSTRAINT_TYPE,
            'column_name', kcu.COLUMN_NAME,
            'ordinal_position', kcu.ORDINAL_POSITION,
            'referenced_table_name', kcu.REFERENCED_TABLE_NAME,
            'referenced_column_name', kcu.REFERENCED_COLUMN_NAME,
            'position_in_unique_constraint', kcu.POSITION_IN_UNIQUE_CONSTRAINT
            """,
            """
            FROM information_schema.TABLE_CONSTRAINTS tc
            LEFT JOIN information_schema.KEY_COLUMN_USAGE kcu
              ON kcu.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
             AND kcu.TABLE_SCHEMA = tc.TABLE_SCHEMA
             AND kcu.TABLE_NAME = tc.TABLE_NAME
             AND kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = DATABASE()
              AND tc.CONSTRAINT_TYPE IN ('PRIMARY KEY', 'UNIQUE', 'FOREIGN KEY')
            ORDER BY tc.TABLE_NAME, tc.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
            """
        ),
    )
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row.get("table_name") or ""),
            str(row.get("constraint_name") or ""),
            str(row.get("constraint_type") or ""),
        )
        grouped.setdefault(key, []).append(row)
    for (table_name, constraint_name, constraint_type), group in grouped.items():
        table = tables.get(table_name)
        if not table:
            continue
        ordered = sorted(group, key=lambda item: int(item.get("ordinal_position") or 0))
        columns = [str(item.get("column_name")) for item in ordered if item.get("column_name")]
        if constraint_type == "PRIMARY KEY":
            table["primary_key"] = columns
        elif constraint_type == "UNIQUE":
            table["unique_constraints"].append({"name": constraint_name, "columns": columns})
        elif constraint_type == "FOREIGN KEY":
            ref_ordered = sorted(
                ordered,
                key=lambda item: int(item.get("position_in_unique_constraint") or item.get("ordinal_position") or 0),
            )
            table["foreign_keys"].append(
                {
                    "name": constraint_name,
                    "columns": columns,
                    "ref_table": str(ordered[0].get("referenced_table_name") or ""),
                    "ref_columns": [
                        str(item.get("referenced_column_name"))
                        for item in ref_ordered
                        if item.get("referenced_column_name")
                    ],
                }
            )


def mysql_check_constraints(
    container: str,
    client_bin: str,
    database: str,
    tables: dict[str, dict[str, Any]],
) -> None:
    try:
        rows = mysql_query_json(
            container,
            client_bin,
            database,
            mysql_json_array(
                """
                'table_name', tc.TABLE_NAME,
                'constraint_name', tc.CONSTRAINT_NAME,
                'check_clause', cc.CHECK_CLAUSE
                """,
                """
                FROM information_schema.TABLE_CONSTRAINTS tc
                JOIN information_schema.CHECK_CONSTRAINTS cc
                  ON cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
                 AND cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                WHERE tc.TABLE_SCHEMA = DATABASE()
                  AND tc.CONSTRAINT_TYPE = 'CHECK'
                ORDER BY tc.TABLE_NAME, tc.CONSTRAINT_NAME
                """
            ),
        )
    except Exception:
        rows = []
    for row in rows:
        table = tables.get(str(row.get("table_name") or ""))
        expression = normalize_expression(row.get("check_clause"))
        if table and expression:
            table["check_constraints"].append({"expression": expression})


def mysql_indexes(
    container: str,
    client_bin: str,
    database: str,
    tables: dict[str, dict[str, Any]],
) -> None:
    rows = mysql_query_json(
        container,
        client_bin,
        database,
        mysql_json_array(
            """
            'table_name', TABLE_NAME,
            'index_name', INDEX_NAME,
            'non_unique', NON_UNIQUE,
            'seq_in_index', SEQ_IN_INDEX,
            'column_name', COLUMN_NAME
            """,
            """
              SELECT *
              FROM information_schema.STATISTICS
              WHERE TABLE_SCHEMA = DATABASE()
              ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
            """
        ),
    )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row.get("table_name") or ""), str(row.get("index_name") or "")),
            [],
        ).append(row)
    for (table_name, index_name), group in grouped.items():
        table = tables.get(table_name)
        if not table:
            continue
        ordered = sorted(group, key=lambda item: int(item.get("seq_in_index") or 0))
        columns = [str(item.get("column_name")) for item in ordered if item.get("column_name")]
        if not columns or index_name == "PRIMARY":
            continue
        table["indexes"].append(
            {
                "name": index_name,
                "columns": columns,
                "unique": not bool(int(ordered[0].get("non_unique") or 0)),
                "origin": mysql_index_origin(table, index_name, columns),
            }
        )


def mysql_index_origin(table: dict[str, Any], index_name: str, columns: list[str]) -> str:
    unique_columns = {tuple(item.get("columns") or []) for item in table.get("unique_constraints") or []}
    if tuple(columns) in unique_columns:
        return "unique_constraint"
    foreign_key_columns = {tuple(item.get("columns") or []) for item in table.get("foreign_keys") or []}
    if tuple(columns) in foreign_key_columns or index_name in {
        str(item.get("name") or "") for item in table.get("foreign_keys") or []
    }:
        return "foreign_key_support"
    return "explicit_index"


def _sqlserver_query(database: str, query: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            f"container:{SS_NAME}",
            "mcr.microsoft.com/mssql-tools",
            "/opt/mssql-tools/bin/sqlcmd",
            "-S",
            "localhost",
            "-U",
            "sa",
            "-P",
            SQLSERVER_PASSWORD,
            "-d",
            database,
            "-b",
            "-Q",
            query,
        ],
        timeout=timeout,
    )


def _sqlserver_script(database: str, script: str, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    command = (
        "cat > /tmp/dbgenie_ddl.sql && "
        f"/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{SQLSERVER_PASSWORD}' "
        f"-d '{database}' -b -I -i /tmp/dbgenie_ddl.sql"
    )
    return run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            f"container:{SS_NAME}",
            "mcr.microsoft.com/mssql-tools",
            "/bin/bash",
            "-c",
            command,
        ],
        input_text=script,
        timeout=timeout,
    )


def completed_process_error(
    cp: subprocess.CompletedProcess[str],
    limit: int = 4000,
) -> str:
    output = "\n".join(
        text.strip()
        for text in (cp.stdout or "", cp.stderr or "")
        if text.strip()
    )
    if not output:
        output = f"process exited with code {cp.returncode}"
    return output[-limit:]


def sqlserver_query_json(database: str, query: str, timeout: int = 90) -> list[dict[str, Any]]:
    cp = run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            f"container:{SS_NAME}",
            "mcr.microsoft.com/mssql-tools",
            "/opt/mssql-tools/bin/sqlcmd",
            "-S",
            "localhost",
            "-U",
            "sa",
            "-P",
            SQLSERVER_PASSWORD,
            "-d",
            database,
            "-b",
            "-w",
            "65535",
            "-y",
            "0",
            "-Y",
            "0",
            "-Q",
            f"SET NOCOUNT ON; {query}",
        ],
        timeout=timeout,
    )
    if cp.returncode != 0:
        raise RuntimeError(completed_process_error(cp))
    text = "".join(line.strip() for line in (cp.stdout or "").splitlines() if line.strip())
    starts = [pos for pos in (text.find("["), text.find("{")) if pos >= 0]
    if starts:
        text = text[min(starts) :]
    return json.loads(text or "[]")


def execute_and_introspect_sqlserver(
    task_id: str,
    ddl: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    database = db_name(task_id)
    init = (
        f"IF DB_ID(N'{database}') IS NOT NULL BEGIN ALTER DATABASE [{database}] "
        f"SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]; END; "
        f"CREATE DATABASE [{database}];"
    )
    cp = _sqlserver_query("master", init, timeout=120)
    if cp.returncode != 0:
        return None, {
            "status": "failed",
            "executed": False,
            "introspected": False,
            "error_type": "create_database_failed",
            "error": completed_process_error(cp),
        }
    cp = _sqlserver_script(database, ddl, timeout=300)
    if cp.returncode != 0:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": "ddl_execution_failed",
            "error": completed_process_error(cp),
        }
    try:
        return execution_passed(introspect_sqlserver(database))
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": True,
            "introspected": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


def introspect_sqlserver(database: str) -> dict[str, Any]:
    table_rows = sqlserver_query_json(
        database,
        """
        SELECT s.name AS table_schema, t.name AS table_name
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        WHERE t.is_ms_shipped = 0
        ORDER BY s.name, t.name
        FOR JSON PATH
        """,
    )
    tables = {
        str(row["table_name"]): {
            "name": str(row["table_name"]),
            "columns": [],
            "primary_key": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": [],
        }
        for row in table_rows
    }
    for row in sqlserver_query_json(
        database,
        """
        SELECT t.name AS table_name,
               c.name AS column_name,
               ty.name AS data_type,
               c.max_length,
               c.precision,
               c.scale,
               c.is_nullable,
               c.is_identity,
               dc.definition AS column_default,
               c.column_id
        FROM sys.columns c
        JOIN sys.tables t ON t.object_id = c.object_id
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        LEFT JOIN sys.default_constraints dc ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
        WHERE t.is_ms_shipped = 0
        ORDER BY t.name, c.column_id
        FOR JSON PATH
        """,
    ):
        table = tables.get(str(row["table_name"]))
        if not table:
            continue
        column = {
            "name": str(row["column_name"]),
            "type": sqlserver_column_type(row),
            "nullable": bool(row.get("is_nullable")),
            "identity": bool(row.get("is_identity")),
        }
        if row.get("column_default") is not None:
            column["default"] = str(row["column_default"])
        table["columns"].append(column)
    sqlserver_key_constraints(database, tables)
    sqlserver_foreign_keys(database, tables)
    sqlserver_check_constraints(database, tables)
    sqlserver_indexes(database, tables)
    return {"tables": list(tables.values())}


def sqlserver_column_type(row: dict[str, Any]) -> str:
    name = str(row.get("data_type") or "")
    lower = name.casefold()
    if lower in {"varchar", "char", "binary", "varbinary"}:
        length = int(row.get("max_length") or 0)
        return f"{name}({'max' if length < 0 else length})"
    if lower in {"nvarchar", "nchar"}:
        length = int(row.get("max_length") or 0)
        return f"{name}({'max' if length < 0 else length // 2})"
    if lower in {"decimal", "numeric"}:
        return f"{name}({int(row.get('precision') or 0)},{int(row.get('scale') or 0)})"
    if lower in {"datetime2", "datetimeoffset", "time"}:
        return f"{name}({int(row.get('scale') or 0)})"
    return name


def sqlserver_key_constraints(database: str, tables: dict[str, dict[str, Any]]) -> None:
    rows = sqlserver_query_json(
        database,
        """
        SELECT t.name AS table_name,
               kc.name AS constraint_name,
               kc.type AS constraint_type,
               c.name AS column_name,
               ic.key_ordinal
        FROM sys.key_constraints kc
        JOIN sys.tables t ON t.object_id = kc.parent_object_id
        JOIN sys.index_columns ic ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
        JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
        WHERE t.is_ms_shipped = 0
          AND ic.is_included_column = 0
        ORDER BY t.name, kc.name, ic.key_ordinal
        FOR JSON PATH
        """,
    )
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (
                str(row.get("table_name") or ""),
                str(row.get("constraint_name") or ""),
                str(row.get("constraint_type") or ""),
            ),
            [],
        ).append(row)
    for (table_name, constraint_name, constraint_type), group in grouped.items():
        table = tables.get(table_name)
        if not table:
            continue
        columns = [
            str(item.get("column_name"))
            for item in sorted(group, key=lambda value: int(value.get("key_ordinal") or 0))
            if item.get("column_name")
        ]
        if constraint_type == "PK":
            table["primary_key"] = columns
        elif constraint_type == "UQ":
            table["unique_constraints"].append({"name": constraint_name, "columns": columns})


def sqlserver_foreign_keys(database: str, tables: dict[str, dict[str, Any]]) -> None:
    rows = sqlserver_query_json(
        database,
        """
        SELECT pt.name AS table_name,
               fk.name AS constraint_name,
               pc.name AS column_name,
               rt.name AS ref_table,
               rc.name AS ref_column,
               fkc.constraint_column_id
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
        JOIN sys.tables pt ON pt.object_id = fk.parent_object_id
        JOIN sys.columns pc ON pc.object_id = fkc.parent_object_id AND pc.column_id = fkc.parent_column_id
        JOIN sys.tables rt ON rt.object_id = fk.referenced_object_id
        JOIN sys.columns rc ON rc.object_id = fkc.referenced_object_id AND rc.column_id = fkc.referenced_column_id
        WHERE pt.is_ms_shipped = 0
        ORDER BY pt.name, fk.name, fkc.constraint_column_id
        FOR JSON PATH
        """,
    )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row.get("table_name") or ""), str(row.get("constraint_name") or "")),
            [],
        ).append(row)
    for (table_name, constraint_name), group in grouped.items():
        table = tables.get(table_name)
        if not table:
            continue
        ordered = sorted(group, key=lambda value: int(value.get("constraint_column_id") or 0))
        table["foreign_keys"].append(
            {
                "name": constraint_name,
                "columns": [str(item.get("column_name")) for item in ordered if item.get("column_name")],
                "ref_table": str(ordered[0].get("ref_table") or ""),
                "ref_columns": [str(item.get("ref_column")) for item in ordered if item.get("ref_column")],
            }
        )


def sqlserver_check_constraints(database: str, tables: dict[str, dict[str, Any]]) -> None:
    rows = sqlserver_query_json(
        database,
        """
        SELECT t.name AS table_name,
               cc.name AS constraint_name,
               cc.definition
        FROM sys.check_constraints cc
        JOIN sys.tables t ON t.object_id = cc.parent_object_id
        WHERE t.is_ms_shipped = 0
        ORDER BY t.name, cc.name
        FOR JSON PATH
        """,
    )
    for row in rows:
        table = tables.get(str(row.get("table_name") or ""))
        expression = normalize_expression(row.get("definition"))
        if table and expression:
            table["check_constraints"].append({"expression": expression})


def sqlserver_indexes(database: str, tables: dict[str, dict[str, Any]]) -> None:
    rows = sqlserver_query_json(
        database,
        """
        SELECT t.name AS table_name,
               i.name AS index_name,
               i.is_unique,
               i.is_primary_key,
               i.is_unique_constraint,
               c.name AS column_name,
               ic.key_ordinal
        FROM sys.indexes i
        JOIN sys.tables t ON t.object_id = i.object_id
        JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
        JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
        WHERE t.is_ms_shipped = 0
          AND i.index_id > 0
          AND i.is_hypothetical = 0
          AND ic.is_included_column = 0
          AND ic.key_ordinal > 0
        ORDER BY t.name, i.name, ic.key_ordinal
        FOR JSON PATH
        """,
    )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row.get("table_name") or ""), str(row.get("index_name") or "")),
            [],
        ).append(row)
    for (table_name, index_name), group in grouped.items():
        table = tables.get(table_name)
        if not table:
            continue
        ordered = sorted(group, key=lambda value: int(value.get("key_ordinal") or 0))
        if bool(ordered[0].get("is_primary_key")):
            continue
        origin = "unique_constraint" if bool(ordered[0].get("is_unique_constraint")) else "explicit_index"
        table["indexes"].append(
            {
                "name": index_name,
                "columns": [str(item.get("column_name")) for item in ordered if item.get("column_name")],
                "unique": bool(ordered[0].get("is_unique")),
                "origin": origin,
            }
        )


def extract_check_expressions(create_sql: str) -> list[str]:
    expressions = []
    lower = create_sql.lower()
    pos = 0
    while True:
        check_pos = lower.find("check", pos)
        if check_pos < 0:
            break
        open_pos = create_sql.find("(", check_pos)
        if open_pos < 0:
            break
        depth = 0
        close_pos = -1
        in_quote: str | None = None
        i = open_pos
        while i < len(create_sql):
            ch = create_sql[i]
            if in_quote:
                if ch == in_quote:
                    if i + 1 < len(create_sql) and create_sql[i + 1] == in_quote:
                        i += 1
                    else:
                        in_quote = None
            elif ch in ("'", '"'):
                in_quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    close_pos = i
                    break
            i += 1
        if close_pos < 0:
            break
        expressions.append(create_sql[open_pos + 1 : close_pos].strip())
        pos = close_pos + 1
    return expressions


def normalize_identifier(value: Any) -> str:
    text = str(value or "").strip()
    if "." in text:
        text = text.split(".")[-1]
    pairs = (("`", "`"), ('"', '"'), ("[", "]"))
    changed = True
    while changed and text:
        changed = False
        for left, right in pairs:
            if text.startswith(left) and text.endswith(right):
                text = text[1:-1]
                changed = True
    return text.casefold()


def canonical_type(value: Any, target_dbms: str = "") -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("unsigned", "").strip()
    text = re.sub(r"\s*\(\s*", "(", text)
    text = re.sub(r"\s*,\s*", ",", text)
    text = re.sub(r"\s*\)\s*", ")", text)
    if text.endswith("[]"):
        return canonical_type(text[:-2], target_dbms) + "[]"
    dbms = target_dbms.casefold()
    if dbms in {"mysql", "mariadb"} and re.fullmatch(r"(tinyint|bit)\(1\)", text):
        return "boolean"
    base = re.sub(r"\(.*\)$", "", text)
    params = text[len(base) :] if text.startswith(base) else ""
    aliases = {
        "int": "integer",
        "integer": "integer",
        "int2": "integer",
        "int4": "integer",
        "int8": "integer",
        "bigint": "integer",
        "smallint": "integer",
        "tinyint": "integer",
        "mediumint": "integer",
        "serial": "integer",
        "bigserial": "integer",
        "bool": "boolean",
        "boolean": "boolean",
        "bit": "boolean",
        "datetime": "datetime",
        "datetime2": "datetime",
        "datetimeoffset": "datetime",
        "smalldatetime": "datetime",
        "timestamp": "datetime",
        "timestamptz": "datetime",
        "timestamp with time zone": "datetime",
        "timestamp without time zone": "datetime",
        "date": "date",
        "time": "time",
        "timetz": "time",
        "time with time zone": "time",
        "time without time zone": "time",
        "varchar": "text",
        "character varying": "text",
        "char": "text",
        "character": "text",
        "nvarchar": "text",
        "nchar": "text",
        "string": "text",
        "text": "text",
        "tinytext": "text",
        "mediumtext": "text",
        "longtext": "text",
        "clob": "text",
        "enum": "text",
        "set": "text",
        "json": "json",
        "jsonb": "json",
        "real": "float",
        "double": "float",
        "double precision": "float",
        "float": "float",
        "float4": "float",
        "float8": "float",
        "decimal": "numeric",
        "numeric": "numeric",
        "money": "numeric",
        "smallmoney": "numeric",
        "number": "numeric",
        "blob": "binary",
        "tinyblob": "binary",
        "mediumblob": "binary",
        "longblob": "binary",
        "binary": "binary",
        "varbinary": "binary",
        "bytea": "binary",
        "uuid": "uuid",
        "uniqueidentifier": "uuid",
    }
    canonical = aliases.get(base, base)
    if dbms == "sqlite":
        if canonical in {"datetime", "date", "time"}:
            return "text"
        if canonical == "boolean":
            return "integer"
    if canonical in {"text", "integer", "boolean", "datetime", "date", "time", "json", "float", "binary", "uuid"}:
        return canonical
    if canonical == "numeric":
        return canonical + params
    return canonical + params


def normalize_expression(value: Any) -> str:
    text = str(value or "").strip().casefold()
    if text.startswith("check"):
        checks = extract_check_expressions(text)
        if checks:
            text = checks[0]
    text = re.sub(r'"([a-z_][a-z0-9_$]*)"', r"\1", text)
    text = re.sub(r"`([a-z_][a-z0-9_$]*)`", r"\1", text)
    text = re.sub(r"\[([a-z_][a-z0-9_$]*)\]", r"\1", text)
    text = re.sub(r"\btrue\b", "1", text)
    text = re.sub(r"\bfalse\b", "0", text)
    text = re.sub(r"::[a-z_][a-z0-9_\s]*(\([^)]*\))?", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([(),=<>+\-*/])\s*", r"\1", text)
    text = re.sub(r"([a-z_][a-z0-9_$]*)=any\(array\[(.*?)\]\)", r"\1 in(\2)", text)
    text = re.sub(r"\b(and|or)\b", r" \1 ", text)
    text = re.sub(r"\s+", " ", text)
    text = strip_balanced_outer_parens(text.strip())
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\(([-+]?\d+(?:\.\d+)?)\)", r"\1", text)
        text = re.sub(r"\(([a-z_][a-z0-9_$]*)\)", r"\1", text)
        text = re.sub(r"\(([a-z_][a-z0-9_$]* is not null)\)", r"\1", text)
        text = re.sub(r"\(([a-z_][a-z0-9_$]* is null)\)", r"\1", text)
        text = strip_balanced_outer_parens(text)
    return text.strip()


def strip_balanced_outer_parens(text: str) -> str:
    while text.startswith("(") and text.endswith(")") and encloses_whole_expression(text):
        text = text[1:-1].strip()
    return text


def encloses_whole_expression(text: str) -> bool:
    depth = 0
    in_quote: str | None = None
    for index, ch in enumerate(text):
        if in_quote:
            if ch == in_quote:
                in_quote = None
            continue
        if ch in ("'", '"', "`"):
            in_quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and index != len(text) - 1:
                return False
            if depth < 0:
                return False
    return depth == 0


def normalize_schema_ir(raw: dict[str, Any] | None, target_dbms: str = "") -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"tables": []}
    tables = []
    for table in dict_items(raw.get("tables")):
        table_name = normalize_identifier(table.get("name"))
        column_order = []
        columns: dict[str, dict[str, Any]] = {}
        for column in dict_items(table.get("columns")):
            column_name = normalize_identifier(column.get("name"))
            if not column_name:
                continue
            column_order.append(column_name)
            columns[column_name] = {
                "name": column_name,
                "type": canonical_type(column.get("type"), target_dbms),
                "nullable": bool(column.get("nullable", True)),
                "identity": bool(
                    column.get("identity")
                    or column.get("auto_increment")
                    or column.get("autoincrement")
                ),
            }
        table_payload = {
            "name": table_name,
            "columns": [columns[name] for name in column_order if name in columns],
            "primary_key": [
                name for name in normalize_columns(table.get("primary_key")) if name in columns
            ],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": [],
        }
        for fk in dict_items(table.get("foreign_keys")):
            fk_columns = [name for name in normalize_columns(fk.get("columns")) if name in columns]
            ref_table = normalize_identifier(
                fk.get("ref_table")
                or fk.get("referenced_table")
                or fk.get("reference_table")
                or fk.get("target_table")
                or dig(fk, "references", "table", default="")
            )
            ref_columns = normalize_columns(
                fk.get("ref_columns")
                or fk.get("referenced_columns")
                or fk.get("reference_columns")
                or fk.get("target_columns")
                or dig(fk, "references", "columns", default=[])
            )
            if fk_columns and ref_table:
                table_payload["foreign_keys"].append(
                    {
                        "columns": fk_columns,
                        "ref_table": ref_table,
                        "ref_columns": ref_columns,
                    }
                )
        for constraint in dict_items(table.get("unique_constraints")):
            columns_in_constraint = [
                name for name in normalize_columns(constraint.get("columns")) if name in columns
            ]
            if columns_in_constraint:
                table_payload["unique_constraints"].append(
                    {"columns": columns_in_constraint}
                )
        for constraint in as_list(table.get("check_constraints")):
            expression = constraint.get("expression") if isinstance(constraint, dict) else constraint
            normalized = normalize_expression(expression)
            if normalized:
                table_payload["check_constraints"].append({"expression": normalized})
        for index in dict_items(table.get("indexes")):
            index_columns = [name for name in normalize_columns(index.get("columns")) if name in columns]
            if index_columns:
                table_payload["indexes"].append(
                    {
                        "name": str(index.get("name") or ""),
                        "columns": index_columns,
                        "unique": bool(index.get("unique", False)),
                        "origin": str(index.get("origin") or "logical_index"),
                    }
                )
        table_payload["foreign_keys"].sort(
            key=lambda item: (tuple(item["columns"]), item["ref_table"], tuple(item["ref_columns"]))
        )
        table_payload["unique_constraints"].sort(key=lambda item: tuple(item["columns"]))
        table_payload["check_constraints"].sort(key=lambda item: item["expression"])
        table_payload["indexes"].sort(key=lambda item: (tuple(item["columns"]), bool(item["unique"])))
        tables.append(table_payload)
    tables.sort(key=lambda item: item["name"])
    return {"tables": tables}


def normalize_columns(value: Any) -> list[str]:
    return [normalize_identifier(item) for item in string_list(value) if normalize_identifier(item)]


def normalize_index_columns(value: Any) -> list[str]:
    columns: list[str] = []
    for item in string_list(value):
        column = normalize_index_column(item)
        if column:
            columns.append(column)
    return columns


def normalize_index_column(value: Any) -> str:
    text = str(value or "").strip()
    text = strip_balanced_outer_parens(text)
    text = re.sub(r"\s+collate\s+[`\"\[\]\w.]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+nulls\s+(first|last)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+(asc|desc)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+nulls\s+(first|last)\s*$", "", text, flags=re.IGNORECASE)
    prefix_length = re.match(r"^([`\"\[]?[\w.]+[`\"\]]?)\(\d+\)$", text)
    if prefix_length:
        text = prefix_length.group(1)
    return normalize_identifier(text)


def item_sets_from_schema(schema: dict[str, Any]) -> dict[str, set[tuple[Any, ...]]]:
    tables = set()
    columns = set()
    datatypes = set()
    primary_keys = set()
    foreign_keys = set()
    constraints = set()
    for table in schema.get("tables") or []:
        table_name = table["name"]
        tables.add((table_name,))
        pk = tuple(table.get("primary_key") or [])
        if pk:
            primary_keys.add((table_name, pk))
        for column in table.get("columns") or []:
            column_name = column["name"]
            columns.add((table_name, column_name))
            datatypes.add((table_name, column_name, column.get("type") or ""))
            if not bool(column.get("nullable", True)):
                constraints.add((table_name, "not_null", (column_name,)))
        for fk in table.get("foreign_keys") or []:
            foreign_keys.add(
                (
                    table_name,
                    tuple(fk.get("columns") or []),
                    fk.get("ref_table") or "",
                    tuple(fk.get("ref_columns") or []),
                )
            )
        for unique in table.get("unique_constraints") or []:
            unique_columns = tuple(unique.get("columns") or [])
            if unique_columns:
                constraints.add((table_name, "unique", unique_columns))
        for check in table.get("check_constraints") or []:
            expression = check.get("expression") or ""
            if expression:
                constraints.add((table_name, "check", expression))
    return {
        "tables": tables,
        "columns": columns,
        "datatypes": datatypes,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "constraints": constraints,
    }


def build_index_inventory(
    schema: dict[str, Any],
    physical_plan: dict[str, Any] | None = None,
) -> dict[tuple[str, tuple[str, ...], bool], dict[str, Any]]:
    inventory: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]] = {}
    table_columns = {
        table["name"]: {column["name"] for column in table.get("columns") or []}
        for table in schema.get("tables") or []
    }
    for table in schema.get("tables") or []:
        table_name = table["name"]
        add_index(inventory, table_name, table.get("primary_key"), True, "primary_key")
        for unique in table.get("unique_constraints") or []:
            add_index(inventory, table_name, unique.get("columns"), True, "unique_constraint")
        for index in table.get("indexes") or []:
            add_index(
                inventory,
                table_name,
                index.get("columns"),
                bool(index.get("unique", False)),
                str(index.get("origin") or "logical_index"),
                name=str(index.get("name") or ""),
            )
    if isinstance(physical_plan, dict):
        raw_indexes = physical_plan.get("indexes")
        if raw_indexes is None:
            raw_indexes = physical_plan.get("index")
        for index in dict_items(raw_indexes):
            table_name = normalize_identifier(index.get("table"))
            columns = normalize_index_columns(index.get("columns"))
            known_columns = table_columns.get(table_name)
            if known_columns is not None:
                columns = [column for column in columns if column in known_columns]
            add_index(
                inventory,
                table_name,
                columns,
                bool(index.get("unique", False)),
                "physical_plan",
                name=str(index.get("name") or ""),
            )
    return inventory


def add_index(
    inventory: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]],
    table: Any,
    columns: Any,
    unique: bool,
    origin: str,
    *,
    name: str = "",
) -> None:
    table_name = normalize_identifier(table)
    column_tuple = tuple(normalize_index_columns(columns))
    if not table_name or not column_tuple:
        return
    key = (table_name, column_tuple, bool(unique))
    if key not in inventory:
        inventory[key] = {
            "table": table_name,
            "columns": list(column_tuple),
            "unique": bool(unique),
            "origins": [],
            "names": [],
        }
    if origin not in inventory[key]["origins"]:
        inventory[key]["origins"].append(origin)
    if name and name not in inventory[key]["names"]:
        inventory[key]["names"].append(name)


def compare_sets(
    predicted: set[tuple[Any, ...]],
    runtime: set[tuple[Any, ...]],
    *,
    detail_limit: int,
) -> dict[str, Any]:
    matched = predicted & runtime
    missing = predicted - runtime
    extra = runtime - predicted
    precision = len(matched) / len(runtime) if runtime else (1.0 if not predicted else 0.0)
    recall = len(matched) / len(predicted) if predicted else (1.0 if not runtime else 0.0)
    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    return {
        "predicted_count": len(predicted),
        "runtime_count": len(runtime),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact": not missing and not extra,
        "missing": [format_item(item) for item in sorted(missing, key=repr)[:detail_limit]],
        "extra": [format_item(item) for item in sorted(extra, key=repr)[:detail_limit]],
    }


def compare_index_inventories(
    predicted: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]],
    runtime: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]],
    *,
    detail_limit: int,
) -> dict[str, Any]:
    return compare_sets(set(predicted), set(runtime), detail_limit=detail_limit)


def filter_runtime_indexes_for_dbms(
    runtime: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]],
    predicted: dict[tuple[str, tuple[str, ...], bool], dict[str, Any]],
    target_dbms: str,
) -> dict[tuple[str, tuple[str, ...], bool], dict[str, Any]]:
    if target_dbms not in {"MySQL", "MariaDB"}:
        return runtime
    return {
        key: value
        for key, value in runtime.items()
        if key in predicted or "foreign_key_support" not in value.get("origins", [])
    }


def format_item(item: tuple[Any, ...]) -> Any:
    def convert(value: Any) -> Any:
        if isinstance(value, tuple):
            return [convert(child) for child in value]
        return value

    return [convert(value) for value in item]


def compare_designs(
    predicted_schema: dict[str, Any],
    physical_plan: dict[str, Any] | None,
    runtime_schema: dict[str, Any],
    *,
    detail_limit: int,
    target_dbms: str = "",
) -> dict[str, Any]:
    predicted_sets = item_sets_from_schema(predicted_schema)
    runtime_sets = item_sets_from_schema(runtime_schema)
    category_results = {
        name: compare_sets(predicted_sets[name], runtime_sets[name], detail_limit=detail_limit)
        for name in (
            "tables",
            "columns",
            "datatypes",
            "primary_keys",
            "foreign_keys",
            "constraints",
        )
    }
    predicted_indexes = build_index_inventory(predicted_schema, physical_plan)
    runtime_indexes = build_index_inventory(runtime_schema)
    runtime_indexes = filter_runtime_indexes_for_dbms(runtime_indexes, predicted_indexes, target_dbms)
    category_results["indexes"] = compare_index_inventories(
        predicted_indexes,
        runtime_indexes,
        detail_limit=detail_limit,
    )
    metric_names = list(category_results)
    implementation_score = sum(category_results[name]["f1"] for name in metric_names) / len(metric_names)
    return {
        "implementation_score": implementation_score,
        "exact": all(category_results[name]["exact"] for name in metric_names),
        "categories": category_results,
        "predicted_index_inventory": [
            predicted_indexes[key] for key in sorted(predicted_indexes, key=repr)
        ][:detail_limit],
        "runtime_index_inventory": [
            runtime_indexes[key] for key in sorted(runtime_indexes, key=repr)
        ][:detail_limit],
    }


def evaluate_run_file(
    path: Path,
    *,
    runtime_ir_dir: Path,
    detail_limit: int,
    write_runtime_ir: bool,
    service_availability: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payload = load_json(path)
    task_id = str(payload.get("task_id") or repo_slug_from_path(path))
    target_dbms = str(dig(payload, "state", "task", "target_dbms", default=""))
    final_ddl = str(payload.get("final_ddl") or "")
    predicted_raw = dig(payload, "state", "artifacts", "logical_model", "payload", "schema_ir", default=None)
    physical_plan = dig(
        payload,
        "state",
        "artifacts",
        "physical_plan",
        "payload",
        "physical_plan",
        default=None,
    )
    base_result = {
        "task_id": task_id,
        "run_path": path.as_posix(),
        "target_dbms": target_dbms,
        "run_status": str(payload.get("status") or ""),
        "has_final_ddl": bool(final_ddl.strip()),
        "has_predicted_schema_ir": isinstance(predicted_raw, dict) and bool(predicted_raw.get("tables")),
        "has_physical_plan": isinstance(physical_plan, dict),
    }
    if target_dbms not in SUPPORTED_DBMS:
        return {
            **base_result,
            "execution": {
                "status": "skipped",
                "executed": False,
                "introspected": False,
                "reason": f"unsupported_dbms:{target_dbms}",
            },
            "consistency": None,
        }
    service = service_availability.get(target_dbms, {"available": True, "reason": ""})
    if not service.get("available", True):
        return {
            **base_result,
            "execution": {
                "status": "skipped",
                "executed": False,
                "introspected": False,
                "reason": f"runtime_unavailable:{service.get('reason')}",
            },
            "consistency": None,
        }
    if not final_ddl.strip():
        return {
            **base_result,
            "execution": {
                "status": "failed",
                "executed": False,
                "introspected": False,
                "error_type": "missing_final_ddl",
                "error": "final_ddl is empty.",
            },
            "consistency": None,
        }

    runtime_raw, execution = execute_and_introspect_runtime(target_dbms, task_id, final_ddl)
    if runtime_raw is None:
        return {**base_result, "execution": execution, "consistency": None}

    runtime_normalized = normalize_schema_ir(runtime_raw, target_dbms)
    predicted_normalized = normalize_schema_ir(predicted_raw, target_dbms)
    runtime_ir_path = runtime_ir_dir / f"{task_id}.runtime_schema_ir.json"
    if write_runtime_ir:
        dump_json(
            runtime_ir_path,
            {
                "task_id": task_id,
                "target_dbms": target_dbms,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "raw_runtime_schema_ir": runtime_raw,
                "normalized_runtime_schema_ir": runtime_normalized,
            },
        )
    consistency = compare_designs(
        predicted_normalized,
        physical_plan if isinstance(physical_plan, dict) else None,
        runtime_normalized,
        detail_limit=detail_limit,
        target_dbms=target_dbms,
    )
    return {
        **base_result,
        "execution": {
            **execution,
            "runtime_ir_path": runtime_ir_path.as_posix() if write_runtime_ir else "",
        },
        "consistency": consistency,
    }


def collect_run_files(run_dir: Path, task_ids: list[str], limit: int | None) -> list[Path]:
    if task_ids:
        paths = []
        for task_id in task_ids:
            path = run_dir / f"{task_id}.json"
            if path.exists():
                paths.append(path)
            else:
                paths.append(Path(task_id))
        return paths[:limit] if limit else paths
    paths = sorted(run_dir.glob("*.json"))
    return paths[:limit] if limit else paths


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_execution = Counter(str(item.get("execution", {}).get("status") or "unknown") for item in results)
    by_dbms = Counter(str(item.get("target_dbms") or "") for item in results)
    scored = [item for item in results if isinstance(item.get("consistency"), dict)]
    category_names = [
        "tables",
        "columns",
        "datatypes",
        "primary_keys",
        "foreign_keys",
        "constraints",
        "indexes",
    ]
    macro: dict[str, float] = {}
    if scored:
        macro["implementation_score"] = sum(
            float(item["consistency"]["implementation_score"]) for item in scored
        ) / len(scored)
        for name in category_names:
            macro[f"{name}_f1"] = sum(
                float(item["consistency"]["categories"][name]["f1"]) for item in scored
            ) / len(scored)
            macro[f"{name}_recall"] = sum(
                float(item["consistency"]["categories"][name]["recall"]) for item in scored
            ) / len(scored)
    else:
        macro["implementation_score"] = 0.0
        for name in category_names:
            macro[f"{name}_f1"] = 0.0
            macro[f"{name}_recall"] = 0.0
    return {
        "sample_count": len(results),
        "scored_count": len(scored),
        "by_execution_status": dict(sorted(by_execution.items())),
        "by_target_dbms": dict(sorted(by_dbms.items())),
        "macro_average": macro,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-ir-dir", required=True, type=Path)
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--detail-limit", type=int, default=25)
    parser.add_argument("--no-runtime-ir", action="store_true")
    parser.add_argument("--keep-containers", action="store_true")
    args = parser.parse_args()

    run_files = collect_run_files(args.run_dir, args.task_id, args.limit)
    dbms_set = {
        str(dig(load_json(path), "state", "task", "target_dbms", default=""))
        for path in run_files
        if path.exists()
    }
    service_availability, started = prepare_runtime_services(dbms_set)
    try:
        results = [
            evaluate_run_file(
                path,
                runtime_ir_dir=args.runtime_ir_dir,
                detail_limit=args.detail_limit,
                write_runtime_ir=not args.no_runtime_ir,
                service_availability=service_availability,
            )
            for path in run_files
        ]
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": {
                "run_dir": args.run_dir.as_posix(),
                "supported_dbms": sorted(SUPPORTED_DBMS),
                "docker_dbms": sorted(DOCKER_DBMS),
                "service_availability": service_availability,
                "task_ids": args.task_id,
                "limit": args.limit,
            },
            "summary": summarize(results),
            "samples": results,
        }
    finally:
        if not args.keep_containers:
            cleanup_runtime_services(started)
    dump_json(args.output, payload)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
