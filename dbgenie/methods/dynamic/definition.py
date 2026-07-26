from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .contracts import ARTIFACT_BY_ROLE, EXPERT_ROLES, VALID_TOOL_TYPES


ALL_CONTEXT_SOURCES = frozenset(
    {
        "task",
        "budget",
        "readiness",
        "artifact",
        "turn",
        "failure_event",
        "tool_request_proposal",
        "tool_result",
        "repair_history",
        "open_assumptions",
        "warnings",
        "errors",
    }
)

FULL_ARTIFACT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "requirement_brief": (),
    "conceptual_model": ("requirement_brief",),
    "logical_model": ("requirement_brief", "conceptual_model"),
    "physical_plan": ("logical_model",),
    "dialect_report": ("logical_model", "physical_plan"),
    "ddl": ("logical_model", "physical_plan", "dialect_report"),
    "test_report": ("requirement_brief", "logical_model", "physical_plan", "ddl"),
    "verification_summary": ("ddl", "test_report"),
}

FULL_REQUIRED_EXPERT_CONTEXT: dict[str, tuple[tuple[str, str], ...]] = {
    "requirement_analyst": (("task", ""),),
    "conceptual_model_designer": (("artifact", "requirement_brief"),),
    "logical_model_designer": (("artifact", "conceptual_model"),),
    "physical_design_specialist": (("artifact", "logical_model"),),
    "dialect_compiler": (
        ("artifact", "logical_model"),
        ("artifact", "physical_plan"),
    ),
    "test_expert": (("artifact", "ddl"),),
}


@dataclass(frozen=True)
class DynamicMethodDefinition:
    name: str
    expert_roles: tuple[str, ...]
    artifact_by_role: Mapping[str, str]
    artifact_dependencies: Mapping[str, tuple[str, ...]]
    required_expert_context: Mapping[str, tuple[tuple[str, str], ...]]
    allowed_tool_types: frozenset[str] = frozenset(VALID_TOOL_TYPES)
    runtime_verification_required: bool = True
    orchestration_mode: str = "scheduler"
    normalization_validation_required: bool = True
    cross_expert_feedback_repair_enabled: bool = True
    fixed_expert_sequence: tuple[str, ...] = ()
    failure_routes: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    failure_category_priority: tuple[str, ...] = ()
    scheduler_context_sources: frozenset[str] = ALL_CONTEXT_SOURCES
    task_visible_to_expert_roles: frozenset[str] | None = None
    task_metadata_visible_to_expert_roles: frozenset[str] | None = None
    expert_skill_overrides: Mapping[str, str] = field(default_factory=dict)
    expert_contract_overrides: Mapping[str, str] = field(default_factory=dict)
    expert_prompt_additions: Mapping[str, str] = field(default_factory=dict)
    scheduler_variant_rules: tuple[str, ...] = ()

    @property
    def artifact_keys(self) -> tuple[str, ...]:
        keys = dict.fromkeys(
            [
                *self.artifact_dependencies.keys(),
                *self.artifact_by_role.values(),
            ]
        )
        return tuple(keys)

    def expert_context_sources(self, role: str) -> frozenset[str]:
        if self.task_visible_to_expert_roles is None or role in self.task_visible_to_expert_roles:
            return ALL_CONTEXT_SOURCES
        return ALL_CONTEXT_SOURCES - {"task"}

    def expert_sees_task_metadata(self, role: str) -> bool:
        return (
            self.task_metadata_visible_to_expert_roles is None
            or role in self.task_metadata_visible_to_expert_roles
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "method_variant": self.name,
            "active_expert_roles": list(self.expert_roles),
            "orchestration_mode": self.orchestration_mode,
            "cross_expert_feedback_repair_enabled": (
                self.cross_expert_feedback_repair_enabled
            ),
        }

    @property
    def verification_mode(self) -> str:
        return "runtime" if self.runtime_verification_required else "design_only"


FULL_METHOD_DEFINITION = DynamicMethodDefinition(
    name="full",
    expert_roles=tuple(EXPERT_ROLES),
    artifact_by_role=dict(ARTIFACT_BY_ROLE),
    artifact_dependencies=FULL_ARTIFACT_DEPENDENCIES,
    required_expert_context=FULL_REQUIRED_EXPERT_CONTEXT,
)
