from __future__ import annotations

from dbgenie.methods.dynamic.definition import (
    ALL_CONTEXT_SOURCES,
    DynamicMethodDefinition,
)


CONCEPTUAL_MODEL_DESIGNER_SKILL = """
# Conceptual Model Designer Skill

Role id: `conceptual_model_designer`

This is the first and only role allowed to read the raw application requirement
and workload descriptions in this ablation. Convert those raw inputs directly
into a conceptual data model. Do not create, imitate, or return a requirement
brief or a separate requirement-analysis artifact.

Responsibilities:
- Decide which concepts in the raw requirement become entities.
- Define entity boundaries, relationship cardinalities, weak entities,
  associative entities, ownership, lifecycle semantics, and conceptual
  invariants.
- Use the raw workload descriptions only as evidence for access-driven
  entities, associative concepts, relationship directions, and lifecycle
  objects.
- Record unresolved ambiguity in `design_assumptions` or `warnings`; do not
  fabricate missing business rules.
- Revise the conceptual model when test feedback identifies a conceptual
  problem.

Boundaries:
- Do not emit requirement-analysis fields or summarize the task as a brief.
- Do not design tables, columns, indexes, physical plans, or DDL.
- Do not use DBMS-specific syntax.
""".strip()


WITHOUT_REQUIREMENT_ANALYST_DEFINITION = DynamicMethodDefinition(
    name="without_requirement_analyst",
    expert_roles=(
        "conceptual_model_designer",
        "logical_model_designer",
        "physical_design_specialist",
        "dialect_compiler",
        "test_expert",
    ),
    artifact_by_role={
        "conceptual_model_designer": "conceptual_model",
        "logical_model_designer": "logical_model",
        "physical_design_specialist": "physical_plan",
        "dialect_compiler": "dialect_report",
        "test_expert": "test_report",
    },
    artifact_dependencies={
        "conceptual_model": (),
        "logical_model": ("conceptual_model",),
        "physical_plan": ("logical_model",),
        "dialect_report": ("logical_model", "physical_plan"),
        "ddl": ("logical_model", "physical_plan", "dialect_report"),
        "test_report": ("logical_model", "physical_plan", "ddl"),
        "verification_summary": ("ddl", "test_report"),
    },
    required_expert_context={
        "conceptual_model_designer": (("task", ""),),
        "logical_model_designer": (("artifact", "conceptual_model"),),
        "physical_design_specialist": (("artifact", "logical_model"),),
        "dialect_compiler": (
            ("artifact", "logical_model"),
            ("artifact", "physical_plan"),
        ),
        "test_expert": (("artifact", "ddl"),),
    },
    scheduler_context_sources=ALL_CONTEXT_SOURCES - {"task"},
    task_visible_to_expert_roles=frozenset({"conceptual_model_designer"}),
    task_metadata_visible_to_expert_roles=frozenset({"conceptual_model_designer"}),
    expert_skill_overrides={
        "conceptual_model_designer": CONCEPTUAL_MODEL_DESIGNER_SKILL,
    },
    scheduler_variant_rules=(
        "No requirement-analysis stage or intermediate requirement brief exists in this "
        "variant. Begin design by invoking conceptual_model_designer.",
        "The scheduler cannot read raw requirement or workload text. Do not ask for task "
        "context and do not reconstruct or relay raw business details in expert instructions.",
        "Only conceptual_model_designer receives the raw task. Every later expert must rely "
        "on the produced conceptual/logical/physical/DDL artifact chain.",
        "Keep requirement-level ambiguities unresolved. Route feedback to "
        "conceptual_model_designer only when it concerns entity boundaries, relationships, "
        "ownership, lifecycle semantics, or conceptual invariants.",
    ),
)
