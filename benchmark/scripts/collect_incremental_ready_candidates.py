from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from dbgenie.core.config import load_config
from dbgenie.core.io import write_json, write_text
from benchmark.construction.github import GitHubAPIError, GitHubClient
from benchmark.construction.schema_materialization import (
    MaterializationPaths,
    SchemaMaterializer,
    build_materialization_report,
)


QUERY_SPECS = [
    ("DuckDB", "duckdb app language:Python stars:>20 archived:false fork:false"),
    ("DuckDB", "duckdb analytics language:Python stars:>20 archived:false fork:false"),
    ("DuckDB", "duckdb dashboard language:Python stars:>20 archived:false fork:false"),
    ("DuckDB", "topic:duckdb stars:>20 archived:false fork:false"),
    ("SQL Server", "ef core sql server language:C# stars:>20 archived:false fork:false"),
    ("SQL Server", "entity framework sql server language:C# stars:>20 archived:false fork:false"),
    ("SQL Server", "asp.net core sql server language:C# stars:>20 archived:false fork:false"),
    ("SQL Server", "mssql entity framework language:C# stars:>20 archived:false fork:false"),
    ("SQLite", "sqlite sqlalchemy app language:Python stars:>20 archived:false fork:false"),
    ("SQLite", "sqlite app language:Python stars:>20 archived:false fork:false"),
    ("MariaDB", "mariadb laravel app language:PHP stars:>20 archived:false fork:false"),
    ("MariaDB", "mariadb app stars:>20 archived:false fork:false"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--existing", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--max-results-per-query", type=int, default=20)
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--max-schema-files", type=int, default=8)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--only-dbms", action="append", help="Only run query specs for the given DBMS. Can be repeated.")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    github = GitHubClient(config.github)
    existing_payload = json.loads(Path(args.existing).read_text(encoding="utf-8"))
    existing_names = {item["full_name"] for item in existing_payload.get("candidates", [])}

    candidates_by_name: dict[str, dict[str, Any]] = {}
    query_summaries = []
    query_specs = QUERY_SPECS
    if args.only_dbms:
        allowed = {item.lower() for item in args.only_dbms}
        query_specs = [(dbms, query) for dbms, query in QUERY_SPECS if dbms.lower() in allowed]

    for index, (dbms, query) in enumerate(query_specs, start=1):
        if args.progress:
            print(f"[{index}/{len(query_specs)}] repo search {dbms}: {query}", file=sys.stderr, flush=True)
        try:
            repos = github.search_repositories(query, per_page=args.max_results_per_query)
        except GitHubAPIError as exc:
            query_summaries.append({"dbms": dbms, "query": query, "error": str(exc)})
            if args.progress:
                print(f"[{index}] failed: {exc}", file=sys.stderr, flush=True)
            continue

        new_items = 0
        for repo in repos:
            if repo.full_name in existing_names:
                continue
            paths = _repo_schema_paths(github, repo.full_name)
            if not paths:
                continue
            candidate = candidates_by_name.setdefault(
                repo.full_name,
                {
                    "full_name": repo.full_name,
                    "url": repo.html_url or f"https://github.com/{repo.full_name}",
                    "dbms_final": dbms,
                    "schema_artifact_final": _artifact_from_path(paths[0]),
                    "domain_final": "unknown",
                    "ecosystem_final": "unknown",
                    "license": repo.license_spdx_id,
                    "stars": str(repo.stargazers_count),
                    "forks": str(repo.forks_count),
                    "pushed_at": repo.pushed_at,
                    "query": f"incremental_repo_search:{query}",
                    "dbms_evidence": query,
                    "source_files": {"schema": [], "requirement_evidence": [], "workload_evidence": []},
                    "local_source_files": {"schema": [], "requirement_evidence": [], "workload_evidence": []},
                },
            )
            for path in paths[:12]:
                if path not in candidate["source_files"]["schema"]:
                    candidate["source_files"]["schema"].append(path)
                    new_items += 1
        query_summaries.append(
            {"dbms": dbms, "query": query, "items": len(repos), "new_schema_hits": new_items}
        )
        if args.sleep_seconds and index < len(query_specs):
            time.sleep(args.sleep_seconds)

    evidence_root = Path(args.evidence_root)
    materializer = SchemaMaterializer(
        MaterializationPaths(
            schema_ir_dir=Path("benchmark/schema_ir_drafts"),
            reference_ddl_dir=Path("benchmark/reference_ddl_drafts"),
        )
    )
    candidates = list(candidates_by_name.values())
    if args.max_candidates:
        candidates = candidates[: args.max_candidates]

    augmented = []
    for index, candidate in enumerate(candidates, start=1):
        if args.progress:
            print(f"[{index}/{len(candidates)}] evidence+extract {candidate['full_name']}", file=sys.stderr, flush=True)
        _download_candidate_files(
            github,
            candidate,
            evidence_root,
            config.dataset.max_file_bytes,
            args.max_schema_files,
        )
        result = materializer.materialize(candidate)
        augmented.append({**candidate, "schema_materialization": result.to_dict()})
        _write_outputs(args, existing_payload, query_summaries, augmented, final=False)

    _write_outputs(args, existing_payload, query_summaries, augmented, final=True)
    return 0


def _write_outputs(
    args: argparse.Namespace,
    existing_payload: dict[str, Any],
    query_summaries: list[dict[str, Any]],
    augmented: list[dict[str, Any]],
    final: bool,
) -> None:
    ready = _ready_candidates(augmented)
    merged_candidates = [*existing_payload.get("candidates", []), *ready]
    output_payload = {
        **existing_payload,
        "source_file": args.existing,
        "incremental_query_summaries": query_summaries,
        "incremental_candidate_count": len(augmented),
        "incremental_ready_count": len(ready),
        "candidate_count": len(merged_candidates),
        "candidates": merged_candidates,
    }
    write_json(args.output, output_payload)

    report = [
        "# 增量 GitHub 样本搜集报告",
        "",
        f"- 状态：{'完成' if final else '进行中，可断点恢复'}",
        f"- 初始样本数：{len(existing_payload.get('candidates', []))}",
        f"- 已处理增量候选数：{len(augmented)}",
        f"- 增量 ready 数：{len(ready)}",
        f"- 合并后样本数：{len(merged_candidates)}",
        "",
        "## Query 统计",
        "",
        *[
            f"- {item.get('dbms')} | items={item.get('items', 0)} | "
            f"new_schema_hits={item.get('new_schema_hits', 0)} | query=`{item.get('query')}`"
            for item in query_summaries
        ],
        "",
        "## 增量 Ready 样本",
        "",
        *[
            f"- `{item['full_name']}` | DBMS={item['dbms_final']} | "
            f"strategy={item['schema_materialization']['strategy']} | "
            f"tables={item['schema_materialization']['table_count']}"
            for item in ready
        ],
        "",
        "## 增量抽取总览",
        "",
        build_materialization_report(augmented, source_file="incremental_repo_search"),
    ]
    write_text(args.report_output, "\n".join(report).rstrip() + "\n")


def _ready_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in candidates
        if item["schema_materialization"]["status"] == "static_extracted"
        and not item["schema_materialization"]["quality_warnings"]
    ]


def _download_candidate_files(
    github: GitHubClient,
    candidate: dict[str, Any],
    evidence_root: Path,
    max_file_bytes: int,
    max_schema_files: int,
) -> None:
    repo_dir = evidence_root / candidate["full_name"].replace("/", "__")
    candidate["local_evidence_dir"] = repo_dir.as_posix()
    for path in candidate["source_files"]["schema"][:max_schema_files]:
        local_path = _local_evidence_path(repo_dir, path)
        if local_path.exists():
            candidate["local_source_files"]["schema"].append(
                {
                    "repo_path": path,
                    "local_path": local_path.as_posix(),
                    "size": local_path.stat().st_size,
                    "sha": "",
                }
            )
            continue
        try:
            repo_file = github.download_file(candidate["full_name"], path)
        except GitHubAPIError:
            continue
        if repo_file.size > max_file_bytes:
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(repo_file.content, encoding="utf-8", errors="ignore")
        candidate["local_source_files"]["schema"].append(
            {
                "repo_path": path,
                "local_path": local_path.as_posix(),
                "size": repo_file.size,
                "sha": repo_file.sha,
            }
        )
    for doc_path in ("README.md", "readme.md"):
        local_path = _local_evidence_path(repo_dir, doc_path)
        if local_path.exists():
            candidate["source_files"]["requirement_evidence"].append(doc_path)
            candidate["local_source_files"]["requirement_evidence"].append(
                {
                    "repo_path": doc_path,
                    "local_path": local_path.as_posix(),
                    "size": local_path.stat().st_size,
                    "sha": "",
                }
            )
            break
        try:
            repo_file = github.download_file(candidate["full_name"], doc_path)
        except GitHubAPIError:
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(repo_file.content, encoding="utf-8", errors="ignore")
        candidate["source_files"]["requirement_evidence"].append(doc_path)
        candidate["local_source_files"]["requirement_evidence"].append(
            {
                "repo_path": doc_path,
                "local_path": local_path.as_posix(),
                "size": repo_file.size,
                "sha": repo_file.sha,
            }
        )
        break


def _local_evidence_path(repo_dir: Path, repo_path: str) -> Path:
    local_path = repo_dir / repo_path
    if len(str(local_path.resolve())) <= 240:
        return local_path
    suffix = Path(repo_path).suffix
    digest = hashlib.sha1(repo_path.encode("utf-8")).hexdigest()[:12]
    safe_name = Path(repo_path).name
    safe_name = "".join(char if char.isalnum() or char in ".-_" else "_" for char in safe_name)
    return repo_dir / "_long_paths" / f"{digest}__{safe_name or 'file'}{suffix if not safe_name.endswith(suffix) else ''}"


def _repo_schema_paths(github: GitHubClient, full_name: str) -> list[str]:
    try:
        paths = github.list_tree_paths(full_name)
    except GitHubAPIError:
        return []
    scored = []
    for path in paths:
        lower = path.lower()
        parts = set(lower.split("/"))
        if parts & {"test", "tests", "__tests__", "spec", "specs", "vendor", "node_modules"}:
            continue
        if any(part.endswith(".tests") or part.endswith(".test") for part in parts):
            continue
        score = 0
        if lower.endswith(("schema.sql", "structure.sql", "db/schema.rb", "db/structure.sql")):
            score = max(score, 220)
        if lower.endswith("schema.prisma"):
            score = max(score, 210)
        if "migrations" in lower and lower.endswith((".cs", ".py", ".rb", ".php", ".ts", ".js", ".sql")):
            score = max(score, 190)
        if lower.endswith("models.py") or lower.endswith(".entity.ts") or lower.endswith("dbcontext.cs"):
            score = max(score, 180)
        if "/models/" in lower and lower.endswith(".cs"):
            score = max(score, 170)
        if lower.endswith(".sql") and any(token in lower for token in ("duckdb", "sqlite", "mssql", "sqlserver", "mariadb", "mysql")):
            score = max(score, 165)
        if lower.endswith((".py", ".ts", ".js", ".cs", ".go", ".java", ".php", ".rb")) and any(
            token in lower
            for token in (
                "duckdb",
                "database",
                "db",
                "storage",
                "repository",
                "repositories",
                "schema",
                "model",
                "models",
            )
        ):
            score = max(score, 135)
        if score:
            scored.append((score - min(path.count("/"), 12), path))
    scored.sort(reverse=True)
    return [path for _, path in scored[:20]]


def _artifact_from_path(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".sql"):
        return "SQL DDL file"
    if lower.endswith("schema.prisma"):
        return "Prisma schema"
    if lower.endswith(".cs") and "migration" in lower:
        return "EF Core migration"
    if lower.endswith(".cs"):
        return "C# entity/model"
    if lower.endswith(".py"):
        return "Python schema/model"
    if lower.endswith(".php"):
        return "PHP migration/model"
    if lower.endswith((".ts", ".js")):
        return "TypeScript/JavaScript schema/model"
    return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
