from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from dbgenie.core.config import DatasetConfig, GitHubConfig

from .filters import RepositoryFilter
from .github import GitHubAPIError, GitHubClient, RepositoryMetadata


DOMAIN_KEYWORDS = {
    "finance": ("finance", "financial", "bank", "banking", "trading", "wallet"),
    "payment_billing": ("payment", "billing", "invoice", "subscription", "stripe"),
    "ecommerce": ("ecommerce", "commerce", "shop", "store", "marketplace", "cart"),
    "education": ("education", "school", "course", "learning", "lms", "classroom"),
    "cms_content": ("cms", "content", "blog", "publishing", "docs", "wiki"),
    "crm_erp": ("crm", "erp", "customer", "sales"),
    "inventory": ("inventory", "warehouse", "stock"),
    "booking": ("booking", "reservation", "appointment", "calendar", "schedule"),
    "healthcare": ("health", "medical", "clinic", "hospital"),
    "forum_community": ("forum", "community", "social", "chat"),
    "analytics": ("analytics", "dashboard", "report", "bi"),
    "collaboration": ("collaboration", "workspace", "project management", "task"),
}

ECOSYSTEM_KEYWORDS = {
    "Django": ("django",),
    "Flask": ("flask",),
    "FastAPI": ("fastapi",),
    "Rails": ("rails", "ruby on rails"),
    "Laravel": ("laravel",),
    "Symfony": ("symfony",),
    "Next.js + Prisma": ("nextjs", "next.js", "prisma"),
    "NestJS": ("nestjs", "nest.js"),
    "Spring Boot": ("spring boot",),
    ".NET EF Core": ("entity framework", "ef core", "asp.net"),
    "GORM": ("gorm",),
    "Ent": ("entgo",),
}

DIALECT_KEYWORDS = {
    "PostgreSQL": ("postgres", "postgresql", "pg"),
    "MySQL": ("mysql",),
    "SQLite": ("sqlite",),
    "SQL Server": ("sql server", "mssql"),
    "Oracle": ("oracle",),
    "MariaDB": ("mariadb",),
    "DuckDB": ("duckdb",),
}


@dataclass(frozen=True)
class RepositoryScreeningRecord:
    repo: RepositoryMetadata
    accepted: bool
    review_status: str = "rejected"
    reasons: list[str] = field(default_factory=list)
    path_count: int = 0
    query: str = ""
    domain_guess: str = "unknown"
    ecosystem_guess: str = "unknown"
    dialect_guess: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_name": self.repo.full_name,
            "url": self.repo.html_url,
            "license": self.repo.license_spdx_id,
            "stars": self.repo.stargazers_count,
            "forks": self.repo.forks_count,
            "contributors": self.repo.contributors_count,
            "pushed_at": self.repo.pushed_at,
            "accepted": self.accepted,
            "review_status": self.review_status,
            "reasons": self.reasons,
            "path_count": self.path_count,
            "query": self.query,
            "domain_guess": self.domain_guess,
            "ecosystem_guess": self.ecosystem_guess,
            "dialect_guess": self.dialect_guess,
        }


@dataclass(frozen=True)
class RepositoryScreeningReport:
    query: str
    scanned: int
    accepted: int
    rejected: int
    review_candidates: int
    reason_counts: dict[str, int]
    records: list[RepositoryScreeningRecord]

    def to_dict(self, include_rejected: bool = True) -> dict[str, Any]:
        records = self.records if include_rejected else [item for item in self.records if item.accepted]
        return {
            "query": self.query,
            "scanned": self.scanned,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "review_candidates": self.review_candidates,
            "acceptance_rate": self.accepted / self.scanned if self.scanned else 0,
            "reason_counts": self.reason_counts,
            "records": [item.to_dict() for item in records],
        }


class RepositoryScreeningPipeline:
    def __init__(self, github_config: GitHubConfig, dataset_config: DatasetConfig) -> None:
        self.github = GitHubClient(github_config)
        self.filter = RepositoryFilter(dataset_config)

    def run(
        self,
        query: str,
        max_repos: int = 50,
        include_tree_filter: bool = True,
    ) -> RepositoryScreeningReport:
        records: list[RepositoryScreeningRecord] = []
        page = 1
        seen: set[str] = set()

        while len(seen) < max_repos:
            repos = self.github.search_repositories(query, page=page)
            if not repos:
                break
            page += 1
            for search_repo in repos:
                if len(seen) >= max_repos:
                    break
                if search_repo.full_name in seen:
                    continue
                seen.add(search_repo.full_name)
                records.append(self._screen_one(search_repo, include_tree_filter, query=query))

        reason_counts: Counter[str] = Counter()
        for record in records:
            for reason in record.reasons:
                reason_counts[reason.split(":", 1)[0]] += 1

        accepted = sum(1 for record in records if record.accepted)
        review_candidates = sum(1 for record in records if record.review_status in {"accepted", "needs_review"})
        return RepositoryScreeningReport(
            query=query,
            scanned=len(records),
            accepted=accepted,
            rejected=len(records) - accepted,
            review_candidates=review_candidates,
            reason_counts=dict(reason_counts),
            records=records,
        )

    def _screen_one(
        self,
        search_repo: RepositoryMetadata,
        include_tree_filter: bool,
        query: str = "",
    ) -> RepositoryScreeningRecord:
        try:
            repo = self.github.get_repository(
                search_repo.full_name,
                include_contributors=self.filter.config.require_contributors_check,
            )
        except GitHubAPIError as exc:
            return RepositoryScreeningRecord(
                repo=search_repo,
                accepted=False,
                review_status="rejected",
                reasons=[f"repo_metadata_error:{exc}"],
                query=query,
            )

        coarse = self.filter.coarse_filter(repo)
        if not coarse.accepted or not include_tree_filter:
            return RepositoryScreeningRecord(
                repo=repo,
                accepted=coarse.accepted,
                review_status="accepted" if coarse.accepted else "rejected",
                reasons=coarse.reasons,
                query=query,
                domain_guess=self._guess_domain(repo, query),
                ecosystem_guess=self._guess_ecosystem(repo, query),
                dialect_guess=self._guess_dialect(repo, query, []),
            )

        try:
            paths = self.github.list_tree_paths(repo.full_name, repo.default_branch)
        except GitHubAPIError as exc:
            return RepositoryScreeningRecord(
                repo=repo,
                accepted=False,
                review_status="rejected",
                reasons=[f"tree_scan_error:{exc}"],
                query=query,
                domain_guess=self._guess_domain(repo, query),
                ecosystem_guess=self._guess_ecosystem(repo, query),
                dialect_guess=self._guess_dialect(repo, query, []),
            )

        path_decision = self.filter.path_filter(paths)
        reasons = [*coarse.reasons, *path_decision.reasons]
        accepted = not reasons
        review_status = "accepted" if accepted else self._review_status(coarse.reasons, path_decision.reasons)
        return RepositoryScreeningRecord(
            repo=repo,
            accepted=accepted,
            review_status=review_status,
            reasons=reasons,
            path_count=len(paths),
            query=query,
            domain_guess=self._guess_domain(repo, query),
            ecosystem_guess=self._guess_ecosystem(repo, query),
            dialect_guess=self._guess_dialect(repo, query, paths),
        )

    @staticmethod
    def _review_status(coarse_reasons: list[str], path_reasons: list[str]) -> str:
        hard_reasons = {
            "license_not_allowed",
            "is_fork",
            "is_template",
            "is_archived",
            "is_disabled",
            "inactive_repository",
            "excluded_keyword",
            "likely_library_or_framework",
            "missing_schema_artifact",
            "insufficient_schema_artifacts",
        }
        reason_keys = {reason.split(":", 1)[0] for reason in [*coarse_reasons, *path_reasons]}
        if reason_keys & hard_reasons:
            return "rejected"
        return "needs_review"

    @staticmethod
    def _repo_text(repo: RepositoryMetadata, query: str) -> str:
        return " ".join([repo.full_name, repo.description, *repo.topics, query]).lower()

    @classmethod
    def _guess_domain(cls, repo: RepositoryMetadata, query: str) -> str:
        text = cls._repo_text(repo, query)
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return domain
        return "unknown"

    @classmethod
    def _guess_ecosystem(cls, repo: RepositoryMetadata, query: str) -> str:
        text = cls._repo_text(repo, query)
        for ecosystem, keywords in ECOSYSTEM_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return ecosystem
        return "unknown"

    @classmethod
    def _guess_dialect(cls, repo: RepositoryMetadata, query: str, paths: list[str]) -> str:
        text = " ".join([cls._repo_text(repo, query), *paths[:500]]).lower()
        if "schema.prisma" in text or "prisma/migrations" in text:
            return "Prisma ecosystem"
        if "db/migrate" in text:
            return "Rails migration ecosystem"
        if "alembic" in text:
            return "Alembic ecosystem"
        if "liquibase" in text:
            return "Liquibase ecosystem"
        if "flyway" in text:
            return "Flyway ecosystem"
        for dialect, keywords in DIALECT_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return dialect
        return "unknown"
