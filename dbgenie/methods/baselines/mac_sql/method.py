from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig
from dbgenie.llm.client import LLMClient, LLMMessage

from ..contracts import BaselineRunOutcome
from .orchestration import execute_mac_sql
from .prompts import PROMPT_VERSION, build_decomposer_messages, prompt_catalog


@dataclass(frozen=True)
class MacSQLMethod:
    name: str = "mac-sql"
    prompt_version: str = PROMPT_VERSION

    @property
    def example_ids(self) -> tuple[str, ...]:
        return ()

    def build_messages(self, task: AgentTaskInput) -> list[LLMMessage]:
        return build_decomposer_messages(task)

    def preview(self, task: AgentTaskInput) -> dict[str, object]:
        return {"mac_sql": prompt_catalog(task)}

    def execute(
        self,
        task: AgentTaskInput,
        llm_config: LLMConfig,
        *,
        llm_client_factory: Callable[[LLMConfig], LLMClient] = LLMClient,
        progress: Callable[[str], None] | None = None,
    ) -> BaselineRunOutcome:
        return execute_mac_sql(
            task,
            llm_config,
            llm_client_factory=llm_client_factory,
            progress=progress,
        )
