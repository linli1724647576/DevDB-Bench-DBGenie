from __future__ import annotations

import copy
import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dbgenie.core.io import write_json
from dbgenie.llm.client import LLMClient, LLMRequestError

from .context import (
    build_state_catalog,
    design_only_completion_status,
    materialize_expert_context,
)
from .contracts import SchedulerAction, ToolRequest, ToolRequestProposal
from .definition import FULL_METHOD_DEFINITION, DynamicMethodDefinition
from .experts import DynamicExpertRunner
from .jsonutil import LLMJSONParseError
from .normalization import THIRD_NORMAL_FORM_TOOL, current_third_normal_form_evidence
from .scheduler import DynamicMethodScheduler, validate_scheduler_action
from .state import DynamicMethodRunResult, DynamicMethodState
from .tools import DynamicMethodToolbox


TEST_EXPERT_IN_TURN_TOOL_TARGETS = {
    "ddl_executor": "ddl",
    "sql_test_runner": "test_report",
    "query_plan_tool": "test_report",
}
TEST_EXPERT_IN_TURN_TOOL_ORDER = tuple(TEST_EXPERT_IN_TURN_TOOL_TARGETS)
FIXED_PIPELINE_JSON_RETRY_LIMIT = 2
FIXED_PIPELINE_FAILURE_CATEGORIES = frozenset(
    {
        "test_fixture",
        "dialect_or_ddl",
        "physical_plan",
        "logical_schema",
        "conceptual_model",
        "requirement_ambiguity",
        "environment_or_tool",
    }
)


@dataclass(frozen=True)
class DynamicMethodOptions:
    run_dir: Path = Path("runs/method")
    dry_run: bool = False
    max_turns: int = 20
    max_repairs: int = 3
    ddl_executor: str = "docker"
    progress_callback: Any = None


class DynamicMethodPipeline:
    def __init__(
        self,
        llm_client: LLMClient,
        options: DynamicMethodOptions | None = None,
        *,
        toolbox: DynamicMethodToolbox | None = None,
        method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
    ) -> None:
        self.llm_client = llm_client
        self.options = options or DynamicMethodOptions()
        self.method_definition = method_definition
        self.toolbox = toolbox or DynamicMethodToolbox(execution_mode=self.options.ddl_executor)
        self.scheduler = (
            DynamicMethodScheduler(
                llm_client,
                llm_attempt_callback=self._progress_llm_attempt_error,
            )
            if method_definition.orchestration_mode == "scheduler"
            else None
        )
        self.expert_runner = DynamicExpertRunner(
            llm_client,
            llm_attempt_callback=self._progress_llm_attempt_error,
        )

    def run(self, task) -> DynamicMethodRunResult:
        state = DynamicMethodState(
            task=task,
            max_turns=self.options.max_turns,
            max_repairs=self.options.max_repairs,
            method_definition=self.method_definition,
        )
        run_path = self._run_path(task.id)
        if self.method_definition.orchestration_mode == "fixed_pipeline":
            state.fixed_pipeline = {
                "initial_sequence": list(self.method_definition.fixed_expert_sequence),
                "cross_expert_feedback_repair_enabled": (
                    self.method_definition.cross_expert_feedback_repair_enabled
                ),
                "repair_rounds": 0,
                "terminal_status": "",
                "terminal_reason": "",
            }
        state.add_turn(
            "scheduler" if self.method_definition.orchestration_mode == "scheduler" else "harness",
            "initialize",
            output={
                "message": "task initialized",
                **state.method_definition.to_metadata(),
            },
        )
        self._progress("start")

        if self.options.dry_run:
            self._bootstrap_dry_run(state)
            self._write_run(run_path, state, status="dry_run")
            self._progress("done status=dry_run")
            return DynamicMethodRunResult(
                task_id=task.id,
                status="dry_run",
                final_ddl=state.final_ddl,
                state=state,
                final_explanation=state.final_explanation,
                run_path=run_path.as_posix(),
                llm=self.llm_client.metadata(),
                evaluation_metrics=_build_evaluation_metrics(state),
                warnings=state.warnings,
                errors=state.errors,
            )

        if not self.llm_client.is_configured():
            state.errors.append("llm_not_configured")
            self._write_run(run_path, state, status="failed")
            self._progress("done status=failed")
            return DynamicMethodRunResult(
                task_id=task.id,
                status="failed",
                final_ddl="",
                state=state,
                final_explanation="",
                run_path=run_path.as_posix(),
                llm=self.llm_client.metadata(),
                evaluation_metrics=_build_evaluation_metrics(state),
                warnings=state.warnings,
                errors=state.errors,
            )

        try:
            if self.method_definition.orchestration_mode == "fixed_pipeline":
                self._run_fixed_pipeline(state)
            else:
                consecutive_scheduler_rejections = 0
                max_consecutive_scheduler_rejections = max(3, min(8, state.max_turns))
                while True:
                    finalize_only = False
                    if state.remaining_scheduler_steps() <= 0:
                        if not _finalize_reserve_available(state):
                            break
                        finalize_only = True
                    try:
                        if self.scheduler is None:  # pragma: no cover - guarded by definition
                            raise RuntimeError("scheduler orchestration has no scheduler instance")
                        decision = self.scheduler.decide(
                            state,
                            finalize_only=finalize_only,
                        )
                    except LLMRequestError as exc:
                        self._progress(_format_llm_request_error_for_terminal(exc, speaker="scheduler"))
                        _record_llm_request_error(state, exc, speaker="scheduler")
                        break
                    except LLMJSONParseError as exc:
                        _record_llm_json_parse_error(state, exc, speaker="scheduler")
                        consecutive_scheduler_rejections += 1
                        if consecutive_scheduler_rejections >= max_consecutive_scheduler_rejections:
                            _record_scheduler_rejection_limit(state, consecutive_scheduler_rejections)
                            break
                        continue
                    state.warnings.extend(decision.warnings)
                    if decision.validation_errors:
                        _record_scheduler_action_rejection(state, decision)
                        consecutive_scheduler_rejections += 1
                        if consecutive_scheduler_rejections >= max_consecutive_scheduler_rejections:
                            _record_scheduler_rejection_limit(state, consecutive_scheduler_rejections)
                            break
                        continue
                    action_applied = self._apply_scheduler_action(state, decision.action)
                    if action_applied:
                        state.consume_scheduler_step(finalize_reserve=finalize_only)
                        consecutive_scheduler_rejections = 0
                    else:
                        consecutive_scheduler_rejections += 1
                        if consecutive_scheduler_rejections >= max_consecutive_scheduler_rejections:
                            _record_scheduler_rejection_limit(state, consecutive_scheduler_rejections)
                            break
                    if state.current_phase == "failed":
                        break
                    if action_applied and decision.action.action_type in {"finalize", "terminate_with_warning"}:
                        break
        except Exception as exc:  # pragma: no cover - exercised through CLI-like integration paths
            _record_unhandled_exception(state, exc)

        final_ddl = str(state.artifact_payload("ddl", "") or state.final_ddl or "")
        state.final_ddl = final_ddl
        status = self._final_status(state)
        if self.method_definition.orchestration_mode == "fixed_pipeline":
            self._finalize_fixed_pipeline(state, status)
        self._write_run(run_path, state, status=status)
        self._progress(f"done status={status}")
        return DynamicMethodRunResult(
            task_id=task.id,
            status=status,
            final_ddl=final_ddl,
            state=state,
            final_explanation=state.final_explanation,
            run_path=run_path.as_posix(),
            llm=self.llm_client.metadata(),
            evaluation_metrics=_build_evaluation_metrics(state),
            warnings=state.warnings,
            errors=state.errors,
        )

    def _run_fixed_pipeline(self, state: DynamicMethodState) -> None:
        sequence = tuple(state.method_definition.fixed_expert_sequence)
        state.current_phase = "fixed_initial_pipeline"
        state.fixed_pipeline = {
            "initial_sequence": list(sequence),
            "cross_expert_feedback_repair_enabled": (
                state.method_definition.cross_expert_feedback_repair_enabled
            ),
            "repair_rounds": 0,
            "terminal_status": "",
            "terminal_reason": "",
        }
        initial_instructions = {
            "requirement_analyst": "Produce the requirement brief from the fixed task context.",
            "conceptual_model_designer": "Produce the conceptual model from the requirement brief.",
            "logical_model_designer": "Produce the logical model from the conceptual model.",
            "physical_design_specialist": "Produce the physical plan from the logical model.",
            "dialect_compiler": "Compile the logical model and physical plan into target-dialect DDL.",
            "test_expert": "Generate tests, request the runtime tool batch, and report terminal verification findings.",
        }
        for role in sequence:
            if not self._invoke_fixed_role(
                state,
                role,
                instruction=initial_instructions.get(role, f"Produce the {role} artifact."),
            ):
                return

        if not state.method_definition.cross_expert_feedback_repair_enabled:
            _complete_fixed_pipeline_without_feedback_repair(state)
            return

        state.current_phase = "fixed_repair_loop"
        while state.current_phase != "failed":
            evidence_status = _fixed_pipeline_evidence_status(state)
            if evidence_status == "ready":
                _set_fixed_pipeline_terminal(
                    state,
                    status="ready",
                    reason="all fixed-pipeline design and runtime readiness conditions passed",
                )
                return

            categories, invalid_categories, category_declared = _test_failure_categories(state)
            selected_category = next(
                (
                    category
                    for category in state.method_definition.failure_category_priority
                    if category in categories
                ),
                "",
            )
            if invalid_categories:
                selected_category = ""
            runtime_failure = _fixed_pipeline_has_runtime_failure(state)
            if not selected_category:
                if evidence_status == "unverified_ready" and not runtime_failure:
                    _set_fixed_pipeline_terminal(
                        state,
                        status="unverified_ready",
                        reason="design artifacts are complete but current real execution evidence is insufficient",
                    )
                    return
                detail = "missing failure_category"
                if invalid_categories:
                    detail = "invalid failure_category: " + ", ".join(invalid_categories)
                elif category_declared:
                    detail = "empty failure_category for a failed or incomplete test result"
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason=detail,
                    category="invalid_failure_category",
                )
                return

            if selected_category in {"environment_or_tool", "requirement_ambiguity"}:
                if selected_category == "requirement_ambiguity":
                    state.open_assumptions.append(
                        {
                            "type": "unresolved_ambiguity",
                            "source": "test_expert",
                            "evidence": _fixed_failure_evidence(state),
                        }
                    )
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason=f"fixed routing stops on {selected_category}",
                    category=selected_category,
                )
                return

            if state.repair_budget_used() >= state.max_repairs:
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason="fixed-pipeline repair budget exhausted",
                    category=selected_category,
                )
                return

            route = tuple(state.method_definition.failure_routes.get(selected_category, ()))
            if not route:
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason=f"no fixed route configured for {selected_category}",
                    category=selected_category,
                )
                return

            repair_round = state.repair_budget_used() + 1
            repair_envelope = _build_fixed_repair_envelope(
                state,
                failure_category=selected_category,
                repair_round=repair_round,
            )
            repair_entry = {
                "repair_id": f"fixed_pipeline_repair_{repair_round}",
                "event_type": "fixed_pipeline_repair_chain",
                "kind": "fixed_pipeline_repair_chain",
                "status": "in_progress",
                "repair_round": repair_round,
                "failure_category": selected_category,
                "observed_failure_categories": sorted(categories),
                "fixed_role_chain": list(route),
                "repair_artifacts": [
                    state.method_definition.artifact_by_role[role]
                    for role in route
                ],
                "artifact_versions_before": state.artifact_versions(),
                "evidence_refs": list(repair_envelope["evidence_refs"]),
                "evidence": copy.deepcopy(repair_envelope["failure_evidence"]),
                "validation_retries": [],
            }
            state.repair_history.append(repair_entry)
            state.fixed_pipeline["repair_rounds"] = state.repair_budget_used()
            for role in route:
                role_repair_envelope = _build_fixed_repair_envelope(
                    state,
                    failure_category=selected_category,
                    repair_round=repair_round,
                )
                role_repair_envelope["trigger_failure_evidence"] = copy.deepcopy(
                    repair_envelope["failure_evidence"]
                )
                role_repair_envelope["trigger_tool_results"] = copy.deepcopy(
                    repair_envelope["tool_results"]
                )
                role_repair_envelope["trigger_evidence_refs"] = list(
                    repair_envelope["evidence_refs"]
                )
                revision_request = {
                    "mode": "fixed_pipeline_repair",
                    "instruction": (
                        f"Repair only the {role} responsibility for failure category "
                        f"{selected_category}, then return a complete current artifact."
                    ),
                    "failure_category": selected_category,
                    "repair_envelope": role_repair_envelope,
                }
                if not self._invoke_fixed_role(
                    state,
                    role,
                    instruction=revision_request["instruction"],
                    revision_request=revision_request,
                    active_repair=repair_entry,
                ):
                    repair_entry["status"] = "failed"
                    repair_entry["artifact_versions_after"] = state.artifact_versions()
                    return
            repair_entry["status"] = "completed"
            repair_entry["artifact_versions_after"] = state.artifact_versions()
            repair_entry["completed_turn_index"] = len(state.turns)

    def _invoke_fixed_role(
        self,
        state: DynamicMethodState,
        role: str,
        *,
        instruction: str,
        revision_request: dict[str, Any] | None = None,
        active_repair: dict[str, Any] | None = None,
    ) -> bool:
        artifact_key = state.method_definition.artifact_by_role[role]
        before_version = int(state.artifacts[artifact_key].version)
        attempt_instruction = instruction
        attempt_revision = copy.deepcopy(revision_request)
        json_retry_entry: dict[str, Any] | None = None
        for json_retry_attempt in range(FIXED_PIPELINE_JSON_RETRY_LIMIT + 1):
            proposal_start = len(state.tool_request_proposals)
            turn_start = len(state.turns)
            action = SchedulerAction(
                action_type="invoke_expert",
                target_role=role,
                target_artifact=artifact_key,
                instruction=attempt_instruction,
                execution_context_selection={},
                metadata={
                    "orchestration_mode": "fixed_pipeline",
                    **(
                        {"revision_request": copy.deepcopy(attempt_revision)}
                        if attempt_revision
                        else {}
                    ),
                },
            )
            self._handle_expert_action(state, action)
            self._settle_fixed_pipeline_proposals(state, proposal_start, role)
            if state.current_phase == "failed":
                if json_retry_entry is not None:
                    json_retry_entry["status"] = "failed"
                return False
            if state.current_phase == "fixed_pipeline_complete":
                if json_retry_entry is not None:
                    json_retry_entry["status"] = "failed"
                return False

            parse_turns = [
                turn
                for turn in state.turns[turn_start:]
                if turn.speaker == role and turn.kind == "llm_output_error"
            ]
            if role == "test_expert" and any(
                turn.speaker == role and turn.kind == "tool_interpretation"
                for turn in state.turns[turn_start:]
            ):
                parse_turns = []
            if not parse_turns:
                if json_retry_entry is not None:
                    json_retry_entry["status"] = "completed"
                    json_retry_entry["artifact_versions_after"] = state.artifact_versions()
                    json_retry_entry["completed_turn_index"] = len(state.turns)
                break

            parse_turn = parse_turns[-1]
            parse_output = parse_turn.output if isinstance(parse_turn.output, dict) else {}
            if json_retry_entry is None:
                json_retry_entry = {
                    "repair_id": f"fixed_pipeline_json_retry_{len(state.repair_history) + 1}",
                    "event_type": "fixed_pipeline_json_retry",
                    "kind": "fixed_pipeline_json_retry",
                    "status": "in_progress",
                    "counts_against_repair_budget": False,
                    "role": role,
                    "artifact": artifact_key,
                    "max_json_retries": FIXED_PIPELINE_JSON_RETRY_LIMIT,
                    "artifact_versions_before": state.artifact_versions(),
                    "attempts": [],
                }
                state.repair_history.append(json_retry_entry)
            json_retry_entry["attempts"].append(
                {
                    "retry_attempt": json_retry_attempt + 1,
                    "turn_ref": f"turn_{parse_turn.index}",
                    "message": str(parse_output.get("message") or "invalid JSON output"),
                    "raw_output_excerpt": str(parse_output.get("raw_output_excerpt") or ""),
                    "raw_output_chars": int(parse_output.get("raw_output_chars") or 0),
                }
            )
            if json_retry_attempt >= FIXED_PIPELINE_JSON_RETRY_LIMIT:
                json_retry_entry["status"] = "failed"
                json_retry_entry["artifact_versions_after"] = state.artifact_versions()
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason=(
                        f"{role} returned invalid JSON after "
                        f"{FIXED_PIPELINE_JSON_RETRY_LIMIT + 1} attempts"
                    ),
                    category="json_output",
                )
                return False

            attempt_instruction = (
                "The previous response was not valid JSON. Return only one complete JSON "
                "object matching the role contract; do not use markdown fences or commentary."
            )
            attempt_revision = copy.deepcopy(revision_request or {})
            attempt_revision.update(
                {
                    "mode": "fixed_pipeline_json_retry",
                    "instruction": attempt_instruction,
                    "json_retry_attempt": json_retry_attempt + 1,
                    "max_json_retries": FIXED_PIPELINE_JSON_RETRY_LIMIT,
                    "json_parse_error": copy.deepcopy(json_retry_entry["attempts"][-1]),
                    "partial_artifact": copy.deepcopy(
                        state.artifact_payload(artifact_key, None)
                    ),
                }
            )

        record = state.artifacts[artifact_key]
        if record.version <= before_version:
            _set_fixed_pipeline_terminal(
                state,
                status="needs_review",
                reason=f"{role} did not produce a new artifact version",
            )
            return False
        if record.status == "validated":
            return True

        validation = copy.deepcopy(record.validation or {})
        if active_repair is None:
            local_retry_index = 1 + sum(
                1
                for item in state.repair_history
                if isinstance(item, dict)
                and item.get("event_type") == "fixed_pipeline_artifact_validation_retry"
            )
            active_repair = {
                "repair_id": f"fixed_pipeline_validation_retry_{local_retry_index}",
                "event_type": "fixed_pipeline_artifact_validation_retry",
                "kind": "fixed_pipeline_artifact_validation_retry",
                "status": "in_progress",
                "counts_against_repair_budget": False,
                "local_retry_index": local_retry_index,
                "repair_round": state.repair_budget_used(),
                "failure_category": "artifact_validation",
                "fixed_role_chain": [role],
                "repair_artifacts": [artifact_key],
                "artifact_versions_before": state.artifact_versions(),
                "validation_retries": [],
            }
            state.repair_history.append(active_repair)

        active_repair.setdefault("validation_retries", []).append(
            {
                "role": role,
                "artifact": artifact_key,
                "failed_version": int(record.version),
                "validation": validation,
            }
        )
        retry_envelope = _build_fixed_repair_envelope(
            state,
            failure_category="artifact_validation",
            repair_round=int(active_repair.get("repair_round") or state.repair_budget_used()),
            validation_failure={
                "role": role,
                "artifact": artifact_key,
                "validation": validation,
            },
        )
        if active_repair.get("event_type") == "fixed_pipeline_repair_chain":
            retry_envelope["trigger_failure_evidence"] = copy.deepcopy(
                active_repair.get("evidence") or {}
            )
            retry_envelope["trigger_evidence_refs"] = list(
                active_repair.get("evidence_refs") or []
            )
        retry_instruction = (
            f"The {artifact_key} artifact failed structural validation. Correct exactly the "
            "reported validation errors and return the complete artifact."
        )
        retry_action = SchedulerAction(
            action_type="invoke_expert",
            target_role=role,
            target_artifact=artifact_key,
            instruction=retry_instruction,
            execution_context_selection={},
            metadata={
                "orchestration_mode": "fixed_pipeline",
                "revision_request": {
                    "mode": "fixed_pipeline_artifact_validation_retry",
                    "instruction": retry_instruction,
                    "repair_envelope": retry_envelope,
                },
            },
        )
        failed_version = int(record.version)
        validation_json_retry_entry: dict[str, Any] | None = None
        for json_retry_attempt in range(FIXED_PIPELINE_JSON_RETRY_LIMIT + 1):
            proposal_start = len(state.tool_request_proposals)
            turn_start = len(state.turns)
            self._handle_expert_action(state, retry_action)
            self._settle_fixed_pipeline_proposals(state, proposal_start, role)
            if state.current_phase in {"failed", "fixed_pipeline_complete"}:
                active_repair["status"] = "failed"
                return False
            parse_turns = [
                turn
                for turn in state.turns[turn_start:]
                if turn.speaker == role and turn.kind == "llm_output_error"
            ]
            if role == "test_expert" and any(
                turn.speaker == role and turn.kind == "tool_interpretation"
                for turn in state.turns[turn_start:]
            ):
                parse_turns = []
            if not parse_turns:
                if validation_json_retry_entry is not None:
                    validation_json_retry_entry["status"] = "completed"
                    validation_json_retry_entry["artifact_versions_after"] = (
                        state.artifact_versions()
                    )
                    validation_json_retry_entry["completed_turn_index"] = len(state.turns)
                break

            parse_turn = parse_turns[-1]
            parse_output = parse_turn.output if isinstance(parse_turn.output, dict) else {}
            if validation_json_retry_entry is None:
                validation_json_retry_entry = {
                    "repair_id": (
                        "fixed_pipeline_validation_json_retry_"
                        f"{len(state.repair_history) + 1}"
                    ),
                    "event_type": "fixed_pipeline_json_retry",
                    "kind": "fixed_pipeline_json_retry",
                    "status": "in_progress",
                    "counts_against_repair_budget": False,
                    "role": role,
                    "stage": "artifact_validation_retry",
                    "artifact": artifact_key,
                    "max_json_retries": FIXED_PIPELINE_JSON_RETRY_LIMIT,
                    "artifact_versions_before": state.artifact_versions(),
                    "attempts": [],
                }
                state.repair_history.append(validation_json_retry_entry)
            validation_json_retry_entry["attempts"].append(
                {
                    "retry_attempt": json_retry_attempt + 1,
                    "turn_ref": f"turn_{parse_turn.index}",
                    "message": str(parse_output.get("message") or "invalid JSON output"),
                    "raw_output_excerpt": str(parse_output.get("raw_output_excerpt") or ""),
                    "raw_output_chars": int(parse_output.get("raw_output_chars") or 0),
                }
            )
            if json_retry_attempt >= FIXED_PIPELINE_JSON_RETRY_LIMIT:
                validation_json_retry_entry["status"] = "failed"
                validation_json_retry_entry["artifact_versions_after"] = (
                    state.artifact_versions()
                )
                active_repair["status"] = "failed"
                _set_fixed_pipeline_terminal(
                    state,
                    status="needs_review",
                    reason=(
                        f"{role} returned invalid JSON after "
                        f"{FIXED_PIPELINE_JSON_RETRY_LIMIT + 1} artifact-validation "
                        "retry attempts"
                    ),
                    category="json_output",
                )
                return False

            retry_revision = copy.deepcopy(
                retry_action.metadata.get("revision_request") or {}
            )
            retry_revision.update(
                {
                    "instruction": (
                        "The previous artifact-validation correction was not valid JSON. "
                        "Return only one complete JSON object matching the role contract."
                    ),
                    "json_retry_attempt": json_retry_attempt + 1,
                    "max_json_retries": FIXED_PIPELINE_JSON_RETRY_LIMIT,
                    "json_parse_error": copy.deepcopy(
                        validation_json_retry_entry["attempts"][-1]
                    ),
                }
            )
            retry_action = SchedulerAction(
                action_type="invoke_expert",
                target_role=role,
                target_artifact=artifact_key,
                instruction=str(retry_revision["instruction"]),
                execution_context_selection={},
                metadata={
                    "orchestration_mode": "fixed_pipeline",
                    "revision_request": retry_revision,
                },
            )
        retried_record = state.artifacts[artifact_key]
        if retried_record.version > failed_version and retried_record.status == "validated":
            if active_repair.get("event_type") == "fixed_pipeline_artifact_validation_retry":
                active_repair["status"] = "completed"
                active_repair["artifact_versions_after"] = state.artifact_versions()
            return True

        active_repair["status"] = "failed"
        active_repair["artifact_versions_after"] = state.artifact_versions()
        _set_fixed_pipeline_terminal(
            state,
            status="needs_review",
            reason=f"artifact validation failed twice for {artifact_key}",
            category="artifact_validation",
        )
        return False

    def _settle_fixed_pipeline_proposals(
        self,
        state: DynamicMethodState,
        proposal_start: int,
        role: str,
    ) -> None:
        if role == "test_expert":
            return
        for proposal in state.tool_request_proposals[proposal_start:]:
            if not isinstance(proposal, dict) or proposal.get("status") != "pending":
                continue
            if proposal.get("tool_type") == "artifact_validator":
                proposal["status"] = "superseded"
                proposal["superseded_reason"] = "artifact_validation_is_automatic"
            else:
                proposal["status"] = "rejected"
                proposal["validation_errors"] = [
                    "fixed_pipeline has no scheduler tool-approval step"
                ]

    def _finalize_fixed_pipeline(self, state: DynamicMethodState, status: str) -> None:
        facts = _collect_evaluation_facts(state)
        reason = str(state.fixed_pipeline.get("terminal_reason") or "fixed pipeline stopped")
        state.final_explanation = (
            f"Fixed expert pipeline completed with status {status}. {reason}. "
            f"DDL present: {facts['ddl_present']}; real DDL execution evidence: "
            f"{facts['ddl_real_execution']}; generated tests: {facts['generated_test_count']}; "
            f"executed SQL tests: {facts['sql_test_total']}; failed SQL tests: "
            f"{facts['sql_test_failed']}. 3NF validation was disabled with the scheduler ablation."
        )
        verification_summary = _build_verification_summary(state)
        state.store_artifact(
            "verification_summary",
            verification_summary,
            producer="harness",
            status="validated",
        )
        state.add_turn(
            "harness",
            "finalize",
            output={
                "status": status,
                "explanation": state.final_explanation,
                "verification_summary": verification_summary,
            },
        )

    def _apply_scheduler_action(self, state: DynamicMethodState, action: SchedulerAction) -> bool:
        validation_errors = validate_scheduler_action(state, action)
        if validation_errors:
            _record_pipeline_action_rejection(state, action, validation_errors)
            return False
        if action.action_type == "call_tool":
            self._handle_tool_action(state, action)
            return True
        if action.action_type == "invoke_expert":
            blocker = _normalization_gate_blocker(state, action)
            if blocker:
                _record_normalization_gate_rejection(state, action, blocker)
                return False
            blocker = _ddl_compiler_gate_blocker(state, action)
            if blocker:
                _record_ddl_compiler_gate_rejection(state, action, blocker)
                return False
            self._handle_expert_action(state, action)
            return True
        if action.action_type == "finalize":
            blocker = _normalization_gate_blocker(state, action)
            if blocker:
                _record_normalization_gate_rejection(state, action, blocker)
                return False
            blocker = _test_evidence_gate_blocker(state, action)
            if blocker:
                _record_test_evidence_gate_rejection(state, action, blocker)
                return False
            self._handle_finalize(state, action)
            return True
        if action.action_type == "terminate_with_warning":
            state.warnings.append(action.stop_reason or "scheduler terminated the run")
            state.add_turn("scheduler", "terminate", output=action.to_dict(), warnings=action.warnings)
            return True
        state.errors.append(f"unsupported scheduler action: {action.action_type}")
        return False

    def _handle_tool_action(self, state: DynamicMethodState, action: SchedulerAction) -> None:
        request = action.tool_request
        if request is None:
            state.errors.append("scheduler requested tool call without tool_request")
            return
        if request.tool_type == THIRD_NORMAL_FORM_TOOL and not request.target_artifact:
            request = request.__class__(
                tool_type=request.tool_type,
                target_artifact="logical_model",
                reason=request.reason,
                payload=request.payload,
            )
        if request.tool_type == "artifact_validator" and not request.target_artifact:
            request = request.__class__(
                tool_type=request.tool_type,
                target_artifact=action.target_artifact or request.target_artifact,
                reason=request.reason,
                payload=request.payload,
            )
        if request.tool_type == THIRD_NORMAL_FORM_TOOL:
            existing_normalization = current_third_normal_form_evidence(state)
            if existing_normalization is not None:
                existing_ref, _existing_record = existing_normalization
                proposal_id = str(request.payload.get("proposal_id") or "") if isinstance(request.payload, dict) else ""
                if proposal_id:
                    state.mark_tool_request_proposal(proposal_id, "superseded")
                state.add_turn(
                    "tool",
                    request.tool_type,
                    output={
                        "skipped": True,
                        "reason": "duplicate_normalization_evidence",
                        "existing_tool_result": existing_ref,
                        "request": request.to_dict(),
                    },
                )
                return
        if request.tool_type == "query_plan_tool":
            existing_query_plan = _matching_query_plan_evidence_for_current_versions(state)
            if existing_query_plan is not None:
                existing_ref, _existing_record = existing_query_plan
                proposal_id = str(request.payload.get("proposal_id") or "") if isinstance(request.payload, dict) else ""
                if proposal_id:
                    state.mark_tool_request_proposal(proposal_id, "superseded")
                warning = (
                    "query_plan_tool skipped because raw evidence already exists "
                    f"for current artifact versions: {existing_ref}"
                )
                state.warnings.append(warning)
                state.add_turn(
                    "tool",
                    request.tool_type,
                    output={
                        "skipped": True,
                        "reason": "duplicate_query_plan_evidence",
                        "existing_tool_result": existing_ref,
                        "request": request.to_dict(),
                    },
                    warnings=[warning],
                )
                return
        result = self.toolbox.execute(state, request)
        state.tool_results.append(
            {
                "request": request.to_dict(),
                "result": result,
                "artifact_versions": state.artifact_versions(),
            }
        )
        proposal_id = str(request.payload.get("proposal_id") or "") if isinstance(request.payload, dict) else ""
        if proposal_id:
            state.mark_tool_request_proposal(proposal_id, "executed")
        if request.tool_type == THIRD_NORMAL_FORM_TOOL:
            _apply_normalization_result(state, result)
        state.add_turn("tool", request.tool_type, output=result)

    def _handle_expert_action(self, state: DynamicMethodState, action: SchedulerAction) -> None:
        if action.target_role not in state.method_definition.expert_roles:
            state.errors.append(f"invalid expert role: {action.target_role}")
            return
        if action.target_role == "test_expert":
            self._handle_test_expert_action(state, action)
            return
        artifact_key = state.method_definition.artifact_by_role[action.target_role]
        before_revision = _artifact_revision_snapshot(state, artifact_key)
        revision = _revision_request_from_action(action)
        execution_context = materialize_expert_context(
            state,
            action.target_role,
            action.execution_context_selection,
        )
        if execution_context.warnings:
            state.warnings.extend(execution_context.warnings)
        self._progress(f"expert {action.target_role}")
        try:
            result = self.expert_runner.run(
                action.target_role,
                state,
                execution_context=execution_context,
                revision_request=revision,
            )
        except LLMRequestError as exc:
            self._progress(_format_llm_request_error_for_terminal(exc, speaker=action.target_role))
            _record_llm_request_error(state, exc, speaker=action.target_role, action=action)
            return
        except LLMJSONParseError as exc:
            _record_llm_json_parse_error(state, exc, speaker=action.target_role, action=action)
            return
        proposal_start = len(state.tool_request_proposals)
        self._store_expert_output(state, action.target_role, result.output)
        turn = state.add_turn(
            action.target_role,
            "expert",
            action=action,
            output=result.output,
            metadata=_expert_turn_metadata(result),
            warnings=result.warnings + execution_context.warnings,
        )
        _record_expert_revision(
            state,
            action,
            artifact_key,
            before_revision,
            turn_index=turn.index,
        )
        if (
            action.target_role == "logical_model_designer"
            and state.method_definition.normalization_validation_required
        ):
            self._auto_validate_current_logical_model(
                state,
                proposal_start=proposal_start,
            )
        self._maybe_compile_after_experts(state, action.target_role)

    def _handle_test_expert_action(self, state: DynamicMethodState, action: SchedulerAction) -> None:
        artifact_key = state.method_definition.artifact_by_role["test_expert"]
        before_revision = _artifact_revision_snapshot(state, artifact_key)
        revision = _revision_request_from_action(action)
        execution_context = materialize_expert_context(
            state,
            "test_expert",
            action.execution_context_selection,
        )
        if execution_context.warnings:
            state.warnings.extend(execution_context.warnings)
        self._progress("expert test_expert")
        try:
            result = self.expert_runner.run(
                "test_expert",
                state,
                execution_context=execution_context,
                revision_request=revision,
            )
        except LLMRequestError as exc:
            self._progress(_format_llm_request_error_for_terminal(exc, speaker="test_expert"))
            _record_llm_request_error(state, exc, speaker="test_expert", action=action)
            return
        except LLMJSONParseError as exc:
            _record_llm_json_parse_error(state, exc, speaker="test_expert", action=action)
            return

        proposal_start = len(state.tool_request_proposals)
        initial_report = self._store_expert_output(state, "test_expert", result.output)
        initial_record = state.artifacts[artifact_key]
        initial_version = int(initial_record.version)
        initial_tests = copy.deepcopy(initial_report.get("generated_tests") or [])
        initial_turn = state.add_turn(
            "test_expert",
            "expert",
            action=action,
            output=result.output,
            metadata=_expert_turn_metadata(result),
            warnings=result.warnings + execution_context.warnings,
        )
        _record_expert_revision(
            state,
            action,
            artifact_key,
            before_revision,
            turn_index=initial_turn.index,
        )

        if initial_record.status != "validated":
            return

        revision_mode = str((revision or {}).get("mode") or "")
        if (
            not state.method_definition.cross_expert_feedback_repair_enabled
            and revision_mode == "fixed_pipeline_artifact_validation_retry"
            and _current_runtime_tool_records(state)
        ):
            correction_proposals = state.tool_request_proposals[proposal_start:]
            _classify_test_expert_proposals(
                state,
                correction_proposals,
                interpretation=True,
            )
            return

        _ensure_fixed_pipeline_ddl_execution_proposal(state)
        proposals = state.tool_request_proposals[proposal_start:]
        executable = _classify_test_expert_proposals(state, proposals, interpretation=False)
        _ensure_fixed_pipeline_sql_execution_proposal(
            state,
            executable,
            generated_tests=initial_tests,
        )
        if not executable:
            return

        batch_id = f"test_expert_turn_{initial_turn.index}"
        tool_result_indexes = self._execute_test_expert_tool_batch(
            state,
            executable,
            batch_id=batch_id,
        )
        if not tool_result_indexes:
            return
        interpretation_context = _build_test_expert_interpretation_context(
            state,
            execution_context.to_dict(),
            initial_report=initial_report,
            initial_version=initial_version,
            tool_result_indexes=tool_result_indexes,
            batch_id=batch_id,
        )
        interpretation_request = {
            "instruction": (
                "Interpret this in-turn tool batch. Preserve generated_tests exactly; update only "
                "execution_feedback, feedback, passed, and warnings. Do not request or assume "
                "another tool execution in this interpretation pass."
            ),
            "mode": "in_turn_tool_interpretation",
            "initial_test_report_version": initial_version,
            "tool_batch_id": batch_id,
        }
        self._progress("expert test_expert interpretation")
        interpretation_retry_limit = (
            FIXED_PIPELINE_JSON_RETRY_LIMIT
            if (
                state.method_definition.orchestration_mode == "fixed_pipeline"
                and not state.method_definition.cross_expert_feedback_repair_enabled
            )
            else 0
        )
        interpretation_retry_entry: dict[str, Any] | None = None
        interpreted = None
        for interpretation_attempt in range(interpretation_retry_limit + 1):
            try:
                interpreted = self.expert_runner.run(
                    "test_expert",
                    state,
                    execution_context=interpretation_context,
                    revision_request=interpretation_request,
                )
                if interpretation_retry_entry is not None:
                    interpretation_retry_entry["status"] = "completed"
                    interpretation_retry_entry["artifact_versions_after"] = (
                        state.artifact_versions()
                    )
                    interpretation_retry_entry["completed_turn_index"] = len(state.turns)
                break
            except LLMRequestError as exc:
                self._progress(
                    _format_llm_request_error_for_terminal(exc, speaker="test_expert")
                )
                _record_recoverable_llm_request_error(
                    state,
                    exc,
                    speaker="test_expert",
                    action=action,
                    stage="test_expert_in_turn_interpretation",
                )
                if not state.method_definition.cross_expert_feedback_repair_enabled:
                    _mark_test_report_interpretation_unavailable(
                        state,
                        "Test Expert tool evidence is available but its automatic interpretation failed.",
                    )
                else:
                    _mark_test_report_unverified(
                        state,
                        "Test Expert tool evidence is available but its automatic interpretation failed.",
                    )
                return
            except LLMJSONParseError as exc:
                _record_llm_json_parse_error(
                    state,
                    exc,
                    speaker="test_expert",
                    action=action,
                )
                if interpretation_retry_limit <= 0:
                    _mark_test_report_unverified(
                        state,
                        "Test Expert tool evidence is available but its automatic interpretation was not valid JSON.",
                    )
                    return
                if interpretation_retry_entry is None:
                    interpretation_retry_entry = {
                        "repair_id": (
                            "fixed_pipeline_interpretation_json_retry_"
                            f"{len(state.repair_history) + 1}"
                        ),
                        "event_type": "fixed_pipeline_json_retry",
                        "kind": "fixed_pipeline_json_retry",
                        "status": "in_progress",
                        "counts_against_repair_budget": False,
                        "role": "test_expert",
                        "stage": "tool_interpretation",
                        "artifact": artifact_key,
                        "max_json_retries": FIXED_PIPELINE_JSON_RETRY_LIMIT,
                        "artifact_versions_before": state.artifact_versions(),
                        "attempts": [],
                    }
                    state.repair_history.append(interpretation_retry_entry)
                interpretation_retry_entry["attempts"].append(
                    {
                        "retry_attempt": interpretation_attempt + 1,
                        "message": str(exc),
                        "raw_output_excerpt": str(exc.raw_text or "")[:4000],
                        "raw_output_chars": len(str(exc.raw_text or "")),
                    }
                )
                if interpretation_attempt >= interpretation_retry_limit:
                    interpretation_retry_entry["status"] = "failed"
                    interpretation_retry_entry["artifact_versions_after"] = (
                        state.artifact_versions()
                    )
                    _set_fixed_pipeline_terminal(
                        state,
                        status="needs_review",
                        reason=(
                            "Test Expert interpretation returned invalid JSON after "
                            f"{interpretation_retry_limit + 1} attempts"
                        ),
                        category="json_output",
                    )
                    return
                interpretation_request = {
                    **interpretation_request,
                    "instruction": (
                        "The previous interpretation was not valid JSON. Preserve generated_tests "
                        "exactly and return only one complete JSON object matching the Test Expert "
                        "contract. Do not request another tool batch."
                    ),
                    "json_retry_attempt": interpretation_attempt + 1,
                    "max_json_retries": interpretation_retry_limit,
                    "json_parse_error": copy.deepcopy(
                        interpretation_retry_entry["attempts"][-1]
                    ),
                }

        if interpreted is None:  # pragma: no cover - loop always returns or assigns
            return

        final_report, tests_changed, mutation_warning = _merge_test_expert_interpretation(
            initial_report,
            interpreted.output,
            initial_tests,
        )
        if mutation_warning:
            state.warnings.append(mutation_warning)
        interpretation_proposal_start = len(state.tool_request_proposals)
        self._store_expert_output(state, "test_expert", final_report)
        interpretation_proposals = state.tool_request_proposals[interpretation_proposal_start:]
        _classify_test_expert_proposals(state, interpretation_proposals, interpretation=True)
        final_version = int(state.artifacts[artifact_key].version)
        _rebind_tool_results_to_test_report_version(
            state,
            tool_result_indexes,
            final_version,
        )
        state.add_turn(
            "test_expert",
            "tool_interpretation",
            action=action,
            output=final_report,
            metadata=_expert_turn_metadata(interpreted),
            warnings=[mutation_warning] if tests_changed and mutation_warning else interpreted.warnings,
        )

    def _execute_test_expert_tool_batch(
        self,
        state: DynamicMethodState,
        proposals: list[dict[str, Any]],
        *,
        batch_id: str,
    ) -> list[int]:
        by_tool = {str(item.get("tool_type") or ""): item for item in proposals}
        ordered = [by_tool[tool_type] for tool_type in TEST_EXPERT_IN_TURN_TOOL_ORDER if tool_type in by_tool]
        result_indexes: list[int] = []
        blocked_by = ""

        for proposal in ordered:
            tool_type = str(proposal.get("tool_type") or "")
            if blocked_by:
                result_indexes.append(
                    _record_skipped_test_expert_tool(
                        state,
                        proposal,
                        reason=f"blocked_by_{blocked_by}_failure",
                        batch_id=batch_id,
                    )
                )
                continue

            request = ToolRequest(
                tool_type=tool_type,
                target_artifact=TEST_EXPERT_IN_TURN_TOOL_TARGETS[tool_type],
                reason=str(proposal.get("reason") or ""),
                payload={
                    **dict(proposal.get("payload_hint") or {}),
                    "proposal_id": str(proposal.get("proposal_id") or ""),
                    "in_turn_batch_id": batch_id,
                },
            )
            try:
                tool_result = self.toolbox.execute(state, request)
            except Exception as exc:  # Tool crashes become evidence for scheduler-directed recovery.
                tool_result = {
                    "tool_type": tool_type,
                    "passed": False,
                    "success": False,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "warnings": ["in-turn tool execution raised an exception"],
                }
            result_indexes.append(
                _record_test_expert_tool_result(
                    state,
                    proposal,
                    request,
                    tool_result,
                    batch_id=batch_id,
                )
            )
            if tool_type == "ddl_executor" and not _ddl_tool_succeeded(tool_result):
                blocked_by = tool_type
            elif tool_type == "sql_test_runner" and not bool(tool_result.get("passed")):
                blocked_by = tool_type
        return result_indexes

    def _handle_finalize(self, state: DynamicMethodState, action: SchedulerAction) -> None:
        state.update_artifact_status("ddl", "validated" if str(state.artifact_payload("ddl", "") or "").strip() else "draft")
        state.final_explanation = action.explanation.strip()
        verification_summary = _build_verification_summary(state)
        state.store_artifact(
            "verification_summary",
            verification_summary,
            producer="tool",
            status="validated",
        )
        state.add_turn("scheduler", "finalize", output={**action.to_dict(), "verification_summary": verification_summary})

    def _bootstrap_dry_run(self, state: DynamicMethodState) -> None:
        requirement_output = {
            "task_summary": "dry run",
            "candidate_concepts": [],
            "candidate_attributes": [],
            "relationship_hints": [],
            "latent_invariants": [],
            "lifecycle_and_history": [],
            "ownership_and_deletion_semantics": [],
            "workload_implications": [],
            "ambiguities": [],
        }
        conceptual_output = {
            "entities": [],
            "relationships": [],
            "conceptual_invariants": [],
            "design_assumptions": [],
            "warnings": ["dry_run"],
        }
        logical_output = {
            "schema_ir": {"tables": []},
            "constraint_traceability": [],
            "design_notes": [],
            "warnings": ["dry_run"],
        }
        if state.method_definition.normalization_validation_required:
            logical_output["normalization_spec"] = {"tables": []}
        physical_output = {"physical_plan": {"indexes": [], "notes": []}, "workload_traceability": [], "warnings": ["dry_run"]}
        dialect_output = {"dialect_notes": ["dry_run"], "ddl": "", "warnings": [], "errors": []}
        test_output = {"generated_tests": [], "execution_feedback": [], "feedback": [], "passed": True, "warnings": ["dry_run"]}
        if "requirement_analyst" in state.method_definition.expert_roles:
            self._store_expert_output(state, "requirement_analyst", requirement_output)
        dry_run_outputs = {
            "conceptual_model_designer": conceptual_output,
            "logical_model_designer": logical_output,
            "physical_design_specialist": physical_output,
            "dialect_compiler": dialect_output,
            "test_expert": test_output,
        }
        for role, output in dry_run_outputs.items():
            if role in state.method_definition.expert_roles:
                self._store_expert_output(state, role, output)
        speaker = (
            "scheduler"
            if state.method_definition.orchestration_mode == "scheduler"
            else "harness"
        )
        state.add_turn(speaker, "dry_run", output={"message": "bootstrapped dry run"})

    def _store_expert_output(self, state: DynamicMethodState, role: str, output: dict[str, Any]) -> dict[str, Any]:
        if role == "test_expert":
            output = _merge_test_report_output(state.artifact_payload("test_report", {}), output)
        validation = self.toolbox.execute(
            state,
            self._validator_request_for_role(state, role, payload=output),
        )
        status = "validated" if validation.get("passed") else "needs_revision"
        state.store_role_artifact(role, output, status=status, validation=validation)
        self._store_tool_request_proposals(state, role, output)
        return output

    def _store_tool_request_proposals(self, state: DynamicMethodState, role: str, output: dict[str, Any]) -> None:
        raw_proposals = output.get("tool_request_proposals") if isinstance(output, dict) else None
        if not isinstance(raw_proposals, list):
            return
        for item in raw_proposals:
            if not isinstance(item, dict):
                continue
            proposal = ToolRequestProposal.from_dict(
                item,
                proposal_id=f"proposal_{len(state.tool_request_proposals) + 1}",
                proposer_role=role,
            )
            if proposal is None:
                continue
            errors = proposal.validate(
                list(state.method_definition.expert_roles),
                state.method_definition.allowed_tool_types,
            )
            if errors:
                rejected = proposal.to_dict()
                rejected["status"] = "rejected"
                rejected["validation_errors"] = list(errors)
                rejected["original_request"] = dict(item)
                rejected["artifact_versions"] = state.artifact_versions()
                state.add_tool_request_proposal(rejected)
                state.warnings.extend(
                    f"rejected tool_request_proposal {proposal.proposal_id}: {error}"
                    for error in errors
                )
                continue
            proposal_payload = proposal.to_dict()
            proposal_payload["artifact_versions"] = state.artifact_versions()
            state.add_tool_request_proposal(proposal_payload)

    def _auto_validate_current_logical_model(
        self,
        state: DynamicMethodState,
        *,
        proposal_start: int,
    ) -> None:
        request = ToolRequest(
            tool_type=THIRD_NORMAL_FORM_TOOL,
            target_artifact="logical_model",
            reason="Automatically validate the newly produced logical model version.",
        )
        result = self.toolbox.execute(state, request)
        state.tool_results.append(
            {
                "request": request.to_dict(),
                "result": result,
                "artifact_versions": state.artifact_versions(),
                "execution": {"mode": "harness_auto_validation"},
            }
        )
        _apply_normalization_result(state, result)
        tool_result_ref = f"tool_result_{len(state.tool_results)}"
        matched = False
        for proposal in state.tool_request_proposals[proposal_start:]:
            if not isinstance(proposal, dict):
                continue
            if proposal.get("tool_type") != THIRD_NORMAL_FORM_TOOL:
                continue
            if proposal.get("status") != "pending":
                continue
            if not matched:
                proposal["status"] = "executed"
                proposal["tool_result_ref"] = tool_result_ref
                proposal["execution_mode"] = "harness_auto_validation"
                matched = True
            else:
                proposal["status"] = "superseded"
                proposal["superseded_reason"] = "duplicate_auto_normalization_request"
        state.add_turn(
            "tool",
            THIRD_NORMAL_FORM_TOOL,
            action={
                "action_type": "auto_call_tool",
                "target_artifact": "logical_model",
            },
            output=result,
            metadata={"execution_mode": "harness_auto_validation"},
        )

    def _validator_request_for_role(
        self,
        state: DynamicMethodState,
        role: str,
        payload: dict[str, Any] | None = None,
    ):
        from .contracts import ToolRequest

        return ToolRequest(
            tool_type="artifact_validator",
            target_artifact=state.method_definition.artifact_by_role[role],
            reason=f"validate {role} artifact",
            payload=payload or {},
        )

    def _maybe_compile_after_experts(self, state: DynamicMethodState, role: str) -> None:
        if role == "dialect_compiler":
            report = state.artifact_payload("dialect_report", {}) or {}
            ddl = str(report.get("ddl") or report.get("final_ddl") or "")
            if ddl.strip():
                state.final_ddl = ddl
                state.update_artifact_status("ddl", "validated")

    def _final_status(self, state: DynamicMethodState) -> str:
        if state.current_phase == "failed":
            return "failed"
        if state.method_definition.orchestration_mode == "fixed_pipeline":
            terminal = str(state.fixed_pipeline.get("terminal_status") or "")
            return terminal or _fixed_pipeline_evidence_status(state)
        if not state.method_definition.runtime_verification_required:
            completion = design_only_completion_status(state)
            return "ready" if completion["ready"] else "needs_review"
        if not str(state.artifact_payload("ddl", "") or "").strip():
            return "needs_review"
        if any(
            record.status == "needs_revision"
            for record in state.artifacts.values()
        ):
            return "needs_review"
        logical_record = state.artifacts.get("logical_model")
        if logical_record is not None and logical_record.version > 0:
            normalization_evidence = current_third_normal_form_evidence(state)
            if normalization_evidence is None:
                return "unverified_ready"
            normalization_result = normalization_evidence[1].get("result")
            if not isinstance(normalization_result, dict) or not normalization_result.get("passed"):
                return "needs_review"
        facts = _collect_evaluation_facts(state)
        if not facts["test_report_produced"] or facts["generated_test_count"] <= 0:
            return "unverified_ready"
        if facts["test_report_passed"] is False:
            return "needs_review"
        if facts["sql_tests_attempted"] and facts["sql_test_tool_passed"] is False:
            return "needs_review"
        if facts["generated_test_count"] > 0 and (
            not facts["sql_tests_attempted"]
            or not facts["sql_test_real_execution"]
            or facts["sql_test_total"] <= 0
        ):
            return "unverified_ready"
        if _pending_tool_request_count(state, {"sql_test_runner", "ddl_executor", "dialect_linter"}) > 0:
            return "unverified_ready"
        if facts["query_plan_required"] and not facts["query_plan_has_raw_evidence"]:
            return "unverified_ready"
        if not facts["ready_evidence"]:
            return "unverified_ready"
        return "ready"

    def _run_path(self, task_id: str) -> Path:
        return self.options.run_dir / f"{task_id}.json"

    def _write_run(self, run_path: Path, state: DynamicMethodState, status: str) -> None:
        payload = {
            "task_id": state.task.id,
            **state.method_definition.to_metadata(),
            "status": status,
            "final_ddl": state.final_ddl,
            "final_explanation": state.final_explanation,
            "evaluation_metrics": _build_evaluation_metrics(state),
            "state": state.to_dict(),
            "llm": self.llm_client.metadata(),
            "warnings": state.warnings,
            "errors": state.errors,
        }
        write_json(run_path, payload)

    def _progress(self, message: str) -> None:
        if callable(self.options.progress_callback):
            self.options.progress_callback(message)

    def _progress_llm_attempt_error(
        self,
        error: LLMRequestError,
        speaker: str,
        record: dict[str, Any],
        total_attempts: int,
    ) -> None:
        self._progress(
            _format_llm_attempt_error_for_terminal(
                error,
                speaker=speaker,
                record=record,
                total_attempts=total_attempts,
            )
        )


def _finalize_reserve_available(state: DynamicMethodState) -> bool:
    if state.finalize_reserve_used:
        return False
    readiness = build_state_catalog(state).get("readiness")
    if not isinstance(readiness, dict):
        return False
    blockers = readiness.get("finalize_blockers")
    return isinstance(blockers, list) and not blockers


def _revision_request_from_action(action: SchedulerAction) -> dict[str, Any] | None:
    metadata = action.metadata if isinstance(action.metadata, dict) else {}
    supplied = metadata.get("revision_request")
    if isinstance(supplied, dict):
        revision = copy.deepcopy(supplied)
        if action.instruction and not revision.get("instruction"):
            revision["instruction"] = action.instruction
        return revision
    return {"instruction": action.instruction} if action.instruction else None


def _complete_fixed_pipeline_without_feedback_repair(
    state: DynamicMethodState,
) -> None:
    _categories, invalid_categories, category_declared = _test_failure_categories(state)
    if not category_declared:
        state.warnings.append(
            "Test Expert omitted diagnostic failure_category; terminal status uses raw evidence only."
        )
    if invalid_categories:
        state.warnings.append(
            "Test Expert returned invalid diagnostic failure_category values: "
            + ", ".join(invalid_categories)
            + "; terminal status uses raw evidence only."
        )

    status = _fixed_pipeline_evidence_status(state)
    facts = _collect_evaluation_facts(state)
    if status == "ready":
        reason = "first-pass design and terminal runtime verification passed"
    elif status == "needs_review":
        reason = (
            "first-pass design or terminal runtime verification failed; "
            "cross-expert feedback repair is disabled"
        )
    elif status == "unverified_ready":
        reason = (
            "first-pass design is complete but terminal runtime evidence or "
            "Test Expert interpretation is incomplete"
        )
    else:
        reason = "fixed pipeline failed before terminal verification completed"
    if facts["status_blockers"]:
        reason += "; blockers: " + ", ".join(facts["status_blockers"])
    _set_fixed_pipeline_terminal(
        state,
        status=status,
        reason=reason,
    )


def _set_fixed_pipeline_terminal(
    state: DynamicMethodState,
    *,
    status: str,
    reason: str,
    category: str = "",
) -> None:
    state.current_phase = "fixed_pipeline_complete"
    state.fixed_pipeline["terminal_status"] = status
    state.fixed_pipeline["terminal_reason"] = reason
    state.fixed_pipeline["terminal_failure_category"] = category
    state.fixed_pipeline["repair_rounds"] = state.repair_budget_used()
    if status != "needs_review":
        return
    state.repair_history.append(
        {
            "repair_id": f"fixed_pipeline_terminal_{len(state.repair_history) + 1}",
            "event_type": "fixed_pipeline_terminal",
            "kind": "fixed_pipeline_terminal",
            "status": "stopped",
            "failure_category": category,
            "fixed_role_chain": [],
            "repair_artifacts": [],
            "repair_round": state.repair_budget_used(),
            "reason": reason,
            "artifact_versions": state.artifact_versions(),
            "evidence_refs": _current_runtime_evidence_refs(state),
        }
    )


def _fixed_pipeline_evidence_status(state: DynamicMethodState) -> str:
    if state.current_phase == "failed":
        return "failed"
    active_artifacts = tuple(dict.fromkeys(state.method_definition.artifact_by_role.values()))
    active_records = [state.artifacts.get(key) for key in active_artifacts]
    if any(record is None or record.version <= 0 for record in active_records):
        return "needs_review"
    if any(record.status != "validated" or record.stale for record in active_records if record):
        return "needs_review"
    ddl_record = state.artifacts.get("ddl")
    if (
        ddl_record is None
        or ddl_record.version <= 0
        or ddl_record.status != "validated"
        or ddl_record.stale
        or not str(state.artifact_payload("ddl", "") or "").strip()
    ):
        return "needs_review"

    facts = _collect_evaluation_facts(state)
    if facts["test_report_passed"] is False or facts["sql_test_tool_passed"] is False:
        return "needs_review"
    if facts["ddl_execution_attempted"] and not facts["ddl_executor_success"]:
        return "needs_review"
    if facts["query_plan_error_count"] > 0 or _runtime_tool_error_observed(state):
        return "needs_review"
    if not facts["test_report_produced"] or facts["generated_test_count"] <= 0:
        return "unverified_ready"
    if (
        not state.method_definition.cross_expert_feedback_repair_enabled
        and not facts["test_interpretation_completed"]
    ):
        return "unverified_ready"
    if not facts["ddl_real_execution"]:
        return "unverified_ready"
    if (
        not facts["sql_tests_attempted"]
        or not facts["sql_test_real_execution"]
        or facts["sql_test_total"] <= 0
    ):
        return "unverified_ready"
    if facts["query_plan_required"] and not facts["query_plan_has_raw_evidence"]:
        return "unverified_ready"
    return "ready" if facts["ready_evidence"] else "unverified_ready"


def _fixed_pipeline_has_runtime_failure(state: DynamicMethodState) -> bool:
    facts = _collect_evaluation_facts(state)
    return bool(
        facts["test_report_passed"] is False
        or facts["sql_test_tool_passed"] is False
        or (
            facts["ddl_execution_attempted"]
            and not facts["ddl_executor_success"]
        )
        or _runtime_tool_error_observed(state)
    )


def _runtime_tool_error_observed(state: DynamicMethodState) -> bool:
    for item in _current_runtime_tool_records(state):
        result = item.get("result") if isinstance(item, dict) else None
        if not isinstance(result, dict):
            continue
        if result.get("skipped") and result.get("reason"):
            return True
        if result.get("passed") is False or result.get("success") is False:
            return True
        if result.get("error_message") or result.get("error"):
            return True
    return False


def _test_failure_categories(
    state: DynamicMethodState,
) -> tuple[set[str], list[str], bool]:
    report = state.artifact_payload("test_report", {}) or {}
    if not isinstance(report, dict):
        return set(), [], False
    values: list[Any] = []
    declared = False
    for key in ("failure_category", "failure_categories"):
        if key in report:
            declared = True
            raw = report.get(key)
            values.extend(raw if isinstance(raw, list) else [raw])
    for collection_key in ("feedback", "execution_feedback"):
        collection = report.get(collection_key)
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            for key in ("failure_category", "failure_categories"):
                if key not in item:
                    continue
                declared = True
                raw = item.get(key)
                values.extend(raw if isinstance(raw, list) else [raw])

    allowed = set(
        state.method_definition.failure_category_priority
        or FIXED_PIPELINE_FAILURE_CATEGORIES
    )
    categories: set[str] = set()
    invalid: list[str] = []
    for value in values:
        normalized = str(value or "").strip().lower()
        if not normalized or normalized == "none":
            continue
        if normalized in allowed:
            categories.add(normalized)
        elif normalized not in invalid:
            invalid.append(normalized)
    return categories, invalid, declared


def _build_fixed_repair_envelope(
    state: DynamicMethodState,
    *,
    failure_category: str,
    repair_round: int,
    validation_failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ddl_record = state.artifacts.get("ddl")
    test_record = state.artifacts.get("test_report")
    tool_results = _current_runtime_tool_records(state)
    evidence_refs = _current_runtime_evidence_refs(state)
    latest_test_turn = next(
        (
            turn
            for turn in reversed(state.turns)
            if turn.speaker == "test_expert"
        ),
        None,
    )
    if latest_test_turn is not None:
        evidence_refs.append(f"turn_{latest_test_turn.index}")
    return {
        "failure_category": failure_category,
        "repair_round": repair_round,
        "artifact_versions": state.artifact_versions(),
        "current_ddl": {
            "version": int(ddl_record.version if ddl_record is not None else 0),
            "payload": copy.deepcopy(state.artifact_payload("ddl", "")),
        },
        "current_test_report": {
            "version": int(test_record.version if test_record is not None else 0),
            "payload": copy.deepcopy(state.artifact_payload("test_report", {})),
        },
        "failure_evidence": _fixed_failure_evidence(state),
        "tool_results": copy.deepcopy(tool_results),
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "validation_failure": copy.deepcopy(validation_failure or {}),
    }


def _fixed_failure_evidence(state: DynamicMethodState) -> dict[str, Any]:
    report = state.artifact_payload("test_report", {}) or {}
    if not isinstance(report, dict):
        report = {}
    failed_tool_results = []
    for item in _current_runtime_tool_records(state):
        result = item.get("result") if isinstance(item, dict) else None
        if not isinstance(result, dict):
            continue
        if (
            result.get("passed") is False
            or result.get("success") is False
            or result.get("error")
            or result.get("error_message")
            or result.get("skipped")
        ):
            failed_tool_results.append(copy.deepcopy(item))
    return {
        "failure_category": copy.deepcopy(report.get("failure_category")),
        "feedback": copy.deepcopy(report.get("feedback") or []),
        "execution_feedback": copy.deepcopy(report.get("execution_feedback") or []),
        "generated_tests": copy.deepcopy(report.get("generated_tests") or []),
        "failed_tool_results": failed_tool_results,
    }


def _current_runtime_tool_records(state: DynamicMethodState) -> list[dict[str, Any]]:
    current_versions = state.artifact_versions()
    records: list[dict[str, Any]] = []
    for index, item in enumerate(state.tool_results, start=1):
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        if not isinstance(request, dict) or request.get("tool_type") not in TEST_EXPERT_IN_TURN_TOOL_ORDER:
            continue
        versions = item.get("artifact_versions")
        if not isinstance(versions, dict):
            continue
        if int(versions.get("ddl", 0) or 0) != int(current_versions.get("ddl", 0) or 0):
            continue
        if request.get("tool_type") in {"sql_test_runner", "query_plan_tool"} and (
            int(versions.get("test_report", 0) or 0)
            != int(current_versions.get("test_report", 0) or 0)
        ):
            continue
        record = copy.deepcopy(item)
        record["ref"] = f"tool_result_{index}"
        records.append(record)
    return records


def _current_runtime_evidence_refs(state: DynamicMethodState) -> list[str]:
    return [str(item.get("ref") or "") for item in _current_runtime_tool_records(state)]


def _expert_turn_metadata(result: Any) -> dict[str, Any]:
    retrieval = getattr(result, "dialect_retrieval", None)
    if not isinstance(retrieval, dict) or not retrieval:
        return {}
    return {"dialect_retrieval": copy.deepcopy(retrieval)}


def _ensure_fixed_pipeline_ddl_execution_proposal(
    state: DynamicMethodState,
) -> None:
    if state.method_definition.orchestration_mode != "fixed_pipeline":
        return
    ddl_record = state.artifacts.get("ddl")
    if (
        ddl_record is None
        or ddl_record.version <= 0
        or not str(ddl_record.payload or "").strip()
        or _matching_ddl_executor_evidence_for_current_version(state) is not None
    ):
        return
    proposal = ToolRequestProposal(
        proposal_id=f"proposal_{len(state.tool_request_proposals) + 1}",
        proposer_role="test_expert",
        tool_type="ddl_executor",
        target_artifact="ddl",
        reason="Harness-required execution attempt for the current fixed-pipeline DDL version.",
        expected_interpreter="test_expert",
    ).to_dict()
    proposal["artifact_versions"] = state.artifact_versions()
    proposal["request_origin"] = "fixed_pipeline_harness"
    proposal["harness_required"] = True
    state.add_tool_request_proposal(proposal)


def _ensure_fixed_pipeline_sql_execution_proposal(
    state: DynamicMethodState,
    executable: list[dict[str, Any]],
    *,
    generated_tests: Any,
) -> None:
    if (
        state.method_definition.orchestration_mode != "fixed_pipeline"
        or state.method_definition.cross_expert_feedback_repair_enabled
        or not isinstance(generated_tests, list)
        or not generated_tests
        or any(item.get("tool_type") == "sql_test_runner" for item in executable)
    ):
        return
    proposal = ToolRequestProposal(
        proposal_id=f"proposal_{len(state.tool_request_proposals) + 1}",
        proposer_role="test_expert",
        tool_type="sql_test_runner",
        target_artifact="test_report",
        reason="Harness-required execution of non-empty generated tests in the terminal verification batch.",
        expected_interpreter="test_expert",
    ).to_dict()
    proposal["artifact_versions"] = state.artifact_versions()
    proposal["request_origin"] = "fixed_pipeline_harness"
    proposal["harness_required"] = True
    state.add_tool_request_proposal(proposal)
    executable.append(state.tool_request_proposals[-1])


def _classify_test_expert_proposals(
    state: DynamicMethodState,
    proposals: list[dict[str, Any]],
    *,
    interpretation: bool,
) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    seen_tools: set[str] = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or proposal.get("status") == "rejected":
            continue
        tool_type = str(proposal.get("tool_type") or "")
        errors: list[str] = []
        expected_target = TEST_EXPERT_IN_TURN_TOOL_TARGETS.get(tool_type)
        if expected_target is None:
            errors.append(
                "test_expert may request only ddl_executor, sql_test_runner, or query_plan_tool"
            )
        elif str(proposal.get("target_artifact") or "") != expected_target:
            errors.append(
                f"{tool_type} requires target_artifact={expected_target} for test_expert in-turn execution"
            )
        if not str(proposal.get("reason") or "").strip():
            errors.append("test_expert in-turn tool proposal requires reason")
        interpreter = str(proposal.get("expected_interpreter") or "")
        if interpreter not in {"", "test_expert"}:
            errors.append("test_expert in-turn proposal expected_interpreter must be empty or test_expert")
        if errors:
            proposal["status"] = "rejected"
            proposal["validation_errors"] = [
                *list(proposal.get("validation_errors") or []),
                *errors,
            ]
            state.warnings.extend(
                f"rejected tool_request_proposal {proposal.get('proposal_id')}: {error}"
                for error in errors
            )
            continue
        if tool_type in seen_tools:
            proposal["status"] = "superseded"
            proposal["superseded_reason"] = "duplicate_tool_type_in_test_expert_batch"
            continue
        seen_tools.add(tool_type)
        if interpretation:
            proposal["status"] = "deferred"
            proposal["deferred_reason"] = "interpretation_proposals_do_not_execute_recursively"
            if state.method_definition.cross_expert_feedback_repair_enabled:
                detail = "scheduler must invoke Test Expert again to start another batch"
            else:
                detail = "terminal verification permits exactly one tool batch"
            state.warnings.append(
                f"deferred tool_request_proposal {proposal.get('proposal_id')} from Test Expert "
                f"interpretation; {detail}"
            )
            continue
        accepted.append(proposal)
    return accepted


def _record_test_expert_tool_result(
    state: DynamicMethodState,
    proposal: dict[str, Any],
    request: ToolRequest,
    result: dict[str, Any],
    *,
    batch_id: str,
) -> int:
    record = {
        "request": request.to_dict(),
        "result": result,
        "artifact_versions": state.artifact_versions(),
        "execution": {
            "mode": "test_expert_in_turn",
            "batch_id": batch_id,
        },
    }
    state.tool_results.append(record)
    proposal["status"] = "executed"
    proposal["tool_result_ref"] = f"tool_result_{len(state.tool_results)}"
    state.add_turn(
        "tool",
        request.tool_type,
        action={
            "action_type": "auto_call_tool",
            "target_role": "test_expert",
            "tool_batch_id": batch_id,
            "proposal_id": proposal.get("proposal_id"),
        },
        output=result,
    )
    return len(state.tool_results) - 1


def _record_skipped_test_expert_tool(
    state: DynamicMethodState,
    proposal: dict[str, Any],
    *,
    reason: str,
    batch_id: str,
    add_turn: bool = True,
) -> int:
    tool_type = str(proposal.get("tool_type") or "")
    request = ToolRequest(
        tool_type=tool_type,
        target_artifact=TEST_EXPERT_IN_TURN_TOOL_TARGETS.get(tool_type, ""),
        reason=str(proposal.get("reason") or ""),
        payload={
            **dict(proposal.get("payload_hint") or {}),
            "proposal_id": str(proposal.get("proposal_id") or ""),
            "in_turn_batch_id": batch_id,
        },
    )
    result = {
        "tool_type": tool_type,
        "skipped": True,
        "passed": False,
        "success": False,
        "reason": reason,
        "warnings": [f"{tool_type} was not executed: {reason}"],
    }
    record = {
        "request": request.to_dict(),
        "result": result,
        "artifact_versions": state.artifact_versions(),
        "execution": {
            "mode": "test_expert_in_turn",
            "batch_id": batch_id,
        },
    }
    state.tool_results.append(record)
    proposal["status"] = "skipped"
    proposal["skip_reason"] = reason
    proposal["tool_result_ref"] = f"tool_result_{len(state.tool_results)}"
    if add_turn:
        state.add_turn(
            "tool",
            tool_type,
            status="skipped",
            action={
                "action_type": "auto_call_tool",
                "target_role": "test_expert",
                "tool_batch_id": batch_id,
                "proposal_id": proposal.get("proposal_id"),
            },
            output=result,
            warnings=list(result["warnings"]),
        )
    return len(state.tool_results) - 1


def _ddl_tool_succeeded(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    success = result.get("success")
    if isinstance(success, bool):
        return success
    return bool(result.get("passed"))


def _build_test_expert_interpretation_context(
    state: DynamicMethodState,
    original_context: dict[str, Any],
    *,
    initial_report: dict[str, Any],
    initial_version: int,
    tool_result_indexes: list[int],
    batch_id: str,
) -> dict[str, Any]:
    batch_results = [
        {
            "ref": f"tool_result_{index + 1}",
            **copy.deepcopy(state.tool_results[index]),
        }
        for index in tool_result_indexes
        if 0 <= index < len(state.tool_results)
    ]
    readiness = build_state_catalog(state).get("readiness", {})
    contents = [
        ("original_execution_context", copy.deepcopy(original_context)),
        (
            "initial_test_report",
            {
                "version": initial_version,
                "payload": copy.deepcopy(initial_report),
            },
        ),
        ("in_turn_tool_results", batch_results),
        ("readiness", copy.deepcopy(readiness)),
    ]
    items = []
    total_chars = 0
    for source, content in contents:
        content_chars = len(json.dumps(content, ensure_ascii=False, default=str))
        total_chars += content_chars
        items.append(
            {
                "source": source,
                "view": "full",
                "content": content,
                "content_chars": content_chars,
                "truncated": False,
            }
        )
    return {
        "selection": {
            "mode": "test_expert_in_turn_interpretation",
            "batch_id": batch_id,
        },
        "items": items,
        "total_chars": total_chars,
        "truncated": False,
        "warnings": [],
    }


def _merge_test_expert_interpretation(
    initial_report: dict[str, Any],
    interpreted_output: dict[str, Any],
    initial_tests: list[Any],
) -> tuple[dict[str, Any], bool, str]:
    final_report = copy.deepcopy(initial_report)
    for key in (
        "execution_feedback",
        "feedback",
        "failure_category",
        "failure_categories",
        "passed",
        "warnings",
    ):
        if key in interpreted_output:
            final_report[key] = copy.deepcopy(interpreted_output[key])
    raw_proposals = interpreted_output.get("tool_request_proposals")
    final_report["tool_request_proposals"] = (
        copy.deepcopy(raw_proposals) if isinstance(raw_proposals, list) else []
    )

    interpreted_tests = interpreted_output.get("generated_tests")
    tests_changed = interpreted_tests != initial_tests
    final_report["generated_tests"] = copy.deepcopy(initial_tests)
    metadata = dict(final_report.get("metadata") or {})
    metadata["in_turn_interpretation"] = True
    metadata["generated_tests_preserved"] = True
    final_report["metadata"] = metadata

    warning = ""
    if tests_changed:
        warning = (
            "Test Expert changed generated_tests during in-turn interpretation; the harness "
            "restored the initial test batch and requires any test revision in a new scheduler turn."
        )
        final_report["passed"] = False
        warnings = list(final_report.get("warnings") or [])
        if warning not in warnings:
            warnings.append(warning)
        final_report["warnings"] = warnings
    return final_report, tests_changed, warning


def _rebind_tool_results_to_test_report_version(
    state: DynamicMethodState,
    tool_result_indexes: list[int],
    test_report_version: int,
) -> None:
    for index in tool_result_indexes:
        if not (0 <= index < len(state.tool_results)):
            continue
        record = state.tool_results[index]
        versions = record.get("artifact_versions")
        if not isinstance(versions, dict):
            versions = {}
            record["artifact_versions"] = versions
        versions["test_report"] = test_report_version


def _mark_test_report_unverified(state: DynamicMethodState, warning: str) -> None:
    record = state.artifacts.get("test_report")
    if record is None or not isinstance(record.payload, dict):
        return
    payload = copy.deepcopy(record.payload)
    payload["passed"] = False
    warnings = list(payload.get("warnings") or [])
    if warning not in warnings:
        warnings.append(warning)
    payload["warnings"] = warnings
    record.payload = payload
    record.status = "needs_revision"
    if warning not in state.warnings:
        state.warnings.append(warning)


def _mark_test_report_interpretation_unavailable(
    state: DynamicMethodState,
    warning: str,
) -> None:
    record = state.artifacts.get("test_report")
    if record is None or not isinstance(record.payload, dict):
        return
    payload = copy.deepcopy(record.payload)
    payload["passed"] = None
    metadata = dict(payload.get("metadata") or {})
    metadata["tool_interpretation_status"] = "unavailable"
    payload["metadata"] = metadata
    warnings = list(payload.get("warnings") or [])
    if warning not in warnings:
        warnings.append(warning)
    payload["warnings"] = warnings
    record.payload = payload
    if warning not in state.warnings:
        state.warnings.append(warning)


def _merge_test_report_output(previous: Any, output: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(previous, dict):
        return dict(output)
    merged = dict(output)
    previous_tests = previous.get("generated_tests")
    current_tests = output.get("generated_tests")
    if (
        isinstance(previous_tests, list)
        and previous_tests
        and (not isinstance(current_tests, list) or not current_tests)
    ):
        merged["generated_tests"] = previous_tests
        metadata = dict(merged.get("metadata") or {})
        metadata["preserved_generated_tests_from_previous_version"] = True
        metadata["preserved_generated_test_count"] = len(previous_tests)
        merged["metadata"] = metadata
    return merged


def _build_verification_summary(state: DynamicMethodState) -> dict[str, Any]:
    facts = _collect_evaluation_facts(state)
    ddl_runs = _tool_results_by_type(state, "ddl_executor")
    sql_runs = _tool_results_by_type(state, "sql_test_runner")
    query_plan_runs = _tool_results_by_type(state, "query_plan_tool")
    latest_ddl = _latest_result(ddl_runs)
    latest_sql = _latest_result(sql_runs)
    latest_query_plan = _latest_result(query_plan_runs)
    normalization_evidence = (
        current_third_normal_form_evidence(state)
        if state.method_definition.normalization_validation_required
        else None
    )
    normalization_result = (
        normalization_evidence[1].get("result")
        if normalization_evidence and isinstance(normalization_evidence[1], dict)
        else None
    )
    warnings: list[str] = []

    if state.method_definition.runtime_verification_required:
        if not ddl_runs and not facts["ddl_verified_by_sql_tests"]:
            warnings.append("no ddl_executor result recorded")
        if not sql_runs:
            warnings.append("no sql_test_runner result recorded")
        elif facts["sql_test_total"] <= 0:
            warnings.append("latest sql_test_runner result has no tests")
        if not query_plan_runs:
            warnings.append("no query_plan_tool result recorded")
        if facts["query_plan_required"] and not facts["query_plan_has_raw_evidence"]:
            warnings.append("query_plan_tool raw evidence required but not recorded")
    if facts["normalization_required"] and not facts["normalization_current_evidence"]:
        warnings.append("third_normal_form_validator result missing for current logical model")
    elif facts["normalization_required"] and facts["normalization_passed"] is False:
        warnings.append("third_normal_form_validator failed for current logical model")

    return {
        "verification_mode": state.method_definition.verification_mode,
        "runtime_verification_required": state.method_definition.runtime_verification_required,
        "limitations": (
            []
            if state.method_definition.runtime_verification_required
            else ["DDL executability was not verified by real DBMS execution."]
        ),
        "ddl_present": facts["ddl_present"],
        "docker_runtime_observed": facts["docker_runtime_observed"],
        "ddl_executor": {
            "run_count": len(ddl_runs),
            "latest_success": facts["ddl_executor_success"],
            "latest_real_execution": facts["ddl_executor_real_execution"],
            "latest_executor": (latest_ddl or {}).get("executor", ""),
            "latest_runtime_version": (latest_ddl or {}).get("runtime_version", ""),
        },
        "sql_test_runner": {
            "run_count": len(sql_runs),
            "latest_passed": facts["sql_test_tool_passed"],
            "latest_test_count": facts["sql_test_total"],
            "latest_passed_count": facts["sql_test_passed"],
            "latest_failed_count": facts["sql_test_failed"],
            "latest_real_execution": facts["sql_test_real_execution"],
            "latest_executor": (latest_sql or {}).get("executor", ""),
            "latest_runtime_version": (latest_sql or {}).get("runtime_version", ""),
        },
        "query_plan_tool": {
            "run_count": len(query_plan_runs),
            "latest_mode": (latest_query_plan or {}).get("mode", ""),
            "latest_observation_count": facts["query_plan_observation_count"],
            "latest_executed_count": facts["query_plan_executed_count"],
            "required": facts["query_plan_required"],
            "has_raw_evidence": facts["query_plan_has_raw_evidence"],
            "latest_executor": (latest_query_plan or {}).get("executor", ""),
            "latest_runtime_version": (latest_query_plan or {}).get("runtime_version", ""),
        },
        "third_normal_form_validator": {
            "required": facts["normalization_required"],
            "current_evidence": facts["normalization_current_evidence"],
            "passed": facts["normalization_passed"],
            "disabled_reason": facts["normalization_disabled_reason"],
            "logical_model_version": facts["logical_model_version"],
            "violation_count": _int_from_keys(normalization_result or {}, "violation_count"),
            "tool_result_ref": normalization_evidence[0] if normalization_evidence else "",
        },
        "ready_evidence": facts["ready_evidence"],
        "warnings": warnings,
    }


def _build_evaluation_metrics(state: DynamicMethodState) -> dict[str, Any]:
    facts = _collect_evaluation_facts(state)
    executed_tests = facts["sql_test_total"] if facts["sql_test_real_execution"] else 0
    passed_tests = facts["sql_test_passed"] if facts["sql_test_real_execution"] else 0
    failed_tests = facts["sql_test_failed"] if facts["sql_test_real_execution"] else 0
    pass_rate = (passed_tests / executed_tests) if executed_tests > 0 else None
    return {
        "ddl": {
            "present": facts["ddl_present"],
            "length": facts["ddl_length"],
            "executable": facts["ddl_executable"],
            "execution_evidence": facts["ddl_execution_evidence"],
            "real_execution": facts["ddl_real_execution"],
        },
        "tests": {
            "generated": facts["generated_test_count"],
            "executed": executed_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": pass_rate,
            "real_execution": facts["sql_test_real_execution"],
        },
        "query_plan": {
            "required": facts["query_plan_required"],
            "executed": facts["query_plan_executed_count"],
            "failed": facts["query_plan_error_count"],
            "has_raw_evidence": facts["query_plan_has_raw_evidence"],
        },
        "normalization": {
            "required": facts["normalization_required"],
            "current_evidence": facts["normalization_current_evidence"],
            "passed": facts["normalization_passed"],
            "logical_model_version": facts["logical_model_version"],
            "disabled_reason": facts["normalization_disabled_reason"],
        },
        "final_state": {
            "ready_evidence": facts["ready_evidence"],
            "verification_mode": state.method_definition.verification_mode,
            "runtime_verification_required": state.method_definition.runtime_verification_required,
            "pending_tool_requests": facts["pending_tool_request_count"],
            "pending_sql_test_requests": facts["pending_sql_test_request_count"],
            "stale_artifacts": facts["stale_artifacts"],
            "status_blockers": facts["status_blockers"],
        },
    }


def _collect_evaluation_facts(state: DynamicMethodState) -> dict[str, Any]:
    ddl = str(state.artifact_payload("ddl", "") or state.final_ddl or "")
    test_report_record = state.artifacts.get("test_report")
    test_report_produced = bool(
        test_report_record is not None and test_report_record.version > 0
    )
    test_report = state.artifact_payload("test_report", {}) or {}
    generated_tests = test_report.get("generated_tests") if isinstance(test_report, dict) else []
    execution_feedback = test_report.get("execution_feedback") if isinstance(test_report, dict) else []
    generated_test_count = len(generated_tests) if isinstance(generated_tests, list) else 0
    execution_feedback_count = len(execution_feedback) if isinstance(execution_feedback, list) else 0
    test_report_passed = test_report.get("passed") if isinstance(test_report, dict) else None
    test_interpretation_completed = any(
        turn.speaker == "test_expert" and turn.kind == "tool_interpretation"
        for turn in state.turns
    )

    if state.method_definition.orchestration_mode == "fixed_pipeline":
        current_runtime_records = _current_runtime_tool_records(state)
        ddl_runs = [
            item
            for item in current_runtime_records
            if isinstance(item.get("request"), dict)
            and item["request"].get("tool_type") == "ddl_executor"
        ]
        sql_runs = [
            item
            for item in current_runtime_records
            if isinstance(item.get("request"), dict)
            and item["request"].get("tool_type") == "sql_test_runner"
        ]
        query_plan_runs = [
            item
            for item in current_runtime_records
            if isinstance(item.get("request"), dict)
            and item["request"].get("tool_type") == "query_plan_tool"
        ]
    else:
        ddl_runs = _tool_results_by_type(state, "ddl_executor")
        sql_runs = _tool_results_by_type(state, "sql_test_runner")
        query_plan_runs = _tool_results_by_type(state, "query_plan_tool")
    latest_ddl = _latest_result(ddl_runs)
    latest_sql = _latest_result(sql_runs)
    latest_query_plan = _latest_result(query_plan_runs)

    sql_test_total = _int_from_keys(latest_sql or {}, "sql_test_count", "test_count")
    sql_test_passed, sql_test_failed, sql_counts_complete = _sql_test_pass_fail_counts(
        latest_sql,
        sql_test_total,
    )
    query_plan_observations = (latest_query_plan or {}).get("observations")
    if not isinstance(query_plan_observations, list):
        query_plan_observations = []
    query_plan_executed = sum(
        1
        for item in query_plan_observations
        if isinstance(item, dict) and item.get("status") == "executed"
    )
    query_plan_errors = sum(
        1
        for item in query_plan_observations
        if isinstance(item, dict) and item.get("status") == "execution_error"
    )
    if state.method_definition.orchestration_mode == "fixed_pipeline":
        query_plan_required = bool(query_plan_runs)
    else:
        query_plan_required = _query_plan_required_for_readiness(
            state,
            generated_tests,
            sql_real=bool((latest_sql or {}).get("real_execution")),
            sql_passed=bool((latest_sql or {}).get("passed")),
            sql_test_count=sql_test_total,
        )
    query_plan_has_raw_evidence = query_plan_executed > 0
    ddl_executor_success = latest_ddl.get("success") if isinstance(latest_ddl, dict) else None
    ddl_executor_real_execution = bool(latest_ddl.get("real_execution")) if isinstance(latest_ddl, dict) else False
    sql_tool_passed = latest_sql.get("passed") if isinstance(latest_sql, dict) else None
    sql_test_real_execution = bool(latest_sql.get("real_execution")) if isinstance(latest_sql, dict) else False
    docker_runtime_observed = any(
        _looks_like_real_docker_result(item.get("result") if isinstance(item, dict) else {})
        for item in state.tool_results
    )
    pending_tool_request_count = _pending_tool_request_count(state)
    pending_sql_test_request_count = _pending_tool_request_count(state, {"sql_test_runner"})
    logical_record = state.artifacts.get("logical_model")
    logical_model_version = int(logical_record.version if logical_record is not None else 0)
    normalization_evidence = (
        current_third_normal_form_evidence(state)
        if state.method_definition.normalization_validation_required
        else None
    )
    normalization_result = (
        normalization_evidence[1].get("result")
        if normalization_evidence and isinstance(normalization_evidence[1], dict)
        else None
    )
    if not isinstance(normalization_result, dict):
        normalization_result = None
    normalization_required = bool(
        state.method_definition.normalization_validation_required
        and logical_model_version > 0
    )
    normalization_current_evidence = normalization_result is not None
    normalization_passed = (
        bool(normalization_result.get("passed"))
        if normalization_result is not None
        else None
    )
    normalization_disabled_reason = (
        "disabled because third-normal-form validation belongs to the ablated scheduler"
        if not state.method_definition.normalization_validation_required
        else ""
    )
    ddl_verified_by_executor = bool(ddl_executor_success) and ddl_executor_real_execution
    ddl_verified_by_sql_tests = sql_test_real_execution and sql_test_total > 0
    if ddl_verified_by_executor:
        ddl_execution_evidence = "ddl_executor"
    elif ddl_verified_by_sql_tests:
        ddl_execution_evidence = "sql_test_runner"
    else:
        ddl_execution_evidence = "none"
    ddl_executable = ddl_verified_by_executor or ddl_verified_by_sql_tests
    ddl_real_execution = ddl_executable
    if state.method_definition.runtime_verification_required:
        ready_evidence = bool(
            ddl.strip()
            and (ddl_verified_by_executor or ddl_verified_by_sql_tests)
            and test_report_produced
            and generated_test_count > 0
            and sql_test_real_execution
            and sql_tool_passed is True
            and sql_test_total > 0
        )
        if state.method_definition.orchestration_mode == "fixed_pipeline":
            active_artifacts = tuple(
                dict.fromkeys(state.method_definition.artifact_by_role.values())
            )
            ready_evidence = bool(
                ready_evidence
                and test_report_passed is not False
                and (
                    state.method_definition.cross_expert_feedback_repair_enabled
                    or test_interpretation_completed
                )
                and (not query_plan_required or query_plan_has_raw_evidence)
                and all(
                    key in state.artifacts
                    and state.artifacts[key].version > 0
                    and state.artifacts[key].status == "validated"
                    and not state.artifacts[key].stale
                    for key in (*active_artifacts, "ddl")
                )
            )
    else:
        ready_evidence = bool(design_only_completion_status(state)["ready"])
    stale_artifacts = [
        key for key, record in state.artifacts.items() if record.stale and record.version > 0
    ]
    if state.method_definition.runtime_verification_required:
        status_blockers = _sample_status_blockers(
            ddl_present=bool(ddl.strip()),
            ddl_executable=ddl_executable,
            test_report_produced=test_report_produced,
            generated_test_count=generated_test_count,
            sql_runs=bool(sql_runs),
            sql_test_real_execution=sql_test_real_execution,
            sql_test_total=sql_test_total,
            sql_tool_passed=sql_tool_passed if isinstance(sql_tool_passed, bool) else None,
            query_plan_required=query_plan_required,
            query_plan_has_raw_evidence=query_plan_has_raw_evidence,
            pending_sql_test_request_count=pending_sql_test_request_count,
            stale_artifacts=stale_artifacts,
            normalization_required=normalization_required,
            normalization_current_evidence=normalization_current_evidence,
            normalization_passed=normalization_passed,
        )
    else:
        status_blockers = list(design_only_completion_status(state)["blockers"])
    if state.current_phase == "failed" and "sample_failed" not in status_blockers:
        status_blockers.append("sample_failed")

    return {
        "ddl_present": bool(ddl.strip()),
        "ddl_length": len(ddl),
        "ddl_execution_attempted": bool(ddl_runs),
        "ddl_executor_run_count": len(ddl_runs),
        "ddl_executable": ddl_executable,
        "ddl_real_execution": ddl_real_execution,
        "ddl_execution_evidence": ddl_execution_evidence,
        "ddl_executor_success": ddl_executor_success,
        "ddl_executor_real_execution": ddl_executor_real_execution,
        "ddl_verified_by_sql_tests": ddl_verified_by_sql_tests,
        "ddl_executor": (latest_ddl or {}).get("executor", ""),
        "ddl_runtime_version": (latest_ddl or {}).get("runtime_version", ""),
        "test_report_produced": test_report_produced,
        "generated_test_count": generated_test_count,
        "test_report_passed": test_report_passed if isinstance(test_report_passed, bool) else None,
        "test_interpretation_completed": test_interpretation_completed,
        "test_report_execution_feedback_count": execution_feedback_count,
        "sql_tests_attempted": bool(sql_runs),
        "sql_test_runner_run_count": len(sql_runs),
        "sql_test_total": sql_test_total,
        "sql_test_passed": sql_test_passed,
        "sql_test_failed": sql_test_failed,
        "sql_test_counts_complete": sql_counts_complete,
        "sql_test_tool_passed": sql_tool_passed if isinstance(sql_tool_passed, bool) else None,
        "sql_test_real_execution": sql_test_real_execution,
        "sql_test_executor": (latest_sql or {}).get("executor", ""),
        "sql_test_runtime_version": (latest_sql or {}).get("runtime_version", ""),
        "query_plan_attempted": bool(query_plan_runs),
        "query_plan_observation_count": len(query_plan_observations),
        "query_plan_executed_count": query_plan_executed,
        "query_plan_error_count": query_plan_errors,
        "query_plan_required": query_plan_required,
        "query_plan_has_raw_evidence": query_plan_has_raw_evidence,
        "docker_runtime_observed": docker_runtime_observed,
        "pending_tool_request_count": pending_tool_request_count,
        "pending_sql_test_request_count": pending_sql_test_request_count,
        "ready_evidence": ready_evidence,
        "logical_model_version": logical_model_version,
        "normalization_required": normalization_required,
        "normalization_current_evidence": normalization_current_evidence,
        "normalization_passed": normalization_passed,
        "normalization_disabled_reason": normalization_disabled_reason,
        "stale_artifacts": stale_artifacts,
        "status_blockers": status_blockers,
    }


def _tool_results_by_type(state: DynamicMethodState, tool_type: str) -> list[dict[str, Any]]:
    return [
        item
        for item in state.tool_results
        if isinstance(item, dict)
        and isinstance(item.get("request"), dict)
        and item["request"].get("tool_type") == tool_type
        and isinstance(item.get("result"), dict)
    ]


def _latest_result(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    result = items[-1].get("result")
    return result if isinstance(result, dict) else None


def _pending_tool_request_count(
    state: DynamicMethodState,
    tool_types: set[str] | None = None,
) -> int:
    count = 0
    for item in state.tool_request_proposals:
        if not isinstance(item, dict) or item.get("status") != "pending":
            continue
        if tool_types is not None and item.get("tool_type") not in tool_types:
            continue
        count += 1
    return count


def _sample_status_blockers(
    *,
    ddl_present: bool,
    ddl_executable: bool,
    test_report_produced: bool,
    generated_test_count: int,
    sql_runs: bool,
    sql_test_real_execution: bool,
    sql_test_total: int,
    sql_tool_passed: bool | None,
    query_plan_required: bool,
    query_plan_has_raw_evidence: bool,
    pending_sql_test_request_count: int,
    stale_artifacts: list[str],
    normalization_required: bool,
    normalization_current_evidence: bool,
    normalization_passed: bool | None,
) -> list[str]:
    blockers: list[str] = []
    if not ddl_present:
        blockers.append("ddl_missing")
    elif not ddl_executable:
        blockers.append("ddl_not_executed")
    if not test_report_produced:
        blockers.append("test_report_missing")
    elif generated_test_count <= 0:
        blockers.append("generated_tests_missing")
    if generated_test_count > 0 and (
        not sql_runs or not sql_test_real_execution or sql_test_total <= 0
    ):
        blockers.append("tests_not_executed")
    if sql_tool_passed is False:
        blockers.append("tests_failed")
    if query_plan_required and not query_plan_has_raw_evidence:
        blockers.append("query_plan_missing")
    if pending_sql_test_request_count > 0:
        blockers.append("pending_sql_test_request")
    if "test_report" in stale_artifacts:
        blockers.append("stale_test_report")
    elif stale_artifacts:
        blockers.append("stale_artifacts")
    if normalization_required and not normalization_current_evidence:
        blockers.append("normalization_validation_missing")
    elif normalization_required and normalization_passed is False:
        blockers.append("normalization_validation_failed")
    return blockers


def _matching_query_plan_evidence_for_current_versions(
    state: DynamicMethodState,
) -> tuple[str, dict[str, Any]] | None:
    current_versions = state.artifact_versions()
    keys = ("ddl", "test_report", "physical_plan")
    for index in range(len(state.tool_results), 0, -1):
        item = state.tool_results[index - 1]
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        result = item.get("result")
        if not isinstance(request, dict) or request.get("tool_type") != "query_plan_tool":
            continue
        if not _query_plan_has_executed_observation(result):
            continue
        artifact_versions = item.get("artifact_versions")
        if not isinstance(artifact_versions, dict):
            continue
        if all(
            int(artifact_versions.get(key, 0) or 0) == int(current_versions.get(key, 0) or 0)
            for key in keys
        ):
            return f"tool_result_{index}", item
    return None


def _query_plan_has_executed_observation(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    observations = result.get("observations")
    if not isinstance(observations, list):
        return False
    return any(isinstance(item, dict) and item.get("status") == "executed" for item in observations)


def _int_from_keys(data: dict[str, Any], *keys: str) -> int:
    for key in keys:
        try:
            value = int(data.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    return 0


def _query_plan_required_for_readiness(
    state: DynamicMethodState,
    generated_tests: Any,
    *,
    sql_real: bool,
    sql_passed: bool,
    sql_test_count: int,
) -> bool:
    return (
        sql_real
        and sql_passed
        and sql_test_count > 0
        and _has_physical_access_paths(state.artifact_payload("physical_plan", {}) or {})
        and _has_workload_or_query_tests(generated_tests)
    )


def _has_physical_access_paths(physical_plan: Any) -> bool:
    if not isinstance(physical_plan, dict):
        return False
    plan = physical_plan.get("physical_plan")
    if not isinstance(plan, dict):
        plan = physical_plan
    indexes = plan.get("indexes")
    return isinstance(indexes, list) and any(isinstance(item, dict) for item in indexes)


def _has_workload_or_query_tests(generated_tests: Any) -> bool:
    if not isinstance(generated_tests, list):
        return False
    for test in generated_tests:
        if not isinstance(test, dict):
            continue
        kind = str(test.get("kind") or test.get("type") or "").strip().lower()
        if "workload" in kind or "query_plan" in kind:
            return True
        if any(key in test for key in ("expected_index", "require_index", "expect_index", "index_name")):
            return True
        if any(test.get(key) for key in ("explain_sql", "explain_query", "workload_sql")):
            return True
    return False


def _sql_test_pass_fail_counts(
    result: dict[str, Any] | None,
    total: int,
) -> tuple[int, int, bool]:
    if not isinstance(result, dict):
        return 0, 0, True
    details = result.get("details")
    if isinstance(details, list):
        passed = sum(
            1
            for item in details
            if isinstance(item, dict) and bool(item.get("passed"))
        )
        failed = sum(
            1
            for item in details
            if isinstance(item, dict) and not bool(item.get("passed"))
        )
        return passed, failed, True
    if bool(result.get("passed")) and total > 0:
        return total, 0, True
    if total <= 0:
        return 0, 0, True
    return 0, total, False


def _record_llm_json_parse_error(
    state: DynamicMethodState,
    error: LLMJSONParseError,
    *,
    speaker: str,
    action: SchedulerAction | None = None,
) -> None:
    stage = str(error.stage or speaker or "llm_output")
    message = f"recoverable LLM JSON parse error at {stage}: {error}"
    state.warnings.append(message)
    raw_text = str(error.raw_text or "")
    state.add_turn(
        speaker,
        "llm_output_error",
        status="rejected",
        action=action,
        output={
            "error_type": type(error).__name__,
            "stage": stage,
            "message": str(error),
            "raw_output_excerpt": raw_text[:4000],
            "raw_output_chars": len(raw_text),
            "retry_guidance": (
                "The previous LLM response was not valid JSON. Inspect this "
                "turn if needed, then retry with a strict JSON-only response "
                "that matches the expected contract."
            ),
        },
        warnings=[message],
        errors=[message],
    )


def _format_llm_attempt_error_for_terminal(
    error: LLMRequestError,
    *,
    speaker: str,
    record: dict[str, Any],
    total_attempts: int,
) -> str:
    stage = str(error.stage or speaker or "llm_request")
    status = f"HTTP {error.status_code}" if error.status_code is not None else "transport"
    attempt = int(record.get("attempt") or error.attempts or 0)
    next_backoff = record.get("next_backoff_seconds")
    header = (
        f"llm_attempt_error speaker={speaker} stage={stage} "
        f"attempt={attempt}/{total_attempts} status={status} "
        f"transient={record.get('transient')}"
    )
    if next_backoff is not None:
        header = f"{header} next_retry_seconds={next_backoff}"
    lines = [header, f"message: {error}"]
    request_metadata = dict(getattr(error, "request_metadata", {}) or {})
    request_summary = {
        key: request_metadata.get(key)
        for key in (
            "request_url",
            "model",
            "timeout_seconds",
            "stream",
            "message_count",
            "message_chars",
        )
        if key in request_metadata
    }
    if request_summary:
        lines.append("request_metadata:")
        lines.append(_json_for_terminal(request_summary))
    response_headers = record.get("response_headers")
    if response_headers:
        lines.append("response_headers:")
        lines.append(_json_for_terminal(response_headers))
    detail = str(record.get("detail") or "")
    if detail:
        lines.append(f"detail ({len(detail)} chars):")
        lines.append(detail)
    return "\n".join(lines)


def _format_llm_request_error_for_terminal(error: LLMRequestError, *, speaker: str) -> str:
    stage = str(error.stage or speaker or "llm_request")
    status = f"HTTP {error.status_code}" if error.status_code is not None else "transport"
    lines = [
        f"llm_request_error speaker={speaker} stage={stage} attempts={error.attempts or 0} status={status}",
        f"message: {error}",
    ]
    request_metadata = dict(getattr(error, "request_metadata", {}) or {})
    if request_metadata:
        lines.append("request_metadata:")
        lines.append(_json_for_terminal(request_metadata))
    attempt_errors = list(getattr(error, "attempt_errors", []) or [])
    if getattr(error, "attempt_errors_reported", False):
        lines.append("attempt_errors: already emitted during retries")
    elif attempt_errors:
        lines.append("attempt_errors:")
        for item in attempt_errors:
            lines.append(
                "attempt "
                f"{item.get('attempt')}: kind={item.get('kind') or ''} "
                f"status_code={item.get('status_code')} transient={item.get('transient')}"
            )
            response_headers = item.get("response_headers")
            if response_headers:
                lines.append("response_headers:")
                lines.append(_json_for_terminal(response_headers))
            detail = str(item.get("detail") or "")
            if detail:
                lines.append(f"detail ({len(detail)} chars):")
                lines.append(detail)
    else:
        detail = str(error.detail or "")
        if detail:
            lines.append(f"detail ({len(detail)} chars):")
            lines.append(detail)
    return "\n".join(lines)


def _json_for_terminal(value: Any) -> str:
    try:
        import json

        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


def _record_llm_request_error(
    state: DynamicMethodState,
    error: LLMRequestError,
    *,
    speaker: str,
    action: SchedulerAction | None = None,
) -> None:
    stage = str(error.stage or speaker or "llm_request")
    status = f"HTTP {error.status_code}" if error.status_code is not None else "transport"
    message = f"LLM request failed at {stage} after {error.attempts or 0} attempt(s): {status}"
    if str(error):
        message = f"{message}: {error}"
    state.current_phase = "failed"
    state.errors.append(message)
    state.add_turn(
        speaker,
        "llm_request_error",
        status="failed",
        action=action,
        output={
            "error_type": type(error).__name__,
            "stage": stage,
            "attempts": error.attempts,
            "status_code": error.status_code,
            "transient": error.transient,
            "message": str(error),
            "detail_excerpt": str(error.detail or "")[:4000],
            "detail_chars": len(str(error.detail or "")),
            "stop_reason": (
                "The LLM request failed after retrying this same stage. "
                "The sample is stopped so the existing intermediate state is preserved."
            ),
        },
        errors=[message],
    )


def _record_recoverable_llm_request_error(
    state: DynamicMethodState,
    error: LLMRequestError,
    *,
    speaker: str,
    action: SchedulerAction | None = None,
    stage: str = "",
) -> None:
    error_stage = str(stage or error.stage or speaker or "llm_request")
    status = f"HTTP {error.status_code}" if error.status_code is not None else "transport"
    message = (
        f"recoverable LLM request failure at {error_stage} after "
        f"{error.attempts or 0} attempt(s): {status}"
    )
    if str(error):
        message = f"{message}: {error}"
    state.warnings.append(message)
    state.add_turn(
        speaker,
        "llm_request_error",
        status="rejected",
        action=action,
        output={
            "error_type": type(error).__name__,
            "stage": error_stage,
            "attempts": error.attempts,
            "status_code": error.status_code,
            "transient": error.transient,
            "message": str(error),
            "detail_excerpt": str(error.detail or "")[:4000],
            "detail_chars": len(str(error.detail or "")),
            "recoverable": True,
            "retry_guidance": (
                "The initial Test Expert report and tool evidence were preserved. "
                "A scheduler-enabled method may invoke Test Expert again; a terminal "
                "fixed pipeline records the sample as unverified instead."
            ),
        },
        warnings=[message],
        errors=[message],
    )


def _record_unhandled_exception(state: DynamicMethodState, error: Exception) -> None:
    message = f"unhandled_exception: {type(error).__name__}: {error}"
    state.current_phase = "failed"
    state.errors.append(message)
    state.add_turn(
        "harness",
        "unhandled_exception",
        status="failed",
        output={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "stop_reason": (
                "The sample stopped because the harness raised an unexpected "
                "exception. Existing intermediate state is preserved."
            ),
        },
        errors=[message],
    )


def _record_scheduler_action_rejection(state: DynamicMethodState, decision: Any) -> None:
    errors = [str(item) for item in decision.validation_errors if str(item)]
    state.warnings.extend(f"scheduler action rejected: {error}" for error in errors)
    state.add_turn(
        "scheduler",
        "invalid_action",
        status="rejected",
        output={
            "raw_action": decision.raw_output,
            "validation_errors": errors,
            "message": (
                "The scheduler action did not match the harness contract. "
                "Inspect this turn and issue a corrected action on the next turn."
            ),
        },
        action={
            "context_selection": decision.decision_context_selection.to_dict(),
            "decision_context": decision.decision_context.to_dict(),
        },
        errors=errors,
    )


def _record_pipeline_action_rejection(
    state: DynamicMethodState,
    action: SchedulerAction,
    validation_errors: list[str],
) -> None:
    errors = [str(item) for item in validation_errors if str(item)]
    state.warnings.extend(f"scheduler action rejected: {error}" for error in errors)
    state.add_turn(
        "scheduler",
        "invalid_action",
        status="rejected",
        action=action,
        output={
            "raw_action": action.to_dict(),
            "validation_errors": errors,
            "message": (
                "The scheduler action is not permitted by the active method variant. "
                "Issue a corrected action using only active roles and allowed context."
            ),
        },
        errors=errors,
    )


def _record_scheduler_rejection_limit(
    state: DynamicMethodState,
    consecutive_rejections: int,
) -> None:
    message = (
        "scheduler stopped after "
        f"{consecutive_rejections} consecutive rejected or malformed decisions; "
        "these attempts did not consume scheduler_steps"
    )
    state.warnings.append(message)
    state.add_turn(
        "harness",
        "scheduler_rejection_limit",
        status="needs_review",
        output={
            "consecutive_rejections": consecutive_rejections,
            "scheduler_steps_consumed": 0,
            "message": message,
        },
        warnings=[message],
    )


def _normalization_gate_blocker(
    state: DynamicMethodState,
    action: SchedulerAction,
) -> str:
    if action.action_type == "invoke_expert" and action.target_role not in {
        "physical_design_specialist",
        "dialect_compiler",
        "test_expert",
    }:
        return ""
    if action.action_type not in {"invoke_expert", "finalize"}:
        return ""
    logical_record = state.artifacts.get("logical_model")
    if logical_record is None or logical_record.version <= 0:
        return ""
    evidence = current_third_normal_form_evidence(state)
    if evidence is None:
        return "normalization_validation_missing"
    result = evidence[1].get("result")
    if not isinstance(result, dict) or not result.get("passed"):
        return "normalization_validation_failed"
    return ""


def _test_evidence_gate_blocker(
    state: DynamicMethodState,
    action: SchedulerAction,
) -> str:
    if action.action_type != "finalize":
        return ""
    if not state.method_definition.runtime_verification_required:
        blockers = design_only_completion_status(state)["blockers"]
        return str(blockers[0]) if blockers else ""
    readiness = build_state_catalog(state).get("readiness")
    if not isinstance(readiness, dict):
        return "test_readiness_missing"
    blockers = readiness.get("finalize_blockers")
    if not isinstance(blockers, list):
        return "test_readiness_missing"
    mandatory_test_blockers = (
        "test_report_missing",
        "generated_tests_missing",
        "stale_test_report",
        "test_report_not_passed",
        "generated_tests_without_real_sql_runner",
        "latest_sql_test_runner_failed",
        "pending_sql_test_runner_proposal",
        "query_plan_without_raw_evidence",
    )
    return next((blocker for blocker in mandatory_test_blockers if blocker in blockers), "")


def _apply_normalization_result(
    state: DynamicMethodState,
    result: dict[str, Any],
) -> None:
    logical_record = state.artifacts.get("logical_model")
    if logical_record is None or logical_record.version <= 0:
        return
    structural_validation = (
        logical_record.validation
        if isinstance(logical_record.validation, dict)
        else {}
    )
    if bool(result.get("passed")) and structural_validation.get("passed") is not False:
        state.update_artifact_status("logical_model", "validated")
    else:
        state.update_artifact_status("logical_model", "needs_revision")


def _ddl_compiler_gate_blocker(
    state: DynamicMethodState,
    action: SchedulerAction,
) -> str:
    if action.action_type != "invoke_expert" or action.target_role != "dialect_compiler":
        return ""
    if not state.method_definition.runtime_verification_required:
        return ""
    ddl_record = state.artifacts.get("ddl")
    if ddl_record is None or ddl_record.version <= 0 or ddl_record.stale:
        return ""
    if _matching_ddl_executor_evidence_for_current_version(state) is not None:
        return ""
    return "current_ddl_execution_missing"


def _matching_ddl_executor_evidence_for_current_version(
    state: DynamicMethodState,
) -> tuple[str, dict[str, Any]] | None:
    ddl_record = state.artifacts.get("ddl")
    ddl_version = int(ddl_record.version if ddl_record is not None else 0)
    if ddl_version <= 0:
        return None
    for index in range(len(state.tool_results), 0, -1):
        item = state.tool_results[index - 1]
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        if not isinstance(request, dict) or request.get("tool_type") != "ddl_executor":
            continue
        artifact_versions = item.get("artifact_versions")
        if not isinstance(artifact_versions, dict):
            continue
        if int(artifact_versions.get("ddl", 0) or 0) == ddl_version:
            return f"tool_result_{index}", item
    return None


def _record_ddl_compiler_gate_rejection(
    state: DynamicMethodState,
    action: SchedulerAction,
    blocker: str,
) -> None:
    ddl_record = state.artifacts.get("ddl")
    ddl_version = int(ddl_record.version if ddl_record is not None else 0)
    message = (
        f"scheduler action rejected: {blocker}; execute ddl_executor for current "
        f"ddl version {ddl_version} before invoking dialect_compiler again"
    )
    state.warnings.append(message)
    state.add_turn(
        "scheduler",
        "invalid_action",
        status="needs_revision",
        action=action,
        output={
            "validation_errors": [message],
            "blocker": blocker,
            "required_tool": "ddl_executor",
            "ddl_version": ddl_version,
        },
        warnings=[message],
    )


def _record_normalization_gate_rejection(
    state: DynamicMethodState,
    action: SchedulerAction,
    blocker: str,
) -> None:
    message = (
        f"scheduler action rejected: {blocker}; call {THIRD_NORMAL_FORM_TOOL} "
        "for the current logical_model version or revise logical_model before continuing"
    )
    state.warnings.append(message)
    state.add_turn(
        "scheduler",
        "invalid_action",
        status="needs_revision",
        action=action,
        output={
            "validation_errors": [message],
            "blocker": blocker,
            "required_tool": THIRD_NORMAL_FORM_TOOL,
            "logical_model_version": int(
                state.artifacts.get("logical_model").version
                if state.artifacts.get("logical_model") is not None
                else 0
            ),
        },
        warnings=[message],
    )


def _record_test_evidence_gate_rejection(
    state: DynamicMethodState,
    action: SchedulerAction,
    blocker: str,
) -> None:
    if state.method_definition.runtime_verification_required:
        message = (
            f"scheduler action rejected: {blocker}; invoke test_expert for the current "
            "DDL and obtain passing in-turn SQL/query-plan evidence before finalizing"
        )
        required_role = "test_expert"
    else:
        message = (
            f"scheduler action rejected: {blocker}; resolve all active design-artifact "
            "and normalization blockers before finalizing"
        )
        required_role = ""
    state.warnings.append(message)
    state.add_turn(
        "scheduler",
        "invalid_action",
        status="needs_revision",
        action=action,
        output={
            "validation_errors": [message],
            "blocker": blocker,
            "required_role": required_role,
        },
        warnings=[message],
    )


def _artifact_revision_snapshot(state: DynamicMethodState, artifact_key: str) -> dict[str, Any]:
    record = state.artifacts.get(artifact_key)
    if record is None:
        return {
            "version": 0,
            "status": "not_started",
            "stale": False,
            "stale_reasons": [],
            "depends_on_versions": {},
        }
    return {
        "version": int(record.version),
        "status": record.status,
        "stale": bool(record.stale),
        "stale_reasons": list(record.stale_reasons),
        "depends_on_versions": dict(record.depends_on_versions),
    }


def _record_expert_revision(
    state: DynamicMethodState,
    action: SchedulerAction,
    artifact_key: str,
    before_revision: dict[str, Any],
    *,
    turn_index: int,
) -> None:
    after_record = state.artifacts.get(artifact_key)
    if after_record is None:
        return
    from_version = int(before_revision.get("version") or 0)
    to_version = int(after_record.version)
    if from_version <= 0 or to_version <= from_version:
        return

    validation = after_record.validation if isinstance(after_record.validation, dict) else {}
    state.repair_history.append(
        {
            "repair_id": f"artifact_revision_{len(state.repair_history) + 1}",
            "event_type": "artifact_revision",
            "kind": "artifact_revision",
            "status": "recorded",
            "artifact": artifact_key,
            "repair_artifacts": [artifact_key],
            "role": action.target_role,
            "from_version": from_version,
            "to_version": to_version,
            "instruction": action.instruction,
            "target_artifact": action.target_artifact,
            "turn_index": turn_index,
            "scheduler_action": {
                "action_type": action.action_type,
                "target_role": action.target_role,
                "target_artifact": action.target_artifact,
                "instruction": action.instruction,
            },
            "before": before_revision,
            "after": {
                "status": after_record.status,
                "validation_passed": validation.get("passed"),
                "validation_errors": validation.get("errors") or [],
                "validation_warnings": validation.get("warnings") or [],
                "depends_on_versions": dict(after_record.depends_on_versions),
            },
        }
    )


def _looks_like_real_docker_result(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    executor = str(result.get("executor") or "")
    return bool(result.get("real_execution")) and "docker" in executor.lower()


def _is_truthy_output(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return bool(value)
