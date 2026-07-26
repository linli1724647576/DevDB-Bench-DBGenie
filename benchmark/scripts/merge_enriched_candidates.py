from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


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
        enriched = enriched_by_name.get(item["full_name"])
        merged_item = {**item}
        if enriched:
            merged_item.update(_conservative_enrichment(item, enriched))
        else:
            merged_item.update(
                {
                    "domain_final": item.get("domain_guess", "unknown"),
                    "ecosystem_final": item.get("ecosystem_guess", "unknown"),
                    "dialect_final": item.get("dialect_guess", "unknown"),
                    "enrichment_applied": False,
                    "enrichment_note": "not_enriched",
                }
            )
        merged.append(merged_item)

    high_confidence = [
        item
        for item in merged
        if item.get("accepted")
        and item.get("domain_final") != "unknown"
        and item.get("ecosystem_final") != "unknown"
        and item.get("dialect_final") != "unknown"
    ]

    payload = {
        "source_file": args.base,
        "enriched_file": args.enriched,
        "candidate_count": len(merged),
        "enriched_count": len(enriched_by_name),
        "high_confidence_count": len(high_confidence),
        "candidates": merged,
        "high_confidence_candidates": high_confidence,
        "summary": {
            "domain_counts": dict(Counter(item["domain_final"] for item in merged)),
            "ecosystem_counts": dict(Counter(item["ecosystem_final"] for item in merged)),
            "dialect_counts": dict(Counter(item["dialect_final"] for item in merged)),
            "high_confidence_domain_counts": dict(Counter(item["domain_final"] for item in high_confidence)),
            "high_confidence_ecosystem_counts": dict(Counter(item["ecosystem_final"] for item in high_confidence)),
            "high_confidence_dialect_counts": dict(Counter(item["dialect_final"] for item in high_confidence)),
        },
    }

    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv_output, high_confidence)
    write_report(args.report_output, payload)
    return 0


def _conservative_enrichment(base: dict[str, Any], enriched: dict[str, Any]) -> dict[str, Any]:
    domain = base.get("domain_guess", "unknown")
    ecosystem = base.get("ecosystem_guess", "unknown")
    dialect = base.get("dialect_guess", "unknown")
    applied = []

    if domain == "unknown" and _evidence_count(enriched, "domain") >= 2:
        domain = enriched.get("domain_enriched", domain)
        applied.append("domain")

    if ecosystem == "unknown" and _strong_ecosystem_evidence(enriched):
        ecosystem = enriched.get("ecosystem_enriched", ecosystem)
        applied.append("ecosystem")

    if dialect == "unknown" and _strong_dialect_evidence(enriched):
        dialect = enriched.get("dialect_enriched", dialect)
        applied.append("dialect")

    return {
        "domain_final": domain,
        "ecosystem_final": ecosystem,
        "dialect_final": dialect,
        "domain_enriched": enriched.get("domain_enriched"),
        "ecosystem_enriched": enriched.get("ecosystem_enriched"),
        "dialect_enriched": enriched.get("dialect_enriched"),
        "enrichment_files": enriched.get("enrichment_files", []),
        "enrichment_evidence": enriched.get("enrichment_evidence", {}),
        "enrichment_applied": bool(applied),
        "enrichment_note": ",".join(applied) if applied else "kept_original_labels",
    }


def _evidence_count(enriched: dict[str, Any], field: str) -> int:
    return len(enriched.get("enrichment_evidence", {}).get(field, []))


def _strong_ecosystem_evidence(enriched: dict[str, Any]) -> bool:
    evidence = set(enriched.get("enrichment_evidence", {}).get("ecosystem", []))
    strong = {
        "django.db",
        "models.model",
        "from flask",
        "flask_sqlalchemy",
        "fastapi",
        "activerecord",
        "create_table",
        "illuminate\\",
        "artisan",
        "springframework",
        "jakarta.persistence",
        "@entity",
        "dbcontext",
        "migrationbuilder",
        "prisma/client",
        "schema.prisma",
        "@nestjs",
        "gorm.io/gorm",
        "entgo.io/ent",
    }
    return bool(evidence & strong)


def _strong_dialect_evidence(enriched: dict[str, Any]) -> bool:
    evidence = set(enriched.get("enrichment_evidence", {}).get("dialect", []))
    strong = {
        "schema.prisma",
        "@prisma/client",
        "db/migrate",
        "create_table",
        "alembic",
        "op.create_table",
        "liquibase",
        "flyway",
        "postgres",
        "postgresql",
        "mysql",
        "sqlite",
        "sql server",
        "mssql",
        "mariadb",
        "duckdb",
    }
    return bool(evidence & strong)


def write_csv(path: str, candidates: list[dict[str, Any]]) -> None:
    fieldnames = [
        "full_name",
        "url",
        "domain_final",
        "ecosystem_final",
        "dialect_final",
        "license",
        "stars",
        "forks",
        "pushed_at",
        "query",
        "enrichment_applied",
        "enrichment_note",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            writer.writerow({field: item.get(field, "") for field in fieldnames})


def write_report(path: str, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# 标注增强后的高置信候选说明",
        "",
        "## 处理方式",
        "",
        "- 只对部分低置信候选下载少量必要文件进行标注增强。",
        "- 增强结果采用保守合并：已有非 unknown 标注不被覆盖；只有原字段为 unknown 且证据较强时才补充。",
        "- 因此该清单比纯自动猜测更稳，但仍需要人工最终确认。",
        "",
        "## 数量",
        "",
        f"- 总候选数：{payload['candidate_count']}",
        f"- 已增强候选数：{payload['enriched_count']}",
        f"- 增强后高置信候选数：{payload['high_confidence_count']}",
        "",
        "## 增强后全体候选领域分布",
        "",
        *format_counter(summary["domain_counts"]),
        "",
        "## 增强后全体候选技术栈分布",
        "",
        *format_counter(summary["ecosystem_counts"]),
        "",
        "## 增强后全体候选方言 / schema 生态分布",
        "",
        *format_counter(summary["dialect_counts"]),
        "",
        "## 增强后高置信候选方言 / schema 生态分布",
        "",
        *format_counter(summary["high_confidence_dialect_counts"]),
        "",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def format_counter(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["- 无"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items(), key=lambda item: item[1], reverse=True)]


if __name__ == "__main__":
    raise SystemExit(main())
