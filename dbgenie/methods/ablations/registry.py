from __future__ import annotations

from dbgenie.methods.dynamic.definition import (
    FULL_METHOD_DEFINITION,
    DynamicMethodDefinition,
)

from .without_requirement_analyst import WITHOUT_REQUIREMENT_ANALYST_DEFINITION
from .without_test_expert import WITHOUT_TEST_EXPERT_DEFINITION
from .without_scheduler import WITHOUT_SCHEDULER_DEFINITION


_METHOD_VARIANTS = {
    FULL_METHOD_DEFINITION.name: FULL_METHOD_DEFINITION,
    WITHOUT_REQUIREMENT_ANALYST_DEFINITION.name: WITHOUT_REQUIREMENT_ANALYST_DEFINITION,
    WITHOUT_TEST_EXPERT_DEFINITION.name: WITHOUT_TEST_EXPERT_DEFINITION,
    WITHOUT_SCHEDULER_DEFINITION.name: WITHOUT_SCHEDULER_DEFINITION,
}


def available_method_variants() -> tuple[str, ...]:
    return tuple(_METHOD_VARIANTS)


def get_method_definition(name: str) -> DynamicMethodDefinition:
    try:
        return _METHOD_VARIANTS[name]
    except KeyError as exc:
        choices = ", ".join(available_method_variants())
        raise ValueError(f"unknown method variant '{name}'; choose one of: {choices}") from exc
