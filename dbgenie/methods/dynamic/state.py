from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dbgenie.agents.types import AgentTaskInput

from .contracts import FeedbackEvent, SchedulerAction, ToolRequestProposal
from .definition import (
    FULL_ARTIFACT_DEPENDENCIES,
    FULL_METHOD_DEFINITION,
    DynamicMethodDefinition,
)


ARTIFACT_DEPENDENCIES: dict[str, tuple[str, ...]] = dict(FULL_ARTIFACT_DEPENDENCIES)


@dataclass
class ArtifactRecord:
    key: str
    status: str = "not_started"
    version: int = 0
    payload: Any = None
    producer: str = ""
    validation: dict[str, Any] = field(default_factory=dict)
    depends_on_versions: dict[str, int] = field(default_factory=dict)
    stale: bool = False
    stale_reasons: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "status": self.status,
            "version": self.version,
            "payload": self.payload,
            "producer": self.producer,
            "validation": self.validation,
            "depends_on_versions": self.depends_on_versions,
            "stale": self.stale,
            "stale_reasons": self.stale_reasons,
        }


@dataclass
class DynamicMethodTurn:
    index: int
    speaker: str
    kind: str
    status: str = "ready"
    action: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "speaker": self.speaker,
            "kind": self.kind,
            "status": self.status,
            "action": self.action,
            "output": self.output,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class DynamicMethodState:
    task: AgentTaskInput
    max_turns: int = 20
    max_repairs: int = 3
    method_definition: DynamicMethodDefinition = field(default_factory=lambda: FULL_METHOD_DEFINITION)
    scheduler_steps: int = 0
    finalize_reserve_used: bool = False
    current_phase: str = "initialized"
    artifacts: dict[str, ArtifactRecord] = field(default_factory=dict)
    turns: list[DynamicMethodTurn] = field(default_factory=list)
    open_assumptions: list[dict[str, Any]] = field(default_factory=list)
    failure_events: list[FeedbackEvent] = field(default_factory=list)
    repair_history: list[dict[str, Any]] = field(default_factory=list)
    tool_request_proposals: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    final_ddl: str = ""
    final_explanation: str = ""
    fixed_pipeline: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        missing_role_mappings = [
            role
            for role in self.method_definition.expert_roles
            if role not in self.method_definition.artifact_by_role
        ]
        if missing_role_mappings:
            raise ValueError(
                "method definition missing artifact mappings for: "
                + ", ".join(missing_role_mappings)
            )
        for key in self.method_definition.artifact_keys:
            self.artifacts.setdefault(key, ArtifactRecord(key=key))

    def add_turn(
        self,
        speaker: str,
        kind: str,
        *,
        status: str = "ready",
        action: SchedulerAction | dict[str, Any] | None = None,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> DynamicMethodTurn:
        turn = DynamicMethodTurn(
            index=len(self.turns) + 1,
            speaker=speaker,
            kind=kind,
            status=status,
            action=action.to_dict() if isinstance(action, SchedulerAction) else dict(action or {}),
            output=output,
            metadata=dict(metadata or {}),
            warnings=warnings or [],
            errors=errors or [],
        )
        self.turns.append(turn)
        return turn

    def store_role_artifact(
        self,
        role: str,
        payload: dict[str, Any],
        *,
        status: str = "draft",
        validation: dict[str, Any] | None = None,
    ) -> str:
        key = self.method_definition.artifact_by_role[role]
        record = self.artifacts.setdefault(key, ArtifactRecord(key=key))
        record.version += 1
        record.status = status
        record.payload = payload
        record.producer = role
        record.validation = validation or {}
        record.depends_on_versions = self.dependency_versions_for(key)
        record.stale = False
        record.stale_reasons = []
        self.refresh_stale_artifacts()
        if role == "dialect_compiler" and isinstance(payload.get("ddl"), str):
            self.store_artifact("ddl", payload["ddl"], producer=role, status="draft")
        return key

    def update_artifact_status(self, key: str, status: str) -> None:
        record = self.artifacts.setdefault(key, ArtifactRecord(key=key))
        record.status = status

    def store_artifact(
        self,
        key: str,
        payload: Any,
        *,
        producer: str = "",
        status: str = "draft",
        validation: dict[str, Any] | None = None,
    ) -> None:
        record = self.artifacts.setdefault(key, ArtifactRecord(key=key))
        record.version += 1
        record.status = status
        record.payload = payload
        record.producer = producer
        record.validation = validation or {}
        record.depends_on_versions = self.dependency_versions_for(key)
        record.stale = False
        record.stale_reasons = []
        self.refresh_stale_artifacts()

    def artifact_payload(self, key: str, default: Any = None) -> Any:
        record = self.artifacts.get(key)
        if record is None or record.payload is None:
            return default
        return record.payload

    def artifact_versions(self) -> dict[str, int]:
        return {key: record.version for key, record in self.artifacts.items()}

    def repair_budget_used(self) -> int:
        return sum(1 for item in self.repair_history if _counts_against_repair_budget(item))

    def normal_scheduler_steps_used(self) -> int:
        return max(0, self.scheduler_steps - int(self.finalize_reserve_used))

    def remaining_scheduler_steps(self) -> int:
        return max(0, self.max_turns - self.normal_scheduler_steps_used())

    def consume_scheduler_step(self, *, finalize_reserve: bool = False) -> None:
        if finalize_reserve:
            if self.finalize_reserve_used:
                raise RuntimeError("finalize scheduler reserve has already been used")
            if self.remaining_scheduler_steps() > 0:
                raise RuntimeError("finalize scheduler reserve is only available after normal budget exhaustion")
            self.finalize_reserve_used = True
        elif self.remaining_scheduler_steps() <= 0:
            raise RuntimeError("scheduler step budget exhausted")
        self.scheduler_steps += 1

    def dependency_versions_for(self, key: str) -> dict[str, int]:
        versions = self.artifact_versions()
        dependencies = self.method_definition.artifact_dependencies.get(key, ())
        return {dep: int(versions.get(dep, 0)) for dep in dependencies}

    def refresh_stale_artifacts(self) -> None:
        current_versions = self.artifact_versions()
        for record in self.artifacts.values():
            record.stale = False
            record.stale_reasons = []

        changed = True
        while changed:
            changed = False
            for key, record in self.artifacts.items():
                if record.version <= 0 or not record.depends_on_versions:
                    continue
                stale_reasons = []
                for dep_key, recorded_version in record.depends_on_versions.items():
                    current_version = int(current_versions.get(dep_key, 0))
                    dep_record = self.artifacts.get(dep_key)
                    if current_version != int(recorded_version):
                        stale_reasons.append(
                            {
                                "dependency": dep_key,
                                "reason": "version_mismatch",
                                "recorded_version": int(recorded_version),
                                "current_version": current_version,
                            }
                        )
                    elif dep_record is not None and dep_record.stale:
                        stale_reasons.append(
                            {
                                "dependency": dep_key,
                                "reason": "upstream_stale",
                                "recorded_version": int(recorded_version),
                                "current_version": current_version,
                            }
                        )
                if stale_reasons != record.stale_reasons:
                    record.stale = bool(stale_reasons)
                    record.stale_reasons = stale_reasons
                    changed = True

    def add_feedback(self, event: FeedbackEvent) -> None:
        self.failure_events.append(event)

    def add_tool_request_proposal(self, proposal: ToolRequestProposal | dict[str, Any]) -> None:
        payload = proposal.to_dict() if isinstance(proposal, ToolRequestProposal) else dict(proposal)
        self.tool_request_proposals.append(payload)

    def mark_tool_request_proposal(self, proposal_id: str, status: str) -> None:
        if not proposal_id:
            return
        for item in self.tool_request_proposals:
            if item.get("proposal_id") == proposal_id:
                item["status"] = status

    def to_scheduler_view(self) -> dict[str, Any]:
        if "task" in self.method_definition.scheduler_context_sources:
            task_view = self.task.to_dict()
        else:
            task_view = {
                "id": self.task.id,
                "target_dbms": self.task.target_dbms,
                "source": self.task.source,
                "requirement_chars": len(str(self.task.requirement or "")),
                "workload_count": len(self.task.workload),
                "metadata_keys": list((self.task.metadata or {}).keys())[:20],
            }
        return {
            **self.method_definition.to_metadata(),
            "task": task_view,
            "current_phase": self.current_phase,
            "budget": {
                "max_turns": self.max_turns,
                "used_turns": self.normal_scheduler_steps_used(),
                "max_scheduler_steps": self.max_turns,
                "used_scheduler_steps": self.normal_scheduler_steps_used(),
                "remaining_scheduler_steps": self.remaining_scheduler_steps(),
                "total_scheduler_decisions": self.scheduler_steps,
                "trace_event_count": len(self.turns),
                "finalize_reserve_used": self.finalize_reserve_used,
                "max_repairs": self.max_repairs,
                "used_repairs": self.repair_budget_used(),
            },
            "artifacts": {
                key: {
                    "status": record.status,
                    "version": record.version,
                    "producer": record.producer,
                    "validation": record.validation,
                    "depends_on_versions": record.depends_on_versions,
                    "stale": record.stale,
                    "stale_reasons": record.stale_reasons,
                    "summary": _summarize_payload(record.payload),
                }
                for key, record in self.artifacts.items()
            },
            "open_assumptions": self.open_assumptions,
            "failure_events": {"count": len(self.failure_events)},
            "tool_request_proposals": {"count": len(self.tool_request_proposals)},
            "tool_results": {"count": len(self.tool_results)},
            "repair_history": {"count": len(self.repair_history)},
            "warnings": {"count": len(self.warnings)},
            "errors": {"count": len(self.errors)},
            "final_ddl_ready": bool(str(self.final_ddl or "").strip()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.method_definition.to_metadata(),
            "task": self.task.to_dict(),
            "current_phase": self.current_phase,
            "budget": {
                "max_turns": self.max_turns,
                "used_turns": self.normal_scheduler_steps_used(),
                "max_scheduler_steps": self.max_turns,
                "used_scheduler_steps": self.normal_scheduler_steps_used(),
                "remaining_scheduler_steps": self.remaining_scheduler_steps(),
                "total_scheduler_decisions": self.scheduler_steps,
                "trace_event_count": len(self.turns),
                "finalize_reserve_used": self.finalize_reserve_used,
                "max_repairs": self.max_repairs,
                "used_repairs": self.repair_budget_used(),
            },
            "scheduler_steps": self.scheduler_steps,
            "trace_event_count": len(self.turns),
            "artifacts": {key: record.to_dict() for key, record in self.artifacts.items()},
            "turns": [turn.to_dict() for turn in self.turns],
            "open_assumptions": self.open_assumptions,
            "failure_events": [event.to_dict() for event in self.failure_events],
            "repair_history": self.repair_history,
            "tool_request_proposals": self.tool_request_proposals,
            "tool_results": self.tool_results,
            "warnings": self.warnings,
            "errors": self.errors,
            "final_ddl": self.final_ddl,
            "final_explanation": self.final_explanation,
            "fixed_pipeline": self.fixed_pipeline,
        }


@dataclass(frozen=True)
class DynamicMethodRunResult:
    task_id: str
    status: str
    final_ddl: str
    state: DynamicMethodState
    final_explanation: str = ""
    run_path: str = ""
    llm: dict[str, Any] = field(default_factory=dict)
    evaluation_metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            **self.state.method_definition.to_metadata(),
            "status": self.status,
            "final_ddl": self.final_ddl,
            "final_explanation": self.final_explanation,
            "evaluation_metrics": self.evaluation_metrics,
            "state": self.state.to_dict(),
            "run_path": self.run_path,
            "llm": self.llm,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _summarize_payload(payload: Any) -> Any:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload[:1200] + ("..." if len(payload) > 1200 else "")
    if isinstance(payload, dict):
        summary: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                summary[key] = value
            elif isinstance(value, list):
                summary[key] = {"count": len(value), "sample": value[:3]}
            elif isinstance(value, dict):
                summary[key] = {"keys": list(value.keys())[:12]}
            if len(summary) >= 12:
                break
        return summary
    if isinstance(payload, list):
        return {"count": len(payload), "sample": payload[:3]}
    return str(payload)[:1200]


def _counts_against_repair_budget(item: Any) -> bool:
    if not isinstance(item, dict):
        return True
    if item.get("counts_against_repair_budget") is False:
        return False
    event_type = str(item.get("event_type") or item.get("kind") or "")
    return event_type not in {
        "artifact_revision",
        "fixed_pipeline_artifact_validation_retry",
        "fixed_pipeline_json_retry",
        "fixed_pipeline_terminal",
    }
