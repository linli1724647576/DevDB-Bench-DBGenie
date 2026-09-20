from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbgenie.core.config import GitHubConfig
from benchmark.construction.github import GitHubAPIError, GitHubClient


@dataclass
class RecollectionPaths:
    evidence_dir: Path = Path("benchmark/evidence_materials/schema_recollection_2026-06-01")


@dataclass
class DownloadedEvidenceFile:
    repo_path: str
    local_path: str
    file_role: str
    reason: str
    size: int = 0
    sha: str = ""


@dataclass
class RecollectionResult:
    full_name: str
    url: str
    dbms_final: str
    schema_strategy: str
    recollection_status: str
    confidence: str
    previous_problem: str
    downloaded_schema_files: list[DownloadedEvidenceFile] = field(default_factory=list)
    still_missing_files: list[str] = field(default_factory=list)
    evidence_coverage_after_recollection: str = "insufficient"
    recommended_next_action: str = "manual_decision_needed"
    notes: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_name": self.full_name,
            "url": self.url,
            "dbms_final": self.dbms_final,
            "schema_strategy": self.schema_strategy,
            "recollection_status": self.recollection_status,
            "confidence": self.confidence,
            "previous_problem": self.previous_problem,
            "downloaded_schema_files": [item.__dict__ for item in self.downloaded_schema_files],
            "still_missing_files": self.still_missing_files,
            "evidence_coverage_after_recollection": self.evidence_coverage_after_recollection,
            "recommended_next_action": self.recommended_next_action,
            "notes": self.notes,
            "errors": self.errors,
        }


class SchemaEvidenceRecollector:
    def __init__(
        self,
        github_config: GitHubConfig,
        paths: RecollectionPaths | None = None,
        max_files_per_repo: int = 120,
        max_file_bytes: int = 500_000,
    ) -> None:
        self.github = GitHubClient(github_config)
        self.paths = paths or RecollectionPaths()
        self.max_files_per_repo = max_files_per_repo
        self.max_file_bytes = max_file_bytes

    def recollect(self, target: dict[str, Any]) -> RecollectionResult:
        full_name = str(target.get("full_name") or "")
        strategy = str(target.get("schema_strategy") or "")
        previous_problem = _summarize_previous_problem(target)
        result = RecollectionResult(
            full_name=full_name,
            url=str(target.get("url") or f"https://github.com/{full_name}"),
            dbms_final=str(target.get("dbms_final") or ""),
            schema_strategy=strategy,
            recollection_status="download_failed",
            confidence="low",
            previous_problem=previous_problem,
        )
        if not full_name:
            result.errors.append("missing full_name")
            return result
        try:
            tree_paths = self.github.list_tree_paths(full_name)
        except GitHubAPIError as exc:
            result.errors.append(str(exc))
            result.notes = "GitHub tree listing failed."
            return result

        selected = self._select_schema_paths(target, tree_paths)
        if not selected:
            result.recollection_status = "not_salvageable"
            result.confidence = "medium"
            result.still_missing_files = _as_str_list(target.get("schema_files_missing_or_needed"))
            result.notes = "No plausible additional schema files found in repository tree."
            return result

        repo_dir = self.paths.evidence_dir / _repo_dir_name(full_name)
        downloaded: list[DownloadedEvidenceFile] = []
        errors: list[str] = []
        for path, role, reason in selected[: self.max_files_per_repo]:
            local_path = repo_dir / path
            if local_path.exists():
                downloaded.append(
                    DownloadedEvidenceFile(
                        repo_path=path,
                        local_path=str(local_path).replace("\\", "/"),
                        file_role=role,
                        reason=f"{reason}; reused existing local file",
                        size=local_path.stat().st_size,
                        sha="",
                    )
                )
                continue
            try:
                repo_file = self.github.download_file(full_name, path)
            except GitHubAPIError as exc:
                errors.append(f"{path}: {exc}")
                continue
            if repo_file.size > self.max_file_bytes:
                errors.append(f"{path}: skipped, size {repo_file.size} > {self.max_file_bytes}")
                continue
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(repo_file.content, encoding="utf-8", errors="ignore")
            downloaded.append(
                DownloadedEvidenceFile(
                    repo_path=path,
                    local_path=str(local_path).replace("\\", "/"),
                    file_role=role,
                    reason=reason,
                    size=repo_file.size,
                    sha=repo_file.sha,
                )
            )

        result.downloaded_schema_files = downloaded
        result.errors = errors
        result.still_missing_files = _remaining_missing_hints(target, downloaded)
        result.evidence_coverage_after_recollection = _estimate_coverage(strategy, downloaded, result.still_missing_files)
        if downloaded and result.evidence_coverage_after_recollection in {"complete_enough", "partial_but_usable"}:
            result.recollection_status = "evidence_completed"
            result.confidence = "high" if result.evidence_coverage_after_recollection == "complete_enough" else "medium"
            result.recommended_next_action = "regenerate_schema_ir"
        elif downloaded:
            result.recollection_status = "partially_completed"
            result.confidence = "medium"
            result.recommended_next_action = "manual_decision_needed"
        else:
            result.recollection_status = "download_failed" if errors else "not_salvageable"
            result.confidence = "low"
            result.recommended_next_action = "manual_decision_needed"
        result.notes = _result_note(result)
        return result

    def _select_schema_paths(
        self,
        target: dict[str, Any],
        tree_paths: list[str],
    ) -> list[tuple[str, str, str]]:
        existing = _existing_repo_paths(target)
        strategy = str(target.get("schema_strategy") or "")
        missing_hints = " ".join(_as_str_list(target.get("schema_files_missing_or_needed"))).lower()
        lower_paths = {path.lower(): path for path in tree_paths}
        selected: list[tuple[str, str, str]] = []

        def add(path: str, role: str, reason: str) -> None:
            if path in existing:
                return
            if any(item[0] == path for item in selected):
                return
            selected.append((path, role, reason))

        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if lower.endswith((".sql", "schema.rb", "structure.sql", "schema.prisma")):
                add(normalized, "canonical_schema", "canonical schema artifact")

        if "django" in strategy:
            self._select_django_paths(tree_paths, missing_hints, add)
        elif "laravel" in strategy:
            self._select_laravel_paths(tree_paths, missing_hints, add)
        elif "alembic" in strategy:
            self._select_alembic_paths(tree_paths, missing_hints, add)
        elif "csharp" in strategy or "ef_core" in strategy:
            self._select_csharp_paths(tree_paths, missing_hints, add)
        else:
            self._select_generic_paths(tree_paths, missing_hints, add)

        # If previous review named concrete files, prefer exact matches.
        for hint in _as_str_list(target.get("schema_files_missing_or_needed")):
            for candidate in _extract_path_like_hints(hint):
                lower_candidate = candidate.lower().strip("/")
                if lower_candidate in lower_paths:
                    add(lower_paths[lower_candidate], "missing_hint_match", "explicitly requested by previous review")
                    continue
                if "*" in candidate:
                    regex = _glob_hint_to_regex(candidate)
                    for lower_path, original in lower_paths.items():
                        if regex.match(lower_path):
                            add(original, "missing_hint_match", "matched wildcard path requested by previous review")

        return _rank_selected(selected)[: self.max_files_per_repo]

    def _select_django_paths(self, tree_paths: list[str], missing_hints: str, add: Any) -> None:
        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if lower.endswith("/models.py") or "/models/" in lower and lower.endswith(".py"):
                add(normalized, "orm_model", "Django model definition")
            if "/migrations/" in lower and lower.endswith(".py") and not lower.endswith("__init__.py"):
                if _migration_is_initial_or_schema_heavy(lower) or _path_relevant_to_hints(lower, missing_hints):
                    add(normalized, "migration_chain", "Django migration needed for schema reconstruction")

    def _select_laravel_paths(self, tree_paths: list[str], missing_hints: str, add: Any) -> None:
        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if "database/migrations/" in lower and lower.endswith(".php"):
                add(normalized, "migration_chain", "Laravel migration")
            if ("/models/" in lower or lower.startswith("app/models/")) and lower.endswith(".php"):
                if _path_relevant_to_hints(lower, missing_hints):
                    add(normalized, "orm_model", "Laravel model auxiliary evidence")
            if lower.endswith("config/database.php") or lower.endswith(".env.example"):
                add(normalized, "db_config", "database provider confirmation")

    def _select_alembic_paths(self, tree_paths: list[str], missing_hints: str, add: Any) -> None:
        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if ("/versions/" in lower or "/migrations/" in lower) and lower.endswith(".py"):
                if not lower.endswith("__init__.py"):
                    add(normalized, "migration_chain", "Alembic migration chain")
            if lower.endswith("models.py") or "/models/" in lower and lower.endswith(".py"):
                add(normalized, "orm_model", "SQLAlchemy model definition")

    def _select_csharp_paths(self, tree_paths: list[str], missing_hints: str, add: Any) -> None:
        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if "/migrations/" in lower and lower.endswith(".cs"):
                add(normalized, "migration_chain", "EF Core migration")
            if lower.endswith(".cs") and any(token in lower for token in ("dbcontext", "/entities/", "/entity/", "/models/")):
                add(normalized, "orm_model", "C# DbContext/entity model")
            if lower.endswith(".csproj"):
                add(normalized, "db_config", "C# project dependency/provider evidence")

    def _select_generic_paths(self, tree_paths: list[str], missing_hints: str, add: Any) -> None:
        for path in tree_paths:
            normalized = path.replace("\\", "/")
            lower = normalized.lower()
            if _is_noise_path(lower):
                continue
            if any(token in lower for token in ("migration", "schema", "model", "entity")) and lower.endswith(
                (".py", ".php", ".rb", ".ts", ".js", ".cs", ".sql")
            ):
                add(normalized, "other", "generic schema-related file")


def _existing_repo_paths(target: dict[str, Any]) -> set[str]:
    paths = set(_as_str_list(target.get("source_files_schema")))
    for item in target.get("local_source_files_schema") or []:
        if isinstance(item, dict) and item.get("repo_path"):
            paths.add(str(item["repo_path"]))
    return paths


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _is_noise_path(lower: str) -> bool:
    return any(
        token in lower
        for token in (
            "node_modules/",
            "vendor/",
            ".venv/",
            "site-packages/",
            "__pycache__/",
            "/tests/",
            "/test/",
            "/spec/",
            "/fixtures/",
            "/docs/",
            "/documentation/",
            "/examples/",
            "/demo/",
        )
    )


def _migration_is_initial_or_schema_heavy(lower: str) -> bool:
    base = lower.rsplit("/", 1)[-1]
    return (
        base.startswith("0001")
        or "initial" in base
        or "create_" in base
        or "_create" in base
        or "add_" in base
        or "alter_" in base
        or "remove_" in base
        or "rename_" in base
        or "index" in base
        or "constraint" in base
    )


def _path_relevant_to_hints(lower: str, hints: str) -> bool:
    if not hints:
        return True
    parts = [part for part in re.split(r"[/_.\-\s]+", lower) if len(part) >= 3]
    return any(part in hints for part in parts[-6:])


def _extract_path_like_hints(text: str) -> list[str]:
    candidates = re.findall(r"[\w./*{}-]+(?:\.py|\.php|\.rb|\.sql|\.cs|\.ts|\.js|\.prisma)", text)
    cleaned = []
    for item in candidates:
        item = item.strip("`'\",，。；;:()[]")
        if item:
            cleaned.append(item)
    return cleaned


def _glob_hint_to_regex(pattern: str) -> re.Pattern[str]:
    escaped = re.escape(pattern.lower().strip("/"))
    escaped = escaped.replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.compile(f"^{escaped}$")


def _rank_selected(selected: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    role_rank = {
        "missing_hint_match": 0,
        "canonical_schema": 1,
        "migration_chain": 2,
        "orm_model": 3,
        "db_config": 4,
        "other": 5,
    }

    def sort_key(item: tuple[str, str, str]) -> tuple[int, int, str]:
        path, role, _ = item
        lower = path.lower()
        initial_bias = 0 if ("0001" in lower or "initial" in lower or "schema.rb" in lower) else 1
        return (role_rank.get(role, 9), initial_bias, lower)

    return sorted(selected, key=sort_key)


def _remaining_missing_hints(target: dict[str, Any], downloaded: list[DownloadedEvidenceFile]) -> list[str]:
    hints = _as_str_list(target.get("schema_files_missing_or_needed"))
    if not hints:
        return []
    downloaded_paths = " ".join(item.repo_path.lower() for item in downloaded)
    remaining = []
    for hint in hints:
        tokens = [token.lower() for token in re.split(r"[/_.\-\s]+", hint) if len(token) >= 4]
        if tokens and any(token in downloaded_paths for token in tokens):
            continue
        remaining.append(hint)
    return remaining


def _estimate_coverage(
    strategy: str,
    downloaded: list[DownloadedEvidenceFile],
    still_missing: list[str],
) -> str:
    roles = {item.file_role for item in downloaded}
    count = len(downloaded)
    if not downloaded:
        return "insufficient"
    if "canonical_schema" in roles:
        return "complete_enough"
    if "static_laravel" in strategy and count >= 8 and "migration_chain" in roles:
        return "complete_enough" if not still_missing else "partial_but_usable"
    if "static_django" in strategy and "orm_model" in roles and "migration_chain" in roles and count >= 8:
        return "complete_enough" if not still_missing else "partial_but_usable"
    if "static_alembic" in strategy and "migration_chain" in roles and count >= 4:
        return "complete_enough" if "orm_model" in roles else "partial_but_usable"
    if "static_csharp" in strategy or "static_ef_core" in strategy:
        if "migration_chain" in roles and ("orm_model" in roles or "db_config" in roles):
            return "partial_but_usable"
    return "partial_but_usable" if count >= 3 else "insufficient"


def _summarize_previous_problem(target: dict[str, Any]) -> str:
    hints = _as_str_list(target.get("schema_files_missing_or_needed"))
    if hints:
        return "; ".join(hints[:3])
    findings = target.get("main_findings") or []
    descriptions = []
    for item in findings[:3]:
        if isinstance(item, dict) and item.get("description"):
            descriptions.append(str(item["description"]))
    return "; ".join(descriptions) if descriptions else "schema evidence was judged incomplete"


def _result_note(result: RecollectionResult) -> str:
    if result.recollection_status == "evidence_completed":
        return f"Downloaded {len(result.downloaded_schema_files)} schema evidence files; ready for Schema IR regeneration."
    if result.recollection_status == "partially_completed":
        return f"Downloaded {len(result.downloaded_schema_files)} files, but evidence may still be incomplete."
    if result.recollection_status == "not_salvageable":
        return "No sufficient schema evidence could be found from repository tree."
    return "Evidence recollection failed or downloaded no files."


def _repo_dir_name(full_name: str) -> str:
    return full_name.replace("/", "__")


def build_recollection_payload(
    targets_doc: dict[str, Any],
    results: list[RecollectionResult],
    output_dir: Path,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    augmented_targets = []
    results_by_name = {result.full_name: result for result in results}
    for result in results:
        status_counts[result.recollection_status] = status_counts.get(result.recollection_status, 0) + 1
    for target in targets_doc.get("targets", []):
        result = results_by_name.get(str(target.get("full_name") or ""))
        augmented = dict(target)
        if result:
            augmented["recollection_status"] = result.recollection_status
            augmented["recollected_source_files_schema"] = [
                item.repo_path for item in result.downloaded_schema_files
            ]
            augmented["recollected_local_source_files_schema"] = [
                {
                    "repo_path": item.repo_path,
                    "local_path": item.local_path,
                    "size": item.size,
                    "sha": item.sha,
                    "file_role": item.file_role,
                }
                for item in result.downloaded_schema_files
            ]
            augmented["evidence_coverage_after_recollection"] = (
                result.evidence_coverage_after_recollection
            )
        augmented_targets.append(augmented)
    return {
        "generated_at": "2026-06-01",
        "review_scope": "schema_evidence_recollection_for_missing_schema_samples",
        "target_count": len(results),
        "output_dir": str(output_dir).replace("\\", "/"),
        "summary": {
            "evidence_completed": status_counts.get("evidence_completed", 0),
            "partially_completed": status_counts.get("partially_completed", 0),
            "not_salvageable": status_counts.get("not_salvageable", 0),
            "download_failed": status_counts.get("download_failed", 0),
        },
        "results": [result.to_dict() for result in results],
        "augmented_targets": augmented_targets,
    }
