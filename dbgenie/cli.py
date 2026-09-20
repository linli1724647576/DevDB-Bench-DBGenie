from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from dbgenie.core.config import get_llm_config, load_config
from dbgenie.core.io import read_json, write_json
from dbgenie.core.sample import BenchmarkSample
from benchmark.construction.quality import DatasetQualityChecker
from benchmark.construction.screening import RepositoryScreeningPipeline
from benchmark.construction.github import GitHubAPIError
from benchmark.construction.enrichment import CandidateEnricher
from dbgenie.evaluation.static_match import (
    GeneratedRuntimeIRConfig,
    ReferenceRuntimeIRConfig,
    StaticMatchConfig,
    evaluate_static_match,
    prepare_generated_runtime_ir,
    prepare_reference_runtime_ir,
)
from benchmark.construction.schema_materialization import (
    MaterializationPaths,
    SchemaMaterializer,
    build_materialization_report,
)
from benchmark.construction.reference_ddl import (
    build_reference_ddl_report,
    generate_reference_ddl_for_candidate,
)
from benchmark.construction.schema_recollection import (
    RecollectionPaths,
    SchemaEvidenceRecollector,
    build_recollection_payload,
)
from benchmark.construction.nl_construction import (
    _validate_requirement_only,
    build_requirement_construction_report,
    build_nl_construction_report,
    construct_candidates,
    construct_requirements,
)
from dbgenie.llm.client import LLMClient
from dbgenie.core.io import write_text
from dbgenie.methods.baselines.cli import run_baseline
from dbgenie.methods.baselines.registry import available_baseline_methods
from dbgenie.methods.ablations.registry import available_method_variants
from dbgenie.methods.dynamic.cli import run_method


def _add_static_design_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--embedding-backend",
        choices=["fastembed", "sentence-transformers", "http"],
        default="fastembed",
    )
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
    )
    parser.add_argument("--embedding-cache-dir", default="models/fastembed")
    parser.add_argument("--embedding-url", default="")
    parser.add_argument("--similarity-threshold", type=float, default=0.6)
    parser.add_argument("--string-threshold", type=float, default=0.75)
    parser.add_argument("--accuracy-f1-threshold", type=float, default=0.9)
    parser.add_argument("--accuracy-medium-f1-threshold", type=float, default=0.8)
    parser.add_argument("--accuracy-hard-f1-threshold", type=float, default=0.7)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument(
        "--generated-runtime-ir-dir",
        help=(
            "Generated runtime IR cache directory. Defaults to "
            "runs/evaluation/generated_runtime_ir_<run-dir-name>."
        ),
    )
    parser.add_argument(
        "--reference-runtime-ir-dir",
        default="runs/evaluation/reference_runtime_ir",
    )
    parser.add_argument("--detail-limit", type=int, default=25)
    parser.add_argument("--no-runtime-ir", action="store_true")
    parser.add_argument("--keep-containers", action="store_true")
    parser.add_argument("--refresh-reference-runtime-ir", action="store_true")
    parser.add_argument("--refresh-generated-runtime-ir", action="store_true")
    parser.add_argument("--accept-legacy-generated-runtime-ir", action="store_true")
    parser.add_argument("--runtime-ir-cache-only", action="store_true")
    parser.add_argument("--no-progress", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dbgenie")
    parser.add_argument("--config", default="configs/default.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-sample")
    validate_parser.add_argument("sample_path")
    validate_parser.add_argument("--output")

    static_match_parser = subparsers.add_parser("evaluate-static-match")
    static_match_parser.add_argument("candidate_json")
    static_match_parser.add_argument("--run-dir", required=True)
    static_match_parser.add_argument("--output", required=True)
    _add_static_design_args(static_match_parser)

    design_static_parser = subparsers.add_parser("evaluate-design-static")
    design_static_parser.add_argument("candidate_json")
    design_static_parser.add_argument("--run-dir", required=True)
    design_static_parser.add_argument("--output", required=True)
    _add_static_design_args(design_static_parser)

    prepare_reference_parser = subparsers.add_parser("prepare-reference-runtime-ir")
    prepare_reference_parser.add_argument("candidate_json")
    prepare_reference_parser.add_argument("--output", required=True)
    prepare_reference_parser.add_argument(
        "--reference-runtime-ir-dir",
        default="runs/evaluation/reference_runtime_ir",
    )
    prepare_reference_parser.add_argument("--task-id", action="append", default=[])
    prepare_reference_parser.add_argument("--limit", type=int)
    prepare_reference_parser.add_argument("--refresh", action="store_true")
    prepare_reference_parser.add_argument("--keep-containers", action="store_true")
    prepare_reference_parser.add_argument("--no-progress", action="store_true")

    prepare_generated_parser = subparsers.add_parser("prepare-generated-runtime-ir")
    prepare_generated_parser.add_argument("candidate_json")
    prepare_generated_parser.add_argument("--run-dir", required=True)
    prepare_generated_parser.add_argument("--output", required=True)
    prepare_generated_parser.add_argument(
        "--generated-runtime-ir-dir",
        help=(
            "Generated runtime IR cache directory. Defaults to "
            "runs/evaluation/generated_runtime_ir_<run-dir-name>."
        ),
    )
    prepare_generated_parser.add_argument("--task-id", action="append", default=[])
    prepare_generated_parser.add_argument("--limit", type=int)
    prepare_generated_parser.add_argument("--refresh", action="store_true")
    prepare_generated_parser.add_argument("--accept-legacy", action="store_true")
    prepare_generated_parser.add_argument("--keep-containers", action="store_true")
    prepare_generated_parser.add_argument("--no-progress", action="store_true")

    screen_parser = subparsers.add_parser("screen-repositories")
    screen_parser.add_argument("--query", required=True)
    screen_parser.add_argument("--max-repos", type=int, default=50)
    screen_parser.add_argument("--skip-tree-filter", action="store_true")
    screen_parser.add_argument("--accepted-only", action="store_true")
    screen_parser.add_argument("--output")

    batch_screen_parser = subparsers.add_parser("screen-repositories-batch")
    batch_screen_parser.add_argument("--max-repos-per-query", type=int, default=20)
    batch_screen_parser.add_argument("--target-accepted", type=int)
    batch_screen_parser.add_argument("--target-candidates", type=int)
    batch_screen_parser.add_argument("--skip-tree-filter", action="store_true")
    batch_screen_parser.add_argument("--accepted-only", action="store_true")
    batch_screen_parser.add_argument("--output")
    batch_screen_parser.add_argument("--progress", action="store_true")

    enrich_parser = subparsers.add_parser("enrich-candidates")
    enrich_parser.add_argument("candidate_json")
    enrich_parser.add_argument("--output", required=True)
    enrich_parser.add_argument("--checkpoint-jsonl")
    enrich_parser.add_argument("--limit", type=int)
    enrich_parser.add_argument("--progress", action="store_true")

    materialize_parser = subparsers.add_parser("materialize-schema")
    materialize_parser.add_argument("candidate_json")
    materialize_parser.add_argument("--output", required=True)
    materialize_parser.add_argument(
        "--schema-ir-dir",
        default="benchmark/schema_ir_drafts",
    )
    materialize_parser.add_argument(
        "--reference-ddl-dir",
        default="benchmark/reference_ddl_drafts",
    )
    materialize_parser.add_argument(
        "--report-output",
        default="docs/schema_materialization_report_2026-05-29.md",
    )
    materialize_parser.add_argument("--limit", type=int)
    materialize_parser.add_argument("--dry-run", action="store_true")
    materialize_parser.add_argument("--progress", action="store_true")

    reference_ddl_parser = subparsers.add_parser("generate-reference-ddl")
    reference_ddl_parser.add_argument("candidate_json")
    reference_ddl_parser.add_argument("--output", required=True)
    reference_ddl_parser.add_argument(
        "--reference-ddl-dir",
        default="benchmark/reference_ddl/final_validated",
    )
    reference_ddl_parser.add_argument(
        "--report-output",
        default="docs/current/reference_ddl_generation_report_2026-06-01.md",
    )
    reference_ddl_parser.add_argument("--limit", type=int)
    reference_ddl_parser.add_argument("--dry-run", action="store_true")
    reference_ddl_parser.add_argument("--progress", action="store_true")

    recollect_parser = subparsers.add_parser("recollect-schema-evidence")
    recollect_parser.add_argument("target_json")
    recollect_parser.add_argument("--output", required=True)
    recollect_parser.add_argument("--augmented-output")
    recollect_parser.add_argument("--checkpoint-jsonl")
    recollect_parser.add_argument(
        "--evidence-dir",
        default="benchmark/evidence_materials/schema_recollection_2026-06-01",
    )
    recollect_parser.add_argument("--limit", type=int)
    recollect_parser.add_argument("--progress", action="store_true")

    nl_parser = subparsers.add_parser("construct-nl-tests")
    nl_parser.add_argument("candidate_json")
    nl_parser.add_argument("--output", required=True)
    nl_parser.add_argument(
        "--draft-dir",
        default=(
            "benchmark/sample_drafts/"
            "final_50_req_br_workload_tests_2026-06-02"
        ),
    )
    nl_parser.add_argument(
        "--report-output",
        default=(
            "docs/current/"
            "requirements_business_rules_workload_tests_construction_report_2026-06-02.md"
        ),
    )
    nl_parser.add_argument("--limit", type=int)
    nl_parser.add_argument("--dry-run", action="store_true")
    nl_parser.add_argument("--progress", action="store_true")

    req_parser = subparsers.add_parser("construct-requirements")
    req_parser.add_argument("candidate_json")
    req_parser.add_argument("--output", required=True)
    req_parser.add_argument(
        "--draft-dir",
        default=(
            "benchmark/sample_drafts/"
            "requirements_only_2026-06-09"
        ),
    )
    req_parser.add_argument(
        "--report-output",
        default="docs/current/requirements_only_construction_report_2026-06-09.md",
    )
    req_parser.add_argument("--limit", type=int)
    req_parser.add_argument("--min-tables", type=int, default=0)
    req_parser.add_argument(
        "--evidence-only",
        action="store_true",
        help=(
            "Regenerate requirements from requirement evidence only; do not pass "
            "Schema IR, reference DDL, schema evidence, or schema summaries to the LLM."
        ),
    )
    req_parser.add_argument("--dry-run", action="store_true")
    req_parser.add_argument("--progress", action="store_true")

    method_parser = subparsers.add_parser('run-method')
    method_parser.add_argument("input_json")
    method_parser.add_argument("--output", required=True)
    method_parser.add_argument(
        "--input-format",
        choices=["auto", "candidate", "task"],
        default="auto",
    )
    method_parser.add_argument("--config", default="configs/default.toml")
    method_parser.add_argument("--llm-profile", default="default")
    method_parser.add_argument(
        "--variant",
        choices=available_method_variants(),
        default="full",
    )
    method_parser.add_argument("--run-dir")
    method_parser.add_argument(
        "--ddl-executor",
        choices=["docker"],
        default="docker",
    )
    method_parser.add_argument(
        "--max-turns",
        "--max-scheduler-steps",
        dest="max_turns",
        type=int,
        default=20,
        help="maximum normal scheduler decisions; trace events do not consume this budget",
    )
    method_parser.add_argument("--max-repairs", type=int, default=3)
    method_parser.add_argument("--limit", type=int)
    method_parser.add_argument("--dry-run", action="store_true")
    method_parser.add_argument("--progress", action="store_true")
    method_parser.add_argument("--jobs", type=int, default=1)

    baseline_parser = subparsers.add_parser("run-baseline")
    baseline_parser.add_argument("input_json")
    baseline_parser.add_argument(
        "--method",
        choices=available_baseline_methods(),
        required=True,
    )
    baseline_parser.add_argument("--output", required=True)
    baseline_parser.add_argument(
        "--input-format",
        choices=["auto", "candidate", "task"],
        default="auto",
    )
    baseline_parser.add_argument("--config", default="configs/default.toml")
    baseline_parser.add_argument("--llm-profile", default="default")
    baseline_parser.add_argument("--run-dir", default="runs/baseline")
    baseline_parser.add_argument("--trace-dir")
    baseline_parser.add_argument("--limit", type=int)
    baseline_parser.add_argument("--preview-prompt", action="store_true")
    baseline_parser.add_argument("--progress", action="store_true")
    baseline_parser.add_argument("--jobs", type=int, default=1)

    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "validate-sample":
        sample = _load_sample(args.sample_path)
        report = DatasetQualityChecker().check_sample(sample)
        payload = {
            "sample_id": sample.id,
            "passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings,
        }
        _emit(payload, args.output)
        return 0 if report.passed else 1

    if args.command == "prepare-reference-runtime-ir":
        result = prepare_reference_runtime_ir(
            ReferenceRuntimeIRConfig(
                candidate_json=Path(args.candidate_json),
                reference_runtime_ir_dir=Path(args.reference_runtime_ir_dir),
                limit=args.limit,
                task_ids=tuple(args.task_id),
                refresh=args.refresh,
                keep_containers=args.keep_containers,
                progress=not args.no_progress,
            )
        )
        write_json(args.output, result)
        return 0 if result["summary"]["failed_count"] == 0 else 1

    if args.command == "prepare-generated-runtime-ir":
        run_dir = Path(args.run_dir)
        generated_runtime_ir_dir = (
            Path(args.generated_runtime_ir_dir)
            if args.generated_runtime_ir_dir
            else Path("runs/evaluation") / f"generated_runtime_ir_{run_dir.name}"
        )
        result = prepare_generated_runtime_ir(
            GeneratedRuntimeIRConfig(
                candidate_json=Path(args.candidate_json),
                run_dir=run_dir,
                generated_runtime_ir_dir=generated_runtime_ir_dir,
                limit=args.limit,
                task_ids=tuple(args.task_id),
                refresh=args.refresh,
                accept_legacy=args.accept_legacy,
                keep_containers=args.keep_containers,
                progress=not args.no_progress,
            )
        )
        write_json(args.output, result)
        return 0 if result["summary"]["failed_count"] == 0 else 1

    if args.command in {"evaluate-static-match", "evaluate-design-static"}:
        run_dir = Path(args.run_dir)
        generated_runtime_ir_dir = (
            Path(args.generated_runtime_ir_dir)
            if args.generated_runtime_ir_dir
            else Path("runs/evaluation") / f"generated_runtime_ir_{run_dir.name}"
        )
        result = evaluate_static_match(
            StaticMatchConfig(
                candidate_json=Path(args.candidate_json),
                run_dir=run_dir,
                generated_runtime_ir_dir=generated_runtime_ir_dir,
                reference_runtime_ir_dir=Path(args.reference_runtime_ir_dir),
                embedding_backend=args.embedding_backend,
                embedding_model=args.embedding_model,
                embedding_cache_dir=(
                    Path(args.embedding_cache_dir) if args.embedding_cache_dir else None
                ),
                embedding_url=args.embedding_url,
                similarity_threshold=args.similarity_threshold,
                string_threshold=args.string_threshold,
                accuracy_f1_threshold=args.accuracy_f1_threshold,
                accuracy_medium_f1_threshold=args.accuracy_medium_f1_threshold,
                accuracy_hard_f1_threshold=args.accuracy_hard_f1_threshold,
                limit=args.limit,
                task_ids=tuple(args.task_id),
                detail_limit=args.detail_limit,
                write_runtime_ir=not args.no_runtime_ir,
                keep_containers=args.keep_containers,
                refresh_reference_runtime_ir=args.refresh_reference_runtime_ir,
                refresh_generated_runtime_ir=args.refresh_generated_runtime_ir,
                accept_legacy_generated_runtime_ir=(
                    args.accept_legacy_generated_runtime_ir
                ),
                runtime_ir_cache_only=args.runtime_ir_cache_only,
                progress=not args.no_progress,
            )
        )
        write_json(args.output, result)
        return 0

    if args.command == "screen-repositories":
        report = RepositoryScreeningPipeline(config.github, config.dataset).run(
            query=args.query,
            max_repos=args.max_repos,
            include_tree_filter=not args.skip_tree_filter,
        )
        _emit(report.to_dict(include_rejected=not args.accepted_only), args.output)
        return 0

    if args.command == "screen-repositories-batch":
        pipeline = RepositoryScreeningPipeline(config.github, config.dataset)
        query_reports = []
        accepted_seen: set[str] = set()
        candidate_seen: set[str] = set()
        scanned_seen: set[str] = set()
        queries = [query for query in config.dataset.screening_queries if query.strip()]
        for index, query in enumerate(queries, start=1):
            if args.progress:
                print(
                    f"[{index}/{len(queries)}] 开始筛选 query: {query}",
                    file=sys.stderr,
                    flush=True,
                )
            try:
                report = pipeline.run(
                    query=query,
                    max_repos=args.max_repos_per_query,
                    include_tree_filter=not args.skip_tree_filter,
                )
            except GitHubAPIError as exc:
                if args.progress:
                    print(
                        f"[{index}/{len(queries)}] query 失败，跳过: {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
                continue
            query_reports.append(report)
            for record in report.records:
                scanned_seen.add(record.repo.full_name)
                if record.accepted:
                    accepted_seen.add(record.repo.full_name)
                if record.review_status in {"accepted", "needs_review"}:
                    candidate_seen.add(record.repo.full_name)
            if args.progress:
                print(
                    f"[{index}/{len(queries)}] 完成: "
                    f"scanned={report.scanned}, accepted={report.accepted}, "
                    f"review_candidates={report.review_candidates}, "
                    f"candidate_unique={len(candidate_seen)}",
                    file=sys.stderr,
                    flush=True,
                )
            if args.target_accepted and len(accepted_seen) >= args.target_accepted:
                break
            if args.target_candidates and len(candidate_seen) >= args.target_candidates:
                break
        seen: set[str] = set()
        records = []
        for report in query_reports:
            for record in report.records:
                if record.repo.full_name in seen:
                    continue
                seen.add(record.repo.full_name)
                if args.accepted_only and not record.accepted:
                    continue
                records.append(record.to_dict())
        payload = {
            "query_count": len(query_reports),
            "max_repos_per_query": args.max_repos_per_query,
            "scanned_unique": len(seen),
            "accepted_unique": sum(1 for item in records if item["accepted"]),
            "candidate_unique": sum(
                1 for item in records if item.get("review_status") in {"accepted", "needs_review"}
            ),
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
            "records": records,
        }
        _emit(payload, args.output)
        return 0

    if args.command == "enrich-candidates":
        payload = read_json(args.candidate_json)
        candidates = payload.get("candidates", [])
        if args.limit:
            candidates = candidates[: args.limit]
        enricher = CandidateEnricher(config.github, config.dataset)
        enriched = []
        checkpoint = None
        if args.checkpoint_jsonl:
            checkpoint_path = Path(args.checkpoint_jsonl)
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint = checkpoint_path.open("w", encoding="utf-8")
        try:
            for index, candidate in enumerate(candidates, start=1):
                if args.progress:
                    print(
                        f"[{index}/{len(candidates)}] enrich {candidate.get('full_name')}",
                        file=sys.stderr,
                        flush=True,
                    )
                result = enricher.enrich(candidate)
                item = {
                    **candidate,
                    "domain_enriched": result.domain,
                    "ecosystem_enriched": result.ecosystem,
                    "dialect_enriched": result.dialect,
                    "dbms_enriched": result.dbms,
                    "schema_artifact_enriched": result.schema_artifact,
                    "enrichment_files": result.downloaded_files,
                    "enrichment_evidence": result.evidence,
                    "enrichment_errors": result.errors,
                }
                enriched.append(item)
                if checkpoint:
                    checkpoint.write(json.dumps(item, ensure_ascii=False) + "\n")
                    checkpoint.flush()
        finally:
            if checkpoint:
                checkpoint.close()
        output_payload = {
            "source_file": args.candidate_json,
            "candidate_count": len(enriched),
            "candidates": enriched,
        }
        write_json(args.output, output_payload)
        return 0

    if args.command == "materialize-schema":
        payload = read_json(args.candidate_json)
        candidates = payload.get("candidates", [])
        if args.limit:
            candidates = candidates[: args.limit]
        materializer = SchemaMaterializer(
            MaterializationPaths(
                schema_ir_dir=Path(args.schema_ir_dir),
                reference_ddl_dir=Path(args.reference_ddl_dir),
            )
        )
        augmented = []
        for index, candidate in enumerate(candidates, start=1):
            if args.progress:
                print(
                    f"[{index}/{len(candidates)}] materialize {candidate.get('full_name')}",
                    file=sys.stderr,
                    flush=True,
                )
            result = materializer.materialize(candidate, dry_run=args.dry_run)
            augmented.append({**candidate, "schema_materialization": result.to_dict()})
        output_payload = {
            "source_file": args.candidate_json,
            "candidate_count": len(augmented),
            "dry_run": bool(args.dry_run),
            "candidates": augmented,
        }
        write_json(args.output, output_payload)
        report = build_materialization_report(augmented, source_file=args.candidate_json)
        write_text(args.report_output, report)
        return 0

    if args.command == "generate-reference-ddl":
        payload = read_json(args.candidate_json)
        candidates = payload.get("candidates", [])
        if args.limit:
            candidates = candidates[: args.limit]
        output_dir = Path(args.reference_ddl_dir)
        augmented = []
        for index, candidate in enumerate(candidates, start=1):
            if args.progress:
                print(
                    f"[{index}/{len(candidates)}] generate reference DDL {candidate.get('full_name')}",
                    file=sys.stderr,
                    flush=True,
                )
            result = generate_reference_ddl_for_candidate(
                candidate,
                output_dir,
                dry_run=args.dry_run,
            )
            augmented.append({**candidate, "reference_ddl_generation": result.to_dict()})
        output_payload = dict(payload)
        results = [candidate["reference_ddl_generation"] for candidate in augmented]
        output_payload.update(
            {
                "description": (
                    "Final validated SchemaIR-ready candidate set with canonical "
                    "reference DDL generation results."
                ),
                "source_file": args.candidate_json,
                "candidate_count": len(augmented),
                "dry_run": bool(args.dry_run),
                "reference_ddl_dir": args.reference_ddl_dir,
                "reference_ddl_summary": {
                    "by_status": dict(Counter(result["status"] for result in results)),
                    "roundtrip": dict(
                        Counter(
                            "passed"
                            if result.get("roundtrip_validation", {}).get("passed")
                            else "failed"
                            for result in results
                        )
                    ),
                    "ddl_file_count": sum(1 for result in results if result.get("ddl_path")),
                    "preserved_source_ddl_sample_count": sum(
                        1 for result in results if result.get("preserved_source_ddl_files")
                    ),
                },
                "candidates": augmented,
            }
        )
        write_json(args.output, output_payload)
        report = build_reference_ddl_report(
            augmented,
            source_file=args.candidate_json,
            output_dir=args.reference_ddl_dir,
            dry_run=args.dry_run,
        )
        write_text(args.report_output, report)
        return 0

    if args.command == "recollect-schema-evidence":
        payload = read_json(args.target_json)
        targets = payload.get("targets", [])
        if args.limit:
            targets = targets[: args.limit]
        recollector = SchemaEvidenceRecollector(
            config.github,
            RecollectionPaths(evidence_dir=Path(args.evidence_dir)),
            max_files_per_repo=config.dataset.max_evidence_files_per_repo,
            max_file_bytes=config.dataset.max_file_bytes,
        )
        results = []
        checkpoint = None
        if args.checkpoint_jsonl:
            checkpoint_path = Path(args.checkpoint_jsonl)
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint = checkpoint_path.open("w", encoding="utf-8")
        try:
            for index, target in enumerate(targets, start=1):
                if args.progress:
                    print(
                        f"[{index}/{len(targets)}] recollect schema evidence {target.get('full_name')}",
                        file=sys.stderr,
                        flush=True,
                    )
                result = recollector.recollect(target)
                results.append(result)
                if checkpoint:
                    checkpoint.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
                    checkpoint.flush()
        finally:
            if checkpoint:
                checkpoint.close()
        output_payload = build_recollection_payload(payload, results, Path(args.evidence_dir))
        write_json(args.output, output_payload)
        if args.augmented_output:
            augmented_payload = {
                "generated_at": output_payload["generated_at"],
                "source_file": args.target_json,
                "target_count": len(output_payload["augmented_targets"]),
                "targets": output_payload["augmented_targets"],
            }
            write_json(args.augmented_output, augmented_payload)
        return 0

    if args.command == "construct-nl-tests":
        payload = read_json(args.candidate_json)
        candidates = payload.get("candidates", [])
        if args.limit:
            candidates = candidates[: args.limit]
        augmented = []
        llm_client = LLMClient(config.llm)
        for index, candidate in enumerate(candidates, start=1):
            if args.progress:
                print(
                    f"[{index}/{len(candidates)}] construct nl/tests {candidate.get('full_name')}",
                    file=sys.stderr,
                    flush=True,
                )
            result = construct_candidates(
                [candidate],
                llm_client=llm_client,
                draft_dir=Path(args.draft_dir),
                dry_run=bool(args.dry_run),
            )[0]
            augmented.append(result)
        output_payload = dict(payload)
        output_payload.update(
            {
                "description": (
                    "Final validated candidate set with generated requirement, "
                    "business rules, workload, tests.integrity, and tests.workload."
                ),
                "source_file": args.candidate_json,
                "candidate_count": len(augmented),
                "dry_run": bool(args.dry_run),
                "draft_dir": args.draft_dir,
                "candidates": augmented,
            }
        )
        write_json(args.output, output_payload)
        report = build_nl_construction_report(
            augmented,
            source_file=args.candidate_json,
            dry_run=bool(args.dry_run),
        )
        write_text(args.report_output, report)
        return 0

    if args.command == "construct-requirements":
        payload = read_json(args.candidate_json)
        source_candidates = payload.get("candidates", [])
        target_indices = list(range(len(source_candidates)))
        if args.min_tables:
            filtered_indices = []
            for index, candidate in enumerate(source_candidates):
                materialization = candidate.get("schema_materialization") or {}
                strict_stats = materialization.get("strict_ir_stats") or {}
                table_count = (
                    materialization.get("table_count")
                    or strict_stats.get("table_count")
                    or 0
                )
                if int(table_count) >= int(args.min_tables):
                    filtered_indices.append(index)
            target_indices = filtered_indices
        if args.limit:
            target_indices = target_indices[: args.limit]
        augmented = []
        llm_client = LLMClient(config.llm)
        for progress_index, candidate_index in enumerate(target_indices, start=1):
            candidate = source_candidates[candidate_index]
            draft_path = (
                Path(args.draft_dir)
                / f"{str(candidate.get('full_name') or '').replace('/', '__')}.requirement_draft.json"
            )
            if draft_path.exists() and not args.dry_run:
                draft = read_json(draft_path)
                draft_mode = (
                    (draft.get("evidence_bundle_summary") or {}).get(
                        "requirement_generation_mode"
                    )
                    or (
                        (draft.get("requirement_only_construction") or {}).get(
                            "agent_outputs"
                        )
                        or {}
                    ).get("requirement_generation_mode")
                )
                requested_mode = (
                    "evidence_only_no_schema_ir"
                    if args.evidence_only
                    else "schema_summary_assisted"
                )
                requirement_result = draft.get("requirement_only_construction") or {}
                existing_requirement = str(requirement_result.get("requirement") or "")
                if existing_requirement and draft_mode == requested_mode:
                    reused = dict(candidate)
                    reused["requirement"] = existing_requirement
                    nl_construction = dict(reused.get("nl_construction") or {})
                    nl_construction["requirement"] = existing_requirement
                    validation = _validate_requirement_only(
                        {"requirement": existing_requirement}
                    )
                    nl_construction["requirement_only"] = {
                        "status": "ready" if validation.get("passed") else "needs_human_review",
                        "validation": validation,
                        "warnings": requirement_result.get("warnings", []),
                        "errors": requirement_result.get("errors", []),
                        "draft_path": draft_path.as_posix(),
                        "reused_existing_draft": True,
                    }
                    reused["nl_construction"] = nl_construction
                    augmented.append((candidate_index, reused))
                    if args.progress:
                        print(
                            f"[{progress_index}/{len(target_indices)}] reuse requirement draft {candidate.get('full_name')}",
                            file=sys.stderr,
                            flush=True,
                        )
                    continue
            if args.progress:
                print(
                    f"[{progress_index}/{len(target_indices)}] construct requirement {candidate.get('full_name')}",
                    file=sys.stderr,
                    flush=True,
                )
            result = construct_requirements(
                [candidate],
                llm_client=llm_client,
                draft_dir=Path(args.draft_dir),
                dry_run=bool(args.dry_run),
                evidence_only=bool(args.evidence_only),
            )[0]
            augmented.append((candidate_index, result))
        output_candidates = list(source_candidates)
        for candidate_index, result in augmented:
            output_candidates[candidate_index] = result
        output_payload = dict(payload)
        output_payload.update(
            {
                "description": (
                    "Candidate set with regenerated requirement text only. "
                    "Business rules, workload, tests.integrity, and tests.workload "
                    "are preserved from the input."
                ),
                "source_file": args.candidate_json,
                "candidate_count": len(output_candidates),
                "requirement_regenerated_count": len(augmented),
                "dry_run": bool(args.dry_run),
                "draft_dir": args.draft_dir,
                "requirement_generation_mode": (
                    "evidence_only_no_schema_ir"
                    if args.evidence_only
                    else "schema_summary_assisted"
                ),
                "candidates": output_candidates,
            }
        )
        write_json(args.output, output_payload)
        augmented_candidates = [result for _, result in augmented]
        report = build_requirement_construction_report(
            augmented_candidates,
            source_file=args.candidate_json,
            dry_run=bool(args.dry_run),
        )
        write_text(args.report_output, report)
        return 0

    if args.command == "run-method":
        return run_method(_subcommand_args(argv, "run-method"))

    if args.command == "run-baseline":
        return run_baseline(_subcommand_args(argv, "run-baseline"))

    parser.error(f"Unknown command: {args.command}")
    return 2


def _load_sample(path: str | Path) -> BenchmarkSample:
    return BenchmarkSample.from_dict(read_json(path))


def _subcommand_args(argv: list[str] | None, command: str) -> list[str]:
    raw = list(sys.argv[1:] if argv is None else argv)
    try:
        index = raw.index(command)
    except ValueError:
        return raw
    return raw[index + 1 :]


def _emit(payload: dict, output_path: str | None) -> None:
    if output_path:
        write_json(output_path, payload)
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
