from __future__ import annotations

import re
from typing import Any


ROLE_ORDER = [
    "requirement_analyst",
    "conceptual_model_designer",
    "conceptual_model_reviewer",
    "logical_model_designer",
    "physical_design_specialist",
    "dialect_compiler",
    "test_expert",
]


ROLE_DISPLAY_NAMES = {
    "requirement_analyst": "Requirement Analyst",
    "conceptual_model_designer": "Conceptual Model Designer",
    "conceptual_model_reviewer": "Conceptual Model Reviewer",
    "logical_model_designer": "Logical Model Designer",
    "physical_design_specialist": "Physical Design Specialist",
    "dialect_compiler": "Dialect Compiler",
    "test_expert": "Test Expert",
}


ROLE_RANK = {role: index for index, role in enumerate(ROLE_ORDER)}


CANONICAL_FAILURE_TYPES = [
    "requirement_issue",
    "conceptual_issue",
    "logical_schema_issue",
    "physical_design_issue",
    "dialect_issue",
    "test_issue",
    "potential_risk",
    "note",
]


ROLE_ALIASES = {
    "requirement": "requirement_analyst",
    "requirement_analysis": "requirement_analyst",
    "requirements": "requirement_analyst",
    "business_rule": "requirement_analyst",
    "business_rules": "requirement_analyst",
    "conceptual": "conceptual_model_designer",
    "conceptual_model": "conceptual_model_designer",
    "conceptual_designer": "conceptual_model_designer",
    "conceptual_model_design": "conceptual_model_designer",
    "conceptual_review": "conceptual_model_reviewer",
    "conceptual_reviewer": "conceptual_model_reviewer",
    "logical": "logical_model_designer",
    "logical_model": "logical_model_designer",
    "logical_schema": "logical_model_designer",
    "schema": "logical_model_designer",
    "schema_design": "logical_model_designer",
    "schema_ir": "logical_model_designer",
    "physical": "physical_design_specialist",
    "physical_design": "physical_design_specialist",
    "physical_plan": "physical_design_specialist",
    "index_design": "physical_design_specialist",
    "performance": "physical_design_specialist",
    "dialect": "dialect_compiler",
    "ddl": "dialect_compiler",
    "ddl_compiler": "dialect_compiler",
    "compiler": "dialect_compiler",
    "migration_compiler": "dialect_compiler",
    "test": "test_expert",
    "testing": "test_expert",
    "tester": "test_expert",
}


FAILURE_TYPE_ROUTES = {
    "requirement_issue": "requirement_analyst",
    "ambiguity": "requirement_analyst",
    "missing_business_rule": "requirement_analyst",
    "constraint_design": "requirement_analyst",
    "conceptual_issue": "conceptual_model_designer",
    "entity_boundary": "conceptual_model_designer",
    "cardinality_issue": "conceptual_model_designer",
    "relationship_issue": "conceptual_model_designer",
    "schema_design": "logical_model_designer",
    "logical_schema_issue": "logical_model_designer",
    "missing_constraint": "logical_model_designer",
    "missing_feature": "logical_model_designer",
    "referential_integrity": "logical_model_designer",
    "redundancy": "logical_model_designer",
    "physical_design_issue": "physical_design_specialist",
    "performance": "physical_design_specialist",
    "missing_index": "physical_design_specialist",
    "redundant_index": "physical_design_specialist",
    "missing_filtered_index": "physical_design_specialist",
    "incomplete_index_included_columns": "physical_design_specialist",
    "dialect_issue": "dialect_compiler",
    "syntax_issue": "dialect_compiler",
    "unsupported_feature": "dialect_compiler",
    "missing_clarity": "dialect_compiler",
    "inconsistency": "dialect_compiler",
    "test_issue": "test_expert",
}

FAILURE_TYPE_ALIASES = {
    "logical_model": "logical_schema_issue",
    "logical_schema": "logical_schema_issue",
    "schema": "logical_schema_issue",
    "schema_design": "logical_schema_issue",
    "referential_integrity": "logical_schema_issue",
    "missing_constraint": "logical_schema_issue",
    "missing_feature": "logical_schema_issue",
    "physical": "physical_design_issue",
    "physical_design": "physical_design_issue",
    "physical_plan": "physical_design_issue",
    "performance": "physical_design_issue",
    "missing_index": "physical_design_issue",
    "redundant_index": "physical_design_issue",
    "dialect": "dialect_issue",
    "ddl": "dialect_issue",
    "syntax": "dialect_issue",
    "syntax_issue": "dialect_issue",
    "unsupported_feature": "dialect_issue",
    "test": "test_issue",
    "testing": "test_issue",
}


def canonical_role(value: Any) -> str:
    key = _canonical_key(value)
    if key in ROLE_RANK:
        return key
    return ROLE_ALIASES.get(key, "")


def feedback_owner(feedback: dict[str, Any]) -> str:
    owner = canonical_role(feedback.get("owner"))
    if owner:
        return owner
    failure_type = canonical_failure_type(feedback.get("failure_type"))
    return FAILURE_TYPE_ROUTES.get(failure_type, "")


def canonical_failure_type(value: Any) -> str:
    key = _canonical_key(value)
    return FAILURE_TYPE_ALIASES.get(key, key)


def normalize_feedback_item(feedback: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(feedback)
    owner = feedback_owner(feedback)
    if owner:
        normalized["owner"] = owner
    failure_type = canonical_failure_type(feedback.get("failure_type"))
    if failure_type:
        normalized["failure_type"] = failure_type
    if "severity" in normalized:
        normalized["severity"] = _canonical_key(normalized.get("severity"))
    return normalized


def role_rank(role: str) -> int:
    return ROLE_RANK.get(role, len(ROLE_ORDER))


def _canonical_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")
