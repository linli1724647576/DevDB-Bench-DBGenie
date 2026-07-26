from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dbgenie.core.config import load_config
from benchmark.construction.github import GitHubAPIError, RepositoryMetadata
from benchmark.construction.screening import RepositoryScreeningPipeline


CODE_SEARCH_QUERIES = [
    # SQL Server provider evidence.
    '"UseSqlServer" "DbContext" language:C#',
    '"Microsoft.EntityFrameworkCore.SqlServer" "MigrationBuilder" language:C#',
    '"provider = \\"sqlserver\\"" "schema.prisma"',
    '"jdbc:sqlserver" "CREATE TABLE"',
    '"mssql" "typeorm" "migration" language:TypeScript',
    # MariaDB provider evidence.
    '"jdbc:mariadb" "CREATE TABLE"',
    '"DB_CONNECTION=mariadb" "migrations" language:PHP',
    '"mariadb" "database/migrations" language:PHP',
    '"mariadb" "typeorm" "migration" language:TypeScript',
    # Oracle provider evidence.
    '"jdbc:oracle" "CREATE TABLE"',
    '"django.db.backends.oracle" "models.Model" language:Python',
    '"Oracle.ManagedDataAccess" "DbContext" language:C#',
    '"cx_Oracle" "CREATE TABLE" language:Python',
    '"oracledb" "CREATE TABLE" language:Python',
    # DuckDB provider evidence.
    '"duckdb.connect" "CREATE TABLE" language:Python',
    '"duckdb_engine" "create_all" language:Python',
    '"duckdb" "sqlalchemy" "create_all" language:Python',
    '"duckdb" "migrations" language:Python',
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-code-results-per-query", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=7.0)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = RepositoryScreeningPipeline(config.github, config.dataset)
    records_by_name = {}
    query_summaries = []

    for index, query in enumerate(CODE_SEARCH_QUERIES, start=1):
        if args.progress:
            print(f"[{index}/{len(CODE_SEARCH_QUERIES)}] code search: {query}", file=sys.stderr, flush=True)
        try:
            full_names = pipeline.github.search_code_repositories(
                query,
                per_page=args.max_code_results_per_query,
            )
        except GitHubAPIError as exc:
            if args.progress:
                print(f"[{index}] code search 失败，跳过: {exc}", file=sys.stderr, flush=True)
            continue

        scanned = 0
        accepted = 0
        review_candidates = 0
        for full_name in full_names:
            if full_name in records_by_name:
                continue
            scanned += 1
            record = pipeline._screen_one(
                RepositoryMetadata(full_name=full_name),
                include_tree_filter=True,
                query=f"code_search:{query}",
            )
            records_by_name[full_name] = record
            if record.accepted:
                accepted += 1
            if record.review_status in {"accepted", "needs_review"}:
                review_candidates += 1
        query_summaries.append(
            {
                "query": query,
                "code_results": len(full_names),
                "new_repos_scanned": scanned,
                "accepted": accepted,
                "review_candidates": review_candidates,
            }
        )
        if args.progress:
            print(
                f"[{index}] 完成: code_results={len(full_names)}, new_scanned={scanned}, "
                f"accepted={accepted}, review_candidates={review_candidates}, total_unique={len(records_by_name)}",
                file=sys.stderr,
                flush=True,
            )
        if index < len(CODE_SEARCH_QUERIES) and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    records = [record.to_dict() for record in records_by_name.values()]
    payload = {
        "query_family": "dbms_provider_code_search",
        "query_count": len(query_summaries),
        "scanned_unique": len(records),
        "accepted_unique": sum(1 for item in records if item["accepted"]),
        "candidate_unique": sum(1 for item in records if item["review_status"] in {"accepted", "needs_review"}),
        "query_summaries": query_summaries,
        "records": records,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

