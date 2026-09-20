from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dbgenie.core.config import load_config
from benchmark.construction.github import GitHubAPIError
from benchmark.construction.screening import RepositoryScreeningPipeline


MINORITY_DIALECT_QUERIES = [
    # SQLite
    "sqlite app language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite application language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite django language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite flask language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite fastapi language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite app language:TypeScript stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite app language:JavaScript stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite app language:Go stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite app language:Rust stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "topic:sqlite app stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite migrations stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sqlite schema stars:>50 pushed:>2025-05-22 archived:false fork:false",
    # MySQL / MariaDB
    "mysql app language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mysql django language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mysql spring boot application language:Java stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mysql nestjs app language:TypeScript stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mysql sequelize app language:JavaScript stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mariadb app language:PHP stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mariadb application stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "topic:mariadb app stars:>50 pushed:>2025-05-22 archived:false fork:false",
    # SQL Server
    "sql server application language:C# stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "sql server asp.net core application stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mssql app language:C# stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "mssql entity framework application stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "topic:sql-server app stars:>50 pushed:>2025-05-22 archived:false fork:false",
    # DuckDB. These queries are intentionally broader because DuckDB is less
    # common in CRUD applications; final inclusion still requires manual review.
    "duckdb app language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "duckdb application language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "duckdb dashboard language:Python stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "duckdb analytics app stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "duckdb streamlit app stars:>50 pushed:>2025-05-22 archived:false fork:false",
    "topic:duckdb app stars:>50 pushed:>2025-05-22 archived:false fork:false",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-repos-per-query", type=int, default=30)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = RepositoryScreeningPipeline(config.github, config.dataset)
    query_reports = []
    seen: set[str] = set()
    accepted_seen: set[str] = set()
    candidate_seen: set[str] = set()

    for index, query in enumerate(MINORITY_DIALECT_QUERIES, start=1):
        if args.progress:
            print(
                f"[{index}/{len(MINORITY_DIALECT_QUERIES)}] 开始筛选 query: {query}",
                file=sys.stderr,
                flush=True,
            )
        try:
            report = pipeline.run(query=query, max_repos=args.max_repos_per_query)
        except GitHubAPIError as exc:
            if args.progress:
                print(f"[{index}] query 失败，跳过: {exc}", file=sys.stderr, flush=True)
            continue
        query_reports.append(report)
        for record in report.records:
            seen.add(record.repo.full_name)
            if record.accepted:
                accepted_seen.add(record.repo.full_name)
            if record.review_status in {"accepted", "needs_review"}:
                candidate_seen.add(record.repo.full_name)
        if args.progress:
            print(
                f"[{index}] 完成: scanned={report.scanned}, accepted={report.accepted}, "
                f"review_candidates={report.review_candidates}, candidate_unique={len(candidate_seen)}",
                file=sys.stderr,
                flush=True,
            )

    deduped = []
    emitted: set[str] = set()
    for report in query_reports:
        for record in report.records:
            if record.repo.full_name in emitted:
                continue
            emitted.add(record.repo.full_name)
            deduped.append(record.to_dict())

    payload = {
        "query_family": "minority_dialects",
        "query_count": len(query_reports),
        "max_repos_per_query": args.max_repos_per_query,
        "scanned_unique": len(seen),
        "accepted_unique": len(accepted_seen),
        "candidate_unique": len(candidate_seen),
        "query_summaries": [
            {
                "query": report.query,
                "scanned": report.scanned,
                "accepted": report.accepted,
                "review_candidates": report.review_candidates,
                "acceptance_rate": report.accepted / report.scanned if report.scanned else 0,
                "reason_counts": report.reason_counts,
            }
            for report in query_reports
        ],
        "records": deduped,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

