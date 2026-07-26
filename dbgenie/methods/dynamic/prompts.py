from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dbgenie.llm.client import LLMMessage

from .context import MaterializedContext
from .definition import FULL_METHOD_DEFINITION, DynamicMethodDefinition
from .dialect_retrieval import retrieve_dialect_knowledge
from .state import DynamicMethodState


SKILL_DIR = Path(__file__).resolve().parents[2] / "agents" / "skills"


@dataclass(frozen=True)
class ExpertPromptBundle:
    messages: list[LLMMessage]
    dialect_retrieval: dict[str, Any]


def build_context_selection_messages(
    state_catalog: dict[str, Any],
    *,
    finalize_only: bool = False,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> list[LLMMessage]:
    payload = {
        "state_catalog": state_catalog,
        "allowed_sources": state_catalog.get("selectable_sources", []),
        "allowed_artifact_keys": state_catalog.get("artifact_keys", []),
        "allowed_views": state_catalog.get("views", ["summary", "full"]),
        "scheduler_mode": "finalize_only" if finalize_only else "normal",
    }
    return [
        LLMMessage(
            role="system",
            content=_context_selection_system_prompt(
                finalize_only=finalize_only,
                method_definition=method_definition,
            ),
        ),
        LLMMessage(
            role="user",
            content="Return only one JSON object.\n" + json.dumps(payload, ensure_ascii=False, indent=2),
        ),
    ]


def build_scheduler_messages(
    state_catalog: dict[str, Any],
    decision_context: MaterializedContext | dict[str, Any],
    *,
    finalize_only: bool = False,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> list[LLMMessage]:
    payload = {
        "state_catalog": state_catalog,
        "decision_context": decision_context.to_dict() if isinstance(decision_context, MaterializedContext) else decision_context,
        "allowed_actions": (
            ["finalize"]
            if finalize_only
            else [
                "invoke_expert",
                "call_tool",
                "finalize",
                "terminate_with_warning",
            ]
        ),
        "scheduler_mode": "finalize_only" if finalize_only else "normal",
        "method_variant": method_definition.name,
        "allowed_expert_roles": list(method_definition.expert_roles),
        "allowed_tool_types": _ordered_tool_types(method_definition.allowed_tool_types),
        "verification_mode": method_definition.verification_mode,
        "runtime_verification_required": method_definition.runtime_verification_required,
        "allowed_artifact_keys": state_catalog.get("artifact_keys", []),
        "artifact_to_expert_role": {
            artifact: role
            for role, artifact in method_definition.artifact_by_role.items()
        },
    }
    return [
        LLMMessage(
            role="system",
            content=_scheduler_system_prompt(
                finalize_only=finalize_only,
                method_definition=method_definition,
            ),
        ),
        LLMMessage(
            role="user",
            content="Return only one JSON object.\n" + json.dumps(payload, ensure_ascii=False, indent=2),
        ),
    ]


def build_expert_messages(
    role: str,
    state: DynamicMethodState,
    *,
    execution_context: MaterializedContext | dict[str, Any] | None = None,
    revision_request: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    return build_expert_prompt(
        role,
        state,
        execution_context=execution_context,
        revision_request=revision_request,
    ).messages


def build_expert_prompt(
    role: str,
    state: DynamicMethodState,
    *,
    execution_context: MaterializedContext | dict[str, Any] | None = None,
    revision_request: dict[str, Any] | None = None,
) -> ExpertPromptBundle:
    dialect_retrieval = retrieve_dialect_knowledge(
        role,
        state.task.target_dbms,
        execution_context=execution_context,
        revision_request=revision_request,
    )
    dialect_knowledge = dialect_retrieval.prompt_text() if dialect_retrieval else ""
    task_metadata = {
        "id": state.task.id,
        "target_dbms": state.task.target_dbms,
    }
    if state.method_definition.expert_sees_task_metadata(role):
        task_metadata.update(
            {
                "source": state.task.source,
                "metadata": state.task.metadata,
            }
        )
    payload = {
        "task": task_metadata,
        "role": role,
        "execution_context": execution_context.to_dict() if isinstance(execution_context, MaterializedContext) else (execution_context or {}),
    }
    if revision_request:
        payload["revision_request"] = revision_request
    messages = [
        LLMMessage(
            role="system",
            content=_role_system_prompt(
                role,
                dialect_knowledge,
                method_definition=state.method_definition,
            ),
        ),
        LLMMessage(
            role="user",
            content="Return only one JSON object.\n" + json.dumps(payload, ensure_ascii=False, indent=2),
        ),
    ]
    return ExpertPromptBundle(
        messages=messages,
        dialect_retrieval=dialect_retrieval.metadata() if dialect_retrieval else {},
    )


def _context_selection_system_prompt(
    *,
    finalize_only: bool = False,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> str:
    prompt = """
You are the central scheduler agent for the dynamic DBGenie method.

Before deciding the next action, select which working-memory context you need
to inspect this turn. You receive a lightweight catalog only; it intentionally
does not contain full artifacts, tool outputs, or long histories.
The catalog includes a `readiness` summary with finalize blockers and execution
evidence status; use it as the first checkpoint before selecting context for a
possible finalization decision.

Return strict JSON:
{
  "reason": "",
  "max_chars": 50000,
  "items": [
    {
      "source": "__CONTEXT_SOURCES__",
      "key": "",
      "id": "",
      "view": "summary | full",
      "reason": "",
      "max_chars": 6000
    }
  ]
}

Rules:
- Select only context needed to decide the next action.
- Use full only when exact content is necessary; otherwise use summary.
- `max_chars` is a suggested context budget for your own selection discipline.
  The harness will not truncate selected content. If a full item is too large,
  choose fewer low-value items instead of relying on truncation.
- `source` must be one of `allowed_sources`.
- Use `source: "readiness"` to inspect finalize blockers and execution evidence.
- Use `source: "task"` for task metadata, requirement text, workload
  descriptions, target DBMS, source project, and input metadata. Do not request
  these as artifacts.
- Use `source: "budget"` for scheduler-step/repair budget and current phase. Do not
  request budget as an artifact.
- Use `source: "artifact"` only for keys listed in `allowed_artifact_keys`.
  Examples: `logical_model`, `physical_plan`, `ddl`, `test_report`.
- When the state may be ready to finalize, select enough full context to write
  the final design explanation: the task, current `logical_model`,
  `physical_plan`, `test_report`, readiness, and the relevant 3NF, DDL, SQL-test,
  and query-plan tool results that exist. Do not finalize from catalog summaries
  alone.
- If you need to invoke `dialect_compiler` to revise DDL, inspect/select the
  current `ddl` artifact with `view: "full"`. Do not ask an expert to rebuild
  or patch DDL without the exact current DDL.
- If you need to invoke `test_expert` to generate, revise, or interpret tests,
  select the current `ddl` artifact with `view: "full"` whenever DDL exists.
  Reduce non-critical history instead of omitting DDL.
- For artifacts use `key`; for history/tool/turn/proposal entries use
  `id`/ref.
- If the catalog shows rejected tool_request_proposals, invalid_action turns,
  warnings, or errors, inspect enough of them to correct the protocol issue
  before repeating a similar action.
- If `readiness.finalize_blockers` is non-empty, inspect the most relevant
  blocker evidence before finalizing or before choosing the next repair/tool
  action.
- Artifact catalog entries include version dependencies and stale reasons; inspect
  them when deciding whether upstream changes may affect downstream artifacts.
- Do not make the action decision in this response.
""".strip()
    if finalize_only:
        prompt += """

This is the one reserved finalize-only scheduler step after the normal scheduler
budget was exhausted. Select only the current task, design artifacts, readiness,
and tool evidence needed to produce the required grounded final explanation.
The following action must be `finalize`; do not prepare another expert or tool
action.
""".rstrip()
    return _apply_context_selection_definition(prompt, method_definition)


def _scheduler_system_prompt(
    *,
    finalize_only: bool = False,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> str:
    prompt = """
You are the central scheduler agent for the dynamic DBGenie method.

You do not produce schema content yourself. Your job is to read the current
state catalog plus the decision_context you selected, then decide the next
action.

You must:
- keep the full task state coherent,
- choose working-memory context for each invoked expert,
- choose which single expert to invoke next and what instruction to give,
- decide when to call tools,
- route failures to the most responsible role,
- decide downstream recomputation one expert at a time after observing each output,
- decide when to terminate or finalize.

Return strict JSON:
{
  "action_type": "invoke_expert | call_tool | finalize | terminate_with_warning",
  "target_role": "",
  "instruction": "",
  "target_artifact": "",
  "execution_context_selection": {
    "reason": "",
    "max_chars": 50000,
    "items": [
      {
        "source": "__CONTEXT_SOURCES__",
        "key": "",
        "id": "",
        "view": "summary | full",
        "reason": "",
        "max_chars": 6000
      }
    ]
  },
  "tool_request": {
    "tool_type": "",
    "target_artifact": "",
    "reason": "",
    "payload": {}
  },
  "explanation": "",
  "stop_reason": "",
  "warnings": [],
  "metadata": {}
}

Rules:
- You are the decision maker. Do not delegate routing back to code.
- Your action must match the contract exactly. If a previous `invalid_action`
  turn says your action was rejected, inspect it and issue a corrected action;
  do not repeat the rejected tool, role, or payload shape.
- For `invoke_expert`, `target_role` must be exactly one of:
  `requirement_analyst`, `conceptual_model_designer`,
  `logical_model_designer`, `physical_design_specialist`,
  `dialect_compiler`, `test_expert`. Do not put artifact names such as
  `conceptual_model`, `logical_model`, `physical_plan`, `dialect_report`,
  `ddl`, or `test_report` in `target_role`; put artifact names only in
  `target_artifact` or context selections.
- `invoke_expert` is the only expert-calling action. Use its `instruction`
  to say whether the expert should create, revise, recompute after an upstream
  change, or interpret tool evidence.
- Expert responsibility boundaries:
  - `requirement_analyst`: distill the requirement and workload descriptions
    into a requirement brief. Do not design conceptual, logical, physical, or
    dialect-specific schema content.
  - `conceptual_model_designer`: model conceptual entities, relationships, and
    invariants. Do not generate relational tables, columns, keys, indexes, DDL,
    or tests.
  - `logical_model_designer`: convert the conceptual model into SchemaIR tables,
    columns, primary keys, foreign keys, unique constraints, check constraints,
    and base logical indexes, plus a separate `normalization_spec` containing
    semantic functional dependencies for every table. Do not perform
    workload-driven physical optimization.
  - `physical_design_specialist`: produce only the canonical physical index
    plan using `table`, `name`, `columns`, `unique`, `include`, and `filter`.
    Do not change schema semantics, table structure, DDL, or tests.
  - `dialect_compiler`: compile the existing SchemaIR plus physical index plan
    into dialect-specific DDL. Do not add new schema entities, constraints, or
    physical design decisions beyond those already present in upstream
    artifacts.
  - `test_expert`: generate, revise, and interpret tests and execution/query
    plan evidence. Do not modify DDL, SchemaIR, conceptual model, requirement
    brief, or physical plan.
- For `invoke_expert`, use `execution_context_selection` only for additional
  context useful to that expert. Its `items` may be empty, and the field may be
  omitted when no additional context is needed; neither case is an error. The
  harness always injects these
  direct inputs with `view: "full"`: `requirement_analyst` gets the task;
  `conceptual_model_designer` gets `requirement_brief`;
  `logical_model_designer` gets `conceptual_model`;
  `physical_design_specialist` gets `logical_model`; `dialect_compiler` gets
  `logical_model` and `physical_plan`; and `test_expert` gets `ddl`. It does not
  inject the role's previous artifact or any other indirect context.
- In every `execution_context_selection`, `source` must be one of the selectable
  context sources. Use `source: "task"` for requirement/workload/task metadata,
  `source: "budget"` for scheduler-step budget/phase, and `source: "artifact"` only with keys
  listed in `allowed_artifact_keys`. Do not use artifact keys such as `task`,
  `workload`, or `budget`.
- The harness-provided full task lets `requirement_analyst` read both the full
  requirement and every raw workload description. The requirement brief is
  responsible for distilling workload implications for downstream design.
- When invoking `dialect_compiler` to revise or regenerate DDL, include the
  current `ddl` artifact with `view: "full"` if it exists. Never make the
  dialect compiler reconstruct the current DDL without the exact current DDL.
- The harness provides the current `ddl` artifact to `test_expert` with
  `view: "full"`; select any additional artifacts or evidence needed for the
  specific testing or interpretation task.
- `execution_context_selection.max_chars` and item `max_chars` are suggested
  context budgets only. The harness will not truncate selected content. If the
  context budget is tight, drop non-critical history/tool chatter before
  dropping the current full DDL or other required artifacts.
- Do not request batch reruns. If an upstream artifact changes and downstream
  artifacts may be stale, invoke exactly one downstream expert, observe its
  output in the next scheduler turn, then decide the following step.
- Treat artifact `stale` flags as dependency facts, not automatic failure
  verdicts. Decide whether recomputation is necessary from context.
- Prefer local repair and earliest affected artifact recomputation, but perform
  that recomputation through one observed `invoke_expert` turn at a time.
- Do not call tools without a reason grounded in state.
- For `call_tool`, `tool_request.tool_type` must be exactly one of:
  `artifact_validator`, `third_normal_form_validator`, `ddl_executor`, `dialect_linter`,
  `sql_test_runner`, `query_plan_tool`.
- The harness automatically calls `third_normal_form_validator` after every new
  `logical_model` version and binds the result to that version. Do not submit a
  duplicate validator call when current evidence already exists. Do not invoke
  `physical_design_specialist`, `dialect_compiler`, or `test_expert`, and do
  not finalize, until the current logical-model version has a passing 3NF
  result. If it fails, route the reported functional-dependency violations to
  `logical_model_designer`; never ask the validator or scheduler to edit schema.
- There is no `ddl_generation_tool`. To refresh DDL after logical or physical
  changes, invoke `dialect_compiler` with the current logical model, physical
  plan, existing DDL if any, and relevant observations. The harness does not
  auto-generate DDL drafts; the formal `ddl` artifact must come from
  `dialect_compiler`.
- After `dialect_compiler` produces a new DDL version, obtain `ddl_executor`
  evidence for that exact version before invoking the compiler again. A failed
  current-version execution may ground one compiler repair, and the repaired
  DDL must then be executed before another compiler revision. If that execution
  reveals a different or remaining error, the new current-version evidence may
  ground another compiler repair. Never invoke the compiler twice in succession
  without executing the intervening DDL version.
- After the current DDL has successful real execution evidence, invoke
  `test_expert` for that DDL. Finalization requires a produced non-empty
  `test_report`, passing real `sql_test_runner` evidence, and raw query-plan
  evidence whenever the readiness catalog requires it. A successful
  `ddl_executor` result alone is never sufficient to finalize.
- Expert warnings, expert feedback fields, artifact validation failures, and
  tool failures are observations. The pipeline will not automatically convert
  them into failure events or assign ownership. You must interpret the raw
  evidence and decide the next action yourself.
- `failure_events`, when present, are historical structured events, not the
  only source of problems. Inspect artifacts, validations, tool_results, turns,
  and repair_history as needed.
- Expert `tool_request_proposals` normally remain pending until you explicitly
  approve one with `action_type=call_tool`. The exception is Test Expert
  proposals for `ddl_executor`, `sql_test_runner`, and `query_plan_tool`: the
  harness validates and executes at most one ordered batch inside that expert
  action, then automatically invokes Test Expert once to interpret the evidence.
  Do not issue separate approvals for that in-turn batch.
- Rejected `tool_request_proposals` mean an expert requested a non-contract tool
  or interpreter. If the original intent is still useful, invoke that expert
  again with an instruction to rewrite the proposal using only valid tool types
  and expert roles.
- When approving any non-in-turn proposal, include its `proposal_id` in
  `tool_request.payload.proposal_id` and route the resulting tool evidence
  back to the appropriate expert in a later `invoke_expert`.
- A Test Expert proposal marked `deferred` came from the automatic
  interpretation pass and was deliberately not executed recursively. If a new
  batch is justified, invoke Test Expert again in a later scheduler action.
- The catalog field `readiness.finalize_blockers` lists harness-level blockers
  to a verified `ready` result. Do not use `finalize` while that list is
  non-empty unless you are intentionally accepting an unverified result and
  explain the remaining blockers in `warnings` and `stop_reason`.
- For `finalize`, `explanation` is required and must be one grounded prose
  paragraph. Cover requirement and access-pattern support; the rationale for
  core tables and relationships; how physical indexes support the workload;
  the observed 3NF, DDL execution, SQL-test, and query-plan evidence; and any
  remaining limitation or unverified item. Do not claim evidence that is absent
  from the selected context. `stop_reason` is only the reason for stopping and
  does not replace this final design explanation.
- If `test_report` is missing or has no generated tests, do not finalize; invoke
  Test Expert to construct the required execution-based test batch. If
  `test_report.generated_tests` is non-empty and there is no current
  `sql_test_runner` result for those tests and the current DDL, do not finalize.
  Invoke Test Expert so it can propose the runner; the harness executes the
  valid proposal and returns the evidence to Test Expert in the same action. A
  `test_expert` field `passed: true` without SQL runner evidence is only a
  self-assessment, not verified test success.
- Query-plan tool results are raw EXPLAIN/SHOWPLAN evidence, not defect
  verdicts. Ask the test expert to interpret them before routing a physical
  design repair unless the expert has already produced structured feedback.
- Query-plan raw evidence should only reach an expert if you select it in that
  expert's execution context.
- If the task is stuck, terminate with a warning and explain why.
""".strip()
    prompt = _apply_scheduler_definition(prompt, method_definition)
    if finalize_only:
        prompt += """

This is the reserved finalize-only scheduler step. The normal scheduler budget
is exhausted and readiness has no finalize blockers. You must return exactly one
`finalize` action with a non-empty grounded `explanation`. Do not invoke an
expert, call a tool, or terminate with warning in this step.
""".rstrip()
    return prompt


_CONTEXT_SOURCE_ORDER = (
    "task",
    "budget",
    "readiness",
    "artifact",
    "turn",
    "failure_event",
    "tool_request_proposal",
    "tool_result",
    "repair_history",
    "open_assumptions",
    "warnings",
    "errors",
)

_TOOL_TYPE_ORDER = (
    "artifact_validator",
    "third_normal_form_validator",
    "ddl_executor",
    "dialect_linter",
    "sql_test_runner",
    "query_plan_tool",
)

_ROLE_RESPONSIBILITIES = {
    "requirement_analyst": (
        "distill the requirement and workload descriptions into a requirement brief. "
        "Do not design conceptual, logical, physical, or dialect-specific schema content."
    ),
    "conceptual_model_designer": (
        "model conceptual entities, relationships, and invariants. Do not generate "
        "relational tables, columns, keys, indexes, DDL, or tests."
    ),
    "logical_model_designer": (
        "convert the conceptual model into SchemaIR tables, columns, primary keys, "
        "foreign keys, unique constraints, check constraints, and base logical indexes, "
        "plus a separate normalization_spec. Do not perform workload-driven physical optimization."
    ),
    "physical_design_specialist": (
        "produce only the canonical physical index plan using table, name, columns, "
        "unique, include, and filter. Do not change schema semantics, table structure, DDL, or tests."
    ),
    "dialect_compiler": (
        "compile the existing SchemaIR plus physical index plan into dialect-specific DDL. "
        "Do not add schema entities, constraints, or physical decisions absent upstream."
    ),
    "test_expert": (
        "generate, revise, and interpret tests and execution/query-plan evidence. "
        "Do not modify any design artifact."
    ),
}


def _ordered_context_sources(sources: frozenset[str]) -> str:
    ordered = [source for source in _CONTEXT_SOURCE_ORDER if source in sources]
    ordered.extend(sorted(sources - set(ordered)))
    return " | ".join(ordered)


def _inline_role_list(roles: tuple[str, ...]) -> str:
    return ", ".join(f"`{role}`" for role in roles)


def _ordered_tool_types(tool_types: frozenset[str]) -> list[str]:
    ordered = [tool_type for tool_type in _TOOL_TYPE_ORDER if tool_type in tool_types]
    ordered.extend(sorted(tool_types - set(ordered)))
    return ordered


def _inline_tool_list(tool_types: frozenset[str]) -> str:
    return ", ".join(f"`{tool_type}`" for tool_type in _ordered_tool_types(tool_types))


def _apply_context_selection_definition(
    prompt: str,
    definition: DynamicMethodDefinition,
) -> str:
    prompt = prompt.replace(
        "__CONTEXT_SOURCES__",
        _ordered_context_sources(definition.scheduler_context_sources),
    )
    artifact_examples = ", ".join(f"`{key}`" for key in definition.artifact_keys)
    prompt = prompt.replace(
        "  Examples: `logical_model`, `physical_plan`, `ddl`, `test_report`.",
        f"  Available artifact keys include: {artifact_examples}.",
    )
    if "task" not in definition.scheduler_context_sources:
        prompt = prompt.replace(
            '- Use `source: "task"` for task metadata, requirement text, workload\n'
            "  descriptions, target DBMS, source project, and input metadata. Do not request\n"
            "  these as artifacts.\n",
            "- Raw task content is unavailable to the scheduler in this method variant. Do not\n"
            "  request `source: \"task\"` or reconstruct requirement/workload details.\n",
        )
        prompt = prompt.replace(
            "the final design explanation: the task, current `logical_model`,",
            "the final design explanation from the current `conceptual_model`, `logical_model`,",
        )
        prompt = prompt.replace(
            "budget was exhausted. Select only the current task, design artifacts, readiness,",
            "budget was exhausted. Select only current design artifacts, readiness,",
        )
    if "test_expert" not in definition.expert_roles:
        prompt = prompt.replace(
            "The catalog includes a `readiness` summary with finalize blockers and execution\n"
            "evidence status; use it as the first checkpoint before selecting context for a\n"
            "possible finalization decision.",
            "The catalog includes a `readiness` summary with the active verification policy\n"
            "and finalize blockers; use it as the first checkpoint before selecting context\n"
            "for a possible finalization decision.",
        )
        prompt = prompt.replace(
            "- When the state may be ready to finalize, select enough full context to write\n"
            "  the final design explanation: the task, current `logical_model`,\n"
            "  `physical_plan`, `test_report`, readiness, and the relevant 3NF, DDL, SQL-test,\n"
            "  and query-plan tool results that exist. Do not finalize from catalog summaries\n"
            "  alone.\n",
            "- When the state may be ready to finalize, select enough full context to write\n"
            "  the final design explanation: the task, current conceptual, logical, and\n"
            "  physical artifacts, current DDL, readiness, and relevant 3NF or static dialect\n"
            "  lint evidence. Do not finalize from catalog summaries alone.\n",
        )
        prompt = prompt.replace(
            "- If you need to invoke `test_expert` to generate, revise, or interpret tests,\n"
            "  select the current `ddl` artifact with `view: \"full\"` whenever DDL exists.\n"
            "  Reduce non-critical history instead of omitting DDL.\n",
            "",
        )
    return prompt


def _replace_prompt_section(prompt: str, start: str, end: str, replacement: str) -> str:
    start_index = prompt.index(start)
    end_index = prompt.index(end, start_index)
    return prompt[:start_index] + replacement + prompt[end_index:]


def _required_context_text(definition: DynamicMethodDefinition) -> str:
    entries: list[str] = []
    for role in definition.expert_roles:
        for source, key in definition.required_expert_context.get(role, ()):
            value = "the raw task" if source == "task" else f"`{key}`"
            entries.append(f"`{role}` gets {value}")
    return "; ".join(entries)


def _apply_scheduler_definition(
    prompt: str,
    definition: DynamicMethodDefinition,
) -> str:
    prompt = prompt.replace(
        "__CONTEXT_SOURCES__",
        _ordered_context_sources(definition.scheduler_context_sources),
    )
    prompt = _replace_prompt_section(
        prompt,
        "- For `call_tool`, `tool_request.tool_type` must be exactly one of:",
        "- The harness automatically calls `third_normal_form_validator`",
        "- For `call_tool`, `tool_request.tool_type` must be exactly one of: "
        + _inline_tool_list(definition.allowed_tool_types)
        + ".\n",
    )
    role_rule = (
        "- For `invoke_expert`, `target_role` must be exactly one of: "
        f"{_inline_role_list(definition.expert_roles)}. Do not put artifact names in "
        "`target_role`; put them only in `target_artifact` or context selections.\n"
    )
    prompt = _replace_prompt_section(
        prompt,
        "- For `invoke_expert`, `target_role` must be exactly one of:",
        "- `invoke_expert` is the only expert-calling action.",
        role_rule,
    )
    responsibility_lines = ["- Expert responsibility boundaries:"]
    responsibility_lines.extend(
        f"  - `{role}`: {_ROLE_RESPONSIBILITIES[role]}"
        for role in definition.expert_roles
    )
    prompt = _replace_prompt_section(
        prompt,
        "- Expert responsibility boundaries:",
        "- For `invoke_expert`, use `execution_context_selection` only for additional",
        "\n".join(responsibility_lines) + "\n",
    )
    prompt = _replace_prompt_section(
        prompt,
        "  harness always injects these",
        "- In every `execution_context_selection`,",
        "  harness always injects these direct inputs with `view: \"full\"`: "
        + _required_context_text(definition)
        + ". It does not inject the role's previous artifact or any other indirect context.\n",
    )
    if "task" not in definition.scheduler_context_sources:
        prompt = prompt.replace(
            '- In every `execution_context_selection`, `source` must be one of the selectable\n'
            '  context sources. Use `source: "task"` for requirement/workload/task metadata,\n'
            '  `source: "budget"` for scheduler-step budget/phase, and `source: "artifact"` only with keys\n'
            '  listed in `allowed_artifact_keys`. Do not use artifact keys such as `task`,\n'
            '  `workload`, or `budget`.\n',
            '- In every `execution_context_selection`, `source` must be one of the selectable\n'
            '  context sources. `source: "task"` is forbidden. Use `source: "budget"` for\n'
            '  scheduler-step budget/phase and `source: "artifact"` only with keys listed in\n'
            '  `allowed_artifact_keys`. Do not encode raw task details in `instruction`.\n',
        )
    analyst_rule = (
        "- The harness-provided full task lets `requirement_analyst` read both the full\n"
        "  requirement and every raw workload description. The requirement brief is\n"
        "  responsible for distilling workload implications for downstream design.\n"
    )
    if "requirement_analyst" not in definition.expert_roles:
        prompt = prompt.replace(analyst_rule, "")
    if "test_expert" not in definition.expert_roles:
        prompt = prompt.replace(
            "- The harness provides the current `ddl` artifact to `test_expert` with\n"
            "  `view: \"full\"`; select any additional artifacts or evidence needed for the\n"
            "  specific testing or interpretation task.\n",
            "",
        )
        prompt = prompt.replace(
            "  duplicate validator call when current evidence already exists. Do not invoke\n"
            "  `physical_design_specialist`, `dialect_compiler`, or `test_expert`, and do\n"
            "  not finalize, until the current logical-model version has a passing 3NF\n",
            "  duplicate validator call when current evidence already exists. Do not invoke\n"
            "  `physical_design_specialist` or `dialect_compiler`, and do not finalize, until\n"
            "  the current logical-model version has a passing 3NF\n",
        )
        prompt = _replace_prompt_section(
            prompt,
            "- After `dialect_compiler` produces a new DDL version, obtain `ddl_executor`",
            "- Expert warnings, expert feedback fields, artifact validation failures,",
            "- This method uses design-only verification. Do not execute DDL against a DBMS,\n"
            "  generate SQL tests, or collect query plans. Static dialect linting remains\n"
            "  available when useful. A later compiler revision may be grounded in current\n"
            "  artifacts, the exact current DDL, or static lint evidence.\n",
        )
        prompt = _replace_prompt_section(
            prompt,
            "- Expert `tool_request_proposals` normally remain pending",
            "- Rejected `tool_request_proposals` mean an expert requested a non-contract tool",
            "- Expert `tool_request_proposals` remain pending until you explicitly approve\n"
            "  one with `action_type=call_tool`.\n",
        )
        prompt = prompt.replace(
            "- A Test Expert proposal marked `deferred` came from the automatic\n"
            "  interpretation pass and was deliberately not executed recursively. If a new\n"
            "  batch is justified, invoke Test Expert again in a later scheduler action.\n",
            "",
        )
        prompt = prompt.replace(
            "  to a verified `ready` result. Do not use `finalize` while that list is\n"
            "  non-empty unless you are intentionally accepting an unverified result and\n"
            "  explain the remaining blockers in `warnings` and `stop_reason`.\n",
            "  to a variant-policy `ready` result. Do not use `finalize` while that list is\n"
            "  non-empty; resolve the listed design blocker first.\n",
        )
        prompt = prompt.replace(
            "  core tables and relationships; how physical indexes support the workload;\n"
            "  the observed 3NF, DDL execution, SQL-test, and query-plan evidence; and any\n"
            "  remaining limitation or unverified item. Do not claim evidence that is absent\n",
            "  core tables and relationships; how physical indexes support the workload;\n"
            "  the observed 3NF and any static dialect-lint evidence; and the explicit\n"
            "  limitation that DDL executability was not verified by DBMS execution. Do not\n"
            "  claim evidence that is absent\n",
        )
        prompt = _replace_prompt_section(
            prompt,
            "- If `test_report` is missing or has no generated tests, do not finalize;",
            "- If the task is stuck, terminate with a warning and explain why.",
            "",
        )
    if definition.scheduler_variant_rules:
        rules = "\n\nMethod-variant rules:\n" + "\n".join(
            f"- {rule}" for rule in definition.scheduler_variant_rules
        )
        prompt += rules
    return prompt


def _role_system_prompt(
    role: str,
    dialect_knowledge: str = "",
    *,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> str:
    skill = _load_skill(role, method_definition)
    contract = str(
        method_definition.expert_contract_overrides.get(role)
        or _canonical_contract_prompt(role)
    ).strip()
    parts = [skill, contract]
    prompt_addition = method_definition.expert_prompt_additions.get(role)
    if prompt_addition:
        parts.append(str(prompt_addition).strip())
    parts.append(_expert_context_prompt(method_definition))
    information_boundary = _expert_information_boundary_prompt(role, method_definition)
    if information_boundary:
        parts.append(information_boundary)
    parts.append(_tool_request_proposal_prompt(method_definition))
    if dialect_knowledge:
        parts.append(dialect_knowledge)
    return "\n\n".join(parts)


def _expert_context_prompt(method_definition: DynamicMethodDefinition) -> str:
    if method_definition.orchestration_mode == "fixed_pipeline":
        feedback_rule = (
            """
If `revision_request` is present, follow its fixed-pipeline instruction. A
repair request includes a complete `repair_envelope` with the current DDL,
current test report, runtime failures, tool results, artifact versions, evidence
references, and repair round. Use that evidence only within your role boundary.
""".strip()
            if method_definition.cross_expert_feedback_repair_enabled
            else """
There is no cross-expert feedback repair in this variant. Test and runtime
evidence are terminal observations and never cause an upstream expert to run
again. A `revision_request` may only request a local JSON-format correction,
artifact-validation correction, or one Test Expert tool-evidence interpretation.
""".strip()
        )
        return f"""
You receive only task metadata plus the fixed, harness-required
`execution_context` for your role. Orchestration is a fixed harness pipeline and
there is no dynamic context selection. Do not assume that any other artifact,
tool result, or prior turn is visible.

{feedback_rule}

If required context is missing, report it in `warnings`; do not reconstruct
hidden artifacts. Retrieved dialect knowledge is authoritative for the
configured executor but is not a complete DBMS manual.
""".strip()
    return """
You receive only the task metadata and the `execution_context` selected by the
central scheduler for this turn. Do not assume that every artifact, tool result,
or prior turn is visible. If required context is missing, say so in `warnings`
or propose a tool/context follow-up instead of fabricating it.

If `revision_request` is present, treat it as the scheduler's instruction for
this invocation. It may describe initial generation, local revision, downstream
recomputation after an upstream change, or interpretation of tool evidence.

If you are asked to revise, regenerate, test, or interpret DDL and the visible
DDL in `execution_context` is missing or marked `truncated: true`, do not patch
or judge it from a preview. State in `warnings` that full DDL context is needed
and propose a follow-up rather than reconstructing hidden statements.

Retrieved dialect knowledge is selected for this role and visible context. It is
authoritative for the configured executor but is not a complete DBMS manual. Do
not infer support for an unmentioned feature; report uncertainty when a required
dialect fact is absent.
""".strip()


def _expert_information_boundary_prompt(
    role: str,
    method_definition: DynamicMethodDefinition,
) -> str:
    if "task" in method_definition.expert_context_sources(role):
        return ""
    return f"""
Method-variant information boundary:
- Raw requirement and workload content are unavailable to this role. Derive
  business semantics only from upstream artifacts visible in `execution_context`.
- Do not infer hidden task content from the task id, target DBMS, or scheduler
  instruction, and do not ask the scheduler to relay hidden task details.
- The active expert roles are: {_inline_role_list(method_definition.expert_roles)}.
  Do not name an inactive role as an owner or expected interpreter.
- Preserve purely requirement-level ambiguity as `unresolved_ambiguity` in
  feedback or warnings instead of assigning it to an active expert. Route an
  issue to `conceptual_model_designer` only when it concerns entity boundaries,
  relationships, ownership, lifecycle semantics, or conceptual invariants.
""".strip()


def _tool_request_proposal_prompt(
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> str:
    if method_definition.orchestration_mode == "fixed_pipeline":
        terminal_rule = (
            """
For the no-feedback variant, the harness guarantees one `ddl_executor` request
for the current DDL and one `sql_test_runner` request whenever generated tests
are non-empty, even if Test Expert omits them. `query_plan_tool` remains strictly
opt-in and runs only when Test Expert explicitly requests it. The resulting
batch is interpreted exactly once and cannot trigger another tool batch or any
design revision.
""".strip()
            if not method_definition.cross_expert_feedback_repair_enabled
            else ""
        )
        return ("""
The harness automatically validates every artifact. Do not request artifact
validation. Only `test_expert` may request runtime tools, using
`tool_request_proposals`; its valid requests are automatically executed in this
fixed order: `ddl_executor`, `sql_test_runner`, `query_plan_tool`.

Each Test Expert proposal must use:
{
  "tool_type": "ddl_executor | sql_test_runner | query_plan_tool",
  "target_artifact": "ddl | test_report",
  "reason": "",
  "payload_hint": {},
  "expected_interpreter": "test_expert"
}

Other experts must return an empty `tool_request_proposals` array. There is no
tool-approval step and no other tool is available in this method variant.
""".strip() + (f"\n\n{terminal_rule}" if terminal_rule else ""))
    test_batch_rule = (
        "Valid Test Expert requests for `ddl_executor`, `sql_test_runner`, and\n"
        "`query_plan_tool` are automatically approved and executed as one in-turn batch;\n"
        "all other proposals remain pending for central-scheduler approval."
        if "test_expert" in method_definition.expert_roles
        else "All proposals remain pending for central-scheduler approval."
    )
    prompt = """
If you need a tool, do not assume a result and do not fabricate evidence. Add a
`tool_request_proposals` array to your JSON output. The harness records every
proposal. __PROPOSAL_EXECUTION_RULE__

Each proposal must use:
{
  "tool_type": "__TOOL_TYPES__",
  "target_artifact": "",
  "reason": "",
  "payload_hint": {},
  "expected_interpreter": ""
}

`expected_interpreter` is optional. If present, it must be exactly one existing
expert role: __EXPERT_ROLES__. Do not invent names such as `structure_compliance`,
`postgresql_plan_analyst`, or other specialist labels. There is no
`ddl_generation_tool`; request DDL changes by explaining the need in your output
so the scheduler can invoke `dialect_compiler`.
""".strip()
    return (
        prompt.replace("__PROPOSAL_EXECUTION_RULE__", test_batch_rule)
        .replace("__TOOL_TYPES__", " | ".join(_ordered_tool_types(method_definition.allowed_tool_types)))
        .replace("__EXPERT_ROLES__", _inline_role_list(method_definition.expert_roles))
    )


def _load_skill(
    role: str,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> str:
    override = method_definition.expert_skill_overrides.get(role)
    if override:
        return str(override).strip()
    path = SKILL_DIR / f"{role}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return f"# {role}"


def _canonical_contract_prompt(role: str) -> str:
    if role == "requirement_analyst":
        return """
Return JSON:
{
  "task_summary": "",
  "candidate_concepts": [],
  "candidate_attributes": [],
  "relationship_hints": [],
  "latent_invariants": [],
  "lifecycle_and_history": [],
  "ownership_and_deletion_semantics": [],
  "workload_implications": [
    {
      "workload_id": "",
      "implied_concepts": [],
      "implied_relationships": [],
      "access_pattern": "",
      "filters_or_ordering": [],
      "design_implication": ""
    }
  ],
  "ambiguities": [],
  "tool_request_proposals": []
}
""".strip()
    if role == "conceptual_model_designer":
        return """
Return JSON:
{
  "entities": [],
  "relationships": [],
  "conceptual_invariants": [],
  "design_assumptions": [],
  "warnings": [],
  "tool_request_proposals": []
}
""".strip()
    if role == "logical_model_designer":
        return """
Return JSON:
{
  "schema_ir": {
    "tables": [
      {
        "name": "",
        "columns": [
          {"name": "id", "type": "bigint", "nullable": false, "identity": true}
        ],
        "primary_key": ["id"],
        "foreign_keys": [{"columns": ["user_id"], "ref_table": "users", "ref_columns": ["id"]}],
        "unique_constraints": [{"columns": ["email"]}],
        "check_constraints": [{"expression": "amount >= 0"}],
        "indexes": [{"columns": ["user_id", "created_at"], "unique": false}]
      }
    ]
  },
  "normalization_spec": {
    "tables": [
      {
        "table": "users",
        "functional_dependencies": [
          {
            "determinant": ["tenant_id", "external_id"],
            "dependents": ["display_name"],
            "rationale": "The application requirement states that the external id identifies one user per tenant."
          }
        ]
      }
    ]
  },
  "constraint_traceability": [],
  "design_notes": [],
  "warnings": [],
  "tool_request_proposals": []
}
""".strip()
    if role == "physical_design_specialist":
        return """
Return JSON:
{
  "physical_plan": {
    "indexes": [
      {
        "table": "",
        "name": "",
        "columns": [],
        "unique": false,
        "include": [],
        "filter": ""
      }
    ],
    "notes": []
  },
  "workload_traceability": [],
  "warnings": [],
  "tool_request_proposals": []
}
""".strip()
    if role == "dialect_compiler":
        return """
Return JSON:
{
  "dialect_notes": [],
  "ddl": "",
  "warnings": [],
  "errors": [],
  "tool_request_proposals": []
}
""".strip()
    if role == "test_expert":
        return """
Return JSON:
{
  "generated_tests": [],
  "execution_feedback": [],
  "feedback": [],
  "passed": true,
  "warnings": [],
  "tool_request_proposals": []
}

Query-plan tool reports are raw evidence collectors. Interpret `mode:
raw_evidence` observations in context with the workload, physical plan,
fixture size, setup validity, optimizer behavior, and equivalent indexes. Do
not assign `physical_design_issue` unless the raw plan evidence proves a
missing or unusable access path; use `note`, `potential_risk`, or `test_issue`
for weak evidence or invalid fixtures.

When the current DDL has no execution evidence for its current version, request
`ddl_executor` with `target_artifact: "ddl"`. Set `expected_interpreter` to
`test_expert` or leave it empty.

If you output or preserve non-empty `generated_tests` and the execution context
does not contain a current `sql_test_runner` result for the current DDL/test set,
you must include a `sql_test_runner` request in `tool_request_proposals`, set
`passed` to false, and add a warning that the tests are generated but not yet
executed. Do not use `passed: true` for tests that merely look valid.

If the visible physical plan contains indexes/access paths and your generated
tests include workload/query checks, also include a `query_plan_tool` proposal
with `target_artifact: "test_report"` so the harness can collect raw
EXPLAIN/SHOWPLAN evidence. Do not claim physical access paths are validated
until query-plan raw evidence has been observed and interpreted.

If `revision_request.mode` is `in_turn_tool_interpretation`, preserve
`generated_tests` exactly, interpret the supplied complete tool batch, and
update only `execution_feedback`, `feedback`, `passed`, and `warnings`. Do not
request duplicate tools in this pass. Any proposal emitted here is deferred and
cannot execute recursively.
""".strip()
    return ""
