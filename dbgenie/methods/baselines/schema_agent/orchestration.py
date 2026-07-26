from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import Any

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import (
    FunctionalTermination,
    MaxMessageTermination,
)
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ModelClientStreamingChunkEvent,
    TextMessage,
)
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_core.models import CreateResult, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import LLMConfig

from ..common import normalize_ddl_output
from ..contracts import BaselineRunOutcome, BaselineRunResult
from .agents import RetryingJSONAgent, SourceFilteringAgent, require_fields, validate_design
from .contexts import source_context, source_or_recipient_context
from .jsonutil import json_text, parse_json_object
from .prompts import (
    CONCEPTUAL_INNER_MAX_MESSAGES,
    OUTER_MAX_MESSAGES,
    PROMPT_VERSION,
    conceptual_designer_prompt,
    conceptual_reviewer_prompt,
    execution_prompt,
    logical_designer_prompt,
    logical_task_payload,
    manager_prompt,
    physical_designer_prompt,
    physical_task_payload,
    qa_prompt,
    society_response_prompt,
)
from .tools import confirm_to_third_normal_form, get_attribute_keys_by_arm_strong


ProgressCallback = Callable[[str], None]
Event = BaseAgentEvent | BaseChatMessage


class _StreamingCreateOpenAIChatCompletionClient(OpenAIChatCompletionClient):
    """Use streaming for AutoGen components that invoke create() directly."""

    async def create(self, *args: Any, **kwargs: Any) -> CreateResult:
        result: CreateResult | None = None
        async for item in super().create_stream(*args, **kwargs):
            if isinstance(item, CreateResult):
                result = item
        if result is None:
            raise RuntimeError("streaming model call did not produce a final result")
        return result


def execute_schema_agent(
    task: AgentTaskInput,
    llm_config: LLMConfig,
    *,
    progress: ProgressCallback | None = None,
) -> BaselineRunOutcome:
    return asyncio.run(_execute_schema_agent(task, llm_config, progress=progress))


async def _execute_schema_agent(
    task: AgentTaskInput,
    llm_config: LLMConfig,
    *,
    progress: ProgressCallback | None,
) -> BaselineRunOutcome:
    emit = progress or (lambda _message: None)
    trace: dict[str, Any] = {
        "task_id": task.id,
        "method": "schema-agent",
        "prompt_version": PROMPT_VERSION,
        "input": logical_task_payload(task),
        "runtime": physical_task_payload(task, {}).get("runtime"),
        "logical_messages": [],
        "artifacts": {},
        "format_retries": [],
        "physical": {},
        "warnings": [],
        "errors": [],
    }
    model_client = _model_client(llm_config)
    try:
        emit("schema_agent logical_design")
        team = _build_team(
            model_client,
            stream=bool(llm_config.stream),
            on_format_retry=lambda role: trace["format_retries"].append(role),
        )
        events, result = await _collect_team(
            team,
            task=json_text(logical_task_payload(task)),
        )
        trace["logical_messages"] = [
            _event_dict(event) for event in events if _include_in_trace(event)
        ]
        trace["logical_stop_reason"] = result.stop_reason if result else "error"
        trace["artifacts"] = _extract_artifacts(events)
        trace["model_call_count"] = _model_call_count(events)

        logical_model = trace["artifacts"].get("logical_model")
        if not isinstance(logical_model, dict) or not logical_model:
            raise RuntimeError("SchemaAgent did not produce a usable logical model")
        accepted = _execution_approved(trace["artifacts"].get("execution_report"))
        trace["logical_model_accepted"] = accepted
        if not accepted:
            trace["warnings"].append(
                "logical workflow stopped without ExecutionAgent approval; using latest logical model"
            )

        emit("schema_agent physical_design")
        physical_agent = AssistantAgent(
            "PhysicalDesignerAgent",
            description="Converts SchemaAgent's final logical model to target-dialect DDL.",
            model_client=model_client,
            system_message=physical_designer_prompt(),
            model_client_stream=bool(llm_config.stream),
        )
        physical_events, physical_result = await _collect_agent(
            physical_agent,
            task=json_text(physical_task_payload(task, logical_model)),
        )
        raw_ddl = _latest_text(physical_events, "PhysicalDesignerAgent")
        final_ddl = normalize_ddl_output(raw_ddl)
        trace["physical"] = {
            "input": physical_task_payload(task, logical_model),
            "messages": [
                _event_dict(event)
                for event in physical_events
                if _include_in_trace(event)
            ],
            "stop_reason": physical_result.stop_reason if physical_result else None,
            "raw_output": raw_ddl,
        }
        trace["model_call_count"] += _model_call_count(physical_events)
        status = "generated" if final_ddl else "failed"
        trace["status"] = status
        return BaselineRunOutcome(
            result=BaselineRunResult(task_id=task.id, status=status, final_ddl=final_ddl),
            trace=trace,
        )
    except Exception as exc:
        trace["status"] = "failed"
        trace["errors"].append(f"{type(exc).__name__}: {exc}")
        return BaselineRunOutcome(
            result=BaselineRunResult(task_id=task.id, status="failed", final_ddl=""),
            trace=trace,
        )
    finally:
        await model_client.close()


def _model_client(config: LLMConfig) -> OpenAIChatCompletionClient:
    if not config.base_url or not config.api_key or not config.model:
        raise RuntimeError("SchemaAgent requires a configured LLM profile")
    kwargs: dict[str, Any] = {
        "model": config.model,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "timeout": float(config.timeout_seconds),
        "max_retries": config.max_retries,
        "model_info": {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.ANY,
            "structured_output": False,
            "multiple_system_messages": False,
        },
    }
    if config.temperature is not None:
        kwargs["temperature"] = config.temperature
    client_type = (
        _StreamingCreateOpenAIChatCompletionClient
        if config.stream
        else OpenAIChatCompletionClient
    )
    return client_type(**kwargs)


def _build_team(
    model_client: OpenAIChatCompletionClient,
    *,
    stream: bool,
    on_format_retry: Callable[[str], None],
) -> SelectorGroupChat:
    def wrapped(delegate: AssistantAgent, validator) -> RetryingJSONAgent:
        return RetryingJSONAgent(
            delegate,
            validator=validator,
            on_format_retry=on_format_retry,
        )

    manager = wrapped(
        AssistantAgent(
            "ManagerAgent",
            model_client=model_client,
            description="Analyzes requirements and implicit cardinalities.",
            system_message=manager_prompt(),
            model_context=source_or_recipient_context("user", "ManagerAgent"),
            model_client_stream=stream,
        ),
        require_fields("requirement_analysis"),
    )
    conceptual_designer = wrapped(
        AssistantAgent(
            "ConceptualDesignerAgent",
            model_client=model_client,
            description="Builds SchemaAgent conceptual models.",
            system_message=conceptual_designer_prompt(),
            model_client_stream=stream,
        ),
        validate_design,
    )
    conceptual_reviewer = wrapped(
        AssistantAgent(
            "ConceptualReviewerAgent",
            model_client=model_client,
            description="Reviews conceptual models using SchemaAgent's pseudocode.",
            system_message=conceptual_reviewer_prompt(),
            model_client_stream=stream,
        ),
        require_fields("Evaluation result", "Pseudocode output", "Revision suggestion"),
    )
    inner_team = RoundRobinGroupChat(
        [conceptual_designer, conceptual_reviewer],
        termination_condition=(
            FunctionalTermination(_conceptual_approval_reached)
            | MaxMessageTermination(CONCEPTUAL_INNER_MAX_MESSAGES)
        ),
    )
    society = SourceFilteringAgent(
        SocietyOfMindAgent(
            "society_of_mind",
            team=inner_team,
            model_client=model_client,
            description="SchemaAgent conceptual design and review team.",
            instruction="Return the final conceptual design produced by your team.",
            response_prompt=society_response_prompt(),
        ),
        sources={"ManagerAgent", "LogicalDesignerAgent", "ExecutionAgent"},
    )
    logical = wrapped(
        AssistantAgent(
            "LogicalDesignerAgent",
            model_client=model_client,
            description="Converts conceptual models to normalized logical schemas.",
            tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form],
            reflect_on_tool_use=True,
            max_tool_iterations=4,
            system_message=logical_designer_prompt(),
            model_client_stream=stream,
            model_context=source_or_recipient_context(
                "ManagerAgent",
                "society_of_mind",
                "LogicalDesignerAgent",
                "ExecutionAgent",
            ),
        ),
        validate_design,
    )
    qa = wrapped(
        AssistantAgent(
            "QAAgent",
            model_client=model_client,
            description="Generates independent natural-language CRUD tests.",
            system_message=qa_prompt(),
            model_client_stream=stream,
            model_context=source_context("user", "ManagerAgent", "QAAgent"),
        ),
        require_fields(
            "Insert Test case",
            "Delete Test case",
            "Query Test case",
            "Update Test case",
        ),
    )
    execution = wrapped(
        AssistantAgent(
            "ExecutionAgent",
            model_client=model_client,
            description="Intuitively validates logical schemas against QA tests.",
            system_message=execution_prompt(),
            model_client_stream=stream,
            model_context=source_or_recipient_context(
                "user",
                "ManagerAgent",
                "LogicalDesignerAgent",
                "QAAgent",
                "ExecutionAgent",
            ),
        ),
        require_fields("Evaluation result", "intuitively check output", "end"),
    )
    return SelectorGroupChat(
        [manager, society, logical, qa, execution],
        model_client=model_client,
        termination_condition=(
            FunctionalTermination(_execution_termination_reached)
            | MaxMessageTermination(OUTER_MAX_MESSAGES)
        ),
        allow_repeated_speaker=True,
        selector_func=select_next_role,
    )


def select_next_role(messages: Sequence[Event]) -> str | None:
    if not messages:
        return "ManagerAgent"
    latest = messages[-1]
    source = str(getattr(latest, "source", ""))
    payload = _try_parse(str(getattr(latest, "content", "")))
    if source == "user":
        return "ManagerAgent"
    if source == "ManagerAgent":
        return "society_of_mind"
    if source == "society_of_mind":
        return _revision_target(payload) or "LogicalDesignerAgent"
    if source == "LogicalDesignerAgent":
        return _revision_target(payload) or "QAAgent"
    if source == "QAAgent":
        return "ExecutionAgent"
    if source == "ExecutionAgent":
        return _revision_target(payload) or "LogicalDesignerAgent"
    return None


def _revision_target(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    text = " ".join(
        str(payload.get(key) or "")
        for key in ("question", "Evaluation result", "Revision suggestion")
    )
    if "ConceptualDesignerAgent" in text:
        return "society_of_mind"
    if "ManagerAgent" in text:
        return "ManagerAgent"
    if "LogicalDesignerAgent" in text:
        return "LogicalDesignerAgent"
    return None


async def _collect_team(
    team: SelectorGroupChat,
    *,
    task: str,
) -> tuple[list[Event], TaskResult | None]:
    events: list[Event] = []
    result: TaskResult | None = None
    async for item in team.run_stream(task=task):
        if isinstance(item, TaskResult):
            result = item
        else:
            events.append(item)
    return events, result


async def _collect_agent(
    agent: AssistantAgent,
    *,
    task: str,
) -> tuple[list[Event], TaskResult | None]:
    events: list[Event] = []
    result: TaskResult | None = None
    async for item in agent.run_stream(task=task):
        if isinstance(item, TaskResult):
            result = item
        else:
            events.append(item)
    return events, result


def _extract_artifacts(events: Sequence[Event]) -> dict[str, Any]:
    sources = {
        "ManagerAgent": "requirement_analysis",
        "society_of_mind": "conceptual_model",
        "LogicalDesignerAgent": "logical_model",
        "QAAgent": "qa_tests",
        "ExecutionAgent": "execution_report",
    }
    artifacts: dict[str, Any] = {}
    for event in events:
        source = str(getattr(event, "source", ""))
        if source not in sources or not isinstance(event, TextMessage):
            continue
        payload = _try_parse(event.content)
        if payload is None:
            continue
        value: Any = payload
        if source == "society_of_mind":
            wrapped_output = payload.get("output")
            value = wrapped_output if isinstance(wrapped_output, dict) else payload
            if not value:
                continue
        elif source == "LogicalDesignerAgent":
            value = payload.get("output") or {}
            if not value:
                continue
        artifacts[sources[source]] = value
    return artifacts


def _execution_approved(value: Any) -> bool:
    return isinstance(value, dict) and str(value.get("end") or "").strip() == "TERMINATE"


def _conceptual_approval_reached(messages: Sequence[Event]) -> bool:
    for message in messages:
        if not isinstance(message, TextMessage) or message.source != "ConceptualReviewerAgent":
            continue
        payload = _try_parse(message.content)
        if (
            isinstance(payload, dict)
            and str(payload.get("Evaluation result") or "").strip() == "Approve"
        ):
            return True
    return False


def _execution_termination_reached(messages: Sequence[Event]) -> bool:
    for message in messages:
        if not isinstance(message, TextMessage) or message.source != "ExecutionAgent":
            continue
        payload = _try_parse(message.content)
        if _execution_approved(payload):
            return True
    return False


def _include_in_trace(event: Event) -> bool:
    return not isinstance(event, ModelClientStreamingChunkEvent)


def _latest_text(events: Sequence[Event], source: str) -> str:
    for event in reversed(events):
        if isinstance(event, TextMessage) and event.source == source:
            return event.content
    return ""


def _try_parse(content: str) -> dict[str, Any] | None:
    try:
        return parse_json_object(content)
    except ValueError:
        return None


def _event_dict(event: Event) -> dict[str, Any]:
    return event.model_dump(mode="json")


def _model_call_count(events: Sequence[Event]) -> int:
    return sum(1 for event in events if getattr(event, "models_usage", None) is not None)
