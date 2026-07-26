from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--csv-output", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidates = [
        item
        for item in data["candidates"]
        if item.get("accepted")
        and item.get("ecosystem_final") != "unknown"
        and item.get("dialect_final") != "unknown"
    ]
    payload = {
        "source_file": args.input,
        "definition": "accepted=true 且 ecosystem_final、dialect_final 均不为 unknown。领域不强制，留给人工复核。",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "summary": {
            "domain_counts": dict(Counter(item["domain_final"] for item in candidates)),
            "ecosystem_counts": dict(Counter(item["ecosystem_final"] for item in candidates)),
            "dialect_counts": dict(Counter(item["dialect_final"] for item in candidates)),
            "license_counts": dict(Counter(item["license"] for item in candidates)),
        },
    }
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv_output, candidates)
    write_report(args.report_output, payload)
    return 0


def write_csv(path: str, candidates: list[dict]) -> None:
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
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            writer.writerow({field: item.get(field, "") for field in fieldnames})


def write_report(path: str, payload: dict) -> None:
    lines = [
        "# Schema 相关高置信候选说明",
        "",
        "## 口径",
        "",
        "- `accepted = true`；",
        "- `ecosystem_final != unknown`；",
        "- `dialect_final != unknown`；",
        "- 不强制要求业务领域非 unknown，因为领域更依赖人工语义判断。",
        "",
        f"候选数量：{payload['candidate_count']}",
        "",
        "## 技术栈 / 数据库生态分布",
        "",
        *fmt(payload["summary"]["ecosystem_counts"]),
        "",
        "## 方言 / schema 生态分布",
        "",
        *fmt(payload["summary"]["dialect_counts"]),
        "",
        "## 业务领域分布",
        "",
        *fmt(payload["summary"]["domain_counts"]),
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def fmt(counter: dict[str, int]) -> list[str]:
    return [f"- `{k}`: {v}" for k, v in sorted(counter.items(), key=lambda item: item[1], reverse=True)]


if __name__ == "__main__":
    raise SystemExit(main())

