from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from dbgenie.llm.client import LLMClient, LLMRequestError

from .context import ContextSelection, MaterializedContext, build_state_catalog, materialize_context
from .contracts import SchedulerAction
from .jsonutil import LLMJSONParseError, parse_json_object
from .prompts import build_context_selection_messages, build_scheduler_messages
from .state import DynamicMethodState


@dataclass
class SchedulerDecision:
    action: SchedulerAction
    raw_output: dict[str, Any]
    decision_context_selection: ContextSelection
    decision_context: MaterializedContext
    context_selection_raw_output: dict[str, Any]
    warnings: list[str]
    validation_errors: list[str]


class DynamicMethodScheduler:
    def __init__(
        self,
        llm_client: LLMClient,
        *,
        llm_attempt_callback: Callable[[LLMRequestError, str, dict[str, Any], int], None] | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.llm_attempt_callback = llm_attempt_callback

    def decide(
        self,
        state: DynamicMethodState,
        *,
        finalize_only: bool = False,
    ) -> SchedulerDecision:
        if finalize_only:
            if state.finalize_reserve_used or state.remaining_scheduler_steps() > 0:
                raise RuntimeError("finalize scheduler reserve is not available")
        elif state.remaining_scheduler_steps() <= 0:
            raise RuntimeError("scheduler step budget exhausted")

        catalog = build_state_catalog(state)
        selection_messages = build_context_selection_messages(
            catalog,
            finalize_only=finalize_only,
            method_definition=state.method_definition,
        )
        try:
            selection_raw = self.llm_client.complete(
                selection_messages,
                stage="scheduler_context_selection",
                on_attempt_error=self._attempt_callback("scheduler"),
            )
        except LLMRequestError as exc:
            exc.stage = "scheduler_context_selection"
            raise
        try:
            selection_payload = parse_json_object(selection_raw)
        except LLMJSONParseError as exc:
            exc.stage = "scheduler_context_selection"
            raise
        selection = ContextSelection.from_dict(selection_payload)
        decision_context = materialize_context(state, selection)

        messages = build_scheduler_messages(
            catalog,
            decision_context,
            finalize_only=finalize_only,
            method_definition=state.method_definition,
        )
        try:
            raw = self.llm_client.complete(
                messages,
                stage="scheduler_action",
                on_attempt_error=self._attempt_callback("scheduler"),
            )
        except LLMRequestError as exc:
            exc.stage = "scheduler_action"
            raise
        try:
            payload = parse_json_object(raw)
        except LLMJSONParseError as exc:
            exc.stage = "scheduler_action"
            raise
        action = SchedulerAction.from_dict(payload)
        warnings = list(action.warnings) + list(decision_context.warnings)
        validation_errors = validate_scheduler_action(state, action)
        if finalize_only and action.action_type != "finalize":
            validation_errors.append(
                "reserved finalize scheduler step permits only action_type=finalize"
            )
        return SchedulerDecision(
            action=action,
            raw_output=payload,
            decision_context_selection=selection,
            decision_context=decision_context,
            context_selection_raw_output=selection_payload,
            warnings=warnings,
            validation_errors=validation_errors,
        )

    def _attempt_callback(self, speaker: str):
        if self.llm_attempt_callback is None:
            return None

        def report(error: LLMRequestError, record: dict[str, Any], total_attempts: int) -> None:
            self.llm_attempt_callback(error, speaker, record, total_attempts)

        return report


def validate_scheduler_action(
    state: DynamicMethodState,
    action: SchedulerAction,
) -> list[str]:
    validation_errors = action.validate(
        list(state.method_definition.expert_roles),
        state.method_definition.allowed_tool_types,
    )
    if action.action_type != "invoke_expert" or action.target_role not in state.method_definition.expert_roles:
        return validation_errors

    allowed_sources = state.method_definition.expert_context_sources(action.target_role)
    selection = ContextSelection.from_dict(action.execution_context_selection)
    for item in selection.items:
        if item.source in allowed_sources:
            continue
        error = (
            f"context source {item.source} is not allowed for expert "
            f"{action.target_role} in method variant {state.method_definition.name}"
        )
        if error not in validation_errors:
            validation_errors.append(error)
    return validation_errors
