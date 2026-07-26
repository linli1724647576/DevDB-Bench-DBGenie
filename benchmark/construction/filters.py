from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from dbgenie.core.config import DatasetConfig

from .github import RepositoryMetadata


ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"}

EXCLUDED_KEYWORDS = {
    "demo",
    "tutorial",
    "example",
    "sample",
    "template",
    "boilerplate",
    "starter",
    "skeleton",
    "scaffold",
    "seed",
    "toy",
    "learning",
    "practice",
    "course",
    "workshop",
    "kata",
    "bootcamp",
    "clone",
    "awesome",
    "curated",
    "list",
    "notes",
    "handbook",
    "cheatsheet",
    "snippets",
    "leetcode",
    "algorithm",
    "interview",
    "exercises",
    "教程",
    "示例",
    "样例",
    "模板",
    "入门",
    "练习",
    "笔记",
    "课程",
    "作业",
    "实验",
    "算法",
    "面试",
    "资料汇总",
}

EXCLUDED_REPO_TYPE_KEYWORDS = {
    "framework",
    "library",
    "package",
    "plugin",
    "sdk",
    "cli",
    "starter",
    "generator",
    "scaffold",
    "boilerplate",
}

EXCLUDED_REPO_NAME_KEYWORDS = {
    "typeorm",
    "sequelize",
    "sqlmodel",
    "django",
    "rails",
    "laravel",
    "gorm",
    "prisma",
    "spring-boot",
    "spring-framework",
}

SCHEMA_PATH_HINTS = (
    ".sql",
    "schema.sql",
    "structure.sql",
    "db/migrate/",
    "prisma/schema.prisma",
    "migrations/",
    "models.py",
    ".entity.ts",
    "entity/",
    "liquibase/",
    "flyway/",
    ".hbm.xml",
    ".mapper.xml",
    "dbcontext.cs",
    "ent/schema/",
)

REQUIREMENT_PATH_HINTS = (
    "readme",
    "docs/",
    "doc/",
    "api",
    "controller",
    "route",
    "service",
    "repository",
    "test",
    "fixture",
    "changelog",
)

APPLICATION_STRUCTURE_HINTS = (
    "controller",
    "controllers/",
    "route",
    "routes/",
    "endpoint",
    "api/",
    "server/",
    "backend/",
    "service",
    "services/",
    "repository",
    "repositories/",
    "dao",
    "mapper",
    "views/",
    "pages/",
    "app/",
)

WORKLOAD_PATH_HINTS = (
    "repository",
    "repositories/",
    "dao",
    "mapper",
    "query",
    "queries",
    "controller",
    "routes/",
    "api/",
    "report",
    "reports",
    "search",
    "filter",
)

SCHEMA_COUNT_HINTS = (
    "db/migrate/",
    "migrations/",
    "database/migrations/",
    "alembic/versions/",
    "ent/schema/",
)

NON_PRIMARY_PATH_PARTS = {
    "example",
    "examples",
    "__fixtures__",
    "fixtures",
    "fixture",
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "template",
    "templates",
    "demo",
    "demos",
    "sample",
    "samples",
    "starter",
    "starters",
    "playground",
    "benchmarks",
    ".github",
    ".vscode",
    ".idea",
}


@dataclass(frozen=True)
class FilterDecision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)


class RepositoryFilter:
    def __init__(self, config: DatasetConfig) -> None:
        self.config = config

    def coarse_filter(self, repo: RepositoryMetadata) -> FilterDecision:
        reasons: list[str] = []
        if repo.license_spdx_id not in ALLOWED_LICENSES:
            reasons.append(f"license_not_allowed:{repo.license_spdx_id}")
        if repo.fork:
            reasons.append("is_fork")
        if repo.is_template:
            reasons.append("is_template")
        if repo.archived:
            reasons.append("is_archived")
        if repo.disabled:
            reasons.append("is_disabled")
        if repo.stargazers_count < self.config.min_stars and repo.forks_count < self.config.min_forks:
            reasons.append("insufficient_stars_or_forks")
        if self.config.require_contributors_check and repo.contributors_count < self.config.min_contributors:
            reasons.append("insufficient_contributors")
        if self._is_stale(repo.pushed_at):
            reasons.append("inactive_repository")
        if self._has_excluded_keyword(repo):
            reasons.append("excluded_keyword")
        if self._has_excluded_repo_type(repo):
            reasons.append("likely_library_or_framework")
        return FilterDecision(accepted=not reasons, reasons=reasons)

    def path_filter(self, paths: list[str]) -> FilterDecision:
        normalized = [path.replace("\\", "/").lower() for path in paths]
        primary_paths = [path for path in normalized if self._is_primary_path(path)]
        reasons: list[str] = []
        if not any(self._matches_any(path, SCHEMA_PATH_HINTS) for path in primary_paths):
            reasons.append("missing_schema_artifact")
        if self._schema_artifact_score(primary_paths) < self.config.min_tables:
            reasons.append("insufficient_schema_artifacts")
        if not any(self._matches_any(path, REQUIREMENT_PATH_HINTS) for path in primary_paths):
            reasons.append("missing_requirement_or_workload_evidence")
        if not any(self._matches_any(path, APPLICATION_STRUCTURE_HINTS) for path in primary_paths):
            reasons.append("missing_application_structure")
        if not any(self._matches_any(path, WORKLOAD_PATH_HINTS) for path in primary_paths):
            reasons.append("missing_workload_evidence")
        application_score = self._application_score(primary_paths)
        if application_score < self.config.min_application_score:
            reasons.append(f"low_application_score:{application_score}")
        return FilterDecision(accepted=not reasons, reasons=reasons)

    def _is_stale(self, pushed_at: str) -> bool:
        if not pushed_at:
            return True
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.active_within_days)
        return pushed < cutoff

    def _has_excluded_keyword(self, repo: RepositoryMetadata) -> bool:
        text = " ".join([repo.full_name, repo.description, *repo.topics]).lower()
        return any(keyword.lower() in text for keyword in EXCLUDED_KEYWORDS)

    def _has_excluded_repo_type(self, repo: RepositoryMetadata) -> bool:
        text = " ".join([repo.description, *repo.topics]).lower()
        name = repo.full_name.rsplit("/", 1)[-1].lower()
        return any(keyword in text for keyword in EXCLUDED_REPO_TYPE_KEYWORDS) or name in EXCLUDED_REPO_NAME_KEYWORDS

    @staticmethod
    def _schema_artifact_score(paths: list[str]) -> int:
        score = 0
        for path in paths:
            if any(hint in path for hint in SCHEMA_COUNT_HINTS):
                score += 1
            elif path.endswith(("schema.sql", "structure.sql", "schema.prisma", "models.py", "dbcontext.cs")):
                score += 3
            elif path.endswith((".entity.ts", ".hbm.xml", ".mapper.xml")):
                score += 1
        return score

    @staticmethod
    def _application_score(paths: list[str]) -> int:
        score = 0
        if any("readme" in path for path in paths):
            score += 1
        if any(path.startswith(("docs/", "doc/")) or "/docs/" in path or "/doc/" in path for path in paths):
            score += 1
        if any(hint in path for path in paths for hint in ("controller", "controllers/", "routes/", "api/")):
            score += 1
        if any(hint in path for path in paths for hint in ("service", "services/")):
            score += 1
        if any(hint in path for path in paths for hint in ("repository", "repositories/", "dao", "mapper")):
            score += 1
        if any(hint in path for path in paths for hint in ("test", "fixture")):
            score += 1
        if any(hint in path for path in paths for hint in ("views/", "pages/", "templates/")):
            score += 1
        return score

    @staticmethod
    def _matches_any(path: str, hints: tuple[str, ...]) -> bool:
        return any(hint in path for hint in hints)

    @staticmethod
    def _is_primary_path(path: str) -> bool:
        parts = set(path.split("/"))
        return not bool(parts & NON_PRIMARY_PATH_PARTS)
