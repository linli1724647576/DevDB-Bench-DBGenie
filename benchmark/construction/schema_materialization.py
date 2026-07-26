from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbgenie.core.io import write_json, write_text
from dbgenie.core.schema_ir import SchemaIR
from benchmark.construction.schema_extraction import (
    ExtractionInputFile,
    extract_schema_static,
)


STATUS_STATIC_EXTRACTED = "static_extracted"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_NEEDS_HUMAN_REVIEW = "needs_human_review"

STRATEGY_STATIC_DIRECT_DDL = "static_direct_ddl"
STRATEGY_STATIC_PRISMA = "static_prisma"
STRATEGY_STATIC_ORM_CANDIDATE = "static_orm_candidate"
STRATEGY_STATIC_SCHEMA_CANDIDATE = "static_schema_candidate"
STRATEGY_SKIPPED = "skipped"

# Backward-compatible names used by earlier experiments/tests.
STATUS_MATERIALIZED = "materialized"
STATUS_INTROSPECTED = "introspected"
STRATEGY_DIRECT_DDL = "direct_ddl"
STRATEGY_NATIVE_MIGRATION = "native_migration_candidate"
STRATEGY_DDL_SYNTHESIS = "ddl_synthesis_candidate"


@dataclass(frozen=True)
class MaterializationPaths:
    schema_ir_dir: Path = Path("benchmark/schema_ir_drafts")
    reference_ddl_dir: Path = Path("benchmark/reference_ddl_drafts")


@dataclass
class SchemaMaterializationResult:
    strategy: str
    status: str
    commands: list[str] = field(default_factory=list)
    used_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extraction_warnings: list[str] = field(default_factory=list)
    unsupported_constructs: list[str] = field(default_factory=list)
    generated_ddl_path: str | None = None
    introspection_ir_path: str | None = None
    table_count: int = 0
    relationship_count: int = 0
    index_count: int = 0
    quality_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "status": self.status,
            "commands": self.commands,
            "used_files": self.used_files,
            "errors": self.errors,
            "extraction_warnings": self.extraction_warnings,
            "unsupported_constructs": self.unsupported_constructs,
            "generated_ddl_path": self.generated_ddl_path,
            "introspection_ir_path": self.introspection_ir_path,
            "table_count": self.table_count,
            "relationship_count": self.relationship_count,
            "index_count": self.index_count,
            "quality_warnings": self.quality_warnings,
        }


@dataclass(frozen=True)
class LocalSchemaFile:
    repo_path: str
    local_path: Path


class SchemaMaterializer:
    """Extract schema evidence files into draft Schema IR.

    The CLI command is still named `materialize-schema` for compatibility with
    earlier experiments, but the default behavior is static extraction. It does
    not start DBMS containers or run framework-native migration tools.
    """

    def __init__(self, paths: MaterializationPaths | None = None) -> None:
        self.paths = paths or MaterializationPaths()

    def materialize(
        self,
        candidate: dict[str, Any],
        dry_run: bool = False,
    ) -> SchemaMaterializationResult:
        schema_files = _schema_files(candidate)
        strategy = _select_strategy(candidate, schema_files)

        if dry_run:
            return SchemaMaterializationResult(
                strategy=strategy,
                status=STATUS_SKIPPED,
                used_files=[item.repo_path for item in schema_files],
                errors=["dry_run: only static strategy selection was executed"],
            )

        if not schema_files:
            return SchemaMaterializationResult(
                strategy=STRATEGY_SKIPPED,
                status=STATUS_SKIPPED,
                errors=["no usable local schema artifact was found"],
            )

        extraction_files = [
            ExtractionInputFile(repo_path=item.repo_path, local_path=item.local_path)
            for item in schema_files
        ]
        extraction = extract_schema_static(candidate, extraction_files)
        result = SchemaMaterializationResult(
            strategy=extraction.strategy,
            status=extraction.status,
            commands=["static schema extraction; no DBMS or framework CLI execution"],
            used_files=extraction.used_files,
            errors=extraction.errors,
            extraction_warnings=extraction.warnings,
            unsupported_constructs=extraction.unsupported_constructs,
        )

        sql_files = [item for item in schema_files if _is_sql_file(item.repo_path)]
        if sql_files:
            ddl_path = (
                self.paths.reference_ddl_dir
                / _repo_slug(candidate)
                / f"{_safe_filename(_candidate_dbms(candidate))}.sql"
            )
            try:
                write_text(ddl_path, _merge_sql_files(sql_files))
                result.generated_ddl_path = ddl_path.as_posix()
            except OSError as exc:
                result.status = STATUS_FAILED
                result.errors.append(f"failed to write DDL draft: {exc}")

        if extraction.schema_ir.tables:
            ir_path = self.paths.schema_ir_dir / f"{_repo_slug(candidate)}.schema_ir.json"
            write_json(ir_path, extraction.schema_ir.to_dict())
            result.introspection_ir_path = ir_path.as_posix()
            result.table_count = extraction.schema_ir.table_count()
            result.relationship_count = sum(
                len(table.foreign_keys) for table in extraction.schema_ir.tables
            )
            result.index_count = sum(len(table.indexes) for table in extraction.schema_ir.tables)
            result.quality_warnings = _quality_warnings(extraction.schema_ir)

        return result


def materialize_candidates(
    candidates: list[dict[str, Any]],
    paths: MaterializationPaths | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    materializer = SchemaMaterializer(paths)
    selected = candidates[:limit] if limit else candidates
    return [
        {**candidate, "schema_materialization": materializer.materialize(candidate, dry_run).to_dict()}
        for candidate in selected
    ]


def build_materialization_report(
    candidates: list[dict[str, Any]],
    source_file: str | None = None,
) -> str:
    materializations = [item.get("schema_materialization", {}) for item in candidates]
    status_counts = _count_by(materializations, "status")
    strategy_counts = _count_by(materializations, "strategy")
    dbms_counts = _count_candidates_by(candidates, "dbms_final")
    artifact_counts = _count_candidates_by(candidates, "schema_artifact_final")
    ready = [
        item
        for item in candidates
        if item.get("schema_materialization", {}).get("status") == STATUS_STATIC_EXTRACTED
        and not item.get("schema_materialization", {}).get("quality_warnings")
    ]
    review = [
        item
        for item in candidates
        if item.get("schema_materialization", {}).get("status")
        in {STATUS_PARTIAL, STATUS_FAILED, STATUS_SKIPPED, STATUS_NEEDS_HUMAN_REVIEW}
    ]

    lines = [
        "# Schema Extraction 报告",
        "",
        "- 生成日期：2026-05-31",
        f"- 输入文件：`{source_file or ''}`",
        f"- 样本数：{len(candidates)}",
        "",
        "## 流程说明",
        "",
        "当前实现采用：`source_files.schema -> Static Schema Extraction -> Schema IR Draft -> Reference DDL Draft -> Human Validation`。",
        "数据库执行和 introspection 仅作为后续可选验证，不再是主流程。",
        "",
        "## 状态统计",
        "",
        _format_counts(status_counts),
        "",
        "## 策略统计",
        "",
        _format_counts(strategy_counts),
        "",
        "## DBMS 分布",
        "",
        _format_counts(dbms_counts),
        "",
        "## Schema Artifact 分布",
        "",
        _format_counts(artifact_counts),
        "",
        "## 可优先进入人工验证的样本",
        "",
        _format_candidate_list(ready),
        "",
        "## 需要人工修正或后续增强的样本",
        "",
        _format_candidate_list(review, include_errors=True),
    ]
    return "\n".join(lines).rstrip() + "\n"

def _schema_files(candidate: dict[str, Any]) -> list[LocalSchemaFile]:
    files: list[LocalSchemaFile] = []
    local_source_files = candidate.get("local_source_files") or {}
    for item in local_source_files.get("schema") or []:
        repo_path = str(item.get("repo_path") or "")
        local_path = item.get("local_path")
        if not repo_path or not local_path:
            continue
        path = Path(str(local_path))
        if path.exists() and path.is_file():
            files.append(LocalSchemaFile(repo_path=repo_path, local_path=path))
    return files


def _select_strategy(candidate: dict[str, Any], schema_files: list[LocalSchemaFile]) -> str:
    if any(_is_sql_file(item.repo_path) for item in schema_files):
        return STRATEGY_STATIC_DIRECT_DDL
    repo_paths = [item.repo_path.lower().replace("\\", "/") for item in schema_files]
    artifact = str(candidate.get("schema_artifact_final") or "").lower()
    if any(path.endswith("schema.prisma") for path in repo_paths) or "prisma" in artifact:
        return STRATEGY_STATIC_PRISMA
    if any(
        marker in path
        for path in repo_paths
        for marker in (
            "db/schema.rb",
            "db/migrate/",
            "database/migrations/",
            "alembic/versions/",
            "migrations/",
        )
    ):
        return STRATEGY_STATIC_ORM_CANDIDATE
    if any(
        marker in artifact
        for marker in ("django", "typeorm", "sequelize", "ef core", "laravel", "rails", "alembic")
    ):
        return STRATEGY_STATIC_ORM_CANDIDATE
    if schema_files:
        return STRATEGY_STATIC_SCHEMA_CANDIDATE
    return STRATEGY_SKIPPED


def _is_sql_file(repo_path: str) -> bool:
    return repo_path.lower().replace("\\", "/").endswith(".sql")


def _merge_sql_files(files: list[LocalSchemaFile]) -> str:
    chunks = []
    for item in sorted(files, key=lambda file: file.repo_path.lower()):
        text = item.local_path.read_text(encoding="utf-8", errors="replace")
        chunks.append(f"-- source: {item.repo_path}\n{text.strip()}\n")
    return "\n\n".join(chunks).strip() + "\n"


def _quality_warnings(schema_ir: SchemaIR) -> list[str]:
    warnings = []
    if not schema_ir.tables:
        warnings.append("Schema IR is empty")
    if schema_ir.table_count() < 3:
        warnings.append("schema has fewer than 3 tables")
    return warnings


def _candidate_dbms(candidate: dict[str, Any]) -> str:
    return str(candidate.get("dbms_final") or candidate.get("dbms") or "unknown")


def _repo_slug(candidate: dict[str, Any]) -> str:
    full_name = str(candidate.get("full_name") or "unknown__repo")
    return full_name.replace("/", "__").replace("\\", "__")


def _safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return safe or "unknown"


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


def _count_candidates_by(candidates: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        value = str(candidate.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "无。"
    return "\n".join(f"- {key}: {value}" for key, value in counts.items())


def _format_candidate_list(
    candidates: list[dict[str, Any]],
    include_errors: bool = False,
    limit: int = 50,
) -> str:
    if not candidates:
        return "无。"
    lines = []
    for candidate in candidates[:limit]:
        materialization = candidate.get("schema_materialization", {})
        line = (
            f"- `{candidate.get('full_name')}` | "
            f"DBMS={candidate.get('dbms_final')} | "
            f"status={materialization.get('status')} | "
            f"strategy={materialization.get('strategy')}"
        )
        if include_errors and materialization.get("errors"):
            line += f" | errors={'; '.join(materialization.get('errors', [])[:2])}"
        lines.append(line)
    if len(candidates) > limit:
        lines.append(f"- ... 另有 {len(candidates) - limit} 个样本未展开")
    return "\n".join(lines)

