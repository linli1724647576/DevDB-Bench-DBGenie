from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from dbgenie.llm.client import LLMClient, LLMRequestError

from .context import MaterializedContext
from .jsonutil import LLMJSONParseError, parse_json_object
from .prompts import build_expert_prompt
from .state import DynamicMethodState


@dataclass
class ExpertResult:
    role: str
    output: dict[str, Any]
    warnings: list[str]
    dialect_retrieval: dict[str, Any] = field(default_factory=dict)


class DynamicExpertRunner:
    def __init__(
        self,
        llm_client: LLMClient,
        *,
        llm_attempt_callback: Callable[[LLMRequestError, str, dict[str, Any], int], None] | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.llm_attempt_callback = llm_attempt_callback

    def run(
        self,
        role: str,
        state: DynamicMethodState,
        *,
        execution_context: MaterializedContext | dict[str, Any] | None = None,
        revision_request: dict[str, Any] | None = None,
    ) -> ExpertResult:
        prompt = build_expert_prompt(
            role,
            state,
            execution_context=execution_context,
            revision_request=revision_request,
        )
        try:
            raw = self.llm_client.complete(
                prompt.messages,
                stage=f"expert:{role}",
                on_attempt_error=self._attempt_callback(role),
            )
        except LLMRequestError as exc:
            exc.stage = f"expert:{role}"
            raise
        try:
            output = parse_json_object(raw)
        except LLMJSONParseError as exc:
            exc.stage = f"expert:{role}"
            raise
        warnings = []
        if not isinstance(output, dict):
            raise ValueError("expert output must be a JSON object")
        if output.get("warnings") and isinstance(output["warnings"], list):
            warnings.extend(str(item) for item in output["warnings"] if str(item))
        retrieval_warnings = prompt.dialect_retrieval.get("warnings")
        if isinstance(retrieval_warnings, list):
            warnings.extend(str(item) for item in retrieval_warnings if str(item))
        return ExpertResult(
            role=role,
            output=output,
            warnings=warnings,
            dialect_retrieval=prompt.dialect_retrieval,
        )

    def _attempt_callback(self, speaker: str):
        if self.llm_attempt_callback is None:
            return None

        def report(error: LLMRequestError, record: dict[str, Any], total_attempts: int) -> None:
            self.llm_attempt_callback(error, speaker, record, total_attempts)

        return report
