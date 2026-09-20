from __future__ import annotations

from dbgenie.methods.dynamic.definition import DynamicMethodDefinition


WITHOUT_TEST_EXPERT_DEFINITION = DynamicMethodDefinition(
    name="without_test_expert",
    expert_roles=(
        "requirement_analyst",
        "conceptual_model_designer",
        "logical_model_designer",
        "physical_design_specialist",
        "dialect_compiler",
    ),
    artifact_by_role={
        "requirement_analyst": "requirement_brief",
        "conceptual_model_designer": "conceptual_model",
        "logical_model_designer": "logical_model",
        "physical_design_specialist": "physical_plan",
        "dialect_compiler": "dialect_report",
    },
    artifact_dependencies={
        "requirement_brief": (),
        "conceptual_model": ("requirement_brief",),
        "logical_model": ("requirement_brief", "conceptual_model"),
        "physical_plan": ("logical_model",),
        "dialect_report": ("logical_model", "physical_plan"),
        "ddl": ("logical_model", "physical_plan", "dialect_report"),
        "verification_summary": ("ddl",),
    },
    required_expert_context={
        "requirement_analyst": (("task", ""),),
        "conceptual_model_designer": (("artifact", "requirement_brief"),),
        "logical_model_designer": (("artifact", "conceptual_model"),),
        "physical_design_specialist": (("artifact", "logical_model"),),
        "dialect_compiler": (
            ("artifact", "logical_model"),
            ("artifact", "physical_plan"),
        ),
    },
    allowed_tool_types=frozenset(
        {
            "artifact_validator",
            "third_normal_form_validator",
            "dialect_linter",
        }
    ),
    runtime_verification_required=False,
    scheduler_variant_rules=(
        "This method variant has no testing stage or testing expert. Complete the "
        "requirement, conceptual, logical, physical, and dialect-compilation stages.",
        "Do not request database execution, generated SQL tests, or query-plan evidence. "
        "The produced DDL is intentionally not executed against a DBMS.",
        "After DDL is produced, use static dialect linting when useful, revise through "
        "dialect_compiler when grounded feedback exists, or finalize the design.",
        "A design-only ready result must explicitly state that DDL executability was not "
        "verified by real DBMS execution.",
    ),
)
