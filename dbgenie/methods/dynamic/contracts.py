from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EXPERT_ROLES = [
    "requirement_analyst",
    "conceptual_model_designer",
    "logical_model_designer",
    "physical_design_specialist",
    "dialect_compiler",
    "test_expert",
]

ARTIFACT_BY_ROLE = {
    "requirement_analyst": "requirement_brief",
    "conceptual_model_designer": "conceptual_model",
    "logical_model_designer": "logical_model",
    "physical_design_specialist": "physical_plan",
    "dialect_compiler": "dialect_report",
    "test_expert": "test_report",
}

ROLE_BY_ARTIFACT = {artifact: role for role, artifact in ARTIFACT_BY_ROLE.items()}
ROLE_ALIASES = {
    **ROLE_BY_ARTIFACT,
    "conceptual": "conceptual_model_designer",
    "conceptual_model": "conceptual_model_designer",
    "logical": "logical_model_designer",
    "logical_model": "logical_model_designer",
    "physical": "physical_design_specialist",
    "physical_design": "physical_design_specialist",
    "physical_plan": "physical_design_specialist",
    "dialect": "dialect_compiler",
    "dialect_report": "dialect_compiler",
    "ddl": "dialect_compiler",
    "tests": "test_expert",
    "test_report": "test_expert",
}

VALID_ACTION_TYPES = {
    "invoke_expert",
    "call_tool",
    "finalize",
    "terminate_with_warning",
}

VALID_TOOL_TYPES = {
    "artifact_validator",
    "third_normal_form_validator",
    "ddl_executor",
    "dialect_linter",
    "sql_test_runner",
    "query_plan_tool",
}

FIXED_TOOL_TARGETS = {
    "third_normal_form_validator": "logical_model",
    "ddl_executor": "ddl",
    "sql_test_runner": "test_report",
    "query_plan_tool": "test_report",
}

VALID_ARTIFACT_STATUS = {
    "not_started",
    "draft",
    "validated",
    "needs_revision",
    "blocked",
}


@dataclass(frozen=True)
class ToolRequest:
    tool_type: str
    target_artifact: str = ""
    reason: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ToolRequest | None":
        if not isinstance(data, dict):
            return None
        tool_type = str(data.get("tool_type") or data.get("type") or "")
        payload = data.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {"value": payload}
        target_artifact = str(data.get("target_artifact") or "")
        if tool_type == "third_normal_form_validator" and not target_artifact:
            target_artifact = "logical_model"
        return cls(
            tool_type=tool_type,
            target_artifact=target_artifact,
            reason=str(data.get("reason") or ""),
            payload=dict(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_type": self.tool_type,
            "target_artifact": self.target_artifact,
            "reason": self.reason,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class ToolRequestProposal:
    proposal_id: str
    proposer_role: str
    tool_type: str
    target_artifact: str = ""
    reason: str = ""
    payload_hint: dict[str, Any] = field(default_factory=dict)
    expected_interpreter: str = ""
    status: str = "pending"

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
        *,
        proposal_id: str = "",
        proposer_role: str = "",
    ) -> "ToolRequestProposal | None":
        if not isinstance(data, dict):
            return None
        payload_hint = data.get("payload_hint") or data.get("payload") or {}
        if not isinstance(payload_hint, dict):
            payload_hint = {"value": payload_hint}
        tool_type = str(data.get("tool_type") or data.get("type") or "")
        target_artifact = str(data.get("target_artifact") or "")
        if tool_type == "third_normal_form_validator" and not target_artifact:
            target_artifact = "logical_model"
        return cls(
            proposal_id=str(data.get("proposal_id") or data.get("id") or proposal_id),
            proposer_role=str(data.get("proposer_role") or proposer_role),
            tool_type=tool_type,
            target_artifact=target_artifact,
            reason=str(data.get("reason") or ""),
            payload_hint=dict(payload_hint),
            expected_interpreter=str(data.get("expected_interpreter") or ""),
            status=str(data.get("status") or "pending"),
        )

    def validate(
        self,
        expert_roles: tuple[str, ...] | list[str] | set[str] | None = None,
        tool_types: set[str] | frozenset[str] | None = None,
    ) -> list[str]:
        allowed_roles = set(EXPERT_ROLES if expert_roles is None else expert_roles)
        allowed_tools = set(VALID_TOOL_TYPES if tool_types is None else tool_types)
        errors = []
        if not self.proposal_id.strip():
            errors.append("tool_request_proposal requires proposal_id")
        if self.proposer_role not in allowed_roles:
            errors.append(f"invalid proposer_role: {self.proposer_role}")
        if self.tool_type not in allowed_tools:
            errors.append(f"invalid proposal tool_type: {self.tool_type}")
        expected_target = FIXED_TOOL_TARGETS.get(self.tool_type)
        if expected_target and self.target_artifact != expected_target:
            errors.append(
                f"{self.tool_type} requires target_artifact={expected_target}"
            )
        if self.expected_interpreter and self.expected_interpreter not in allowed_roles:
            errors.append(f"invalid expected_interpreter: {self.expected_interpreter}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposer_role": self.proposer_role,
            "tool_type": self.tool_type,
            "target_artifact": self.target_artifact,
            "reason": self.reason,
            "payload_hint": self.payload_hint,
            "expected_interpreter": self.expected_interpreter,
            "status": self.status,
        }


@dataclass(frozen=True)
class SchedulerAction:
    action_type: str
    target_role: str = ""
    instruction: str = ""
    target_artifact: str = ""
    execution_context_selection: dict[str, Any] = field(default_factory=dict)
    tool_request: ToolRequest | None = None
    explanation: str = ""
    stop_reason: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchedulerAction":
        if not isinstance(data, dict):
            raise ValueError("scheduler action must be a JSON object")
        action_type = str(data.get("action_type") or data.get("next_action") or "")
        return cls(
            action_type=action_type,
            target_role=_normalize_target_role(str(data.get("target_role") or "")),
            instruction=str(data.get("instruction") or data.get("revision_instruction") or ""),
            target_artifact=str(data.get("target_artifact") or ""),
            execution_context_selection=dict(data.get("execution_context_selection") or {}),
            tool_request=ToolRequest.from_dict(data.get("tool_request")),
            explanation=str(data.get("explanation") or data.get("final_explanation") or ""),
            stop_reason=str(data.get("stop_reason") or ""),
            warnings=_string_list(data.get("warnings")),
            metadata=dict(data.get("metadata") or {}),
        )

    def validate(
        self,
        expert_roles: tuple[str, ...] | list[str] | set[str] | None = None,
        tool_types: set[str] | frozenset[str] | None = None,
    ) -> list[str]:
        allowed_roles = set(EXPERT_ROLES if expert_roles is None else expert_roles)
        allowed_tools = set(VALID_TOOL_TYPES if tool_types is None else tool_types)
        errors = []
        if self.action_type not in VALID_ACTION_TYPES:
            errors.append(f"invalid scheduler action_type: {self.action_type}")
        if self.action_type == "invoke_expert":
            if self.target_role not in allowed_roles:
                errors.append(f"invalid target_role for expert action: {self.target_role}")
        if self.action_type == "call_tool":
            if not self.tool_request:
                errors.append("call_tool requires tool_request")
            elif self.tool_request.tool_type not in allowed_tools:
                errors.append(f"invalid tool_type: {self.tool_request.tool_type}")
            elif not self.tool_request.target_artifact and self.tool_request.tool_type == "artifact_validator":
                errors.append(f"{self.tool_request.tool_type} requires target_artifact")
            elif (
                self.tool_request.tool_type == "third_normal_form_validator"
                and self.tool_request.target_artifact
                and self.tool_request.target_artifact != "logical_model"
            ):
                errors.append("third_normal_form_validator requires target_artifact=logical_model")
        if self.action_type == "finalize" and not self.explanation.strip():
            errors.append("finalize requires non-empty explanation")
        return errors

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "action_type": self.action_type,
            "target_role": self.target_role,
            "instruction": self.instruction,
            "target_artifact": self.target_artifact,
            "execution_context_selection": self.execution_context_selection,
            "explanation": self.explanation,
            "stop_reason": self.stop_reason,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }
        if self.tool_request:
            payload["tool_request"] = self.tool_request.to_dict()
        return payload


@dataclass(frozen=True)
class FeedbackEvent:
    event_id: str
    event_type: str
    severity: str
    source: str
    evidence: Any = ""
    suspected_owner: str = ""
    affected_artifacts: list[str] = field(default_factory=list)
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "evidence": self.evidence,
            "suspected_owner": self.suspected_owner,
            "affected_artifacts": self.affected_artifacts,
            "suggested_action": self.suggested_action,
        }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _normalize_target_role(value: str) -> str:
    normalized = value.strip()
    if normalized in EXPERT_ROLES:
        return normalized
    return ROLE_ALIASES.get(normalized, normalized)
