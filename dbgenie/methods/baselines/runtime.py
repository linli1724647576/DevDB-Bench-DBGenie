from __future__ import annotations

import importlib.metadata
import re
import sqlite3
from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeDescription:
    version: str
    environment: str

    def to_prompt_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "environment": self.environment,
        }


_FIXED_RUNTIMES: dict[str, RuntimeDescription] = {
    "postgresql": RuntimeDescription(
        version="PostgreSQL 16",
        environment="Docker image postgres:16-alpine",
    ),
    "mysql": RuntimeDescription(
        version="MySQL 8.4",
        environment="Docker image mysql:8.4 with default InnoDB behavior",
    ),
    "mariadb": RuntimeDescription(
        version="MariaDB 11.4",
        environment="Docker image mariadb:11.4",
    ),
    "sqlserver": RuntimeDescription(
        version="SQL Server 2022",
        environment="Docker image mcr.microsoft.com/mssql/server:2022-latest",
    ),
}


def runtime_description(target_dbms: str) -> RuntimeDescription:
    dialect = _normalize_dialect(target_dbms)
    if dialect in _FIXED_RUNTIMES:
        return _FIXED_RUNTIMES[dialect]
    if dialect == "sqlite":
        return RuntimeDescription(
            version=f"SQLite {sqlite3.sqlite_version}",
            environment="Python sqlite3 in-memory database with foreign keys enabled",
        )
    if dialect == "duckdb":
        return RuntimeDescription(
            version=f"DuckDB {_installed_version('duckdb')}",
            environment="Python duckdb package in an in-memory database",
        )
    return RuntimeDescription(
        version=str(target_dbms or "unspecified"),
        environment="No project runtime is configured for this DBMS",
    )


def _normalize_dialect(target_dbms: str) -> str:
    compact = re.sub(r"[^a-z0-9]", "", str(target_dbms or "").lower())
    aliases = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "mysql": "mysql",
        "mariadb": "mariadb",
        "sqlite": "sqlite",
        "sqlite3": "sqlite",
        "duckdb": "duckdb",
        "mssql": "sqlserver",
        "sqlserver": "sqlserver",
        "microsoftsqlserver": "sqlserver",
    }
    return aliases.get(compact, compact)


def _installed_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"
