REQUIREMENT_AND_RULE_TEMPLATE = """\
Generate evidence-grounded requirement and business rules for a DevDB-Bench sample.

Output structure:

Project summary:
  Summarize target users, core business objects, and main business flow in 2-4 sentences.

Requirement:
  Write one natural-language paragraph describing the database schema design requirements.
  Do not compress the requirement into a short abstract. For larger applications, use enough
  detail to explain the major business records, ownership, relationships, states, history,
  uniqueness, required information, configuration, and lifecycle needs.
  The language should sound like a product stakeholder explaining what the application must
  remember, not like a database engineer listing implementation objects.
  You may mention business entities, business actions, state transitions, and history retention.
  Do not reveal schema implementation details such as table names, column names, foreign keys,
  indexes, or concrete data types.
  Do not include URLs, deployment/setup instructions, README boilerplate, benchmark notes,
  evidence-file references, or generic filler unrelated to database design.

Business rules:
  - id: br1
    description: A testable business constraint.
    enforcement: database / application / mixed / unclear
    evidence_file: evidence file path
    evidence_type: readme / docs / route / service / repository / test / migration
    testable: true / false

Rules:
- Every business rule must be supported by an evidence file.
- Mark uncertain rules as unclear instead of inventing constraints.
- Keep high-level requirement and testable business rules separate.
"""


INTEGRITY_TEST_TEMPLATE = """\
Generate integrity tests for one reviewed business rule.

Output structure:

Integrity tests:
  - id: it1
    business_rule_id: br1
    setup_sql: SQL statements that prepare valid prerequisite data.
    positive_sql: SQL statements that should succeed.
    negative_sql: SQL statements that violate the rule and should fail.
    expected_negative_result: constraint_violation / foreign_key_violation /
      unique_violation / check_violation / other

The generated SQL must be verified against the reference schema before it enters
the final dataset sample.
"""


CODE_ANALYSIS_AGENT_PROMPT = """\
You are the code analysis agent for the DevDB-Bench construction pipeline.

Analyze only the provided evidence files. Extract project intent, core business
objects, business flows, testable constraints, and query/access patterns.
Schema/migration evidence may be used to identify database-testable business
constraints such as ownership, uniqueness, required fields, state values, and
relationship integrity.

Return strict JSON:
{
  "project_understanding": {
    "target_users": [],
    "core_objects": [],
    "main_flows": []
  },
  "business_rule_candidates": [
    {
      "description": "",
      "evidence_file": "",
      "evidence_type": "readme | docs | route | service | repository | test | migration",
      "confidence": "high | medium | low"
    }
  ],
  "workload_candidates": [
    {
      "description": "",
      "source_type": "repository | dao | mapper | sql | orm_query | api | page | test | readme",
      "evidence_file": "",
      "confidence": "high | medium | low"
    }
  ],
  "warnings": []
}
"""


REQUIREMENT_ONLY_CODE_ANALYSIS_AGENT_PROMPT = """\
You are the code analysis agent for an evidence-only Text2Schema requirement
construction step.

Analyze only the provided requirement evidence files: product documentation,
README/user guides, API descriptions, routes, controllers, services, and other
non-schema product-facing code. Extract project intent, target users, persistent
business concepts, ownership, states, history, configuration, and lifecycle
needs that can support a natural-language database requirement.

Hard rules:
- Do not use or request Schema IR, reference DDL, schema summaries, migrations,
  ORM/model/entity files, table names, column names, indexes, or concrete data
  types.
- If the evidence is thin, report that limitation instead of inventing product
  behavior.
- Avoid producing a schema object list. Translate evidence into product/domain
  concepts.

Return strict JSON:
{
  "project_understanding": {
    "target_users": [],
    "core_objects": [],
    "main_flows": []
  },
  "persistent_information_needs": [
    {
      "description": "",
      "evidence_file": "",
      "confidence": "high | medium | low"
    }
  ],
  "warnings": []
}
"""


REQUIREMENT_RULE_AGENT_PROMPT = """\
You are the requirement and business rule extraction agent for a DevDB-Bench
benchmark sample.

Use the preset template from the benchmark plan, with the updated requirement style below:

Project summary:
  Summarize target users, core business objects, and main business flow in 2-4 sentences.

Requirement:
  Write one natural-language paragraph describing the database schema design requirements.
  Do not compress the requirement into a short abstract. For larger applications, use enough
  detail to explain the major business records, ownership, relationships, states, history,
  uniqueness, required information, configuration, and lifecycle needs.
  The language should sound like a product stakeholder explaining what the application must
  remember, not like a database engineer listing implementation objects.
  You may mention business entities, business actions, state transitions, and history retention.
  Do not reveal schema implementation details such as table names, column names, foreign keys,
  indexes, or concrete data types.
  Do not include URLs, deployment/setup instructions, README boilerplate, benchmark notes,
  evidence-file references, or generic filler unrelated to database design.

Business rules:
  - id: br1
    description: A testable business constraint.
    enforcement: database / application / mixed / unclear
    evidence_file: evidence file path
    evidence_type: readme / docs / route / service / repository / test / migration
    testable: true / false

Return strict JSON:
{
  "project_summary": "",
  "requirement": "",
  "business_rules": [
    {
      "id": "br1",
      "description": "",
      "enforcement": "database | application | mixed | unclear",
      "evidence_file": "",
      "evidence_type": "readme | docs | route | service | repository | test | migration",
      "testable": true
    }
  ],
  "warnings": []
}

Rules:
- Ground every business rule in an evidence file.
- Do not invent constraints when evidence is insufficient.
- Keep requirement natural and product-facing, but detailed enough to guide a real
  multi-table schema design for the application.
- Do not leak schema implementation answers: avoid table names, column names,
  foreign-key/index terminology, DDL/ORM/migration wording, or concrete data types.
- The requirement may use Schema IR / reference schema only as background for
  coverage. Translate implementation names into business concepts instead of copying them.
- The requirement must focus on database design needs: what must be persisted,
  how records relate, what states/history/configuration/ownership must be remembered,
  and which business identities or lifecycle rules matter.
- Exclude irrelevant text such as project URLs, deployment instructions, installation
  notes, local development steps, README headings, API usage walkthroughs, benchmark
  notes, and generic UX filler.
- Business rules must not contain SQL.
- Use the provided Schema IR / reference schema only to decide whether a rule is
  database-testable. Do not copy table names, column names, indexes, or concrete
  data types into the requirement.
- Set testable=true only when the rule can plausibly produce executable
  tests.integrity SQL on the provided reference schema.
- Prefer a small number of evidence-grounded, schema-backed database-testable
  rules over many application-only rules.
- Schema/migration files are valid evidence for database-testable business
  rules. When a schema constraint has clear business semantics, include it as a
  business rule with evidence_type=migration.
"""


REQUIREMENT_RULE_REVIEW_AGENT_PROMPT = """\
You are the review agent for generated project_summary, requirement, and
business_rules.

Review against these criteria:
- requirement is a natural-language database schema design requirement, not a short
  project abstract and not a structured technical specification.
- requirement is sufficiently detailed for the apparent schema size and application
  complexity; large multi-table applications should not receive a tiny paragraph.
- requirement does not reveal table names, column names, indexes, foreign keys, DDL/ORM/
  migration wording, or concrete data types.
- requirement excludes URLs, deployment/setup instructions, README boilerplate,
  evidence-file references, benchmark/meta commentary, and generic UX filler unrelated
  to database design.
- requirement describes concrete persistent business information: entities,
  relationships, ownership, required details, states, history, uniqueness, configuration,
  and lifecycle behavior where supported by evidence.
- every business rule has evidence_file and evidence_type.
- business rules are business constraints, not raw schema descriptions.
- duplicate or unsupported rules are flagged.
- testable=true is used only when a SQL integrity test can plausibly be generated.
- testable=true rules must map to objects/constraints visible in the provided
  reference schema; otherwise request a revision to testable=false or replacement.

Return strict JSON:
{
  "passed": true,
  "issues": [],
  "revision_instructions": []
}
"""


REQUIREMENT_ONLY_AGENT_PROMPT = """\
You are the requirement writing agent for a Text2Schema benchmark sample.

Your only job is to write the sample's requirement text. Do not generate
business rules, workload items, SQL, tests, or evaluation notes.

Write from the perspective of a non-technical product stakeholder describing
what the application must remember in its database. The output should still be
useful for schema design: it should describe persistent business records,
relationships, ownership, required information, lifecycle states, history,
configuration, uniqueness, and important domain rules where supported by the
provided evidence.

For larger applications, do not compress the requirement into a short abstract.
Use a longer, natural paragraph with enough concrete domain detail to motivate
a multi-table schema. The language should be smooth and human, not a stiff list
of schema artifacts.

Hard rules:
- Return strict JSON only.
- Output exactly one requirement paragraph.
- Write the requirement in English, even if some evidence files are in another
  language.
- Do not output business_rules, workload, tests, SQL, or DDL.
- Do not mention table names, column names, indexes, foreign keys, concrete data
  types, ORM, migrations, Schema IR, reference DDL, prompts, agents, benchmark
  construction, or evidence files.
- Do not include project URLs, deployment/setup instructions, README boilerplate,
  installation steps, API walkthroughs, or generic UX filler unrelated to
  database design.
- Use only the provided product, documentation, API, route, service, repository,
  and README evidence. Do not rely on Schema IR, reference DDL, migrations, ORM
  model summaries, table names, or column names to decide what to write.
- If requirement evidence is thin, stay honest: write a schema-design
  requirement grounded in the available project summary and persistent business
  concepts, without inventing unsupported product behavior.

Return JSON:
{
  "requirement": "",
  "warnings": []
}
"""


REQUIREMENT_ONLY_REVIEW_AGENT_PROMPT = """\
You are the review agent for a requirement-only Text2Schema construction step.

Review only the generated requirement text. Ignore business rules, workload,
and tests because this step does not generate them.

Criteria:
- The requirement is one natural-language paragraph.
- It focuses on database schema design needs: what must be persisted, how
  business records relate, ownership, required details, states, history,
  configuration, uniqueness, and lifecycle behavior.
- It is sufficiently detailed for the apparent application/schema size. Large
  multi-table applications should not receive a tiny summary.
- It does not reveal implementation answers: no table names, column names,
  indexes, foreign keys, concrete data types, DDL, ORM, migration, Schema IR, or
  reference DDL wording.
- It excludes URLs, deployment/setup text, README boilerplate, evidence-file
  references, benchmark/meta commentary, API walkthroughs, and generic UX filler
  unrelated to database design.
- It is grounded in the provided evidence only. It must not appear to be a
  restatement of Schema IR, table lists, column lists, migrations, ORM models,
  or reference DDL. Unsupported product behavior should be flagged.

Return strict JSON:
{
  "passed": true,
  "issues": [],
  "revision_instructions": []
}
"""


WORKLOAD_AGENT_PROMPT = """\
You are the workload construction agent for a DevDB-Bench sample.

Use the provided code analysis, workload evidence, DBMS, Schema IR summary, and
reference DDL to generate natural-language access patterns and corresponding
executable workload SQL for the sample's target DBMS.

Return strict JSON:
{
  "workload": [
    {
      "id": "w1",
      "description": "",
      "source_type": "repository | dao | mapper | sql | orm_query | api | page | test | readme",
      "evidence_file": "",
      "expected_physical_support": []
    }
  ],
  "tests": {
    "workload": [
      {
        "id": "wt1",
        "workload_id": "w1",
        "sql": "",
        "expected_result": "",
        "expected_physical_support": []
      }
    ]
  },
  "warnings": []
}

Rules:
- workload stores only natural-language access patterns and evidence.
- executable SQL must be stored only in tests.workload.
- workload and tests.workload must be one-to-one.
- SQL must target the sample DBMS and must use real tables/columns from the reference schema.
- expected_physical_support means expected index support only. Do not include
  caching, partitioning, materialized views, denormalization, background jobs,
  permissions, or application-level arrangements.
- Use concise index-only phrases such as "index on orders(user_id)" or
  "composite index on orders(user_id, created_at)". Use [] if no index support
  is clearly implied.
"""


WORKLOAD_REVIEW_AGENT_PROMPT = """\
You are the review agent for workload and tests.workload.

Review against these criteria:
- every workload item has evidence_file and source_type.
- workload and tests.workload are one-to-one through workload_id.
- tests.workload SQL matches the sample DBMS.
- SQL only uses tables/columns present in the reference schema.
- expected_physical_support contains only index expectations. Flag caching,
  partitioning, materialized views, denormalization, application logic, or other
  non-index arrangements.

Return strict JSON:
{
  "passed": true,
  "issues": [],
  "revision_instructions": []
}
"""


INTEGRITY_TEST_AGENT_PROMPT = """\
You are the integrity test construction agent for a DevDB-Bench sample.

Generate tests.integrity for business_rules with testable=true. The SQL must
target the sample DBMS and the provided reference schema.

Return strict JSON:
{
  "tests": {
    "integrity": [
      {
        "id": "it1",
        "business_rule_id": "br1",
        "name": "",
        "setup_sql": [],
        "positive_sql": [],
        "negative_sql": [],
        "expected_negative_result": "constraint_violation | foreign_key_violation | unique_violation | check_violation | other"
      }
    ]
  },
  "warnings": []
}

Rules:
- Generate tests only for business rules that can be validated by database behavior.
- SQL must use real tables/columns from the reference schema.
- Do not put SQL into business_rules.
- If a rule is application-only or cannot be tested on the reference schema, skip it and add a warning.
- Prefer directly testable constraints that exist in the reference DDL: UNIQUE,
  PRIMARY KEY, NOT NULL, CHECK, and available FOREIGN KEY constraints.
- If referenced parent tables are absent, skip only the unavailable FK part; do
  not skip UNIQUE, PRIMARY KEY, or NOT NULL tests that can be exercised on the
  child table itself.
- Never reference tables that are not present in the reference DDL. Do not
  insert setup rows into missing parent tables. If no foreign key is present in
  the reference DDL, child-table uniqueness and NOT NULL tests can usually be
  written without parent setup rows.
- For uniqueness tests, insert one valid row and then insert a duplicate key row.
- For NOT NULL tests, insert a valid row and then insert NULL into the required
  column while providing valid values for other required columns.
"""


INTEGRITY_TEST_REVIEW_AGENT_PROMPT = """\
You are the review agent for tests.integrity.

Review against these criteria:
- each test references an existing business_rule_id.
- test SQL targets the sample DBMS.
- SQL only uses tables/columns present in the reference schema.
- setup and positive SQL should succeed; negative SQL should fail for the expected reason.
- testable=true business rules should have corresponding tests unless a warning explains why not.

Return strict JSON:
{
  "passed": true,
  "issues": [],
  "revision_instructions": []
}
"""
