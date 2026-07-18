# DevDB-Bench Annotation Guidelines

To ensure the quality, consistency, and reliability of DevDB-Bench, each constructed benchmark instance is manually reviewed before inclusion. The annotation process follows three quality-control aspects: reference executability, consistency validation, and answer leakage with linguistic quality. This document defines the annotator roles, qualification criteria, review scope, annotation workflow, conflict resolution procedure.

---

## 1. Annotator Roles

We adopt a three-person annotation setup.

### 1.1 Primary Annotators

Two primary annotators independently review each benchmark instance. Their responsibilities include:

- checking reference executability;
- validating consistency between constructed artifacts and retained evidence;
- inspecting answer leakage and linguistic quality.

Each primary annotator records labels and concise notes for issues requiring revision or adjudication.

### 1.2 Adjudicator

Resolves disagreements between annotators and determines final labels.

---

## 2. Annotator Qualification Criteria

Annotators are expected to have experience in database systems and software engineering. A qualified annotator should satisfy the following criteria.

**Educational Background.** Annotators should be PhD students (or equivalent) in Computer Science or related fields.

**Database Background.** Annotators should understand relational schema design, integrity constraints, indexes, and DBMS dialect differences. They should also be able to interpret DDL execution feedback.

**Software Engineering Background.** Annotators should be able to read common application artifacts, such as migration files, ORM models, configuration files, API routes, tests, and project documentation, and infer application semantics from them.

**Text-to-DDL Understanding.** Annotators should understand the benchmark input and output format, distinguish application-level requirements from schema specifications, and identify cases where the input leaks the reference database design.

---

## 3. Annotation Scope and Review Targets

Each benchmark instance consists of repository metadata, retained evidence files, and constructed artifacts. Annotators review the following materials when available and produce DDL execution records during annotation:

- repository metadata, such as repository name, license, target DBMS, framework;
- database design evidence, such as DDL files, migration files, ORM models;
- application evidence, such as README files, API routes, controllers, services, query code, tests;
- constructed Design IR;
- generated reference DDL;
- natural-language requirement;
- access-pattern descriptions.

The review is organized according to the three quality-control aspects:

### 3.1 Reference Executability

Annotators verify whether the reference DDL can be executed under the target DBMS.

Annotation procedure:

1. Execute the reference DDL under the target DBMS.
2. Inspect the DBMS response.
3. Assign Pass if the DDL executes successfully.
4. Assign Needs Revision if execution fails but the error can be reliably repaired using the DBMS error message and schema evidence, and provide a revision plan.
5. Assign Drop if the execution failure cannot be reliably resolved.

### 3.2 Consistency Validation

Annotators verify whether the constructed reference design and benchmark input are consistent with retained repository evidence. This aspect includes reference design consistency, requirement-evidence consistency, access-pattern-evidence consistency, and benchmark input sufficiency.

#### 3.2.1 Reference Design Consistency

Annotators check two mappings:

- The database schema represented in the original database design artifacts is correctly preserved in the Design IR.
- The Design IR is correctly rendered into the reference DDL for the target DBMS.

Labels:

- **Consistent**: Both mappings should preserve tables, columns, relationships, integrity constraints, referential actions, and indexes.
- **Inconsistent**: at least one supported schema element is omitted, added, or incorrectly rendered. Annotators should record the issue and provide a revision plan.

#### 3.2.2 Requirement-Evidence Consistency

Annotators verify whether the natural-language requirement is supported by retained application evidence, focusing on business concepts and data operations.

Review criteria:

- Business concepts in the requirement, such as actors, domain objects, ownership, status, lifecycle, authorization, or configuration needs, are supported by application evidence.
- Data operations implied by the requirement are supported when the requirement mentions them.
- The requirement does not introduce functionality unsupported by repository evidence.

Labels:

- **Consistent**: the requirement is supported by retained application evidence.
- **Inconsistent**: the requirement contains unsupported business concepts or data operations. Annotators should record the issue and provide a revision plan.

#### 3.2.3 Access-Pattern-Evidence Consistency

Annotators verify whether each access-pattern description is supported by retained access-pattern evidence, focusing on business concepts and data operations.

Review criteria:

- Business concepts used in the access pattern, such as actor, target object, ownership, role, or status, are supported by evidence.
- Data operations in the access pattern, such as creation, retrieval, update, deletion, filtering, sorting, are supported by evidence.
- The Access-Pattern does not introduce functionality unsupported by repository evidence.

Labels:

- **Consistent**: the access pattern is supported by retained application evidence.
- **Inconsistent**: the access pattern contains unsupported business concepts or data operations. Annotators should record the issue and provide a revision plan.

#### 3.2.4 Benchmark Input Sufficiency

Annotators check whether the requirement and access patterns provide sufficient application-level information for constructing the essential parts of the reference DDL.

Labels:

- **Sufficient**: The requirement and access patterns together provide enough information to motivate the main persistent objects and relationships.
- **Insufficient but Revisable**: essential design decisions cannot be inferred from the benchmark input, but the missing application-level information can be recovered from retained evidence. Annotators should record the missing information and provide a revision plan.
- **Insufficient Evidence**: essential design decisions cannot be supported even with the retained evidence. The instance should be removed from the benchmark.

### 3.3 Answer Leakage and Linguistic Quality

Annotators inspect the requirement and access-pattern descriptions for implementation details that may directly reveal the reference design. Such details include exact table or column identifiers, SQL fragments, and explicit database constructs such as `FOREIGN KEY`, `JOIN`, and `INDEX`.

Annotators also ensure that the descriptions naturally express application-level business requirements and data access scenarios rather than resembling schema specifications or pseudo-SQL.

Labels:

- **Pass**: the descriptions contain no direct answer leakage and are expressed as natural application-level requirements or access scenarios.
- **Needs Revision**: the descriptions contain leakage, unsupported information, or unnatural implementation-level wording. Annotators should revise them according to retained evidence.

---

## 4. Annotation Workflow

Annotators follow the same workflow for each benchmark instance:

1. Load the instance package and inspect repository metadata.
2. Review the retained schema evidence and application evidence.
3. Execute the reference DDL under the target DBMS and record the DBMS response.
4. Perform consistency validation by comparing the Design IR and reference DDL against schema evidence.
5. Perform consistency validation by comparing the requirement and access-pattern descriptions against application evidence.
6. Check whether the benchmark input provides sufficient application-level information for the essential reference design decisions.
7. Inspect the requirement and access patterns for answer leakage and linguistic quality.
8. Assign labels according to the criteria defined for each quality-control aspect and sub-aspect.
9. Assign the final decision: keep, revise, or drop.
10. Record concise notes for any issue requiring revision or adjudication.

---

## 5. Independence and Conflict Resolution

To reduce bias, two primary annotators review each instance independently. They do not share intermediate judgments during the independent review phase.

For each quality-control aspect and sub-aspect, annotators record the corresponding label and provide notes when an issue is found. If both annotators agree on all major aspects and the final decision, the instance proceeds according to that decision. If they disagree, the instance is sent to the adjudicator.

The adjudicator reviews:

- the two annotators' labels and notes;
- the retained evidence files;
- the DDL execution records and validation notes;
- the current Design IR, reference DDL, requirement, and access patterns.

The adjudicator assigns the final decision and records the reason for resolving the disagreement. All disagreements must be resolved before an instance is included in the final benchmark.

---

## 6. Quality Assurance and Bias Mitigation

### 6.1 Evidence-Based Review

All judgments must be grounded in retained repository evidence and DDL execution records. Annotators should not infer missing schema elements or business requirements from general domain knowledge alone.

### 6.2 Standardized Criteria

All annotators use the same review aspects and labeling rules.

### 6.3 Role Separation

Annotation and dataset construction are conducted as separate stages. Annotators do not participate in the earlier construction process, which helps reduce confirmation bias during manual review.

### 6.4 Independent Double Annotation

Each instance receives two independent annotations without communication between the primary annotators. This helps reduce anchoring effects and confirmation bias.

### 6.5 Adjudication

Disagreements are resolved by a third expert. The adjudicator bases the final decision on retained evidence, DDL execution records, and the criteria in this guideline.

### 6.6 Disagreement Auditing

All disagreements are logged with concise reasons. Recurring patterns are used to refine guideline interpretation. Ambiguous cases are revised or removed.

### 6.7 Inter-Annotator Agreement

Agreement between the two primary annotators is measured before adjudication using Cohen's kappa. In our annotation process, the overall agreement reaches kappa = 0.92, indicating high consistency before adjudication.
