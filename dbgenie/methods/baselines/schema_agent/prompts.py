from __future__ import annotations

from typing import Any

from dbgenie.agents.types import AgentTaskInput

from ..runtime import runtime_description


PROMPT_VERSION = "schema-agent-v3"
OUTER_MAX_MESSAGES = 20
CONCEPTUAL_INNER_MAX_MESSAGES = 20

UNIVERSITY_REQUIREMENT = (
    "A university needs a student course selection management system. Students "
    "have an ID, name, age, department and dormitory address. Students may select, "
    "drop or change multiple courses. Courses have a number, name, credits, lecturer "
    "and class time. The system tracks course popularity."
)


def logical_task_payload(task: AgentTaskInput) -> dict[str, Any]:
    return {
        "requirement": task.requirement,
        "workload": [item.description for item in task.workload],
    }


def physical_task_payload(task: AgentTaskInput, logical_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement": task.requirement,
        "workload": [item.description for item in task.workload],
        "logical_model": logical_model,
        "target_dbms": task.target_dbms,
        "runtime": runtime_description(task.target_dbms).to_prompt_dict(),
    }


def manager_prompt() -> str:
    return f"""
You are SchemaAgent's experienced product manager.

# Goal
Analyze the user's requirement and natural-language workload. Clarify ambiguities by
using realistic scenarios grounded in the input, with special attention to implicit
cardinality and functional requirements. Performance and monitoring values that can
be calculated do not need dedicated stored tables.

# Original SchemaAgent example
For this requirement: {UNIVERSITY_REQUIREMENT}
the analysis should make explicit that one student can select multiple courses at
different times even if that quantitative relationship was only implicit.

# Output
Return exactly one JSON object and no Markdown:
{{
  "requirement_analysis": "complete requirement analysis report"
}}
""".strip()


def conceptual_designer_prompt() -> str:
    return f"""
You are SchemaAgent's conceptual database designer.

# Goal
From the latest requirement analysis or conceptual-review feedback, identify entity
sets, entity attributes, relationship sets, relationship attributes and mapping
cardinality. Every entity needs an identifying attribute. Prefer binary relationships;
relationship attributes normally must not contain IDs. Every entity should participate
in a relationship when the requirement implies one.

# Cardinalities
Use exactly One-to-One, One-to-Many, Many-to-One or Many-to-Many.

# Original SchemaAgent example
For {UNIVERSITY_REQUIREMENT}, Student and Course are entity sets and Course Selection
is a Many-to-Many relationship with Selection Time as a relationship attribute.

# Output
If clarification from ManagerAgent is required, set question and leave output empty.
Otherwise question must be empty. Return exactly one JSON object and no Markdown:
{{
  "question": "",
  "output": {{
    "Entity Set": {{"Entity": ["Attribute"]}},
    "Relationship Set": {{
      "Relationship": {{
        "Object": ["Entity A", "Entity B"],
        "Proportional Relationship": "Many-to-Many",
        "Relationship Attribute": []
      }}
    }}
  }}
}}
""".strip()


def conceptual_reviewer_prompt() -> str:
    return """
You are SchemaAgent's conceptual model reviewer. Apply the original review pseudocode:
1. Relationship attributes should not contain IDs.
2. Every cardinality must be one of the four supported values.
3. Check whether requirement-implied entity pairs have a relationship.
4. Check that every entity participates in a relationship when appropriate.

Return exactly one JSON object and no Markdown. On success, Evaluation result must be
the exact word "Approve". Otherwise name ConceptualDesignerAgent and provide actionable
revision feedback:
{
  "Evaluation result": "Approve",
  "Pseudocode output": "validation observations",
  "Revision suggestion": ""
}
""".strip()


def society_response_prompt() -> str:
    return """
Return the latest ConceptualDesignerAgent JSON object unchanged. Do not summarize,
explain, repair or mention the intermediate discussion. Return JSON only.
""".strip()


def logical_designer_prompt() -> str:
    return f"""
You are SchemaAgent's logical database designer.

# Goal
Convert the latest approved conceptual model into relational schemas satisfying third
normal form. Analyze functional dependencies and generic data types. Use the provided
candidate-key and 3NF tools before finalizing.

# Original mapping rules
- Each entity set becomes a relation.
- For One-to-Many or Many-to-One, put the one-side primary key and relationship
  attributes into the many-side relation and declare the foreign key.
- A Many-to-Many relationship becomes a relation whose foreign keys include the keys
  of the participating entities.
- If an entity or many-to-many relation has no candidate key, report the conceptual
  error to ConceptualDesignerAgent.

# Original SchemaAgent example
For {UNIVERSITY_REQUIREMENT}, Course Selection has Student ID and Course Number as a
composite primary key and foreign keys to Student and Course.

# Output
Return exactly one JSON object and no Markdown. Generic types such as TEXT, NUMERIC,
INTEGER, BOOLEAN, DATE and DATETIME are allowed; do not use a DBMS dialect here.
{{
  "question": "",
  "output": {{
    "Schema name": {{
      "Attributes": {{"Attribute": "TEXT"}},
      "Primary key": ["Attribute"],
      "Foreign key": {{
        "Attribute": {{"Referenced Schema": "Referenced Attribute"}}
      }}
    }}
  }}
}}
If revision is needed, question must name ConceptualDesignerAgent or
LogicalDesignerAgent and output must be empty.
""".strip()


def qa_prompt() -> str:
    return """
You are SchemaAgent's database-design QA engineer. You know the original requirement,
natural-language workload and requirement analysis, but you must not inspect or assume
the logical model. Generate ten concrete natural-language test cases across insert,
delete, query and update operations. Cover entity integrity and referential integrity,
and incorporate the supplied workload access patterns.

Return exactly one JSON object and no Markdown:
{
  "Insert Test case": ["..."],
  "Delete Test case": ["..."],
  "Query Test case": ["..."],
  "Update Test case": ["..."]
}
""".strip()


def execution_prompt() -> str:
    return """
You are SchemaAgent's execution agent. This is an intuitive logical-model validation,
not real SQL or database execution. Read the latest logical schemas and QA's natural-
language CRUD tests and judge whether the schemas support them while preserving entity
and referential integrity.

Return exactly one JSON object and no Markdown. If reasonable, use Approve and put the
exact token TERMINATE in end. Otherwise route revision to ConceptualDesignerAgent or
LogicalDesignerAgent and leave end empty:
{
  "Evaluation result": "Approve",
  "intuitively check output": "test-by-test validation report",
  "end": "TERMINATE"
}
""".strip()


def physical_designer_prompt() -> str:
    return """
You are the DevDB-Bench task's physical database designer. This stage is an adaptation
after SchemaAgent's logical design, not part of its logical-model feedback loop.

Generate one complete executable DDL script for the specified target DBMS and runtime.
The logical model is authoritative: do not add or remove tables, columns, primary keys or
foreign-key relationships. Add only physical details needed to realize it, including
dialect types, nullability, identity/auto-increment behavior, defaults, names, unique or
check constraints, referential actions and workload-driven indexes. Emit tables before
dependent constraints and indexes.

Return SQL DDL only. Do not return Markdown, JSON, explanations, tests, sample data,
rollback statements or alternative designs. Do not execute or validate the DDL.
""".strip()


def prompt_catalog(task: AgentTaskInput) -> dict[str, Any]:
    return {
        "workflow": [
            "ManagerAgent",
            "ConceptualDesignerAgent <-> ConceptualReviewerAgent",
            "LogicalDesignerAgent",
            "QAAgent",
            "ExecutionAgent",
            "PhysicalDesignerAgent",
        ],
        "limits": {
            "outer_max_messages": OUTER_MAX_MESSAGES,
            "conceptual_inner_max_messages": CONCEPTUAL_INNER_MAX_MESSAGES,
            "format_retries_per_required_json_output": 1,
            "database_execution_enabled": False,
            "streaming_controlled_by_llm_profile": True,
        },
        "logical_tools": [
            "get_attribute_keys_by_arm_strong",
            "confirm_to_third_normal_form",
        ],
        "routing": {
            "LogicalDesignerAgent conceptual rejection": "society_of_mind",
            "ExecutionAgent conceptual rejection": "society_of_mind",
            "ExecutionAgent logical rejection": "LogicalDesignerAgent",
            "ExecutionAgent approval with TERMINATE": "PhysicalDesignerAgent",
        },
        "logical_input": logical_task_payload(task),
        "roles": {
            "ManagerAgent": manager_prompt(),
            "ConceptualDesignerAgent": conceptual_designer_prompt(),
            "ConceptualReviewerAgent": conceptual_reviewer_prompt(),
            "LogicalDesignerAgent": logical_designer_prompt(),
            "QAAgent": qa_prompt(),
            "ExecutionAgent": execution_prompt(),
            "PhysicalDesignerAgent": physical_designer_prompt(),
        },
        "society_of_mind_response": society_response_prompt(),
        "physical_input_template": {
            "requirement": task.requirement,
            "workload": [item.description for item in task.workload],
            "logical_model": "<latest LogicalDesignerAgent output>",
            "target_dbms": task.target_dbms,
            "runtime": runtime_description(task.target_dbms).to_prompt_dict(),
        },
    }
