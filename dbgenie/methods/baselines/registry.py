from __future__ import annotations

from .contracts import BaselineMethod
from .few_shot.method import FewShotMethod
from .mac_sql.method import MacSQLMethod
from .schema_agent.method import SchemaAgentMethod


_METHOD_FACTORIES = {
    "few-shot": FewShotMethod,
    "mac-sql": MacSQLMethod,
    "schema-agent": SchemaAgentMethod,
}


def available_baseline_methods() -> tuple[str, ...]:
    return tuple(_METHOD_FACTORIES)


def get_baseline_method(name: str) -> BaselineMethod:
    try:
        factory = _METHOD_FACTORIES[name]
    except KeyError as exc:
        choices = ", ".join(available_baseline_methods())
        raise ValueError(f"unknown baseline method '{name}'; choose one of: {choices}") from exc
    return factory()
