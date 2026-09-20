from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbgenie.core.io import read_json, write_json
from dbgenie.core.schema_ir import SchemaIR
from dbgenie.llm.client import LLMClient, LLMMessage

from .prompts import (
    CODE_ANALYSIS_AGENT_PROMPT,
    INTEGRITY_TEST_AGENT_PROMPT,
    INTEGRITY_TEST_REVIEW_AGENT_PROMPT,
    REQUIREMENT_ONLY_CODE_ANALYSIS_AGENT_PROMPT,
    REQUIREMENT_ONLY_AGENT_PROMPT,
    REQUIREMENT_ONLY_REVIEW_AGENT_PROMPT,
    REQUIREMENT_RULE_AGENT_PROMPT,
    REQUIREMENT_RULE_REVIEW_AGENT_PROMPT,
    WORKLOAD_AGENT_PROMPT,
    WORKLOAD_REVIEW_AGENT_PROMPT,
)


@dataclass(frozen=True)
class NLConstructionPaths:
    draft_dir: Path = Path(
        "benchmark/sample_drafts/"
        "final_50_req_br_workload_tests_2026-06-02"
    )


@dataclass
class NLConstructionResult:
    status: str
    project_summary: str = ""
    requirement: str = ""
    business_rules: list[dict[str, Any]] = field(default_factory=list)
    workload: list[dict[str, Any]] = field(default_factory=list)
    tests: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {"integrity": [], "workload": []}
    )
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    draft_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "project_summary": self.project_summary,
            "requirement": self.requirement,
            "business_rules": self.business_rules,
            "workload": self.workload,
            "tests": self.tests,
            "agent_outputs": self.agent_outputs,
            "validation": self.validation,
            "warnings": self.warnings,
            "errors": self.errors,
            "draft_path": self.draft_path,
        }


@dataclass
class RequirementOnlyConstructionResult:
    status: str
    requirement: str = ""
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    draft_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "requirement": self.requirement,
            "agent_outputs": self.agent_outputs,
            "validation": self.validation,
            "warnings": self.warnings,
            "errors": self.errors,
            "draft_path": self.draft_path,
        }


class NLConstructionPipeline:
    def __init__(self, llm_client: LLMClient, paths: NLConstructionPaths | None = None) -> None:
        self.llm_client = llm_client
        self.paths = paths or NLConstructionPaths()

    def construct(self, candidate: dict[str, Any], dry_run: bool = False) -> NLConstructionResult:
        bundle = _build_evidence_bundle(candidate)
        result = NLConstructionResult(status="dry_run" if dry_run else "failed")
        if dry_run:
            result.agent_outputs = {
                "code_analysis_prompt": _messages_to_dict(
                    self._code_analysis_messages(bundle)
                ),
                "requirement_business_rule_prompt": _messages_to_dict(
                    self._requirement_messages(bundle, {"dry_run": True})
                ),
                "requirement_business_rule_review_prompt": _messages_to_dict(
                    self._requirement_review_messages(bundle, {"dry_run": True})
                ),
                "integrity_test_prompt": _messages_to_dict(
                    self._integrity_messages(bundle, {"business_rules": []})
                ),
                "integrity_test_review_prompt": _messages_to_dict(
                    self._integrity_review_messages(bundle, {"tests": {"integrity": []}})
                ),
                "workload_prompt": _messages_to_dict(
                    self._workload_messages(bundle, {"dry_run": True})
                ),
                "workload_review_prompt": _messages_to_dict(
                    self._workload_review_messages(bundle, {"workload": []})
                ),
            }
            result.validation = _validate_constructed_fields(candidate, result.to_dict())
            self._write_draft(candidate, bundle, result)
            return result

        if not self.llm_client.is_configured():
            result.errors.append("llm_not_configured")
            self._write_draft(candidate, bundle, result)
            return result

        try:
            code_analysis = self._call_json(self._code_analysis_messages(bundle))
            requirement_payload = self._call_json(
                self._requirement_messages(bundle, code_analysis)
            )
            requirement_review = self._call_json(
                self._requirement_review_messages(bundle, requirement_payload)
            )
            if not requirement_review.get("passed"):
                revision = {
                    "previous_output": requirement_payload,
                    "review": requirement_review,
                }
                requirement_payload = self._call_json(
                    self._requirement_messages(bundle, code_analysis, revision)
                )
                requirement_review = self._call_json(
                    self._requirement_review_messages(bundle, requirement_payload)
                )

            integrity_payload = self._call_json(
                self._integrity_messages(bundle, requirement_payload)
            )
            integrity_review = self._call_json(
                self._integrity_review_messages(bundle, requirement_payload, integrity_payload)
            )
            if _needs_integrity_feedback(requirement_payload, integrity_payload):
                revision = {
                    "previous_output": requirement_payload,
                    "integrity_generation_result": integrity_payload,
                    "revision_goal": (
                        "Revise business_rules so testable=true is used only for "
                        "evidence-grounded rules that can be tested on the provided "
                        "reference schema. Convert unsupported application-only rules "
                        "to testable=false, and add/replace with database-testable "
                        "rules when requirement/schema evidence and reference schema "
                        "support them. Do not make every rule testable=false if "
                        "schema-backed uniqueness, required-field, foreign-key, or "
                        "state constraints are available. If parent/reference tables "
                        "are missing, keep unique/not-null/primary-key rules testable "
                        "when they can be tested on tables present in the reference DDL."
                    ),
                }
                requirement_payload = self._call_json(
                    self._requirement_messages(bundle, code_analysis, revision)
                )
                requirement_review = self._call_json(
                    self._requirement_review_messages(bundle, requirement_payload)
                )
                integrity_payload = self._call_json(
                    self._integrity_messages(bundle, requirement_payload)
                )
                integrity_review = self._call_json(
                    self._integrity_review_messages(bundle, requirement_payload, integrity_payload)
                )

            workload_payload = self._call_json(
                self._workload_messages(bundle, code_analysis)
            )
            workload_review = self._call_json(
                self._workload_review_messages(bundle, workload_payload)
            )
            if not workload_review.get("passed"):
                revision = {
                    "previous_output": workload_payload,
                    "review": workload_review,
                }
                workload_payload = self._call_json(
                    self._workload_messages(bundle, code_analysis, revision)
                )
                workload_review = self._call_json(
                    self._workload_review_messages(bundle, workload_payload)
                )

            result.project_summary = str(requirement_payload.get("project_summary", ""))
            result.requirement = str(requirement_payload.get("requirement", ""))
            result.business_rules = _as_list(requirement_payload.get("business_rules"))
            result.workload = _as_list(workload_payload.get("workload"))
            result.tests = {
                "integrity": _as_list(
                    (integrity_payload.get("tests") or {}).get("integrity")
                ),
                "workload": _as_list((workload_payload.get("tests") or {}).get("workload")),
            }
            result.agent_outputs = {
                "code_analysis": code_analysis,
                "requirement_business_rule": requirement_payload,
                "requirement_business_rule_review": requirement_review,
                "integrity_test": integrity_payload,
                "integrity_test_review": integrity_review,
                "workload": workload_payload,
                "workload_review": workload_review,
            }
            result.warnings.extend(_as_str_list(requirement_payload.get("warnings")))
            result.warnings.extend(_as_str_list(integrity_payload.get("warnings")))
            result.warnings.extend(_as_str_list(workload_payload.get("warnings")))
            result.validation = _validate_constructed_fields(candidate, result.to_dict())
            result.status = "ready" if result.validation.get("passed") else "needs_human_review"
        except Exception as exc:  # Keep batch processing alive for other samples.
            result.status = "failed"
            result.errors.append(str(exc))

        self._write_draft(candidate, bundle, result)
        return result

    def construct_requirement_only(
        self,
        candidate: dict[str, Any],
        dry_run: bool = False,
        evidence_only: bool = False,
    ) -> RequirementOnlyConstructionResult:
        bundle = (
            _build_requirement_evidence_only_bundle(candidate)
            if evidence_only
            else _build_evidence_bundle(candidate)
        )
        result = RequirementOnlyConstructionResult(status="dry_run" if dry_run else "failed")
        if dry_run:
            result.agent_outputs = {
                "requirement_generation_mode": (
                    "evidence_only_no_schema_ir" if evidence_only else "schema_summary_assisted"
                ),
                "code_analysis_prompt": _messages_to_dict(
                    self._code_analysis_messages(bundle, requirement_only=evidence_only)
                ),
                "requirement_only_prompt": _messages_to_dict(
                    self._requirement_only_messages(
                        bundle,
                        {"dry_run": True},
                        evidence_only=evidence_only,
                    )
                ),
                "requirement_only_review_prompt": _messages_to_dict(
                    self._requirement_only_review_messages(
                        bundle,
                        {"requirement": ""},
                        evidence_only=evidence_only,
                    )
                ),
            }
            result.validation = _validate_requirement_only(result.to_dict())
            self._write_requirement_draft(candidate, bundle, result)
            return result

        if not self.llm_client.is_configured():
            result.errors.append("llm_not_configured")
            self._write_requirement_draft(candidate, bundle, result)
            return result

        try:
            code_analysis = self._call_json(
                self._code_analysis_messages(bundle, requirement_only=evidence_only)
            )
            requirement_payload = self._call_json(
                self._requirement_only_messages(
                    bundle,
                    code_analysis,
                    evidence_only=evidence_only,
                )
            )
            review = self._call_json(
                self._requirement_only_review_messages(
                    bundle,
                    requirement_payload,
                    evidence_only=evidence_only,
                )
            )
            if not review.get("passed"):
                revision = {
                    "previous_output": requirement_payload,
                    "review": review,
                }
                requirement_payload = self._call_json(
                    self._requirement_only_messages(
                        bundle,
                        code_analysis,
                        revision,
                        evidence_only=evidence_only,
                    )
                )
                review = self._call_json(
                    self._requirement_only_review_messages(
                        bundle,
                        requirement_payload,
                        evidence_only=evidence_only,
                    )
                )

            local_validation = _validate_requirement_only(
                {"requirement": str(requirement_payload.get("requirement", ""))}
            )
            if not local_validation.get("passed"):
                revision = {
                    "previous_output": requirement_payload,
                    "review": review,
                    "local_validation": local_validation,
                    "revision_goal": (
                        "Rewrite the requirement to remove every locally flagged issue. "
                        "Keep it as one natural paragraph focused on database design, but "
                        "avoid implementation terms such as table, column, foreign key, "
                        "DDL, ORM, and migration unless the word is clearly part of the "
                        "business domain. Do not include benchmark/meta wording."
                    ),
                }
                requirement_payload = self._call_json(
                    self._requirement_only_messages(
                        bundle,
                        code_analysis,
                        revision,
                        evidence_only=evidence_only,
                    )
                )
                review = self._call_json(
                    self._requirement_only_review_messages(
                        bundle,
                        requirement_payload,
                        evidence_only=evidence_only,
                    )
                )

            result.requirement = str(requirement_payload.get("requirement", ""))
            result.agent_outputs = {
                "requirement_generation_mode": (
                    "evidence_only_no_schema_ir" if evidence_only else "schema_summary_assisted"
                ),
                "code_analysis": code_analysis,
                "requirement_only": requirement_payload,
                "requirement_only_review": review,
            }
            result.warnings.extend(_as_str_list(requirement_payload.get("warnings")))
            if not review.get("passed"):
                result.warnings.extend(_as_str_list(review.get("issues")))
            result.validation = _validate_requirement_only(result.to_dict())
            result.status = "ready" if result.validation.get("passed") else "needs_human_review"
        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))

        self._write_requirement_draft(candidate, bundle, result)
        return result

    def _call_json(self, messages: list[LLMMessage]) -> dict[str, Any]:
        retry_messages = list(messages)
        last_error: Exception | None = None
        for attempt in range(1, 4):
            raw = self.llm_client.complete(retry_messages)
            try:
                parsed = _parse_json_response(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                retry_messages = [
                    *messages,
                    LLMMessage(
                        "user",
                        "Your previous response was not valid JSON. Return only strict "
                        "JSON matching the requested object schema. Do not include "
                        "markdown fences, comments, or explanatory text.",
                    ),
                ]
                continue
            if not isinstance(parsed, dict):
                last_error = RuntimeError("LLM response JSON must be an object.")
                continue
            return parsed
        raise RuntimeError(str(last_error or "LLM response JSON parse failed."))

    def _code_analysis_messages(
        self,
        bundle: dict[str, Any],
        requirement_only: bool = False,
    ) -> list[LLMMessage]:
        system_prompt = (
            REQUIREMENT_ONLY_CODE_ANALYSIS_AGENT_PROMPT
            if requirement_only
            else CODE_ANALYSIS_AGENT_PROMPT
        )
        return [
            LLMMessage("system", system_prompt),
            LLMMessage(
                "user",
                _bundle_to_prompt(
                    bundle,
                    include_schema=False,
                    requirement_only=requirement_only,
                ),
            ),
        ]

    def _requirement_messages(
        self,
        bundle: dict[str, Any],
        code_analysis: dict[str, Any],
        revision: dict[str, Any] | None = None,
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "code_analysis": code_analysis,
            "requirement_evidence": bundle["requirement_evidence"],
            "schema_evidence_for_business_rules": bundle["schema_evidence"],
            "schema_summary_for_testability_only": bundle["schema_summary"],
        }
        if revision:
            payload["revision"] = revision
        return [
            LLMMessage("system", REQUIREMENT_RULE_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _requirement_review_messages(
        self,
        bundle: dict[str, Any],
        requirement_payload: dict[str, Any],
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "requirement_business_rule_output": requirement_payload,
            "requirement_evidence": bundle["requirement_evidence"],
            "schema_evidence_for_business_rules": bundle["schema_evidence"],
            "schema_summary_for_testability_only": bundle["schema_summary"],
        }
        return [
            LLMMessage("system", REQUIREMENT_RULE_REVIEW_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _requirement_only_messages(
        self,
        bundle: dict[str, Any],
        code_analysis: dict[str, Any],
        revision: dict[str, Any] | None = None,
        evidence_only: bool = False,
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "code_analysis": code_analysis,
            "requirement_evidence": bundle["requirement_evidence"],
            "generation_policy": (
                "Evidence-only mode: Schema IR, reference DDL, schema evidence, "
                "migration files, ORM models, table names, and column names are "
                "not provided to the requirement writer."
            ),
        }
        if not evidence_only:
            payload["existing_short_requirement"] = bundle.get("existing_requirement", "")
        if not evidence_only:
            payload["schema_summary_for_coverage_only"] = _requirement_schema_summary(
                bundle["schema_summary"]
            )
        if revision:
            payload["revision"] = revision
        return [
            LLMMessage("system", REQUIREMENT_ONLY_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _requirement_only_review_messages(
        self,
        bundle: dict[str, Any],
        requirement_payload: dict[str, Any],
        evidence_only: bool = False,
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "requirement_output": requirement_payload,
            "requirement_evidence": bundle["requirement_evidence"],
            "review_policy": (
                "Evidence-only mode: judge against product/documentation evidence, "
                "not against Schema IR or reference DDL. Flag schema-list-like prose."
            ),
        }
        if not evidence_only:
            payload["schema_summary_for_coverage_only"] = _requirement_schema_summary(
                bundle["schema_summary"]
            )
        return [
            LLMMessage("system", REQUIREMENT_ONLY_REVIEW_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _integrity_messages(
        self,
        bundle: dict[str, Any],
        requirement_payload: dict[str, Any],
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "business_rules": requirement_payload.get("business_rules", []),
            "schema_summary": bundle["schema_summary"],
            "reference_ddl": bundle["reference_ddl"],
        }
        return [
            LLMMessage("system", INTEGRITY_TEST_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _integrity_review_messages(
        self,
        bundle: dict[str, Any],
        requirement_payload: dict[str, Any],
        integrity_payload: dict[str, Any] | None = None,
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "business_rules": requirement_payload.get("business_rules", []),
            "integrity_test_output": integrity_payload or {},
            "schema_summary": bundle["schema_summary"],
            "reference_ddl": bundle["reference_ddl"],
        }
        return [
            LLMMessage("system", INTEGRITY_TEST_REVIEW_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _workload_messages(
        self,
        bundle: dict[str, Any],
        code_analysis: dict[str, Any],
        revision: dict[str, Any] | None = None,
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "code_analysis": code_analysis,
            "workload_evidence": bundle["workload_evidence"],
            "schema_summary": bundle["schema_summary"],
            "reference_ddl": bundle["reference_ddl"],
        }
        if revision:
            payload["revision"] = revision
        return [
            LLMMessage("system", WORKLOAD_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _workload_review_messages(
        self,
        bundle: dict[str, Any],
        workload_payload: dict[str, Any],
    ) -> list[LLMMessage]:
        payload = {
            "sample": _sample_context(bundle),
            "workload_output": workload_payload,
            "workload_evidence": bundle["workload_evidence"],
            "schema_summary": bundle["schema_summary"],
        }
        return [
            LLMMessage("system", WORKLOAD_REVIEW_AGENT_PROMPT),
            LLMMessage("user", json.dumps(payload, ensure_ascii=False, indent=2)),
        ]

    def _write_draft(
        self,
        candidate: dict[str, Any],
        bundle: dict[str, Any],
        result: NLConstructionResult,
    ) -> None:
        draft_path = self.paths.draft_dir / f"{_repo_slug(candidate)}.sample_draft.json"
        result.draft_path = draft_path.as_posix()
        payload = {
            "candidate": _candidate_header(candidate),
            "evidence_bundle_summary": {
                "schema_evidence_files": [
                    item["repo_path"] for item in bundle["schema_evidence"]
                ],
                "requirement_evidence_files": [
                    item["repo_path"] for item in bundle["requirement_evidence"]
                ],
                "workload_evidence_files": [
                    item["repo_path"] for item in bundle["workload_evidence"]
                ],
                "schema_ir_path": bundle["schema_ir_path"],
                "reference_ddl_path": bundle["reference_ddl_path"],
            },
            "nl_construction": result.to_dict(),
        }
        write_json(draft_path, payload)

    def _write_requirement_draft(
        self,
        candidate: dict[str, Any],
        bundle: dict[str, Any],
        result: RequirementOnlyConstructionResult,
    ) -> None:
        draft_path = self.paths.draft_dir / f"{_repo_slug(candidate)}.requirement_draft.json"
        result.draft_path = draft_path.as_posix()
        generation_mode = (
            result.agent_outputs.get("requirement_generation_mode", "unknown")
            if isinstance(result.agent_outputs, dict)
            else "unknown"
        )
        evidence_summary = {
            "requirement_evidence_files": [
                item["repo_path"] for item in bundle["requirement_evidence"]
            ],
            "requirement_generation_mode": generation_mode,
        }
        if generation_mode != "evidence_only_no_schema_ir":
            evidence_summary.update(
                {
                    "schema_evidence_files": [
                        item["repo_path"] for item in bundle["schema_evidence"]
                    ],
                    "schema_ir_path": bundle["schema_ir_path"],
                    "reference_ddl_path": bundle["reference_ddl_path"],
                }
            )
        payload = {
            "candidate": _candidate_header(candidate),
            "evidence_bundle_summary": evidence_summary,
            "requirement_only_construction": result.to_dict(),
        }
        write_json(draft_path, payload)


def construct_candidates(
    candidates: list[dict[str, Any]],
    llm_client: LLMClient,
    draft_dir: Path,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    pipeline = NLConstructionPipeline(llm_client, NLConstructionPaths(draft_dir=draft_dir))
    augmented = []
    for candidate in candidates:
        result = pipeline.construct(candidate, dry_run=dry_run)
        augmented.append(_augment_candidate(candidate, result))
    return augmented


def construct_requirements(
    candidates: list[dict[str, Any]],
    llm_client: LLMClient,
    draft_dir: Path,
    dry_run: bool = False,
    evidence_only: bool = False,
) -> list[dict[str, Any]]:
    pipeline = NLConstructionPipeline(llm_client, NLConstructionPaths(draft_dir=draft_dir))
    augmented = []
    for candidate in candidates:
        result = pipeline.construct_requirement_only(
            candidate,
            dry_run=dry_run,
            evidence_only=evidence_only,
        )
        augmented.append(_augment_candidate_requirement_only(candidate, result))
    return augmented


def build_requirement_construction_report(
    candidates: list[dict[str, Any]],
    source_file: str,
    dry_run: bool,
) -> str:
    statuses = Counter(
        str(
            ((candidate.get("nl_construction") or {}).get("requirement_only") or {}).get(
                "status",
                "unknown",
            )
        )
        for candidate in candidates
    )
    ready = [
        candidate
        for candidate in candidates
        if ((candidate.get("nl_construction") or {}).get("requirement_only") or {}).get("status")
        == "ready"
    ]
    review = [
        candidate
        for candidate in candidates
        if ((candidate.get("nl_construction") or {}).get("requirement_only") or {}).get("status")
        not in {"ready", "dry_run"}
    ]
    lengths = [len(str(candidate.get("requirement") or "")) for candidate in candidates]
    lines = [
        "# Requirement-only 构造报告",
        "",
        f"- 输入文件：`{source_file}`",
        f"- 样本数：{len(candidates)}",
        f"- dry run：{dry_run}",
        "",
        "## 状态统计",
        "",
        *[f"- {key}: {value}" for key, value in sorted(statuses.items())],
        "",
        "## Requirement 长度",
        "",
        f"- 平均长度：{(sum(lengths) / len(lengths)):.1f}" if lengths else "- 平均长度：0",
        f"- 最短长度：{min(lengths)}" if lengths else "- 最短长度：0",
        f"- 最长长度：{max(lengths)}" if lengths else "- 最长长度：0",
        "",
        "## 已 ready 样本",
        "",
        *_format_requirement_only_candidate_list(ready),
        "",
        "## 需要复核样本",
        "",
        *_format_requirement_only_candidate_list(review, include_errors=True),
    ]
    return "\n".join(lines) + "\n"


def build_nl_construction_report(
    candidates: list[dict[str, Any]],
    source_file: str,
    dry_run: bool,
) -> str:
    statuses = Counter(
        str((candidate.get("nl_construction") or {}).get("status") or "unknown")
        for candidate in candidates
    )
    dbms_counts = Counter(str(candidate.get("dbms_final") or "unknown") for candidate in candidates)
    ready = [
        candidate for candidate in candidates
        if (candidate.get("nl_construction") or {}).get("status") == "ready"
    ]
    review = [
        candidate for candidate in candidates
        if (candidate.get("nl_construction") or {}).get("status") not in {"ready", "dry_run"}
    ]
    lines = [
        "# Requirements / Business Rules / Workload / Tests 构造报告",
        "",
        f"- 输入文件：`{source_file}`",
        f"- 样本数：{len(candidates)}",
        f"- dry run：{dry_run}",
        "",
        "## 状态统计",
        "",
        *[f"- {key}: {value}" for key, value in sorted(statuses.items())],
        "",
        "## DBMS 分布",
        "",
        *[f"- {key}: {value}" for key, value in sorted(dbms_counts.items())],
        "",
        "## 已 ready 样本",
        "",
        *_format_candidate_list(ready),
        "",
        "## 需要复核样本",
        "",
        *_format_candidate_list(review, include_errors=True),
        "",
        "## LLM 配置位置",
        "",
        "- `configs/default.toml` 的 `[llm]`：`base_url`、`api_key`、`model`、`timeout_seconds`。",
        "- 或环境变量：`DBGENIE_LLM_BASE_URL`、`DBGENIE_LLM_API_KEY`、`DBGENIE_LLM_MODEL`。",
        "- `base_url` 可以填服务根路径，也可以直接填到 `/chat/completions`；客户端会自动补齐。",
    ]
    return "\n".join(lines) + "\n"


def _augment_candidate(candidate: dict[str, Any], result: NLConstructionResult) -> dict[str, Any]:
    augmented = dict(candidate)
    augmented["project_summary"] = result.project_summary
    augmented["requirement"] = result.requirement
    augmented["business_rules"] = result.business_rules
    augmented["workload"] = result.workload
    augmented["tests"] = result.tests
    augmented["nl_construction"] = {
        "status": result.status,
        "validation": result.validation,
        "warnings": result.warnings,
        "errors": result.errors,
        "draft_path": result.draft_path,
    }
    return augmented


def _augment_candidate_requirement_only(
    candidate: dict[str, Any],
    result: RequirementOnlyConstructionResult,
) -> dict[str, Any]:
    augmented = dict(candidate)
    if result.requirement:
        augmented["requirement"] = result.requirement
    nl_construction = dict(augmented.get("nl_construction") or {})
    if result.requirement:
        nl_construction["requirement"] = result.requirement
    nl_construction["requirement_only"] = {
        "status": result.status,
        "validation": result.validation,
        "warnings": result.warnings,
        "errors": result.errors,
        "draft_path": result.draft_path,
    }
    augmented["nl_construction"] = nl_construction
    return augmented


def _build_evidence_bundle(candidate: dict[str, Any]) -> dict[str, Any]:
    schema_ir_path = _schema_ir_path(candidate)
    reference_ddl_path = _reference_ddl_path(candidate)
    schema_ir = SchemaIR.from_dict(read_json(schema_ir_path)) if schema_ir_path else SchemaIR()
    reference_ddl = _read_optional_text(reference_ddl_path)
    return {
        "candidate": _candidate_header(candidate),
        "schema_evidence": _load_local_evidence(candidate, "schema"),
        "requirement_evidence": _load_local_evidence(candidate, "requirement_evidence"),
        "workload_evidence": _load_local_evidence(candidate, "workload_evidence"),
        "schema_ir_path": schema_ir_path.as_posix() if schema_ir_path else "",
        "reference_ddl_path": reference_ddl_path.as_posix() if reference_ddl_path else "",
        "schema_summary": _schema_summary(schema_ir),
        "reference_ddl": _truncate(reference_ddl, 30000),
        "existing_requirement": str(candidate.get("requirement") or ""),
    }


def _build_requirement_evidence_only_bundle(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate": _candidate_header(candidate),
        "schema_evidence": [],
        "requirement_evidence": _load_local_evidence(candidate, "requirement_evidence"),
        "workload_evidence": [],
        "schema_ir_path": "",
        "reference_ddl_path": "",
        "schema_summary": {"table_count": 0, "tables": []},
        "reference_ddl": "",
        "existing_requirement": "",
    }


def _load_local_evidence(candidate: dict[str, Any], key: str) -> list[dict[str, Any]]:
    files = ((candidate.get("local_source_files") or {}).get(key)) or []
    loaded = []
    for item in files[:12]:
        local_path = Path(str(item.get("local_path") or ""))
        content = _read_optional_text(local_path)
        loaded.append(
            {
                "repo_path": str(item.get("repo_path") or ""),
                "local_path": local_path.as_posix() if local_path else "",
                "evidence_type": _evidence_type(str(item.get("repo_path") or "")),
                "content": _truncate(content, 8000),
            }
        )
    return loaded


def _schema_ir_path(candidate: dict[str, Any]) -> Path | None:
    path = (
        (candidate.get("schema_materialization") or {}).get("final_ir_path")
        or (candidate.get("schema_materialization") or {}).get("introspection_ir_path")
    )
    if path and Path(path).exists():
        return Path(path)
    fallback = Path(
        "benchmark/schema_ir/final_merged_validated_2026-06-01"
    ) / f"{_repo_slug(candidate)}.schema_ir.json"
    return fallback if fallback.exists() else None


def _reference_ddl_path(candidate: dict[str, Any]) -> Path | None:
    path = (candidate.get("reference_ddl_generation") or {}).get("ddl_path")
    if path and Path(path).exists():
        return Path(path)
    dbms = str(candidate.get("dbms_final") or "unknown")
    fallback = (
        Path("benchmark/reference_ddl/final_merged_validated_2026-06-01")
        / _repo_slug(candidate)
        / f"{_dbms_file_label(dbms)}.sql"
    )
    return fallback if fallback.exists() else None


def _schema_summary(schema_ir: SchemaIR) -> dict[str, Any]:
    tables = []
    for table in schema_ir.tables[:80]:
        tables.append(
            {
                "name": table.name,
                "columns": [column.to_dict() for column in table.columns],
                "primary_key": table.primary_key,
                "foreign_keys": [foreign_key.to_dict() for foreign_key in table.foreign_keys],
                "unique_constraints": [
                    constraint.to_dict() for constraint in table.unique_constraints
                ],
                "indexes": [index.to_dict() for index in table.indexes],
            }
        )
    return {
        "table_count": schema_ir.table_count(),
        "tables": tables,
    }


def _validate_constructed_fields(
    candidate: dict[str, Any],
    constructed: dict[str, Any],
) -> dict[str, Any]:
    issues = []
    business_rules = _as_list(constructed.get("business_rules"))
    workload = _as_list(constructed.get("workload"))
    tests = constructed.get("tests") or {}
    integrity_tests = _as_list(tests.get("integrity"))
    workload_tests = _as_list(tests.get("workload"))
    requirement = str(constructed.get("requirement") or "")
    if not requirement:
        issues.append("missing_requirement")
    if _requirement_leaks_schema(candidate, requirement):
        issues.append("requirement_may_leak_schema_terms")
    for rule in business_rules:
        if not rule.get("evidence_file"):
            issues.append(f"business_rule_missing_evidence:{rule.get('id')}")
    for item in workload:
        if not item.get("evidence_file"):
            issues.append(f"workload_missing_evidence:{item.get('id')}")
    testable_rule_ids = {
        str(rule.get("id")) for rule in business_rules if bool(rule.get("testable"))
    }
    integrity_rule_ids = {str(test.get("business_rule_id")) for test in integrity_tests}
    missing_integrity = sorted(testable_rule_ids - integrity_rule_ids)
    if missing_integrity:
        issues.append(f"missing_integrity_tests:{','.join(missing_integrity)}")
    workload_ids = {str(item.get("id")) for item in workload}
    workload_test_ids = {str(test.get("workload_id")) for test in workload_tests}
    if workload_ids != workload_test_ids:
        issues.append("workload_and_tests_workload_not_one_to_one")
    for item in workload:
        non_index_support = _non_index_physical_support(item.get("expected_physical_support"))
        if non_index_support:
            issues.append(
                f"workload_non_index_physical_support:{item.get('id')}:"
                f"{','.join(non_index_support)}"
            )
    known_tables = _candidate_table_names(candidate)
    for test in integrity_tests:
        unknown = _unknown_sql_tables(_integrity_test_sql(test), known_tables)
        if unknown:
            issues.append(
                f"integrity_sql_unknown_table:{test.get('id')}:{','.join(sorted(unknown))}"
            )
    for test in workload_tests:
        non_index_support = _non_index_physical_support(test.get("expected_physical_support"))
        if non_index_support:
            issues.append(
                f"workload_test_non_index_physical_support:{test.get('id')}:"
                f"{','.join(non_index_support)}"
            )
        unknown = _unknown_sql_tables([str(test.get("sql") or "")], known_tables)
        if unknown:
            issues.append(
                f"workload_sql_unknown_table:{test.get('id')}:{','.join(sorted(unknown))}"
            )
    return {
        "passed": not issues,
        "issues": issues,
        "dbms": str(candidate.get("dbms_final") or ""),
    }


def _validate_requirement_only(constructed: dict[str, Any]) -> dict[str, Any]:
    requirement = str(constructed.get("requirement") or "").strip()
    issues = []
    if not requirement:
        issues.append("missing_requirement")
    forbidden = {
        "requirement_contains_url": r"https?://|www\.",
        "requirement_contains_deployment_text": (
            r"\bdeployed here\b|\binstall\b|\bdocker pull\b|\blocal build\b"
        ),
        "requirement_contains_meta_text": (
            r"Schema IR|reference DDL|evidence file"
        ),
        "requirement_contains_schema_implementation_terms": (
            r"\bforeign key\b|\bforeign keys\b|\bDDL\b|\bORM\b|"
            r"\bmigration\b|\bmigrations\b|\bindex\b|\bindexes\b|"
            r"\btable\b|\btables\b|\bcolumn\b|\bcolumns\b"
        ),
        "requirement_contains_identifier_like_terms": (
            r"\b[a-z]+_[a-z0-9_]+\b"
        ),
        "requirement_contains_generic_filler": (
            r"feel coherent|non-technical operator|not silently lost|find the right record"
        ),
    }
    for issue, pattern in forbidden.items():
        if re.search(pattern, requirement, flags=re.IGNORECASE):
            issues.append(issue)
    if "\n\n" in requirement:
        issues.append("requirement_not_single_paragraph")
    return {"passed": not issues, "issues": issues}


def _requirement_schema_summary(schema_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "table_count": schema_summary.get("table_count", 0),
        "tables": (schema_summary.get("tables") or [])[:160],
    }


def _candidate_table_names(candidate: dict[str, Any]) -> set[str]:
    schema_path = _schema_ir_path(candidate)
    if not schema_path:
        return set()
    schema = SchemaIR.from_dict(read_json(schema_path))
    return {table.name.lower() for table in schema.tables}


def _integrity_test_sql(test: dict[str, Any]) -> list[str]:
    statements = []
    for key in ("setup_sql", "positive_sql", "negative_sql"):
        value = test.get(key)
        if isinstance(value, list):
            statements.extend(str(item) for item in value)
        elif isinstance(value, str):
            statements.append(value)
    return statements


def _unknown_sql_tables(statements: list[str], known_tables: set[str]) -> set[str]:
    if not known_tables:
        return set()
    referenced: set[str] = set()
    patterns = [
        r"\binto\s+([`\"\[]?[\w.]+[`\"\]]?)",
        r"\bfrom\s+([`\"\[]?[\w.]+[`\"\]]?)",
        r"\bjoin\s+([`\"\[]?[\w.]+[`\"\]]?)",
        r"\bupdate\s+([`\"\[]?[\w.]+[`\"\]]?)",
        r"\btruncate\s+(?:table\s+)?([`\"\[]?[\w.]+[`\"\]]?)",
    ]
    for statement in statements:
        lower = statement.lower()
        for pattern in patterns:
            for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
                table = _clean_table_identifier(match.group(1))
                if table and table not in known_tables:
                    referenced.add(table)
    return referenced


def _non_index_physical_support(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    invalid = []
    banned_tokens = (
        "cache",
        "caching",
        "partition",
        "materialized",
        "view",
        "denormal",
        "background",
        "job",
        "queue",
        "permission",
        "authorization",
        "trigger",
        "constraint",
        "foreign key",
        "fk",
    )
    for item in value:
        text = str(item).strip()
        lower = text.lower()
        if not text:
            continue
        if "index" not in lower:
            invalid.append(text)
            continue
        if any(token in lower for token in banned_tokens):
            invalid.append(text)
    return invalid


def _clean_table_identifier(identifier: str) -> str:
    cleaned = identifier.strip().strip("`\"[]")
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned.lower()


def _needs_integrity_feedback(
    requirement_payload: dict[str, Any],
    integrity_payload: dict[str, Any],
) -> bool:
    rules = _as_list(requirement_payload.get("business_rules"))
    testable_count = sum(1 for rule in rules if bool(rule.get("testable")))
    integrity_count = len(_as_list((integrity_payload.get("tests") or {}).get("integrity")))
    return testable_count > 0 and integrity_count == 0


def _requirement_leaks_schema(candidate: dict[str, Any], requirement: str) -> bool:
    schema_path = _schema_ir_path(candidate)
    if not schema_path:
        return False
    schema = SchemaIR.from_dict(read_json(schema_path))
    text = requirement.lower()
    for table in schema.tables[:40]:
        if re.search(rf"\b{re.escape(table.name.lower())}\b", text):
            return True
        for column in table.columns[:20]:
            if "_" in column.name and re.search(rf"\b{re.escape(column.name.lower())}\b", text):
                return True
    return False


def _parse_json_response(raw: str) -> Any:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _messages_to_dict(messages: list[LLMMessage]) -> list[dict[str, str]]:
    return [message.__dict__ for message in messages]


def _bundle_to_prompt(
    bundle: dict[str, Any],
    include_schema: bool = True,
    requirement_only: bool = False,
) -> str:
    payload = {
        "sample": _sample_context(bundle),
        "requirement_evidence": bundle["requirement_evidence"],
    }
    if requirement_only:
        payload["analysis_policy"] = (
            "Requirement evidence only. Infer product intent, persistent business "
            "concepts, users, flows, ownership, states, and history from README, "
            "docs, API descriptions, routes, services, repositories, and user guides. "
            "Do not use or request Schema IR, reference DDL, schema evidence, "
            "migrations, ORM models, table names, or column names."
        )
    else:
        payload["schema_evidence_for_business_rules"] = bundle["schema_evidence"]
        payload["workload_evidence"] = bundle["workload_evidence"]
    if include_schema:
        payload["schema_summary"] = bundle["schema_summary"]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _sample_context(bundle: dict[str, Any]) -> dict[str, Any]:
    return dict(bundle["candidate"])


def _candidate_header(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": candidate.get("full_name"),
        "url": candidate.get("url"),
        "dbms_final": candidate.get("dbms_final"),
        "domain_final": candidate.get("domain_final"),
        "ecosystem_final": candidate.get("ecosystem_final"),
        "schema_artifact_final": candidate.get("schema_artifact_final"),
    }


def _format_candidate_list(
    candidates: list[dict[str, Any]],
    include_errors: bool = False,
    limit: int = 20,
) -> list[str]:
    if not candidates:
        return ["- 无"]
    lines = []
    for candidate in candidates[:limit]:
        construction = candidate.get("nl_construction") or {}
        line = (
            f"- `{candidate.get('full_name')}` | DBMS={candidate.get('dbms_final')} | "
            f"status={construction.get('status')}"
        )
        if include_errors:
            errors = construction.get("errors") or []
            warnings = construction.get("warnings") or []
            if errors:
                line += f" | errors={'; '.join(map(str, errors[:2]))}"
            if warnings:
                line += f" | warnings={'; '.join(map(str, warnings[:2]))}"
        lines.append(line)
    if len(candidates) > limit:
        lines.append(f"- ... 另有 {len(candidates) - limit} 个样本未展开")
    return lines


def _format_requirement_only_candidate_list(
    candidates: list[dict[str, Any]],
    include_errors: bool = False,
    limit: int = 20,
) -> list[str]:
    if not candidates:
        return ["- 无"]
    lines = []
    for candidate in candidates[:limit]:
        construction = ((candidate.get("nl_construction") or {}).get("requirement_only") or {})
        line = (
            f"- `{candidate.get('full_name')}` | DBMS={candidate.get('dbms_final')} | "
            f"status={construction.get('status')}"
        )
        if include_errors:
            errors = construction.get("errors") or []
            warnings = construction.get("warnings") or []
            issues = (construction.get("validation") or {}).get("issues") or []
            if errors:
                line += f" | errors={'; '.join(map(str, errors[:2]))}"
            if warnings:
                line += f" | warnings={'; '.join(map(str, warnings[:2]))}"
            if issues:
                line += f" | issues={'; '.join(map(str, issues[:2]))}"
        lines.append(line)
    if len(candidates) > limit:
        lines.append(f"- ... 另有 {len(candidates) - limit} 个样本未展开")
    return lines


def _read_optional_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def _as_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _repo_slug(candidate: dict[str, Any]) -> str:
    full_name = str(candidate.get("full_name") or "unknown__repo")
    return full_name.replace("/", "__")


def _dbms_file_label(dbms: str) -> str:
    return {
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mariadb": "MariaDB",
        "sqlite": "SQLite",
        "sql server": "SQL Server",
    }.get(dbms.lower(), dbms.replace("/", "_"))


def _evidence_type(path: str) -> str:
    lower = path.lower()
    if "readme" in lower:
        return "readme"
    if lower.startswith("docs/") or "/docs/" in lower:
        return "docs"
    if "route" in lower or "controller" in lower:
        return "route"
    if "service" in lower:
        return "service"
    if any(token in lower for token in ("repository", "dao", "mapper")):
        return "repository"
    if "test" in lower or "spec" in lower:
        return "test"
    if "migration" in lower or "migrate" in lower:
        return "migration"
    return "docs"
