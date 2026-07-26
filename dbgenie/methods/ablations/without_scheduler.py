from __future__ import annotations

from dbgenie.methods.dynamic.definition import (
    FULL_ARTIFACT_DEPENDENCIES,
    FULL_REQUIRED_EXPERT_CONTEXT,
    DynamicMethodDefinition,
)


FIXED_EXPERT_SEQUENCE = (
    "requirement_analyst",
    "conceptual_model_designer",
    "logical_model_designer",
    "physical_design_specialist",
    "dialect_compiler",
    "test_expert",
)

LOGICAL_MODEL_DESIGNER_SKILL = """
# Logical Model Designer Skill

Role id: `logical_model_designer`

Convert the conceptual model into canonical logical SchemaIR. Design tables,
columns, keys, foreign keys, uniqueness, checks, nullability, defaults, and
state constraints. Preserve constraint traceability and mark DB-managed
surrogate integer keys with `identity: true`.

Do not output final DDL, migration SQL, physical indexes, or non-canonical
field names.
""".strip()

LOGICAL_MODEL_CONTRACT = """
Return JSON:
{
  "schema_ir": {
    "tables": [
      {
        "name": "",
        "columns": [
          {"name": "id", "type": "bigint", "nullable": false, "identity": true}
        ],
        "primary_key": ["id"],
        "foreign_keys": [{"columns": ["user_id"], "ref_table": "users", "ref_columns": ["id"]}],
        "unique_constraints": [{"columns": ["email"]}],
        "check_constraints": [{"expression": "amount >= 0"}],
        "indexes": [{"columns": ["user_id", "created_at"], "unique": false}]
      }
    ]
  },
  "constraint_traceability": [],
  "design_notes": [],
  "warnings": [],
  "tool_request_proposals": []
}
""".strip()

DIALECT_COMPILER_SKILL = """
# Dialect Compiler Skill

Role id: `dialect_compiler`

Compile the visible logical SchemaIR and physical index plan into executable
DDL for the target DBMS. Preserve upstream semantics, use retrieved dialect
knowledge, and return one complete DDL script. During repair, use the exact
current DDL and runtime errors in `repair_envelope`; do not change conceptual,
logical, or physical design decisions.
""".strip()

TEST_EXPERT_SKILL = """
# Test Expert Skill

Role id: `test_expert`

Generate executable invariant and workload tests for the visible DDL. Request
the permitted runtime tools, then interpret their raw current-version evidence.
Do not modify any design artifact, choose a target role, or request an upstream
repair. This is a terminal verification stage: report the first-pass design's
observed quality and stop after interpreting the one supplied tool batch.
""".strip()

TEST_EXPERT_CONTRACT = """
Return JSON:
{
  "generated_tests": [],
  "execution_feedback": [],
  "feedback": [],
  "failure_category": [],
  "passed": true,
  "warnings": [],
  "tool_request_proposals": []
}

When the current DDL has no current-version real execution evidence, request
`ddl_executor`. When generated tests lack current-version SQL execution, also
request `sql_test_runner`. Request `query_plan_tool` when your workload checks
explicitly require query-plan evidence.

`failure_category` is diagnostic only. When used, choose only from
`test_fixture`, `dialect_or_ddl`, `physical_plan`, `logical_schema`,
`conceptual_model`, `requirement_ambiguity`, or `environment_or_tool`. It never
selects a repair route or causes another expert to run.

If `revision_request.mode` is `in_turn_tool_interpretation`, preserve
`generated_tests` exactly, interpret the complete supplied tool batch, update
the feedback, failure category, pass flag, and warnings, and do not request
another tool batch in that response. The pipeline ends after this report.
""".strip()


WITHOUT_SCHEDULER_DEFINITION = DynamicMethodDefinition(
    name="without_scheduler",
    expert_roles=FIXED_EXPERT_SEQUENCE,
    artifact_by_role={
        "requirement_analyst": "requirement_brief",
        "conceptual_model_designer": "conceptual_model",
        "logical_model_designer": "logical_model",
        "physical_design_specialist": "physical_plan",
        "dialect_compiler": "dialect_report",
        "test_expert": "test_report",
    },
    artifact_dependencies=dict(FULL_ARTIFACT_DEPENDENCIES),
    required_expert_context=dict(FULL_REQUIRED_EXPERT_CONTEXT),
    allowed_tool_types=frozenset(
        {
            "artifact_validator",
            "ddl_executor",
            "sql_test_runner",
            "query_plan_tool",
        }
    ),
    runtime_verification_required=True,
    orchestration_mode="fixed_pipeline",
    normalization_validation_required=False,
    cross_expert_feedback_repair_enabled=False,
    fixed_expert_sequence=FIXED_EXPERT_SEQUENCE,
    expert_skill_overrides={
        "logical_model_designer": LOGICAL_MODEL_DESIGNER_SKILL,
        "dialect_compiler": DIALECT_COMPILER_SKILL,
        "test_expert": TEST_EXPERT_SKILL,
    },
    expert_contract_overrides={
        "logical_model_designer": LOGICAL_MODEL_CONTRACT,
        "test_expert": TEST_EXPERT_CONTRACT,
    },
)
