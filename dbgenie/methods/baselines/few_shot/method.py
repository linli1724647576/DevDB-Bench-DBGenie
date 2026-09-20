from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig
from dbgenie.llm.client import LLMClient, LLMMessage

from ..common import messages_to_dict, generate_once
from ..contracts import BaselineRunOutcome
from .prompts import EXAMPLE_IDS, PROMPT_VERSION, build_few_shot_messages


@dataclass(frozen=True)
class FewShotMethod:
    name: str = "few-shot"
    prompt_version: str = PROMPT_VERSION

    @property
    def example_ids(self) -> tuple[str, ...]:
        return EXAMPLE_IDS

    def build_messages(self, task: AgentTaskInput) -> list[LLMMessage]:
        return build_few_shot_messages(task)

    def preview(self, task: AgentTaskInput) -> dict[str, object]:
        return {"messages": messages_to_dict(self.build_messages(task))}

    def execute(
        self,
        task: AgentTaskInput,
        llm_config: LLMConfig,
        *,
        llm_client_factory: Callable[[LLMConfig], LLMClient] = LLMClient,
        progress: Callable[[str], None] | None = None,
    ) -> BaselineRunOutcome:
        del progress
        return BaselineRunOutcome(
            result=generate_once(self, task, llm_client_factory(llm_config))
        )
