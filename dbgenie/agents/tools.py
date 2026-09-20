from __future__ import annotations

import importlib.util
import re
import sqlite3
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from dbgenie.core.schema_ir import SchemaIR
from benchmark.construction.reference_ddl import clean_identifier, normalize_dialect


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class DDLExecutionResult:
    success: bool
    error_type: str = ""
    error_message: str = ""
    executor: str = "static_ddl_check"
    real_execution: bool = False
    dialect: str = ""
    database: str = ""
    container: str = ""
    table_count_runtime: int | None = None
    runtime_version: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "success": self.success,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "executor": self.executor,
            "real_execution": self.real_execution,
            "stub": not self.real_execution,
        }
        if self.dialect:
            payload["dialect"] = self.dialect
        if self.database:
            payload["database"] = self.database
        if self.container:
            payload["container"] = self.container
        if self.table_count_runtime is not None:
            payload["table_count_runtime"] = self.table_count_runtime
        if self.runtime_version:
            payload["runtime_version"] = self.runtime_version
        if self.warnings:
            payload["warnings"] = self.warnings
        return payload


DDLExecutionStubResult = DDLExecutionResult


class AgentArtifactValidator:
    def validate_role_artifact(self, role: str, payload: dict[str, Any]) -> ValidationResult:
        if role == "requirement_analyst":
            return self.validate_requirement_brief(payload)
        if role == "conceptual_model_designer":
            return self.validate_conceptual_model(payload)
        if role == "conceptual_model_reviewer":
            return self.validate_conceptual_review(payload)
        if role == "logical_model_designer":
            schema_payload = payload.get("schema_ir") if isinstance(payload, dict) else None
            if not isinstance(schema_payload, dict):
                return ValidationResult(
                    passed=False,
                    errors=["logical_model missing schema_ir"],
                )
            return self.validate_schema_ir(schema_payload)
        if role == "physical_design_specialist":
            return self.validate_physical_plan(payload)
        if role == "dialect_compiler":
            return self.validate_dialect_report(payload)
        if role == "test_expert":
            return self.validate_test_report(payload)
        return ValidationResult(passed=True)

    def validate_requirement_brief(self, payload: dict[str, Any]) -> ValidationResult:
        required = [
            "task_summary",
            "candidate_concepts",
            "candidate_attributes",
            "relationship_hints",
            "latent_invariants",
            "workload_implications",
            "ambiguities",
        ]
        return _validate_required_fields(payload, required)

    def validate_conceptual_model(self, payload: dict[str, Any]) -> ValidationResult:
        result = _validate_required_fields(payload, ["entities", "relationships"])
        warnings = list(result.warnings)
        if isinstance(payload.get("entities"), list) and not payload["entities"]:
            warnings.append("conceptual_model has no entities")
        return ValidationResult(
            passed=not result.errors,
            warnings=warnings,
            errors=result.errors,
        )

    def validate_conceptual_review(self, payload: dict[str, Any]) -> ValidationResult:
        return _validate_required_fields(
            payload,
            ["passed", "issues", "revision_instructions"],
        )

    def validate_schema_ir(self, payload: dict[str, Any]) -> ValidationResult:
        try:
            schema = SchemaIR.from_dict(payload)
        except (KeyError, TypeError, ValueError) as exc:
            return ValidationResult(passed=False, errors=[f"invalid schema_ir: {exc}"])
        warnings = []
        errors = []
        if not isinstance(payload.get("tables"), list):
            errors.append("schema_ir.tables must be a list")
        if not schema.tables:
            errors.append("schema_ir has no tables")
        table_names = {clean_identifier(table.name).lower(): table for table in schema.tables}
        for table in schema.tables:
            table_name = clean_identifier(table.name)
            if not table_name:
                errors.append("table has empty name")
            if not table.columns:
                warnings.append(f"table has no columns: {table.name}")
            column_names = {
                clean_identifier(column.name).lower()
                for column in table.columns
                if clean_identifier(column.name)
            }
            if len(column_names) < len(table.columns):
                errors.append(f"table has duplicate or empty columns: {table.name}")
            for column in table.primary_key:
                if clean_identifier(column).lower() not in column_names:
                    errors.append(f"primary key references missing column: {table.name}.{column}")
            for foreign_key in table.foreign_keys:
                for column in foreign_key.columns:
                    if clean_identifier(column).lower() not in column_names:
                        errors.append(
                            f"foreign key references missing local column: {table.name}.{column}"
                        )
                ref_table = table_names.get(clean_identifier(foreign_key.ref_table).lower())
                if not ref_table:
                    errors.append(
                        f"foreign key references missing table: {table.name}->{foreign_key.ref_table}"
                    )
                    continue
                ref_columns = {
                    clean_identifier(column.name).lower()
                    for column in ref_table.columns
                    if clean_identifier(column.name)
                }
                for column in foreign_key.ref_columns:
                    if clean_identifier(column).lower() not in ref_columns:
                        errors.append(
                            "foreign key references missing target column: "
                            f"{table.name}->{foreign_key.ref_table}.{column}"
                        )
        return ValidationResult(passed=not errors, warnings=warnings, errors=errors)

    def validate_physical_plan(self, payload: dict[str, Any]) -> ValidationResult:
        result = _validate_required_fields(payload, ["physical_plan"])
        warnings = list(result.warnings)
        plan = payload.get("physical_plan")
        indexes = []
        if isinstance(plan, dict):
            raw_indexes = plan.get("indexes") or []
            if isinstance(raw_indexes, list):
                indexes = raw_indexes
            else:
                warnings.append("physical_plan.indexes should be a list")
        elif isinstance(plan, list):
            indexes = plan
        elif "physical_plan" in payload:
            warnings.append("physical_plan should be an object or list")
        for index, item in enumerate(indexes, start=1):
            if not isinstance(item, dict):
                warnings.append(f"physical index #{index} is not an object")
                continue
            for key in ("table", "columns"):
                if key not in item:
                    warnings.append(f"physical index #{index} missing {key}")
        return ValidationResult(
            passed=not result.errors,
            warnings=warnings,
            errors=result.errors,
        )

    def validate_dialect_report(self, payload: dict[str, Any]) -> ValidationResult:
        result = _validate_required_fields(payload, ["dialect_notes", "warnings", "errors"])
        warnings = list(result.warnings)
        ddl = payload.get("ddl")
        if ddl is not None and not isinstance(ddl, str):
            warnings.append("dialect_report.ddl should be a string when present")
        return ValidationResult(
            passed=not result.errors,
            warnings=warnings,
            errors=result.errors,
        )

    def validate_test_report(self, payload: dict[str, Any]) -> ValidationResult:
        return _validate_required_fields(
            payload,
            ["generated_tests", "execution_feedback", "feedback", "passed"],
        )


class AgentToolbox:
    def __init__(
        self,
        execution_mode: str = "static",
        docker_runner: Any | None = None,
    ) -> None:
        if execution_mode not in {"static", "docker", "auto"}:
            raise ValueError("execution_mode must be one of: static, docker, auto")
        self.validator = AgentArtifactValidator()
        self.execution_mode = execution_mode
        self.docker_executor = DockerDDLExecutor(runner=docker_runner)

    def execute_ddl(self, ddl: str, target_dbms: str) -> DDLExecutionResult:
        dialect = normalize_dialect(target_dbms)
        if not ddl.strip():
            return DDLExecutionResult(
                success=False,
                error_type="empty_ddl",
                error_message="DDL is empty.",
            )
        if "create table" not in ddl.lower():
            return DDLExecutionResult(
                success=False,
                error_type="no_create_table",
                error_message="DDL executor requires at least one CREATE TABLE statement.",
            )
        if dialect == "sqlite":
            return _execute_sqlite_ddl(ddl)
        if dialect == "duckdb":
            duckdb_result = _execute_duckdb_ddl(ddl)
            if duckdb_result is not None:
                return duckdb_result
        if self.execution_mode in {"docker", "auto"}:
            if dialect in DOCKER_DIALECTS:
                return self.docker_executor.execute_ddl(ddl, dialect)
            return _unsupported_real_ddl_execution(dialect)
        return _static_ddl_check(ddl, dialect)

    def execute_ddl_stub(self, ddl: str) -> DDLExecutionStubResult:
        return _static_ddl_check(ddl, "")

    def lint_ddl(self, ddl: str, target_dbms: str) -> dict[str, Any]:
        return _lint_ddl_static(ddl, normalize_dialect(target_dbms))

    def run_generated_tests(
        self,
        tests: list[dict[str, Any]],
        ddl: str = "",
        target_dbms: str = "",
    ) -> dict[str, Any]:
        dialect = normalize_dialect(target_dbms)
        sql_tests = [
            item for item in tests if isinstance(item, dict) and _test_sql_statements(item)
        ]
        if dialect == "sqlite" and sql_tests and ddl.strip():
            return _run_sqlite_generated_tests(ddl, sql_tests)
        if dialect == "duckdb" and sql_tests and ddl.strip():
            duckdb_result = _run_duckdb_generated_tests(
                ddl,
                sql_tests,
            )
            if duckdb_result is not None:
                return duckdb_result
        if self.execution_mode == "static":
            return _static_generated_test_check(tests, sql_tests, dialect)
        if not sql_tests:
            return _generated_tests_not_executed(
                tests,
                sql_tests,
                dialect,
                error_type="no_sql_tests",
                error_message="No SQL test statements were provided for real execution.",
            )
        if not ddl.strip():
            return _generated_tests_not_executed(
                tests,
                sql_tests,
                dialect,
                error_type="missing_ddl",
                error_message="DDL is required before SQL tests can be executed.",
            )
        if self.execution_mode in {"docker", "auto"} and dialect in DOCKER_DIALECTS:
            return self.docker_executor.run_generated_tests(ddl, sql_tests, dialect)
        return _generated_tests_not_executed(
            tests,
            sql_tests,
            dialect,
            error_type="unsupported_real_execution",
            error_message=f"Real SQL test execution is not available for dialect: {dialect or 'unknown'}.",
        )

    def run_generated_tests_stub(self, tests: list[dict[str, Any]]) -> dict[str, Any]:
        return self.run_generated_tests(tests)

    def explain_generated_tests(
        self,
        tests: list[dict[str, Any]],
        ddl: str = "",
        target_dbms: str = "",
        physical_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dialect = normalize_dialect(target_dbms)
        query_tests = [
            item
            for item in tests
            if isinstance(item, dict) and _test_explain_queries(item)
        ]
        if not query_tests:
            return _query_plan_report(
                executor="no_explainable_query_tests",
                dialect=dialect,
                real_execution=False,
                stub=False,
                runtime_version="",
                test_count=len(tests),
                observations=[],
                warnings=["No explainable query tests were provided."],
            )
        if dialect == "sqlite" and ddl.strip():
            return _run_sqlite_explain(ddl, query_tests, test_count=len(tests))
        if dialect == "duckdb" and ddl.strip():
            duckdb_result = _run_duckdb_explain(
                ddl,
                query_tests,
                test_count=len(tests),
            )
            if duckdb_result is not None:
                return duckdb_result
        if self.execution_mode == "static":
            return _static_explain_check(query_tests, test_count=len(tests), dialect=dialect)
        if not ddl.strip():
            return _query_plan_not_executed(
                query_tests,
                test_count=len(tests),
                dialect=dialect,
                error_type="missing_ddl",
                error_message="DDL is required before query-plan evidence can be collected.",
            )
        if self.execution_mode in {"docker", "auto"} and dialect in DOCKER_DIALECTS:
            return self.docker_executor.explain_generated_tests(
                ddl,
                query_tests,
                dialect,
                physical_plan=physical_plan,
            )
        return _query_plan_not_executed(
            query_tests,
            test_count=len(tests),
            dialect=dialect,
            error_type="unsupported_real_execution",
            error_message=f"Real query-plan execution is not available for dialect: {dialect or 'unknown'}.",
        )


DOCKER_DIALECTS = {"postgresql", "mysql", "mariadb", "sqlserver"}
DOCKER_PASSWORD = "dbgenie_pass"
SQLSERVER_PASSWORD = "DBGenie_Strong_Pass_2026!"
POSTGRES_CONTAINER = "dbgenie_agents_postgres"
MYSQL_CONTAINER = "dbgenie_agents_mysql"
MARIADB_CONTAINER = "dbgenie_agents_mariadb"
SQLSERVER_CONTAINER = "dbgenie_agents_sqlserver"
_DOCKER_DIALECT_LOCKS: dict[str, threading.RLock] = {}
_DOCKER_DIALECT_LOCKS_GUARD = threading.Lock()


def _docker_dialect_lock(dialect: str) -> threading.RLock:
    key = str(dialect or "").lower()
    with _DOCKER_DIALECT_LOCKS_GUARD:
        lock = _DOCKER_DIALECT_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _DOCKER_DIALECT_LOCKS[key] = lock
        return lock


class DockerDDLExecutor:
    def __init__(self, runner: Any | None = None) -> None:
        self.runner = runner or _run_process

    def execute_ddl(self, ddl: str, dialect: str) -> DDLExecutionResult:
        with _docker_dialect_lock(dialect):
            return self._execute_ddl_locked(ddl, dialect)

    def _execute_ddl_locked(self, ddl: str, dialect: str) -> DDLExecutionResult:
        try:
            if dialect == "postgresql":
                return self._execute_postgres(ddl)
            if dialect == "mysql":
                return self._execute_mysql_like(ddl, "mysql")
            if dialect == "mariadb":
                return self._execute_mysql_like(ddl, "mariadb")
            if dialect == "sqlserver":
                return self._execute_sqlserver(ddl)
        except subprocess.TimeoutExpired as exc:
            return DDLExecutionResult(
                success=False,
                error_type="docker_timeout",
                error_message=str(exc),
                executor=f"docker_{dialect}",
                real_execution=True,
                dialect=dialect,
            )
        except Exception as exc:
            return DDLExecutionResult(
                success=False,
                error_type="docker_execution_error",
                error_message=str(exc),
                executor=f"docker_{dialect}",
                real_execution=True,
                dialect=dialect,
                runtime_version=self.runtime_version(dialect),
            )
        return DDLExecutionResult(
            success=False,
            error_type="unsupported_docker_dialect",
            error_message=f"Unsupported Docker dialect: {dialect}",
            executor=f"docker_{dialect}",
            real_execution=True,
            dialect=dialect,
            runtime_version=self.runtime_version(dialect),
        )

    def runtime_version(self, dialect: str) -> str:
        try:
            if dialect == "postgresql":
                result = self._run_ok(
                    [
                        "docker",
                        "exec",
                        POSTGRES_CONTAINER,
                        "psql",
                        "-U",
                        "postgres",
                        "-d",
                        "postgres",
                        "-tAc",
                        "SHOW server_version;",
                    ],
                    timeout=20,
                )
                return f"postgresql {str(result.stdout or '').strip()}"
            if dialect in {"mysql", "mariadb"}:
                container = MYSQL_CONTAINER if dialect == "mysql" else MARIADB_CONTAINER
                client_bin = "mysql" if dialect == "mysql" else "mariadb"
                result = self._run_ok(
                    [
                        "docker",
                        "exec",
                        "-i",
                        container,
                        client_bin,
                        "-h127.0.0.1",
                        "--protocol=tcp",
                        "-uroot",
                        f"-p{DOCKER_PASSWORD}",
                        "-N",
                        "-B",
                        "-e",
                        "SELECT VERSION();",
                    ],
                    timeout=20,
                )
                return f"{dialect} {str(result.stdout or '').strip()}"
            if dialect == "sqlserver":
                result = self._run_ok(
                    self._sqlserver_query_cmd(
                        "master",
                        "SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128));",
                        terse=True,
                    ),
                    timeout=20,
                )
                return f"sqlserver {str(result.stdout or '').strip()}"
        except Exception:
            return ""
        return ""

    def run_generated_tests(
        self,
        ddl: str,
        tests: list[dict[str, Any]],
        dialect: str,
    ) -> dict[str, Any]:
        with _docker_dialect_lock(dialect):
            return self._run_generated_tests_locked(ddl, tests, dialect)

    def _run_generated_tests_locked(
        self,
        ddl: str,
        tests: list[dict[str, Any]],
        dialect: str,
    ) -> dict[str, Any]:
        details = []
        for index, test in enumerate(tests, start=1):
            script = _combine_sql_script([ddl, *_test_setup_statements(test)], dialect=dialect)
            expect_success = _test_expect_success(test)
            result = self.execute_ddl(script, dialect)
            detail = _execution_detail_from_result(index, test, result, expect_success)
            if result.success and expect_success:
                detail["assertions"] = self._run_row_assertions(
                    result.database,
                    test,
                    dialect,
                )
                if any(not item.get("passed", False) for item in detail["assertions"]):
                    detail["passed"] = False
                    detail["error_type"] = "assertion_failed"
            details.append(detail)
        return {
            "executor": f"docker_{dialect}",
            "real_execution": True,
            "stub": False,
            "runtime_version": self.runtime_version(dialect),
            "test_count": len(tests),
            "sql_test_count": len(tests),
            "passed": all(item["passed"] for item in details),
            "details": details,
        }

    def explain_generated_tests(
        self,
        ddl: str,
        tests: list[dict[str, Any]],
        dialect: str,
        physical_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with _docker_dialect_lock(dialect):
            return self._explain_generated_tests_locked(ddl, tests, dialect, physical_plan)

    def _explain_generated_tests_locked(
        self,
        ddl: str,
        tests: list[dict[str, Any]],
        dialect: str,
        physical_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del physical_plan
        observations = []
        warnings = []
        for index, test in enumerate(tests, start=1):
            script = _combine_sql_script([ddl, *_test_setup_statements(test)], dialect=dialect)
            setup = self.execute_ddl(script, dialect)
            test_id = test.get("id") or f"t{index}"
            queries = _test_explain_queries(test)
            if not setup.success:
                warnings.append(f"EXPLAIN setup failed for {test_id}.")
                for query_index, query in enumerate(queries, start=1):
                    observations.append(
                        _query_plan_observation(
                            test,
                            test_index=index,
                            query_index=query_index,
                            query=query,
                            status="execution_error",
                            error_type="explain_setup_failed",
                            error_message=setup.error_message,
                        )
                    )
                if not queries:
                    observations.append(
                        _query_plan_observation(
                            test,
                            test_index=index,
                            query_index=1,
                            query="",
                            status="execution_error",
                            error_type="explain_setup_failed",
                            error_message=setup.error_message,
                        )
                    )
                continue
            for query_index, query in enumerate(queries, start=1):
                try:
                    plan_text = self._explain_query(setup.database, query, dialect)
                    observations.append(
                        _query_plan_observation(
                            test,
                            test_index=index,
                            query_index=query_index,
                            query=query,
                            status="executed",
                            plan=plan_text,
                        )
                    )
                except Exception as exc:
                    warnings.append(f"EXPLAIN execution failed for {test_id}.")
                    observations.append(
                        _query_plan_observation(
                            test,
                            test_index=index,
                            query_index=query_index,
                            query=query,
                            status="execution_error",
                            error_type="explain_execution_error",
                            error_message=str(exc),
                        )
                    )
        return _query_plan_report(
            executor=f"docker_{dialect}_explain",
            dialect=dialect,
            real_execution=True,
            stub=False,
            runtime_version=self.runtime_version(dialect),
            test_count=len(tests),
            observations=observations,
            warnings=warnings,
        )

    def _run_row_assertions(
        self,
        database: str,
        test: dict[str, Any],
        dialect: str,
    ) -> list[dict[str, Any]]:
        details = []
        for query_index, query in enumerate(_test_assertion_queries(test), start=1):
            try:
                count = self._query_row_count(database, query, dialect)
                details.append(_row_count_assertion_detail(test, query_index, query, count))
            except Exception as exc:
                details.append(
                    {
                        "query_index": query_index,
                        "query": _short_sql(query),
                        "passed": False,
                        "error_type": "assertion_query_error",
                        "error_message": str(exc),
                    }
                )
        return details

    def _query_row_count(self, database: str, query: str, dialect: str) -> int:
        sql = _row_count_sql(query)
        if dialect == "postgresql":
            result = self._run_ok(
                [
                    "docker",
                    "exec",
                    POSTGRES_CONTAINER,
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    database,
                    "-tAc",
                    sql,
                ],
                timeout=60,
            )
            return int(_last_int(result.stdout) or 0)
        if dialect in {"mysql", "mariadb"}:
            container = MYSQL_CONTAINER if dialect == "mysql" else MARIADB_CONTAINER
            client_bin = "mysql" if dialect == "mysql" else "mariadb"
            result = self._run_ok(
                [
                    "docker",
                    "exec",
                    "-i",
                    container,
                    client_bin,
                    "-h127.0.0.1",
                    "--protocol=tcp",
                    "-uroot",
                    f"-p{DOCKER_PASSWORD}",
                    "-N",
                    "-B",
                    database,
                    "-e",
                    sql,
                ],
                timeout=60,
            )
            return int(_last_int(result.stdout) or 0)
        if dialect == "sqlserver":
            result = self._run_ok(self._sqlserver_query_cmd(database, sql), timeout=60)
            return int(_last_int(result.stdout) or 0)
        raise ValueError(f"unsupported assertion dialect: {dialect}")

    def _explain_query(self, database: str, query: str, dialect: str) -> str:
        clean_query = _strip_trailing_semicolon(query)
        if dialect == "postgresql":
            result = self._run_ok(
                [
                    "docker",
                    "exec",
                    POSTGRES_CONTAINER,
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    database,
                    "-tAc",
                    f"EXPLAIN {clean_query};",
                ],
                timeout=60,
            )
            return result.stdout or ""
        if dialect in {"mysql", "mariadb"}:
            container = MYSQL_CONTAINER if dialect == "mysql" else MARIADB_CONTAINER
            client_bin = "mysql" if dialect == "mysql" else "mariadb"
            result = self._run_ok(
                [
                    "docker",
                    "exec",
                    "-i",
                    container,
                    client_bin,
                    "-h127.0.0.1",
                    "--protocol=tcp",
                    "-uroot",
                    f"-p{DOCKER_PASSWORD}",
                    "-B",
                    database,
                    "-e",
                    f"EXPLAIN {clean_query};",
                ],
                timeout=60,
            )
            return result.stdout or ""
        if dialect == "sqlserver":
            result = self._run_ok(
                self._sqlserver_script_cmd(database),
                input_text=_sqlserver_showplan_script(clean_query),
                timeout=60,
            )
            return result.stdout or ""
        raise ValueError(f"unsupported explain dialect: {dialect}")

    def _execute_postgres(self, ddl: str) -> DDLExecutionResult:
        container = POSTGRES_CONTAINER
        self._ensure_container(
            name=container,
            image="postgres:16-alpine",
            env={"POSTGRES_PASSWORD": DOCKER_PASSWORD},
            ready_cmd=["docker", "exec", container, "pg_isready", "-U", "postgres"],
            wait_seconds=90,
        )
        database = _database_name(ddl)
        self._run_ok(
            [
                "docker",
                "exec",
                container,
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
        self._run_ok(
            [
                "docker",
                "exec",
                container,
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
        self._run_ok(
            [
                "docker",
                "exec",
                "-i",
                container,
                "psql",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "postgres",
                "-d",
                database,
            ],
            input_text=ddl,
            timeout=180,
        )
        count = self._run_ok(
            [
                "docker",
                "exec",
                container,
                "psql",
                "-U",
                "postgres",
                "-d",
                database,
                "-tAc",
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE';",
            ],
            timeout=30,
        )
        return DDLExecutionResult(
            success=True,
            executor="docker_postgresql",
            real_execution=True,
            dialect="postgresql",
            database=database,
            container=container,
            table_count_runtime=_last_int(count.stdout),
            runtime_version=self.runtime_version("postgresql"),
        )

    def _execute_mysql_like(self, ddl: str, dialect: str) -> DDLExecutionResult:
        if dialect == "mysql":
            container = MYSQL_CONTAINER
            image = "mysql:8.4"
            env = {"MYSQL_ROOT_PASSWORD": DOCKER_PASSWORD}
            admin_bin = "mysqladmin"
            client_bin = "mysql"
        else:
            container = MARIADB_CONTAINER
            image = "mariadb:11.4"
            env = {"MARIADB_ROOT_PASSWORD": DOCKER_PASSWORD}
            admin_bin = "mariadb-admin"
            client_bin = "mariadb"
        connection_args = [
            client_bin,
            "-h127.0.0.1",
            "--protocol=tcp",
            "-uroot",
            f"-p{DOCKER_PASSWORD}",
        ]
        self._ensure_container(
            name=container,
            image=image,
            env=env,
            ready_cmd=[
                "docker",
                "exec",
                container,
                admin_bin,
                "ping",
                "-h127.0.0.1",
                "--protocol=tcp",
                "-uroot",
                f"-p{DOCKER_PASSWORD}",
            ],
            wait_seconds=120,
        )
        database = _database_name(ddl)
        self._run_ok(
            ["docker", "exec", "-i", container, *connection_args],
            input_text=f"DROP DATABASE IF EXISTS `{database}`; CREATE DATABASE `{database}`;",
            timeout=60,
        )
        self._run_ok(
            ["docker", "exec", "-i", container, *connection_args, database],
            input_text=ddl,
            timeout=180,
        )
        count = self._run_ok(
            [
                "docker",
                "exec",
                "-i",
                container,
                *connection_args,
                "-N",
                "-B",
                database,
                "-e",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE();",
            ],
            timeout=30,
        )
        return DDLExecutionResult(
            success=True,
            executor=f"docker_{dialect}",
            real_execution=True,
            dialect=dialect,
            database=database,
            container=container,
            table_count_runtime=_last_int(count.stdout),
            runtime_version=self.runtime_version(dialect),
        )

    def _execute_sqlserver(self, ddl: str) -> DDLExecutionResult:
        container = SQLSERVER_CONTAINER
        self._ensure_container(
            name=container,
            image="mcr.microsoft.com/mssql/server:2022-latest",
            env={
                "ACCEPT_EULA": "Y",
                "MSSQL_SA_PASSWORD": SQLSERVER_PASSWORD,
            },
            ready_cmd=self._sqlserver_query_cmd("master", "SELECT 1"),
            wait_seconds=150,
        )
        database = _database_name(ddl)
        file_token = uuid.uuid4().hex
        data_logical_name = f"{database}_{file_token}"
        log_logical_name = f"{data_logical_name}_log"
        data_file = f"/var/opt/mssql/data/{data_logical_name}.mdf"
        log_file = f"/var/opt/mssql/data/{log_logical_name}.ldf"
        init = (
            f"IF DB_ID(N'{database}') IS NOT NULL BEGIN ALTER DATABASE [{database}] "
            f"SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]; END; "
            f"CREATE DATABASE [{database}] "
            f"ON PRIMARY (NAME = N'{data_logical_name}', FILENAME = N'{data_file}') "
            f"LOG ON (NAME = N'{log_logical_name}', FILENAME = N'{log_file}');"
        )
        self._run_ok(self._sqlserver_query_cmd("master", init), timeout=120)
        self._run_ok(self._sqlserver_script_cmd(database), input_text=ddl, timeout=240)
        count = self._run_ok(
            self._sqlserver_query_cmd(
                database,
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE';",
            ),
            timeout=60,
        )
        return DDLExecutionResult(
            success=True,
            executor="docker_sqlserver",
            real_execution=True,
            dialect="sqlserver",
            database=database,
            container=container,
            table_count_runtime=_last_int(count.stdout),
            runtime_version=self.runtime_version("sqlserver"),
        )

    def _sqlserver_query_cmd(
        self,
        database: str,
        query: str,
        *,
        terse: bool = False,
    ) -> list[str]:
        query = _sqlserver_nocount_query(query)
        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            f"container:{SQLSERVER_CONTAINER}",
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
            "-I",
        ]
        if terse:
            command.extend(["-h", "-1", "-W"])
        command.extend(["-Q", query])
        return command

    def _sqlserver_script_cmd(self, database: str) -> list[str]:
        command = (
            "cat > /tmp/dbgenie_ddl.sql && "
            f"/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{SQLSERVER_PASSWORD}' "
            f"-d '{database}' -b -I -i /tmp/dbgenie_ddl.sql"
        )
        return [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            f"container:{SQLSERVER_CONTAINER}",
            "mcr.microsoft.com/mssql-tools",
            "/bin/bash",
            "-c",
            command,
        ]

    def _ensure_container(
        self,
        name: str,
        image: str,
        env: dict[str, str],
        ready_cmd: list[str],
        wait_seconds: int,
    ) -> None:
        exists = self.runner(["docker", "inspect", name], timeout=15)
        if exists.returncode != 0:
            cmd = ["docker", "run", "-d", "--name", name]
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])
            cmd.append(image)
            self._run_ok(cmd, timeout=180)
        else:
            running = self.runner(
                ["docker", "inspect", "-f", "{{.State.Running}}", name],
                timeout=15,
            )
            if (running.stdout or "").strip().lower() != "true":
                self._run_ok(["docker", "start", name], timeout=60)
        deadline = time.time() + wait_seconds
        last_error = ""
        while time.time() < deadline:
            ready = self.runner(ready_cmd, timeout=20)
            if ready.returncode == 0:
                return
            last_error = _command_error(ready)
            time.sleep(1)
        raise RuntimeError(f"Docker container {name} did not become ready: {last_error}")

    def _run_ok(
        self,
        cmd: list[str],
        input_text: str | None = None,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        cp = self.runner(cmd, input_text=input_text, timeout=timeout)
        if cp.returncode != 0:
            raise RuntimeError(_command_error(cp))
        return cp


def _validate_required_fields(payload: dict[str, Any], fields: list[str]) -> ValidationResult:
    errors = []
    warnings = []
    if not isinstance(payload, dict):
        return ValidationResult(passed=False, errors=["artifact must be an object"])
    for field_name in fields:
        if field_name not in payload:
            errors.append(f"missing required field: {field_name}")
    for field_name in fields:
        if field_name in payload and payload.get(field_name) is None:
            warnings.append(f"field is null: {field_name}")
    return ValidationResult(passed=not errors, warnings=warnings, errors=errors)


def _execute_sqlite_ddl(ddl: str) -> DDLExecutionResult:
    table_count = None
    try:
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.executescript(ddl)
            table_count = int(
                connection.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table';"
                ).fetchone()[0]
            )
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return DDLExecutionResult(
            success=False,
            error_type="sqlite_execution_error",
            error_message=str(exc),
            executor="sqlite_memory",
            real_execution=True,
            dialect="sqlite",
            runtime_version=f"sqlite {sqlite3.sqlite_version}",
        )
    return DDLExecutionResult(
        success=True,
        executor="sqlite_memory",
        real_execution=True,
        dialect="sqlite",
        table_count_runtime=table_count,
        runtime_version=f"sqlite {sqlite3.sqlite_version}",
    )


def _run_sqlite_generated_tests(
    ddl: str,
    tests: list[dict[str, Any]],
) -> dict[str, Any]:
    details = []
    for index, test in enumerate(tests, start=1):
        connection = None
        expect_success = _test_expect_success(test)
        try:
            connection = sqlite3.connect(":memory:")
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.executescript(ddl)
            statements = _test_setup_statements(test)
            try:
                for statement in statements:
                    connection.executescript(statement)
                detail = _execution_detail_from_success(index, test, expect_success)
                if expect_success:
                    detail["assertions"] = _run_sqlite_row_assertions(connection, test)
                    if any(not item.get("passed", False) for item in detail["assertions"]):
                        detail["passed"] = False
                        detail["error_type"] = "assertion_failed"
                details.append(detail)
            except sqlite3.Error as exc:
                details.append(
                    _execution_detail_from_exception(
                        index,
                        test,
                        exc,
                        expect_success,
                        "sqlite_execution_error",
                    )
                )
        except Exception as exc:
            details.append(
                {
                    "index": index,
                    "id": test.get("id") or f"t{index}",
                    "passed": False,
                    "expected_success": expect_success,
                    "error_type": "sqlite_setup_error",
                    "error_message": str(exc),
                }
            )
        finally:
            if connection is not None:
                connection.close()
    return {
        "executor": "sqlite_memory",
        "real_execution": True,
        "runtime_version": f"sqlite {sqlite3.sqlite_version}",
        "test_count": len(tests),
        "sql_test_count": len(tests),
        "passed": all(item.get("passed") for item in details),
        "details": details,
    }


def _test_sql_statements(test: dict[str, Any]) -> list[str]:
    raw = (
        test.get("sql")
        or test.get("statement")
        or test.get("statements")
        or test.get("query")
    )
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    return []


def _test_setup_statements(test: dict[str, Any]) -> list[str]:
    statements = []
    for key in ("setup_sql", "setup", "pre_sql", "before_sql"):
        statements.extend(_sql_list(test.get(key)))

    has_assertion = _has_row_count_expectation(test)
    for key in ("sql", "statement", "statements"):
        statements.extend(_sql_list(test.get(key)))

    if not statements and not has_assertion:
        statements.extend(_sql_list(test.get("query")))
    return statements


def _test_assertion_queries(test: dict[str, Any]) -> list[str]:
    raw = (
        test.get("assert_sql")
        or test.get("assertion_sql")
        or test.get("check_sql")
        or test.get("expected_sql")
    )
    queries = _sql_list(raw)
    if not queries and _has_row_count_expectation(test):
        queries = _sql_list(
            test.get("query")
            or test.get("select_sql")
            or test.get("workload_sql")
            or _first_select_statement(_sql_list(test.get("sql")))
        )
    return [query for query in queries if _looks_like_query(query)]


def _test_explain_queries(test: dict[str, Any]) -> list[str]:
    raw = (
        test.get("explain_sql")
        or test.get("explain_query")
        or test.get("query")
        or test.get("select_sql")
        or test.get("workload_sql")
    )
    queries = _sql_list(raw)
    if not queries:
        queries = [
            statement
            for statement in _sql_list(test.get("sql"))
            if _looks_like_query(statement)
        ]
    return [query for query in queries if _looks_like_query(query)]


def _sql_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_sql_list(item))
        return result
    if isinstance(value, dict):
        return _sql_list(
            value.get("sql")
            or value.get("statement")
            or value.get("query")
            or value.get("text")
        )
    return [str(value).strip()] if str(value).strip() else []


def _first_select_statement(statements: list[str]) -> str:
    for statement in statements:
        if _looks_like_query(statement):
            return statement
    return ""


def _looks_like_query(sql: str) -> bool:
    text = str(sql or "").strip().lower()
    return text.startswith("select ") or text.startswith("with ")


def _test_expect_success(test: dict[str, Any]) -> bool:
    for key in ("expect_success", "should_succeed", "valid"):
        if key in test:
            return _bool_value(test.get(key))
    for key in ("should_fail", "expect_failure", "expected_failure", "must_fail"):
        if key in test:
            return not _bool_value(test.get(key))
    if test.get("expected_error") or test.get("error_pattern"):
        return False
    return True


def _has_row_count_expectation(test: dict[str, Any]) -> bool:
    return any(
        key in test
        for key in (
            "expected_row_count",
            "expected_rows",
            "row_count",
            "min_row_count",
            "max_row_count",
        )
    )


def _execution_detail_from_result(
    index: int,
    test: dict[str, Any],
    result: DDLExecutionResult,
    expect_success: bool,
) -> dict[str, Any]:
    detail = _execution_detail_base(index, test, expect_success)
    passed = result.success == expect_success
    if not result.success and not expect_success:
        passed = _error_matches_expectation(test, result.error_message)
    if result.success and not expect_success:
        error_type = "unexpected_success"
        error_message = "Test was expected to fail but succeeded."
    else:
        error_type = (
            "expected_error_mismatch"
            if not result.success and not expect_success and not passed
            else result.error_type
        )
        error_message = result.error_message
    detail.update(
        {
            "passed": passed,
            "error_type": error_type,
            "error_message": error_message,
            "executor": result.executor,
            "database": result.database,
            "container": result.container,
        }
    )
    return detail


def _execution_detail_from_success(
    index: int,
    test: dict[str, Any],
    expect_success: bool,
) -> dict[str, Any]:
    detail = _execution_detail_base(index, test, expect_success)
    detail.update(
        {
            "passed": expect_success,
            "error_type": "" if expect_success else "unexpected_success",
            "error_message": "" if expect_success else "Test was expected to fail but succeeded.",
        }
    )
    return detail


def _execution_detail_from_exception(
    index: int,
    test: dict[str, Any],
    exc: Exception,
    expect_success: bool,
    error_type: str,
) -> dict[str, Any]:
    detail = _execution_detail_base(index, test, expect_success)
    message = str(exc)
    passed = (not expect_success) and _error_matches_expectation(test, message)
    detail.update(
        {
            "passed": passed,
            "error_type": (
                ""
                if passed
                else "expected_error_mismatch"
                if not expect_success
                else error_type
            ),
            "error_message": message,
        }
    )
    return detail


def _execution_detail_base(
    index: int,
    test: dict[str, Any],
    expect_success: bool,
) -> dict[str, Any]:
    return {
        "index": index,
        "id": test.get("id") or f"t{index}",
        "kind": test.get("kind") or test.get("type") or "",
        "expected_success": expect_success,
    }


def _error_matches_expectation(test: dict[str, Any], message: str) -> bool:
    expected = str(test.get("expected_error") or "").strip()
    pattern = str(test.get("error_pattern") or "").strip()
    if expected and expected.lower() not in str(message or "").lower():
        return False
    if pattern:
        try:
            return re.search(pattern, str(message or ""), flags=re.IGNORECASE) is not None
        except re.error:
            return pattern.lower() in str(message or "").lower()
    return True


def _run_sqlite_row_assertions(
    connection: sqlite3.Connection,
    test: dict[str, Any],
) -> list[dict[str, Any]]:
    details = []
    for query_index, query in enumerate(_test_assertion_queries(test), start=1):
        try:
            count = int(connection.execute(_row_count_sql(query)).fetchone()[0])
            details.append(_row_count_assertion_detail(test, query_index, query, count))
        except sqlite3.Error as exc:
            details.append(
                {
                    "query_index": query_index,
                    "query": _short_sql(query),
                    "passed": False,
                    "error_type": "assertion_query_error",
                    "error_message": str(exc),
                }
            )
    return details


def _run_duckdb_row_assertions(connection: Any, test: dict[str, Any]) -> list[dict[str, Any]]:
    details = []
    for query_index, query in enumerate(_test_assertion_queries(test), start=1):
        try:
            count = int(connection.execute(_row_count_sql(query)).fetchone()[0])
            details.append(_row_count_assertion_detail(test, query_index, query, count))
        except Exception as exc:
            details.append(
                {
                    "query_index": query_index,
                    "query": _short_sql(query),
                    "passed": False,
                    "error_type": "assertion_query_error",
                    "error_message": str(exc),
                }
            )
    return details


def _row_count_assertion_detail(
    test: dict[str, Any],
    query_index: int,
    query: str,
    actual_count: int,
) -> dict[str, Any]:
    expected = _optional_int(
        test.get("expected_row_count", test.get("expected_rows", test.get("row_count")))
    )
    min_count = _optional_int(test.get("min_row_count"))
    max_count = _optional_int(test.get("max_row_count"))
    passed = True
    if expected is not None:
        passed = actual_count == expected
    if min_count is not None:
        passed = passed and actual_count >= min_count
    if max_count is not None:
        passed = passed and actual_count <= max_count
    return {
        "query_index": query_index,
        "query": _short_sql(query),
        "passed": passed,
        "actual_row_count": actual_count,
        "expected_row_count": expected,
        "min_row_count": min_count,
        "max_row_count": max_count,
    }


def _row_count_sql(query: str) -> str:
    return f"SELECT COUNT(*) FROM ({_strip_trailing_semicolon(query)}) AS dbgenie_count_wrapper;"


def _strip_trailing_semicolon(query: str) -> str:
    return str(query or "").strip().rstrip(";").strip()


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "unique"}


def _short_sql(sql: str, limit: int = 240) -> str:
    text = " ".join(str(sql or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _lint_ddl_static(ddl: str, dialect: str) -> dict[str, Any]:
    errors = []
    warnings = []
    lowered = ddl.lower()
    if not ddl.strip():
        errors.append("DDL is empty.")
    if "create table" not in lowered:
        errors.append("DDL does not contain CREATE TABLE.")
    if ddl.count("(") != ddl.count(")"):
        errors.append("DDL appears to have unbalanced parentheses.")
    if ddl.strip() and not ddl.rstrip().endswith(";"):
        warnings.append("DDL does not end with a semicolon.")

    checks = _dialect_lint_checks(dialect)
    for pattern, message in checks.get("errors", []):
        if re.search(pattern, ddl, flags=re.IGNORECASE):
            errors.append(message)
    for pattern, message in checks.get("warnings", []):
        if re.search(pattern, ddl, flags=re.IGNORECASE):
            warnings.append(message)
    return {
        "executor": "static_dialect_linter",
        "dialect": dialect,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _dialect_lint_checks(dialect: str) -> dict[str, list[tuple[str, str]]]:
    if dialect == "postgresql":
        return {
            "errors": [
                (r"\bAUTO_INCREMENT\b", "PostgreSQL does not support AUTO_INCREMENT."),
                (r"\bIDENTITY\s*\(\s*1\s*,\s*1\s*\)", "PostgreSQL does not use IDENTITY(1,1)."),
                (r"`[^`]+`", "PostgreSQL identifiers should not use MySQL backticks."),
                (r"\bENGINE\s*=", "PostgreSQL does not support MySQL ENGINE clauses."),
                (r"\bUNSIGNED\b", "PostgreSQL does not support MySQL UNSIGNED integer syntax."),
            ],
            "warnings": [],
        }
    if dialect in {"mysql", "mariadb"}:
        return {
            "errors": [
                (r"\bSERIAL\s+PRIMARY\s+KEY\b", "MySQL/MariaDB should use AUTO_INCREMENT for portable generated keys."),
                (r"\bIDENTITY\s*\(\s*1\s*,\s*1\s*\)", "MySQL/MariaDB do not use SQL Server IDENTITY(1,1)."),
                (r"\bRETURNING\b", "MySQL/MariaDB DDL should not contain PostgreSQL RETURNING syntax."),
                (r"\"[A-Za-z_][A-Za-z0-9_]*\"", "MySQL/MariaDB identifiers should not rely on double quotes."),
            ],
            "warnings": [
                (r"\bBOOLEAN\b", "MySQL/MariaDB BOOLEAN is an alias for TINYINT(1)."),
            ],
        }
    if dialect == "sqlserver":
        return {
            "errors": [
                (r"\bAUTO_INCREMENT\b", "SQL Server uses IDENTITY, not AUTO_INCREMENT."),
                (r"\bSERIAL\b", "SQL Server does not support PostgreSQL SERIAL."),
                (r"`[^`]+`", "SQL Server identifiers should not use MySQL backticks."),
                (r"\bLIMIT\s+\d+", "SQL Server uses TOP/OFFSET rather than LIMIT."),
                (r"\bRETURNING\b", "SQL Server uses OUTPUT rather than PostgreSQL RETURNING."),
            ],
            "warnings": [
                (r"\bBOOLEAN\b", "SQL Server normally uses BIT rather than BOOLEAN."),
            ],
        }
    if dialect == "sqlite":
        return {
            "errors": [
                (r"\bIDENTITY\s*\(\s*1\s*,\s*1\s*\)", "SQLite does not support IDENTITY(1,1)."),
                (r"\bENGINE\s*=", "SQLite does not support MySQL ENGINE clauses."),
            ],
            "warnings": [
                (r"\bSERIAL\b", "SQLite does not have a native SERIAL type."),
            ],
        }
    if dialect == "duckdb":
        return {
            "errors": [
                (r"\bAUTO_INCREMENT\b", "DuckDB does not support MySQL AUTO_INCREMENT syntax."),
                (r"\bENGINE\s*=", "DuckDB does not support MySQL ENGINE clauses."),
            ],
            "warnings": [],
        }
    return {"errors": [], "warnings": []}


def _query_plan_report(
    *,
    executor: str,
    dialect: str,
    real_execution: bool,
    stub: bool,
    runtime_version: str,
    test_count: int,
    observations: list[dict[str, Any]],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "tool_type": "query_plan_tool",
        "mode": "raw_evidence",
        "executor": executor,
        "real_execution": real_execution,
        "stub": stub,
        "dialect": dialect,
        "runtime_version": runtime_version,
        "test_count": test_count,
        "query_count": len(observations),
        "observations": observations,
        "warnings": warnings or [],
    }


def _query_plan_observation(
    test: dict[str, Any],
    *,
    test_index: int,
    query_index: int,
    query: str,
    status: str,
    plan: str = "",
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "test_id": str(test.get("id") or f"t{test_index}"),
        "test_index": test_index,
        "query_index": query_index,
        "query": _short_sql(query),
        "status": status,
    }
    input_metadata = _query_plan_input_metadata(test)
    if input_metadata:
        observation["input_metadata"] = input_metadata
    if status == "executed":
        observation["plan"] = str(plan or "")[:4000]
    else:
        observation["error_type"] = error_type
        observation["error_message"] = error_message
    return observation


def _query_plan_input_metadata(test: dict[str, Any]) -> dict[str, Any]:
    metadata = {}
    if "expected_index" in test:
        metadata["expected_index"] = test.get("expected_index")
    elif "index" in test:
        metadata["index"] = test.get("index")
    elif "index_name" in test:
        metadata["index_name"] = test.get("index_name")
    if "require_index" in test:
        metadata["require_index"] = test.get("require_index")
    elif "expect_index" in test:
        metadata["expect_index"] = test.get("expect_index")
    return metadata


def _run_sqlite_explain(
    ddl: str,
    tests: list[dict[str, Any]],
    *,
    test_count: int | None = None,
) -> dict[str, Any]:
    observations = []
    warnings = []
    for index, test in enumerate(tests, start=1):
        connection = None
        try:
            connection = sqlite3.connect(":memory:")
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.executescript(ddl)
            for statement in _test_setup_statements(test):
                connection.executescript(statement)
            for query_index, query in enumerate(_test_explain_queries(test), start=1):
                rows = connection.execute(
                    f"EXPLAIN QUERY PLAN {_strip_trailing_semicolon(query)}"
                ).fetchall()
                plan_text = "\n".join(" | ".join(str(part) for part in row) for row in rows)
                observations.append(
                    _query_plan_observation(
                        test,
                        test_index=index,
                        query_index=query_index,
                        query=query,
                        status="executed",
                        plan=plan_text,
                    )
                )
        except sqlite3.Error as exc:
            warnings.append(f"SQLite EXPLAIN failed for {test.get('id') or f't{index}'}.")
            queries = _test_explain_queries(test) or [""]
            for query_index, query in enumerate(queries, start=1):
                observations.append(
                    _query_plan_observation(
                        test,
                        test_index=index,
                        query_index=query_index,
                        query=query,
                        status="execution_error",
                        error_type="explain_execution_error",
                        error_message=str(exc),
                    )
                )
        finally:
            if connection is not None:
                connection.close()
    return _query_plan_report(
        executor="sqlite_explain",
        dialect="sqlite",
        real_execution=True,
        stub=False,
        runtime_version=f"sqlite {sqlite3.sqlite_version}",
        test_count=test_count if test_count is not None else len(tests),
        observations=observations,
        warnings=warnings,
    )


def _run_duckdb_explain(
    ddl: str,
    tests: list[dict[str, Any]],
    *,
    test_count: int | None = None,
) -> dict[str, Any] | None:
    if importlib.util.find_spec("duckdb") is None:
        return None
    import duckdb
    runtime_version = f"duckdb {getattr(duckdb, '__version__', '')}".strip()

    observations = []
    warnings = []
    for index, test in enumerate(tests, start=1):
        connection = None
        try:
            connection = duckdb.connect(database=":memory:")
            connection.execute(ddl)
            for statement in _test_setup_statements(test):
                connection.execute(statement)
            for query_index, query in enumerate(_test_explain_queries(test), start=1):
                rows = connection.execute(f"EXPLAIN {_strip_trailing_semicolon(query)}").fetchall()
                plan_text = "\n".join(" | ".join(str(part) for part in row) for row in rows)
                observations.append(
                    _query_plan_observation(
                        test,
                        test_index=index,
                        query_index=query_index,
                        query=query,
                        status="executed",
                        plan=plan_text,
                    )
                )
        except Exception as exc:
            warnings.append(f"DuckDB EXPLAIN failed for {test.get('id') or f't{index}'}.")
            queries = _test_explain_queries(test) or [""]
            for query_index, query in enumerate(queries, start=1):
                observations.append(
                    _query_plan_observation(
                        test,
                        test_index=index,
                        query_index=query_index,
                        query=query,
                        status="execution_error",
                        error_type="explain_execution_error",
                        error_message=str(exc),
                    )
                )
        finally:
            if connection is not None:
                connection.close()
    return _query_plan_report(
        executor="duckdb_explain",
        dialect="duckdb",
        real_execution=True,
        stub=False,
        runtime_version=runtime_version,
        test_count=test_count if test_count is not None else len(tests),
        observations=observations,
        warnings=warnings,
    )


def _static_explain_check(
    tests: list[dict[str, Any]],
    *,
    test_count: int | None = None,
    dialect: str = "",
) -> dict[str, Any]:
    observations = []
    for index, test in enumerate(tests, start=1):
        for query_index, query in enumerate(_test_explain_queries(test), start=1):
            observations.append(
                _query_plan_observation(
                    test,
                    test_index=index,
                    query_index=query_index,
                    query=query,
                    status="not_executed",
                    error_type="static_fallback",
                    error_message="EXPLAIN not executed; raw query-plan evidence is unavailable.",
                )
            )
    return _query_plan_report(
        executor="static_explain_check",
        dialect=dialect,
        real_execution=False,
        stub=True,
        runtime_version=_static_runtime_version(dialect),
        test_count=test_count if test_count is not None else len(tests),
        observations=observations,
        warnings=["EXPLAIN not executed; static fallback cannot collect query-plan evidence."],
    )


def _query_plan_not_executed(
    tests: list[dict[str, Any]],
    *,
    test_count: int,
    dialect: str,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    observations = []
    for index, test in enumerate(tests, start=1):
        for query_index, query in enumerate(_test_explain_queries(test), start=1):
            observations.append(
                _query_plan_observation(
                    test,
                    test_index=index,
                    query_index=query_index,
                    query=query,
                    status="not_executed",
                    error_type=error_type,
                    error_message=error_message,
                )
            )
    return _query_plan_report(
        executor="query_plan_not_executed",
        dialect=dialect,
        real_execution=False,
        stub=False,
        runtime_version="",
        test_count=test_count,
        observations=observations,
        warnings=[error_message],
    )


def _evaluate_explain_plan(
    test: dict[str, Any],
    plan_text: str,
    physical_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    expected = _expected_index_name(test, physical_plan)
    plan_text = str(plan_text or "")
    plan_lower = plan_text.lower()
    expected_present = bool(expected) and expected.lower() in plan_lower
    index_access_observed = _plan_has_index_access(plan_text)
    uses_index = expected_present or (index_access_observed and not expected)
    if expected and not uses_index:
        uses_index = _plan_has_acceptable_expected_index_substitute(plan_text, expected)
    requires_index = bool(expected) or _bool_value(test.get("require_index") or test.get("expect_index"))
    warnings = []
    if requires_index and not uses_index:
        warnings.append("Expected index usage was not observed in the query plan.")
    elif expected and index_access_observed and not expected_present:
        warnings.append(
            "Expected index name was not present, but the database used an index access path."
        )
    return {
        "passed": not requires_index or uses_index,
        "uses_index": uses_index,
        "expected_index": expected,
        "warnings": warnings,
    }


def _expected_index_name(
    test: dict[str, Any],
    physical_plan: dict[str, Any] | None,
) -> str:
    explicit = test.get("expected_index") or test.get("index") or test.get("index_name")
    if explicit:
        return str(explicit)
    queries = " ".join(_test_explain_queries(test)).lower()
    for item in _physical_plan_indexes(physical_plan):
        name = str(item.get("name") or item.get("index_name") or "")
        table = str(item.get("table") or item.get("table_name") or "").lower()
        columns = [str(column).lower() for column in _sql_list(item.get("columns"))]
        if name and table and table in queries and columns and all(column in queries for column in columns):
            return name
    return ""


def _plan_has_index_access(plan_text: str) -> bool:
    plan_lower = str(plan_text or "").lower()
    if any(token in plan_lower for token in ("index seek", "index scan", "bitmap index")):
        return True
    if re.search(r"\bindex\b", plan_lower) and re.search(r"\b(seek|scan)\b", plan_lower):
        return True
    return _mysql_explain_used_key(plan_text)


def _mysql_explain_used_key(plan_text: str) -> bool:
    lines = [line for line in str(plan_text or "").splitlines() if line.strip()]
    if not lines:
        return False
    header_index = -1
    headers: list[str] = []
    for index, line in enumerate(lines):
        parts = line.split("\t")
        lowered = [part.strip().lower() for part in parts]
        if "key" in lowered and "possible_keys" in lowered:
            header_index = index
            headers = lowered
            break
    if header_index < 0:
        return False
    try:
        key_index = headers.index("key")
    except ValueError:
        return False
    for line in lines[header_index + 1 :]:
        parts = line.split("\t")
        if len(parts) <= key_index:
            continue
        key_value = parts[key_index].strip()
        if key_value and key_value.upper() != "NULL":
            return True
    return False


def _plan_has_acceptable_expected_index_substitute(plan_text: str, expected: str) -> bool:
    if not _plan_has_index_access(plan_text):
        return False
    plan_text = str(plan_text or "")
    expected_lower = expected.lower()
    # SQL Server may satisfy a planned unique lookup with an auto-named UNIQUE
    # constraint index instead of the LLM-proposed physical index name.
    if "uq__" in plan_text.lower() and any(
        token in expected_lower for token in ("unique", "uq_", "_player_id", "mapper")
    ):
        return True
    for used in _plan_index_names(plan_text):
        if _index_names_are_compatible(used, expected):
            return True
    return False


def _plan_index_names(plan_text: str) -> list[str]:
    names: list[str] = []
    patterns = [
        r"\b(?:Bitmap\s+)?Index\s+Scan\s+(?:using|on)\s+\"?([A-Za-z_][\w$]*)\"?",
        r"\bIndex\s+Seek\s*\(\s*OBJECT:\s*\(\[[^\]]+\]\.\[[^\]]+\]\.\[([^\]]+)\]",
        r"\bIndex\s+Scan\s*\(\s*OBJECT:\s*\(\[[^\]]+\]\.\[[^\]]+\]\.\[([^\]]+)\]",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, str(plan_text or ""), flags=re.IGNORECASE):
            names.append(match.group(1))
    names.extend(_mysql_explain_key_names(plan_text))
    seen = set()
    result = []
    for name in names:
        normalized = clean_identifier(name).lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(name)
    return result


def _mysql_explain_key_names(plan_text: str) -> list[str]:
    lines = [line for line in str(plan_text or "").splitlines() if line.strip()]
    if not lines:
        return []
    for index, line in enumerate(lines):
        parts = line.split("\t")
        headers = [part.strip().lower() for part in parts]
        if "key" not in headers or "possible_keys" not in headers:
            continue
        key_index = headers.index("key")
        names = []
        for row in lines[index + 1 :]:
            values = row.split("\t")
            if len(values) <= key_index:
                continue
            key_value = values[key_index].strip()
            if key_value and key_value.upper() != "NULL":
                names.append(key_value)
        return names
    return []


def _index_names_are_compatible(used: str, expected: str) -> bool:
    used_tokens = _index_name_tokens(used)
    expected_tokens = _index_name_tokens(expected)
    if not used_tokens or not expected_tokens:
        return False
    used_text = "_".join(used_tokens)
    expected_text = "_".join(expected_tokens)
    if used_text == expected_text:
        return True
    if expected_text in used_text:
        return True
    expected_core = _drop_index_prefix_tokens(expected_tokens)
    used_core = _drop_index_prefix_tokens(used_tokens)
    if used_core == expected_core:
        return True
    if used_core and expected_core and "_".join(expected_core) in "_".join(used_core):
        return True
    if used_core and expected_core:
        expected_set = set(expected_core)
        used_set = set(used_core)
        if expected_set and expected_set.issubset(used_set):
            return True
        if _tokens_are_acknowledgement_equivalent(used_set, expected_set):
            return True
    return False


def _index_name_tokens(name: str) -> list[str]:
    cleaned = clean_identifier(name).lower()
    return [token for token in re.split(r"[^a-z0-9]+", cleaned) if token and not token.isdigit()]


def _drop_index_prefix_tokens(tokens: list[str]) -> list[str]:
    result = list(tokens)
    while result and result[0] in {"idx", "ix", "index"}:
        result.pop(0)
    return result


def _tokens_are_acknowledgement_equivalent(
    used_tokens: set[str],
    expected_tokens: set[str],
) -> bool:
    if "unacknowledged" not in used_tokens or "acknowledged" not in expected_tokens:
        return False
    comparable_expected = expected_tokens - {"acknowledged", "user", "id"}
    comparable_used = used_tokens - {"unacknowledged", "generated", "at", "date", "created"}
    return bool(comparable_expected) and comparable_expected.issubset(comparable_used)


def _physical_plan_indexes(physical_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(physical_plan, dict):
        return []
    plan = physical_plan.get("physical_plan")
    if isinstance(plan, dict):
        indexes = plan.get("indexes") or []
    elif isinstance(plan, list):
        indexes = plan
    else:
        indexes = physical_plan.get("indexes") or []
    return [item for item in indexes if isinstance(item, dict)]


def _execute_duckdb_ddl(ddl: str) -> DDLExecutionResult | None:
    if importlib.util.find_spec("duckdb") is None:
        return None
    import duckdb
    runtime_version = f"duckdb {getattr(duckdb, '__version__', '')}".strip()

    connection = None
    try:
        connection = duckdb.connect(database=":memory:")
        connection.execute(ddl)
        row = connection.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'main';"
        ).fetchone()
        table_count = int(row[0]) if row else None
    except Exception as exc:
        return DDLExecutionResult(
            success=False,
            error_type="duckdb_execution_error",
            error_message=str(exc),
            executor="duckdb_memory",
            real_execution=True,
            dialect="duckdb",
            runtime_version=runtime_version,
        )
    finally:
        if connection is not None:
            connection.close()
    return DDLExecutionResult(
        success=True,
        executor="duckdb_memory",
        real_execution=True,
        dialect="duckdb",
        table_count_runtime=table_count,
        runtime_version=runtime_version,
    )


def _run_duckdb_generated_tests(
    ddl: str,
    tests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if importlib.util.find_spec("duckdb") is None:
        return None
    import duckdb
    runtime_version = f"duckdb {getattr(duckdb, '__version__', '')}".strip()

    details = []
    for index, test in enumerate(tests, start=1):
        connection = None
        expect_success = _test_expect_success(test)
        try:
            connection = duckdb.connect(database=":memory:")
            connection.execute(ddl)
            statements = _test_setup_statements(test)
            try:
                for statement in statements:
                    connection.execute(statement)
                detail = _execution_detail_from_success(index, test, expect_success)
                if expect_success:
                    detail["assertions"] = _run_duckdb_row_assertions(connection, test)
                    if any(not item.get("passed", False) for item in detail["assertions"]):
                        detail["passed"] = False
                        detail["error_type"] = "assertion_failed"
                details.append(detail)
            except Exception as exc:
                details.append(
                    _execution_detail_from_exception(
                        index,
                        test,
                        exc,
                        expect_success,
                        "duckdb_execution_error",
                    )
                )
        except Exception as exc:
            details.append(
                {
                    "index": index,
                    "id": test.get("id") or f"t{index}",
                    "passed": False,
                    "expected_success": expect_success,
                    "error_type": "duckdb_setup_error",
                    "error_message": str(exc),
                }
            )
        finally:
            if connection is not None:
                connection.close()
    return {
        "executor": "duckdb_memory",
        "real_execution": True,
        "runtime_version": runtime_version,
        "test_count": len(tests),
        "sql_test_count": len(tests),
        "passed": all(item.get("passed") for item in details),
        "details": details,
    }


def _static_ddl_check(
    ddl: str,
    dialect: str,
    warnings: list[str] | None = None,
) -> DDLExecutionResult:
    success = bool(ddl.strip()) and "create table" in ddl.lower()
    return DDLExecutionResult(
        success=success,
        error_type="" if success else "no_create_table",
        error_message=(
            "Static DDL check passed."
            if success
            else "DDL executor requires at least one CREATE TABLE statement."
        ),
        executor="static_ddl_check",
        real_execution=False,
        dialect=dialect,
        runtime_version=_static_runtime_version(dialect),
        warnings=warnings or [],
    )


def _unsupported_real_ddl_execution(dialect: str) -> DDLExecutionResult:
    return DDLExecutionResult(
        success=False,
        error_type="unsupported_real_execution",
        error_message=f"Real DDL execution is not available for dialect: {dialect or 'unknown'}.",
        executor="ddl_execution_not_available",
        real_execution=False,
        dialect=dialect,
        runtime_version="",
        warnings=["Static DDL fallback is disabled for dynamic method verification."],
    )


def _static_generated_test_check(
    tests: list[dict[str, Any]],
    sql_tests: list[dict[str, Any]],
    dialect: str,
) -> dict[str, Any]:
    return {
        "executor": "static_generated_test_check",
        "real_execution": False,
        "stub": True,
        "runtime_version": _static_runtime_version(dialect),
        "test_count": len(tests),
        "sql_test_count": len(sql_tests),
        "passed": True,
        "details": [],
    }


def _generated_tests_not_executed(
    tests: list[dict[str, Any]],
    sql_tests: list[dict[str, Any]],
    dialect: str,
    *,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    return {
        "executor": "sql_test_runner_not_executed",
        "real_execution": False,
        "stub": False,
        "runtime_version": "",
        "test_count": len(tests),
        "sql_test_count": len(sql_tests),
        "passed": False,
        "details": [],
        "error_type": error_type,
        "error_message": error_message,
        "warnings": [error_message],
    }


def _static_runtime_version(dialect: str) -> str:
    if dialect == "sqlite":
        return f"sqlite {sqlite3.sqlite_version}"
    if dialect == "duckdb" and importlib.util.find_spec("duckdb") is not None:
        import duckdb

        return f"duckdb {getattr(duckdb, '__version__', '')}".strip()
    return ""


def _combine_sql_script(parts: list[str], *, dialect: str = "") -> str:
    statements = []
    for part in parts:
        text = str(part or "").strip()
        if not text:
            continue
        if text.endswith(";") or _ends_with_sqlserver_go(text, dialect):
            statements.append(text)
        else:
            statements.append(f"{text};")
    return "\n\n".join(statements) + ("\n" if statements else "")


def _ends_with_sqlserver_go(text: str, dialect: str) -> bool:
    if normalize_dialect(dialect) != "sqlserver":
        return False
    for line in reversed(str(text or "").splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        return re.fullmatch(r"(?i)GO(?:\s+\d+)?", stripped) is not None
    return False


def _sqlserver_nocount_query(query: str) -> str:
    stripped = str(query or "").lstrip()
    if stripped.lower().startswith("set nocount on"):
        return query
    return f"SET NOCOUNT ON; {query}"


def _sqlserver_showplan_script(query: str) -> str:
    clean_query = _strip_trailing_semicolon(query)
    return (
        "SET NOCOUNT ON;\n"
        "GO\n"
        "SET SHOWPLAN_TEXT ON;\n"
        "GO\n"
        f"{clean_query};\n"
        "GO\n"
        "SET SHOWPLAN_TEXT OFF;\n"
        "GO\n"
    )


def _database_name(seed: str) -> str:
    # Each DBMS has its own container, and same-dialect executions are serialized.
    # Reusing one scratch database prevents every DDL revision and generated test
    # from leaving another permanent database in the container data directory.
    del seed
    return "t2d_runtime"


def _last_int(text: str) -> int | None:
    for line in reversed(str(text or "").splitlines()):
        if re.search(r"\(\s*\d+\s+rows?\s+affected\s*\)", line, re.IGNORECASE):
            continue
        numbers = re.findall(r"\d+", line)
        if numbers:
            return int(numbers[-1])
    return None


def _command_error(cp: Any) -> str:
    message = str(getattr(cp, "stderr", "") or getattr(cp, "stdout", "") or "").strip()
    if message:
        return message[-4000:]
    args = getattr(cp, "args", "")
    if isinstance(args, list):
        command = " ".join(str(item) for item in args)
    else:
        command = str(args)
    return f"command failed: {command}".strip()


def _run_process(
    cmd: list[str],
    input_text: str | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
