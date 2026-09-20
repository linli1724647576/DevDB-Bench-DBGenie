from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig
from dbgenie.llm.client import LLMClient, LLMMessage

from ..contracts import BaselineRunOutcome
from .jsonutil import json_text
from .prompts import PROMPT_VERSION, prompt_catalog


@dataclass(frozen=True)
class SchemaAgentMethod:
    name: str = "schema-agent"
    prompt_version: str = PROMPT_VERSION

    @property
    def example_ids(self) -> tuple[str, ...]:
        return ()

    def build_messages(self, task: AgentTaskInput) -> list[LLMMessage]:
        catalog = prompt_catalog(task)
        return [
            LLMMessage(role="system", content=str(catalog["roles"]["ManagerAgent"])),
            LLMMessage(role="user", content=json_text(catalog["logical_input"])),
        ]

    def preview(self, task: AgentTaskInput) -> dict[str, object]:
        return {"schema_agent": prompt_catalog(task)}

    def execute(
        self,
        task: AgentTaskInput,
        llm_config: LLMConfig,
        *,
        llm_client_factory: Callable[[LLMConfig], LLMClient] = LLMClient,
        progress: Callable[[str], None] | None = None,
    ) -> BaselineRunOutcome:
        del llm_client_factory
        try:
            from .orchestration import execute_schema_agent
        except ImportError as exc:
            raise RuntimeError(
                "SchemaAgent requires method dependencies; install with "
                "python -m pip install -e \".[method]\""
            ) from exc
        return execute_schema_agent(task, llm_config, progress=progress)
