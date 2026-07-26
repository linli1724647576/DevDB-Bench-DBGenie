from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--csv-output", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidates = data["candidates"]
    high_confidence = [
        item
        for item in candidates
        if item.get("accepted")
        and item.get("domain_guess") != "unknown"
        and item.get("ecosystem_guess") != "unknown"
        and item.get("dialect_guess") != "unknown"
    ]

    payload = {
        "source_file": args.input,
        "definition": (
            "严格自动通过 accepted=true，且 domain_guess、ecosystem_guess、"
            "dialect_guess 均不为 unknown。注意这些字段仍是自动启发式标注，"
            "不是人工最终确认。"
        ),
        "high_confidence_count": len(high_confidence),
        "candidates": high_confidence,
        "summary": {
            "domain_counts": dict(Counter(item["domain_guess"] for item in high_confidence)),
            "ecosystem_counts": dict(Counter(item["ecosystem_guess"] for item in high_confidence)),
            "dialect_counts": dict(Counter(item["dialect_guess"] for item in high_confidence)),
            "license_counts": dict(Counter(item["license"] for item in high_confidence)),
        },
    }

    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(args.csv_output, high_confidence)
    write_report(args.report_output, payload, len(candidates))
    return 0


def write_csv(path: str, candidates: list[dict[str, Any]]) -> None:
    fieldnames = [
        "full_name",
        "url",
        "domain_guess",
        "ecosystem_guess",
        "dialect_guess",
        "license",
        "stars",
        "forks",
        "pushed_at",
        "path_count",
        "query",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            writer.writerow({field: item.get(field, "") for field in fieldnames})


def write_report(path: str, payload: dict[str, Any], total_count: int) -> None:
    summary = payload["summary"]
    lines = [
        "# 高置信候选仓库清单说明",
        "",
        "## 口径",
        "",
        "本清单筛选条件：",
        "",
        "- `accepted = true`，即通过当前自动仓库筛选；",
        "- `domain_guess != unknown`；",
        "- `ecosystem_guess != unknown`；",
        "- `dialect_guess != unknown`。",
        "",
        "注意：这里的“高置信”仍然是自动启发式口径，不等于人工最终确认。它表示三个关键标注字段都有自动证据，而不是字段缺失。",
        "",
        "## 数量",
        "",
        f"- 原候选总数：{total_count}",
        f"- 高置信候选数：{payload['high_confidence_count']}",
        "",
        "## 业务领域分布",
        "",
        *format_counter(summary["domain_counts"]),
        "",
        "## 技术栈 / 数据库生态分布",
        "",
        *format_counter(summary["ecosystem_counts"]),
        "",
        "## SQL 方言 / schema 生态分布",
        "",
        *format_counter(summary["dialect_counts"]),
        "",
        "## License 分布",
        "",
        *format_counter(summary["license_counts"]),
        "",
        "## 输出文件",
        "",
        "- JSON：`benchmark/candidates/high_confidence_candidate_repositories_2026-05-26.json`",
        "- CSV：`benchmark/candidates/high_confidence_candidate_repositories_2026-05-26.csv`",
        "",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def format_counter(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["- 无"]
    return [
        f"- `{key}`: {value}"
        for key, value in sorted(counter.items(), key=lambda item: item[1], reverse=True)
    ]


if __name__ == "__main__":
    raise SystemExit(main())

