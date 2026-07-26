from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkloadDescription:
    id: str
    description: str
    source: str = ""
    evidence_file: str = ""

    @classmethod
    def from_any(cls, value: Any, index: int) -> "WorkloadDescription":
        if isinstance(value, str):
            return cls(id=f"w{index}", description=value)
        if isinstance(value, dict):
            return cls(
                id=str(value.get("id") or f"w{index}"),
                description=str(value.get("description") or value.get("query") or ""),
                source=str(value.get("source") or value.get("source_type") or ""),
                evidence_file=str(value.get("evidence_file") or ""),
            )
        return cls(id=f"w{index}", description=str(value))

    def to_dict(self) -> dict[str, Any]:
        payload = {"id": self.id, "description": self.description}
        if self.source:
            payload["source"] = self.source
        if self.evidence_file:
            payload["evidence_file"] = self.evidence_file
        return payload


@dataclass(frozen=True)
class AgentTaskInput:
    id: str
    requirement: str
    workload: list[WorkloadDescription]
    target_dbms: str
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "requirement": self.requirement,
            "workload": [item.to_dict() for item in self.workload],
            "target_dbms": self.target_dbms,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class AgentTurn:
    index: int
    role: str
    status: str
    prompt_messages: list[dict[str, str]] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "role": self.role,
            "status": self.status,
            "prompt_messages": self.prompt_messages,
            "output": self.output,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class SharedMemoryMessage:
    index: int
    speaker: str
    kind: str
    content: str
    artifact_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "index": self.index,
            "speaker": self.speaker,
            "kind": self.kind,
            "content": self.content,
        }
        if self.artifact_key:
            payload["artifact_key"] = self.artifact_key
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass
class BlackboardState:
    task: AgentTaskInput
    artifacts: dict[str, Any] = field(default_factory=dict)
    turns: list[AgentTurn] = field(default_factory=list)
    shared_messages: list[SharedMemoryMessage] = field(default_factory=list)
    private_contexts: dict[str, dict[str, Any]] = field(default_factory=dict)
    repair_history: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_turn(self, turn: AgentTurn) -> None:
        self.turns.append(turn)

    def add_shared_message(self, message: SharedMemoryMessage) -> None:
        self.shared_messages.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.to_dict(),
            "artifacts": self.artifacts,
            "turns": [turn.to_dict() for turn in self.turns],
            "shared_messages": [
                message.to_dict() for message in self.shared_messages
            ],
            "private_contexts": self.private_contexts,
            "repair_history": self.repair_history,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class AgentRunResult:
    task_id: str
    status: str
    final_ddl: str = ""
    llm: dict[str, Any] = field(default_factory=dict)
    blackboard: BlackboardState | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    run_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "final_ddl": self.final_ddl,
            "llm": self.llm,
            "blackboard": self.blackboard.to_dict() if self.blackboard else {},
            "warnings": self.warnings,
            "errors": self.errors,
            "run_path": self.run_path,
        }
