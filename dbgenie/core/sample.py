from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema_ir import SchemaIR


@dataclass(frozen=True)
class BusinessRule:
    id: str
    description: str
    enforcement: str = "unclear"
    evidence_file: str = ""
    evidence_type: str = ""
    testable: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BusinessRule":
        return cls(
            id=str(data["id"]),
            description=str(data.get("description", "")),
            enforcement=str(data.get("enforcement", "unclear")),
            evidence_file=str(data.get("evidence_file", "")),
            evidence_type=str(data.get("evidence_type", "")),
            testable=bool(data.get("testable", True)),
        )


@dataclass(frozen=True)
class WorkloadItem:
    id: str
    description: str
    source: str = ""
    evidence_file: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkloadItem":
        return cls(
            id=str(data["id"]),
            description=str(data.get("description", "")),
            source=str(data.get("source", "")),
            evidence_file=str(data.get("evidence_file", "")),
        )


@dataclass(frozen=True)
class IntegrityTest:
    id: str
    business_rule_id: str
    name: str = ""
    setup_sql: list[str] = field(default_factory=list)
    positive_sql: list[str] = field(default_factory=list)
    negative_sql: list[str] = field(default_factory=list)
    expected_negative_result: str = "constraint_violation"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntegrityTest":
        return cls(
            id=str(data["id"]),
            business_rule_id=str(data.get("business_rule_id", "")),
            name=str(data.get("name", "")),
            setup_sql=list(data.get("setup_sql", [])),
            positive_sql=list(data.get("positive_sql", [])),
            negative_sql=list(data.get("negative_sql", [])),
            expected_negative_result=str(
                data.get("expected_negative_result", "constraint_violation")
            ),
        )


@dataclass(frozen=True)
class WorkloadTest:
    id: str
    workload_id: str
    sql: str
    expected_result: str = ""
    expected_physical_support: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkloadTest":
        return cls(
            id=str(data["id"]),
            workload_id=str(data.get("workload_id", "")),
            sql=str(data.get("sql", "")),
            expected_result=str(data.get("expected_result", "")),
            expected_physical_support=list(data.get("expected_physical_support", [])),
        )


@dataclass(frozen=True)
class Reference:
    canonical_dialect: str
    ddl_by_dialect: dict[str, str]
    schema_ir: SchemaIR
    acceptable_alternatives: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Reference":
        return cls(
            canonical_dialect=str(data.get("canonical_dialect", "")),
            ddl_by_dialect=dict(data.get("ddl_by_dialect", {})),
            schema_ir=SchemaIR.from_dict(data.get("schema_ir", {})),
            acceptable_alternatives=list(data.get("acceptable_alternatives", [])),
        )


@dataclass(frozen=True)
class SampleTests:
    integrity: list[IntegrityTest] = field(default_factory=list)
    workload: list[WorkloadTest] = field(default_factory=list)
    migration: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SampleTests":
        return cls(
            integrity=[IntegrityTest.from_dict(item) for item in data.get("integrity", [])],
            workload=[WorkloadTest.from_dict(item) for item in data.get("workload", [])],
            migration=list(data.get("migration", [])),
        )


@dataclass(frozen=True)
class BenchmarkSample:
    id: str
    source: str
    domain: str
    target_dbms: str
    requirement: str
    business_rules: list[BusinessRule]
    workload: list[WorkloadItem]
    reference: Reference
    tests: SampleTests
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkSample":
        return cls(
            id=str(data["id"]),
            source=str(data.get("source", "")),
            domain=str(data.get("domain", "")),
            target_dbms=str(data.get("target_dbms", "")),
            requirement=str(data.get("requirement", "")),
            business_rules=[
                BusinessRule.from_dict(item) for item in data.get("business_rules", [])
            ],
            workload=[WorkloadItem.from_dict(item) for item in data.get("workload", [])],
            reference=Reference.from_dict(data.get("reference", {})),
            tests=SampleTests.from_dict(data.get("tests", {})),
            metadata=dict(data.get("metadata", {})),
        )

