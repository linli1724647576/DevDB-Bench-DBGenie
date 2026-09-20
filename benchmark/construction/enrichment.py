from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from dbgenie.core.config import DatasetConfig, GitHubConfig

from .filters import NON_PRIMARY_PATH_PARTS
from .github import GitHubAPIError, GitHubClient
from .screening import DIALECT_KEYWORDS, DOMAIN_KEYWORDS, ECOSYSTEM_KEYWORDS


MANIFEST_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "gemfile",
    "composer.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    ".csproj",
    "go.mod",
    "cargo.toml",
}

README_HINTS = ("readme",)
SCHEMA_HINTS = (
    "schema.sql",
    "structure.sql",
    "schema.prisma",
    "migration.sql",
    "db/schema.rb",
    "db/structure.sql",
    "models.py",
    ".entity.ts",
    "dbcontext.cs",
    "pom.xml",
    "composer.json",
    "package.json",
)

DBMS_CONFIG_HINTS = (
    "database.yml",
    "database.yaml",
    "config/database.php",
    "settings.py",
    "settings/base.py",
    "settings/dev.py",
    "settings/production.py",
    "alembic.ini",
    "env.py",
    "appsettings.json",
    "appsettings.development.json",
    ".env.example",
    ".env.sample",
    "docker-compose.yml",
    "docker-compose.yaml",
)

DOMAIN_CONTENT_KEYWORDS = {
    **DOMAIN_KEYWORDS,
    "payment_billing": (*DOMAIN_KEYWORDS["payment_billing"], "checkout", "refund", "plan"),
    "education": (*DOMAIN_KEYWORDS["education"], "student", "teacher", "quiz", "assignment"),
    "healthcare": (*DOMAIN_KEYWORDS["healthcare"], "patient", "doctor"),
    "inventory": (*DOMAIN_KEYWORDS["inventory"], "sku", "supplier"),
}

ECOSYSTEM_CONTENT_KEYWORDS = {
    **ECOSYSTEM_KEYWORDS,
    "Flask": ("from flask", "import flask", "flask_sqlalchemy"),
    "Django": ("django", "django.db", "models.model"),
    "FastAPI": ("fastapi", "sqlmodel", "pydantic"),
    "Rails": ("rails", "activerecord", "create_table"),
    "Laravel": ("laravel", "illuminate\\", "artisan", "eloquent"),
    "Spring Boot": ("spring-boot", "springframework", "jakarta.persistence", "@entity"),
    ".NET EF Core": ("entityframeworkcore", "dbcontext", "migrationbuilder"),
    "Next.js + Prisma": ("next", "nextjs", "prisma/client", "schema.prisma"),
    "NestJS": ("nestjs", "@nestjs", "typeorm", "prisma/client"),
    "GORM": ("gorm.io/gorm", "gorm.model"),
    "Ent": ("entgo.io/ent", "ent/schema"),
}


@dataclass(frozen=True)
class EnrichmentResult:
    domain: str
    ecosystem: str
    dialect: str
    dbms: str = "unknown"
    schema_artifact: str = "unknown"
    downloaded_files: list[str] = field(default_factory=list)
    evidence: dict[str, list[str]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class CandidateEnricher:
    def __init__(self, github_config: GitHubConfig, dataset_config: DatasetConfig) -> None:
        self.github = GitHubClient(github_config)
        self.dataset_config = dataset_config

    def enrich(self, candidate: dict[str, Any]) -> EnrichmentResult:
        full_name = candidate["full_name"]
        errors: list[str] = []
        try:
            paths = self.github.list_tree_paths(full_name)
        except GitHubAPIError as exc:
            return EnrichmentResult(
                domain=candidate.get("domain_guess", "unknown"),
                ecosystem=candidate.get("ecosystem_guess", "unknown"),
                dialect=candidate.get("dialect_guess", "unknown"),
                dbms=_dbms_from_legacy_label(candidate.get("dialect_guess", "unknown")),
                schema_artifact=_schema_artifact_from_legacy_label(candidate.get("dialect_guess", "unknown")),
                errors=[str(exc)],
            )

        selected_paths = self._select_paths(paths)
        contents: list[tuple[str, str]] = []
        for path in selected_paths:
            try:
                repo_file = self.github.download_file(full_name, path)
            except GitHubAPIError as exc:
                errors.append(f"{path}: {exc}")
                continue
            if repo_file.size > self.dataset_config.max_file_bytes:
                continue
            contents.append((path, repo_file.content[:20000]))

        text = self._combined_text(candidate, paths, contents)
        domain, domain_evidence = self._classify(text, DOMAIN_CONTENT_KEYWORDS)
        ecosystem, ecosystem_evidence = self._classify(text, ECOSYSTEM_CONTENT_KEYWORDS)
        dialect, dialect_evidence = self._classify_dialect(text)
        dbms, dbms_evidence = self._classify_dbms(text)
        schema_artifact, schema_artifact_evidence = self._classify_schema_artifact(text)

        return EnrichmentResult(
            domain=domain or candidate.get("domain_guess", "unknown"),
            ecosystem=ecosystem or candidate.get("ecosystem_guess", "unknown"),
            dialect=dialect or candidate.get("dialect_guess", "unknown"),
            dbms=dbms or _dbms_from_legacy_label(candidate.get("dialect_guess", "unknown")),
            schema_artifact=(
                schema_artifact
                or _schema_artifact_from_legacy_label(candidate.get("dialect_guess", "unknown"))
            ),
            downloaded_files=[path for path, _ in contents],
            evidence={
                "domain": domain_evidence,
                "ecosystem": ecosystem_evidence,
                "dialect": dialect_evidence,
                "dbms": dbms_evidence,
                "schema_artifact": schema_artifact_evidence,
            },
            errors=errors[:10],
        )

    def _select_paths(self, paths: list[str]) -> list[str]:
        primary_paths = [path for path in paths if self._is_primary_path(path)]
        scored: list[tuple[int, str]] = []
        for path in primary_paths:
            lower = path.lower()
            filename = lower.rsplit("/", 1)[-1]
            depth = lower.count("/")
            score = 0
            if any(hint in filename for hint in README_HINTS):
                score += 100 - min(depth, 8)
            if (filename in MANIFEST_FILES or filename.endswith(".csproj")) and depth <= 2:
                score += 90 - depth
            if filename in DBMS_CONFIG_HINTS or any(hint in lower for hint in DBMS_CONFIG_HINTS):
                score += 95 - min(depth, 8)
            if any(hint in lower for hint in SCHEMA_HINTS):
                score += 80
            if "migration" in lower or "migrations/" in lower:
                score += 50
            if score:
                scored.append((score, path))
        scored.sort(reverse=True)
        limit = 14
        return [path for _, path in scored[:limit]]

    @staticmethod
    def _is_primary_path(path: str) -> bool:
        parts = set(path.lower().split("/"))
        return not bool(parts & NON_PRIMARY_PATH_PARTS)

    @staticmethod
    def _combined_text(
        candidate: dict[str, Any],
        paths: list[str],
        contents: list[tuple[str, str]],
    ) -> str:
        pieces = [
            candidate.get("full_name", ""),
            candidate.get("query", ""),
            candidate.get("domain_guess", ""),
            candidate.get("ecosystem_guess", ""),
            candidate.get("dialect_guess", ""),
            " ".join(paths[:1000]),
        ]
        for path, content in contents:
            pieces.append(path)
            pieces.append(content)
        return "\n".join(pieces).lower()

    @staticmethod
    def _classify(text: str, keyword_map: dict[str, tuple[str, ...]]) -> tuple[str, list[str]]:
        scores: Counter[str] = Counter()
        evidence: dict[str, list[str]] = {}
        for label, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[label] += 1
                    evidence.setdefault(label, []).append(keyword)
        if not scores:
            return "", []
        label, _ = scores.most_common(1)[0]
        return label, evidence.get(label, [])[:8]

    @staticmethod
    def _classify_dialect(text: str) -> tuple[str, list[str]]:
        special = {
            "Prisma ecosystem": ("schema.prisma", "prisma/migrations", "@prisma/client"),
            "Rails migration ecosystem": ("db/migrate", "create_table", "activerecord"),
            "Alembic ecosystem": ("alembic", "op.create_table"),
            "Liquibase ecosystem": ("liquibase",),
            "Flyway ecosystem": ("flyway",),
        }
        scores: Counter[str] = Counter()
        evidence: dict[str, list[str]] = {}
        for label, keywords in {**special, **DIALECT_KEYWORDS}.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[label] += 1
                    evidence.setdefault(label, []).append(keyword)
        if not scores:
            return "", []
        label, _ = scores.most_common(1)[0]
        return label, evidence.get(label, [])[:8]

    @staticmethod
    def _classify_schema_artifact(text: str) -> tuple[str, list[str]]:
        patterns = {
            "Prisma schema": ("schema.prisma", "prisma/migrations", "@prisma/client"),
            "Rails migration": ("db/migrate", "activerecord::migration"),
            "Alembic migration": ("alembic.ini", "alembic/versions", "op.create_table"),
            "Django ORM models": ("django.db", "models.model"),
            "Laravel migration": ("database/migrations", "illuminate\\database\\migrations"),
            "EF Core migration": ("migrationbuilder", "dbcontextmodelsnapshot"),
            "TypeORM entity/migration": ("typeorm", ".entity.ts", "createquerybuilder"),
            "Sequelize model/migration": ("sequelize", "queryinterface.createtable"),
            "SQL DDL file": ("create table", "alter table", "foreign key"),
            "Liquibase changelog": ("liquibase", "databasechangelog"),
            "Flyway migration": ("flyway", "db/migration"),
        }
        return CandidateEnricher._classify(text, patterns)

    @staticmethod
    def _classify_dbms(text: str) -> tuple[str, list[str]]:
        # Ordered from more specific to more general. Evidence intentionally uses
        # DBMS/provider/config tokens, not migration framework names.
        patterns: list[tuple[str, tuple[str, ...]]] = [
            (
                "SQL Server",
                (
                    'provider = "sqlserver"',
                    "provider = 'sqlserver'",
                    "microsoft.entityframeworkcore.sqlserver",
                    "usesqlserver",
                    "jdbc:sqlserver",
                    "sql server",
                    "mssql",
                    "tedious",
                    "django-mssql",
                ),
            ),
            (
                "PostgreSQL",
                (
                    'provider = "postgresql"',
                    "provider = 'postgresql'",
                    "adapter: postgresql",
                    "django.db.backends.postgresql",
                    "postgresql://",
                    "postgres://",
                    "jdbc:postgresql",
                    "db_connection=pgsql",
                    "db_connection = pgsql",
                    "npgsql",
                    "usenpgsql",
                    "psycopg",
                    "asyncpg",
                    "postgresql",
                    "postgres",
                ),
            ),
            (
                "MariaDB",
                (
                    "jdbc:mariadb",
                    "db_connection=mariadb",
                    "db_connection = mariadb",
                    "mariadb",
                ),
            ),
            (
                "MySQL",
                (
                    'provider = "mysql"',
                    "provider = 'mysql'",
                    "adapter: mysql2",
                    "django.db.backends.mysql",
                    "mysql://",
                    "jdbc:mysql",
                    "db_connection=mysql",
                    "db_connection = mysql",
                    "pymysql",
                    "mysqlclient",
                    "pomelo.entityframeworkcore.mysql",
                    "usemysql",
                    "mysql",
                ),
            ),
            (
                "SQLite",
                (
                    'provider = "sqlite"',
                    "provider = 'sqlite'",
                    "adapter: sqlite3",
                    "django.db.backends.sqlite3",
                    "sqlite://",
                    "sqlite:///",
                    "jdbc:sqlite",
                    "db_connection=sqlite",
                    "db_connection = sqlite",
                    "microsoft.entityframeworkcore.sqlite",
                    "usesqlite",
                    "sqlite3.connect",
                    "better-sqlite3",
                    "sqlite",
                ),
            ),
            (
                "Oracle",
                (
                    "jdbc:oracle",
                    "cx_oracle",
                    "oracledb",
                    "django.db.backends.oracle",
                    "oracle.manageddataaccess",
                    "oracle",
                ),
            ),
            (
                "DuckDB",
                (
                    "duckdb.connect",
                    "duckdb://",
                    "duckdb_engine",
                    "import duckdb",
                    "duckdb",
                ),
            ),
        ]
        scores: Counter[str] = Counter()
        evidence: dict[str, list[str]] = {}
        for label, keywords in patterns:
            for keyword in keywords:
                if keyword in text:
                    scores[label] += _dbms_keyword_weight(keyword)
                    evidence.setdefault(label, []).append(keyword)
        if not scores:
            return "", []
        label, _ = scores.most_common(1)[0]
        return label, evidence.get(label, [])[:8]


def _dbms_keyword_weight(keyword: str) -> int:
    if keyword in {"postgres", "postgresql", "mysql", "sqlite", "mariadb", "oracle", "duckdb", "mssql"}:
        return 1
    return 3


def _dbms_from_legacy_label(label: str | None) -> str:
    if label in DIALECT_KEYWORDS:
        return label
    return "unknown"


def _schema_artifact_from_legacy_label(label: str | None) -> str:
    mapping = {
        "Prisma ecosystem": "Prisma schema",
        "Rails migration ecosystem": "Rails migration",
        "Alembic ecosystem": "Alembic migration",
        "Liquibase ecosystem": "Liquibase changelog",
        "Flyway ecosystem": "Flyway migration",
    }
    return mapping.get(label or "", "unknown")
