from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dbgenie.core.config import load_config
from benchmark.construction.filters import NON_PRIMARY_PATH_PARTS
from benchmark.construction.github import GitHubAPIError, GitHubClient


CODE_EXTENSIONS = (
    ".py",
    ".rb",
    ".php",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".cs",
    ".go",
    ".rs",
    ".kt",
    ".scala",
)

DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc", ".yaml", ".yml", ".json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--checkpoint-jsonl")
    parser.add_argument("--max-schema-files", type=int, default=12)
    parser.add_argument("--max-requirement-files", type=int, default=6)
    parser.add_argument("--max-workload-files", type=int, default=10)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    github = GitHubClient(config.github)
    input_path = Path(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])

    existing = _read_checkpoint(Path(args.checkpoint_jsonl)) if args.checkpoint_jsonl else {}
    remaining = [item for item in candidates if item.get("full_name") not in existing]
    if args.limit:
        remaining = remaining[: args.limit]

    checkpoint = None
    if args.checkpoint_jsonl:
        checkpoint_path = Path(args.checkpoint_jsonl)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = checkpoint_path.open("a", encoding="utf-8")

    try:
        for index, candidate in enumerate(remaining, start=1):
            full_name = candidate["full_name"]
            if args.progress:
                print(f"[{index}/{len(remaining)}] collect evidence {full_name}", file=sys.stderr, flush=True)
            result = collect_one(
                github=github,
                candidate=candidate,
                evidence_root=Path(args.evidence_root),
                max_file_bytes=config.dataset.max_file_bytes,
                max_schema_files=args.max_schema_files,
                max_requirement_files=args.max_requirement_files,
                max_workload_files=args.max_workload_files,
            )
            existing[full_name] = result
            if checkpoint:
                checkpoint.write(json.dumps(result, ensure_ascii=False) + "\n")
                checkpoint.flush()
    finally:
        if checkpoint:
            checkpoint.close()

    augmented = []
    for candidate in candidates:
        result = existing.get(candidate.get("full_name"))
        if result:
            merged = {**candidate}
            merged["source_files"] = result["source_files"]
            merged["local_evidence_dir"] = result["local_evidence_dir"]
            merged["local_source_files"] = result["local_source_files"]
            merged["evidence_collection_errors"] = result["errors"]
            augmented.append(merged)
        else:
            augmented.append(candidate)

    output_payload = {
        **payload,
        "evidence_root": str(Path(args.evidence_root).as_posix()),
        "evidence_candidate_count": sum(1 for item in augmented if item.get("source_files")),
        "candidates": augmented,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def collect_one(
    github: GitHubClient,
    candidate: dict[str, Any],
    evidence_root: Path,
    max_file_bytes: int,
    max_schema_files: int,
    max_requirement_files: int,
    max_workload_files: int,
) -> dict[str, Any]:
    full_name = candidate["full_name"]
    errors: list[str] = []
    try:
        paths = github.list_tree_paths(full_name)
    except GitHubAPIError as exc:
        return _empty_result(candidate, evidence_root, [f"tree_scan_error:{exc}"])

    primary_paths = [path for path in paths if _is_primary_path(path)]
    source_files = {
        "schema": _select_schema_paths(primary_paths, max_schema_files),
        "requirement_evidence": _select_requirement_paths(primary_paths, max_requirement_files),
        "workload_evidence": _select_workload_paths(primary_paths, max_workload_files),
    }

    repo_dir = evidence_root / _repo_dir_name(full_name)
    local_source_files = {"schema": [], "requirement_evidence": [], "workload_evidence": []}
    for category, selected_paths in source_files.items():
        for repo_path in selected_paths:
            try:
                repo_file = github.download_file(full_name, repo_path)
            except GitHubAPIError as exc:
                errors.append(f"{repo_path}: {exc}")
                continue
            if repo_file.size > max_file_bytes:
                errors.append(f"{repo_path}: file_too_large:{repo_file.size}")
                continue
            local_path = repo_dir / repo_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(repo_file.content, encoding="utf-8", errors="ignore")
            local_source_files[category].append(
                {
                    "repo_path": repo_path,
                    "local_path": local_path.as_posix(),
                    "size": repo_file.size,
                    "sha": repo_file.sha,
                }
            )

    return {
        "full_name": full_name,
        "source_files": source_files,
        "local_evidence_dir": repo_dir.as_posix(),
        "local_source_files": local_source_files,
        "errors": errors[:20],
    }


def _select_schema_paths(paths: list[str], limit: int) -> list[str]:
    return _select(paths, _schema_score, limit)


def _select_requirement_paths(paths: list[str], limit: int) -> list[str]:
    return _select(paths, _requirement_score, limit)


def _select_workload_paths(paths: list[str], limit: int) -> list[str]:
    return _select(paths, _workload_score, limit)


def _select(paths: list[str], scorer, limit: int) -> list[str]:
    scored = []
    for path in paths:
        score = scorer(path)
        if score > 0:
            scored.append((score, _depth_penalty(path), path))
    scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [path for _, _, path in scored[:limit]]


def _schema_score(path: str) -> int:
    lower = path.lower()
    filename = lower.rsplit("/", 1)[-1]
    score = 0
    if lower.endswith("prisma/schema.prisma"):
        score = max(score, 220)
    if lower.endswith(("schema.sql", "structure.sql", "db/schema.rb", "db/structure.sql")):
        score = max(score, 210)
    if "supabase/migrations/" in lower:
        score = max(score, 205)
    if "database/migrations/" in lower or "db/migrate/" in lower or "migrations/" in lower:
        score = max(score, 190)
    if "alembic/versions/" in lower:
        score = max(score, 190)
    if lower.endswith(("models.py", "models.ts", "models.rb")):
        score = max(score, 170)
    if lower.endswith((".entity.ts", ".entity.js", "dbcontext.cs")):
        score = max(score, 170)
    if "/models/" in lower and lower.endswith(CODE_EXTENSIONS):
        score = max(score, 120)
    if lower.endswith(".sql"):
        score = max(score, 115)
    if "migration" in filename and lower.endswith(CODE_EXTENSIONS):
        score = max(score, 105)
    return score - min(path.count("/"), 10)


def _requirement_score(path: str) -> int:
    lower = path.lower()
    filename = lower.rsplit("/", 1)[-1]
    if not lower.endswith(DOC_EXTENSIONS):
        return 0
    score = 0
    if filename in {"readme.md", "readme.rst", "readme.txt"}:
        score = max(score, 220)
    if lower.startswith(("docs/", "doc/")) or "/docs/" in lower or "/doc/" in lower:
        score = max(score, 160)
    if any(token in lower for token in ("api", "openapi", "swagger", "architecture", "usage", "user-guide")):
        score = max(score, 180)
    if any(token in lower for token in ("changelog", "license", "security", "contributing", "code_of_conduct")):
        score -= 80
    return max(0, score - min(path.count("/"), 10))


def _workload_score(path: str) -> int:
    lower = path.lower()
    filename = lower.rsplit("/", 1)[-1]
    score = 0
    if lower.endswith(DOC_EXTENSIONS) and any(token in lower for token in ("api", "openapi", "swagger")):
        score = max(score, 180)
    if not lower.endswith(CODE_EXTENSIONS):
        return score
    if any(token in lower for token in ("repository", "repositories", "dao", "mapper")):
        score = max(score, 190)
    if any(token in lower for token in ("query", "queries", "search", "filter", "report", "analytics")):
        score = max(score, 175)
    if any(token in lower for token in ("controller", "controllers", "route", "routes", "api", "endpoint")):
        score = max(score, 165)
    if any(token in lower for token in ("service", "services", "usecase", "use_case")):
        score = max(score, 140)
    if filename in {"urls.py", "views.py"}:
        score = max(score, 130)
    return max(0, score - min(path.count("/"), 10))


def _depth_penalty(path: str) -> int:
    return max(0, 20 - path.count("/"))


def _is_primary_path(path: str) -> bool:
    parts = set(path.lower().split("/"))
    return not bool(parts & NON_PRIMARY_PATH_PARTS)


def _repo_dir_name(full_name: str) -> str:
    return full_name.replace("/", "__")


def _empty_result(candidate: dict[str, Any], evidence_root: Path, errors: list[str]) -> dict[str, Any]:
    full_name = candidate["full_name"]
    return {
        "full_name": full_name,
        "source_files": {"schema": [], "requirement_evidence": [], "workload_evidence": []},
        "local_evidence_dir": (evidence_root / _repo_dir_name(full_name)).as_posix(),
        "local_source_files": {"schema": [], "requirement_evidence": [], "workload_evidence": []},
        "errors": errors,
    }


def _read_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    results: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        results[item["full_name"]] = item
    return results


if __name__ == "__main__":
    raise SystemExit(main())

