from __future__ import annotations

from dataclasses import dataclass, field

from dbgenie.llm.client import LLMClient, LLMMessage

from .evidence import EvidenceFile
from .prompts import INTEGRITY_TEST_TEMPLATE, REQUIREMENT_AND_RULE_TEMPLATE


@dataclass(frozen=True)
class RequirementDraft:
    raw_text: str
    warnings: list[str] = field(default_factory=list)


class RequirementRuleGenerator:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate_draft(self, evidence_files: list[EvidenceFile]) -> RequirementDraft:
        if not self.llm_client.is_configured():
            return RequirementDraft(
                raw_text="",
                warnings=["llm_not_configured"],
            )
        evidence_block = self._format_evidence(evidence_files)
        response = self.llm_client.complete(
            [
                LLMMessage(role="system", content=REQUIREMENT_AND_RULE_TEMPLATE),
                LLMMessage(role="user", content=evidence_block),
            ]
        )
        return RequirementDraft(raw_text=response)

    def generate_integrity_tests(self, business_rule_text: str, schema_ddl: str) -> RequirementDraft:
        if not self.llm_client.is_configured():
            return RequirementDraft(raw_text="", warnings=["llm_not_configured"])
        response = self.llm_client.complete(
            [
                LLMMessage(role="system", content=INTEGRITY_TEST_TEMPLATE),
                LLMMessage(
                    role="user",
                    content=f"Business rule:\n{business_rule_text}\n\nReference DDL:\n{schema_ddl}",
                ),
            ]
        )
        return RequirementDraft(raw_text=response)

    @staticmethod
    def _format_evidence(evidence_files: list[EvidenceFile]) -> str:
        chunks = []
        for item in evidence_files:
            chunks.append(
                f"### {item.path} ({item.evidence_type})\n"
                f"{item.content[:4000]}"
            )
        return "\n\n".join(chunks)

