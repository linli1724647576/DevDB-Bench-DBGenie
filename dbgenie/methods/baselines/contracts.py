from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig
from dbgenie.llm.client import LLMClient, LLMMessage


@dataclass(frozen=True)
class BaselineRunResult:
    task_id: str
    status: str
    final_ddl: str

    def to_dict(self) -> dict[str, str]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "final_ddl": self.final_ddl,
        }


@dataclass(frozen=True)
class BaselineRunOutcome:
    result: BaselineRunResult
    trace: dict[str, Any] | None = None


class BaselineMethod(Protocol):
    name: str
    prompt_version: str

    @property
    def example_ids(self) -> tuple[str, ...]: ...

    def build_messages(self, task: AgentTaskInput) -> list[LLMMessage]: ...

    def preview(self, task: AgentTaskInput) -> dict[str, Any]: ...

    def execute(
        self,
        task: AgentTaskInput,
        llm_config: LLMConfig,
        *,
        llm_client_factory: Callable[[LLMConfig], LLMClient] = LLMClient,
        progress: Callable[[str], None] | None = None,
    ) -> BaselineRunOutcome: ...
