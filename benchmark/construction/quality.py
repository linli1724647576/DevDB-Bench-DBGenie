from __future__ import annotations

from dataclasses import dataclass, field

from dbgenie.core.sample import BenchmarkSample


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DatasetQualityChecker:
    def check_sample(self, sample: BenchmarkSample) -> QualityReport:
        errors: list[str] = []
        warnings: list[str] = []

        if not sample.requirement.strip():
            errors.append("missing_requirement")
        if sample.reference.schema_ir.table_count() == 0:
            errors.append("missing_reference_schema_ir")

        business_rule_ids = {rule.id for rule in sample.business_rules}
        integrity_rule_ids = {test.business_rule_id for test in sample.tests.integrity}
        workload_ids = {item.id for item in sample.workload}
        workload_test_ids = {test.workload_id for test in sample.tests.workload}

        for rule in sample.business_rules:
            if not rule.evidence_file:
                errors.append(f"business_rule_missing_evidence:{rule.id}")
            if rule.testable and rule.id not in integrity_rule_ids:
                errors.append(f"testable_business_rule_without_integrity_test:{rule.id}")

        for test in sample.tests.integrity:
            if test.business_rule_id not in business_rule_ids:
                errors.append(f"integrity_test_unknown_business_rule:{test.id}")

        for item in sample.workload:
            if not item.evidence_file:
                errors.append(f"workload_missing_evidence:{item.id}")
            if item.id not in workload_test_ids:
                errors.append(f"workload_without_workload_test:{item.id}")

        for test in sample.tests.workload:
            if test.workload_id not in workload_ids:
                errors.append(f"workload_test_unknown_workload:{test.id}")

        if not sample.reference.ddl_by_dialect:
            warnings.append("missing_reference_ddl_by_dialect")

        return QualityReport(passed=not errors, errors=errors, warnings=warnings)

