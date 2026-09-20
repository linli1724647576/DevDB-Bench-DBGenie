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

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidate_records = [
        record
        for record in raw["records"]
        if record.get("review_status") in {"accepted", "needs_review"}
    ]
    deduped: dict[str, dict[str, Any]] = {}
    for record in candidate_records:
        full_name = record["full_name"]
        existing = deduped.get(full_name)
        if existing is None:
            deduped[full_name] = record
            continue
        if _rank(record) > _rank(existing):
            deduped[full_name] = record

    candidates = sorted(
        deduped.values(),
        key=lambda item: (_rank(item), item.get("stars", 0)),
        reverse=True,
    )

    payload = {
        "source_file": args.input,
        "candidate_count": len(candidates),
        "strict_accepted_count": sum(1 for item in candidates if item.get("accepted")),
        "needs_review_count": sum(1 for item in candidates if item.get("review_status") == "needs_review"),
        "candidates": candidates,
        "summary": build_summary(raw, candidates),
    }
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(args.csv_output, candidates)
    write_report(args.report_output, payload)
    return 0


def _rank(record: dict[str, Any]) -> int:
    if record.get("accepted"):
        return 2
    if record.get("review_status") == "needs_review":
        return 1
    return 0


def build_summary(raw: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "query_count": raw.get("query_count", 0),
        "scanned_unique": raw.get("scanned_unique", 0),
        "raw_record_count": len(raw.get("records", [])),
        "candidate_count": len(candidates),
        "strict_accepted_count": sum(1 for item in candidates if item.get("accepted")),
        "needs_review_count": sum(1 for item in candidates if item.get("review_status") == "needs_review"),
        "domain_counts": dict(Counter(item.get("domain_guess", "unknown") for item in candidates)),
        "ecosystem_counts": dict(Counter(item.get("ecosystem_guess", "unknown") for item in candidates)),
        "dialect_counts": dict(Counter(item.get("dialect_guess", "unknown") for item in candidates)),
        "license_counts": dict(Counter(item.get("license", "unknown") for item in candidates)),
        "top_rejection_reasons": _reason_counts(raw.get("records", [])),
        "query_summaries": raw.get("query_summaries", []),
    }


def _reason_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        for reason in record.get("reasons", []):
            counter[reason.split(":", 1)[0]] += 1
    return dict(counter.most_common())


def write_csv(path: str, candidates: list[dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "full_name",
        "url",
        "review_status",
        "accepted",
        "domain_guess",
        "ecosystem_guess",
        "dialect_guess",
        "license",
        "stars",
        "forks",
        "contributors",
        "pushed_at",
        "path_count",
        "query",
        "reasons",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            row = {field: item.get(field, "") for field in fieldnames}
            row["reasons"] = ";".join(item.get("reasons", []))
            writer.writerow(row)


def write_report(path: str, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# GitHub 应用仓库候选搜集总结",
        "",
        "## 搜集目标",
        "",
        "- 搜集真实应用仓库候选，不下载源码文件。",
        "- 候选需尽量覆盖不同业务领域、技术栈、数据库生态和 SQL 方言。",
        "- 本轮先整理约 150 个候选仓库，后续全部进入人工验证流程，最终保留 50-100 个高质量样本。",
        "",
        "## 本轮结果",
        "",
        f"- 使用 query 数量：{summary['query_count']}",
        f"- 扫描去重仓库数：{summary['scanned_unique']}",
        f"- 原始记录数：{summary['raw_record_count']}",
        f"- 候选仓库数：{summary['candidate_count']}",
        f"- 严格自动通过数：{summary['strict_accepted_count']}",
        f"- 待人工复核候选数：{summary['needs_review_count']}",
        "",
        "## 输出文件",
        "",
        "- JSON 候选集：`runs/candidate_repositories_2026-05-26.json`",
        "- CSV 候选集：`runs/candidate_repositories_2026-05-26.csv`",
        "- 原始筛选输出：`runs/candidate_repositories_raw_2026-05-26_v4.json`",
        "",
        "## 业务领域分布（自动猜测）",
        "",
        *format_counter(summary["domain_counts"]),
        "",
        "## 技术栈 / 数据库生态分布（自动猜测）",
        "",
        *format_counter(summary["ecosystem_counts"]),
        "",
        "## SQL 方言 / schema 生态分布（自动猜测）",
        "",
        *format_counter(summary["dialect_counts"]),
        "",
        "## License 分布",
        "",
        *format_counter(summary["license_counts"]),
        "",
        "## 主要拒绝原因",
        "",
        *format_counter(summary["top_rejection_reasons"], limit=12),
        "",
        "## 观察与问题",
        "",
        "- GitHub Search query 只能作为候选召回入口，不能证明仓库一定是真实应用。",
        "- topic-based query 的精度比普通关键词更高，但召回不稳定。",
        "- Go、Java、C# 等生态在当前 query 下召回较少，需要后续补充更贴近具体框架和业务领域的 query。",
        "- 自动领域、技术栈、方言识别只是基于 repo metadata、query 和路径的启发式猜测，必须人工复核。",
        "- 部分仓库可能因为 license metadata 缺失、schema 放在非常规路径、或应用结构命名不同而被误拒。",
        "- 本轮没有下载源码文件，只保存仓库链接和元数据；后续人工验证时再按需查看必要文件。",
        "",
        "## 下一步人工验证建议",
        "",
        "对每个候选仓库至少检查：",
        "",
        "- 是否真实应用，而不是框架、库、模板、教程或示例集合；",
        "- license 是否允许研究使用；",
        "- database design 是否可抽取，且至少包含多张相关表；",
        "- 原始数据库生态或 SQL 方言是什么；",
        "- README / docs / route / service / repository / tests 是否足以支撑 requirement、business rules 和 workload 构造；",
        "- 是否应进入最终 50-100 个样本。",
        "",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def format_counter(counter: dict[str, int], limit: int | None = None) -> list[str]:
    items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
    if limit is not None:
        items = items[:limit]
    if not items:
        return ["- 无"]
    return [f"- `{key}`: {value}" for key, value in items]


if __name__ == "__main__":
    raise SystemExit(main())

