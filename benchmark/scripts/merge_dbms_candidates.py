from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DBMS_LABELS = {"PostgreSQL", "MySQL", "SQLite", "MariaDB", "SQL Server", "Oracle", "DuckDB"}

SCHEMA_ARTIFACT_LABELS = {
    "Prisma ecosystem": "Prisma schema",
    "Alembic ecosystem": "Alembic migration",
    "Rails migration ecosystem": "Rails migration",
    "Liquibase ecosystem": "Liquibase changelog",
    "Flyway ecosystem": "Flyway migration",
}

STRONG_DBMS_EVIDENCE = {
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
    "jdbc:mariadb",
    "db_connection=mariadb",
    "db_connection = mariadb",
    "mariadb",
    'provider = "sqlserver"',
    "provider = 'sqlserver'",
    "microsoft.entityframeworkcore.sqlserver",
    "usesqlserver",
    "jdbc:sqlserver",
    "tedious",
    "jdbc:oracle",
    "cx_oracle",
    "oracledb",
    "django.db.backends.oracle",
    "oracle.manageddataaccess",
    "duckdb.connect",
    "duckdb://",
    "duckdb_engine",
    "import duckdb",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--enriched", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--csv-output", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    enriched_payload = json.loads(Path(args.enriched).read_text(encoding="utf-8"))
    enriched_by_name = {item["full_name"]: item for item in enriched_payload["candidates"]}

    merged = []
    for item in base["candidates"]:
        enriched = enriched_by_name.get(item["full_name"], {})
        merged.append(_merge_one(item, enriched))

    dbms_confident = [
        item for item in merged if item.get("accepted") and item.get("dbms_final") != "unknown"
    ]

    payload = {
        "source_file": args.base,
        "enriched_file": args.enriched,
        "candidate_count": len(merged),
        "dbms_confident_count": len(dbms_confident),
        "definition": "accepted=true 且 dbms_final != unknown；不要求业务领域、技术栈或 schema 生态完全可信。",
        "candidates": merged,
        "dbms_confident_candidates": dbms_confident,
        "summary": {
            "dbms_counts": dict(Counter(item["dbms_final"] for item in merged)),
            "dbms_confident_counts": dict(Counter(item["dbms_final"] for item in dbms_confident)),
            "schema_artifact_counts": dict(Counter(item["schema_artifact_final"] for item in merged)),
            "domain_counts": dict(Counter(item.get("domain_final", "unknown") for item in merged)),
            "ecosystem_counts": dict(Counter(item.get("ecosystem_final", "unknown") for item in merged)),
        },
    }

    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv_output, dbms_confident)
    write_report(args.report_output, payload)
    return 0


def _merge_one(base: dict[str, Any], enriched: dict[str, Any]) -> dict[str, Any]:
    dialect_guess = base.get("dialect_guess", "unknown")
    dbms = _dbms_from_legacy_label(dialect_guess)
    schema_artifact = _schema_artifact_from_legacy_label(dialect_guess)

    enriched_dbms = enriched.get("dbms_enriched", "unknown")
    if enriched_dbms != "unknown" and _has_strong_dbms_evidence(enriched):
        dbms = enriched_dbms

    enriched_schema_artifact = enriched.get("schema_artifact_enriched", "unknown")
    if enriched_schema_artifact != "unknown":
        schema_artifact = enriched_schema_artifact

    return {
        **base,
        "domain_final": enriched.get("domain_enriched") or base.get("domain_guess", "unknown"),
        "ecosystem_final": enriched.get("ecosystem_enriched") or base.get("ecosystem_guess", "unknown"),
        "dialect_final_legacy": enriched.get("dialect_enriched") or dialect_guess,
        "dbms_final": dbms,
        "schema_artifact_final": schema_artifact,
        "dbms_enriched": enriched.get("dbms_enriched"),
        "schema_artifact_enriched": enriched.get("schema_artifact_enriched"),
        "enrichment_files": enriched.get("enrichment_files", []),
        "enrichment_evidence": enriched.get("enrichment_evidence", {}),
        "dbms_evidence": enriched.get("enrichment_evidence", {}).get("dbms", []),
    }


def _has_strong_dbms_evidence(enriched: dict[str, Any]) -> bool:
    evidence = set(enriched.get("enrichment_evidence", {}).get("dbms", []))
    return bool(evidence & STRONG_DBMS_EVIDENCE)


def _dbms_from_legacy_label(label: str | None) -> str:
    return label if label in DBMS_LABELS else "unknown"


def _schema_artifact_from_legacy_label(label: str | None) -> str:
    return SCHEMA_ARTIFACT_LABELS.get(label or "", "unknown")


def write_csv(path: str, candidates: list[dict[str, Any]]) -> None:
    fieldnames = [
        "full_name",
        "url",
        "dbms_final",
        "schema_artifact_final",
        "domain_final",
        "ecosystem_final",
        "license",
        "stars",
        "forks",
        "pushed_at",
        "query",
        "dbms_evidence",
        "enrichment_files",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            row = {field: item.get(field, "") for field in fieldnames}
            row["dbms_evidence"] = ";".join(item.get("dbms_evidence", []))
            row["enrichment_files"] = ";".join(item.get("enrichment_files", []))
            writer.writerow(row)


def write_report(path: str, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# DBMS 明确候选仓库报告",
        "",
        "## 口径",
        "",
        "- `accepted = true`；",
        "- `dbms_final != unknown`；",
        "- 不要求业务领域、技术栈 / 数据库生态完全可信；",
        "- Prisma、Alembic、Rails migration 等不再算作 DBMS，只记录为 schema 产物 / 迁移生态。",
        "",
        "## 数量",
        "",
        f"- 总候选数：{payload['candidate_count']}",
        f"- DBMS 明确候选数：{payload['dbms_confident_count']}",
        "",
        "## DBMS 分布",
        "",
        *fmt(summary["dbms_confident_counts"]),
        "",
        "## Schema 产物 / 迁移生态分布",
        "",
        *fmt(summary["schema_artifact_counts"]),
        "",
        "## 说明",
        "",
        "- `dbms_final` 才是后续统计 SQL 方言分布时应使用的字段。",
        "- `schema_artifact_final` 只说明 schema 的表达形式或迁移工具，不等价于 SQL 方言。",
        "- `domain_final` 和 `ecosystem_final` 保留为辅助信息，但本清单不以它们作为筛选条件。",
        "",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def fmt(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["- 无"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items(), key=lambda item: item[1], reverse=True)]


if __name__ == "__main__":
    raise SystemExit(main())
