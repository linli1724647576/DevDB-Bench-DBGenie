# DBGenie Example

This example demonstrates how DBGenie transforms a natural-language application requirement, access-pattern descriptions, and a target DBMS dialect into an executable database design.

## 1. Case Selection

We use the open-source project Donkie/Spoolman, an application for managing 3D-printing filament inventory. The target DBMS is PostgreSQL.

DBGenie receives three types of input:

1. A natural-language application requirement:

> The database must support managing filament inventory by tracking manufacturers, filament definitions, and individual spools. Manufacturer records should capture identifying details and optional notes or external references. Filament records should describe the material, physical properties such as density and diameter, color information, recommended print settings, pricing or article details, and may be associated with a manufacturer. Spool records should link to a filament and keep inventory details such as measured weights, amount used, first and last use times, storage location, lot information, purchase price, comments, and whether the spool has been archived. The system must also persist application settings as configurable key-value data. Users must be able to attach custom key-value metadata to manufacturers, filaments, and spools without duplicating the same key for the same parent item, while preserving the relationships between spools, filaments, manufacturers, and their custom metadata.

2. Access-pattern descriptions extracted from the application code:

> **w1.** Find manufacturers whose name contains a given search term (case-insensitive), sorted alphabetically, returning the first ten results.
>
> **w2.** Retrieve a specific manufacturer by its unique identifier.
>
> **w3.** Create a new manufacturer with its name, notes, the weight of an empty spool, and any custom attributes.
>
> **w4.** Update a manufacturer's name and notes.
>
> **w5.** Find spools that are not archived, whose filament's material contains a given search phrase, and that are stored at a given location. Return the twenty most recently used spools.
>
> **w6.** Retrieve a specific spool by its unique identifier, along with its associated filament and manufacturer details.
>
> **w7.** Create a new spool record specifying the filament it uses, its price, its initial total weight, the weight of the empty spool itself, the storage location, a lot number, notes, and any custom attributes.
>
> **w8.** Change the storage location of a spool to a new specified location.
>
> **w9.** Record usage of a spool by reducing its remaining weight by a specified amount and updating the total weight used so far.
>
> **w10.** Retrieve a list of all distinct filament materials used in the system.
>
> **w11.** List all storage locations that have at least one spool assigned.
>
> **w12.** For all spools that are stored in a given location, change their location to a new specified location.
>
> **w13.** Get the value of a system setting using its unique setting key.
>
> **w14.** Create or update a system setting with a given key, storing its value and the current time.
>
> **w15.** Find spools that have a custom attribute with a given name and value (for example, a spool with color attribute set to red).

3. Target DBMS dialect: PostgreSQL.

## 2. Execution

The main execution path was:

![](https://raw.githubusercontent.com/jyqaaa/Image-Hosting/main/img/DBGenie%20example%E6%B5%81%E7%A8%8B%E5%9B%BE.png)

The figure summarizes how DBGenie coordinates this execution. Task initialization places the requirements, access patterns, and target dialect in the Working State. At each stage, the Central Scheduler selects relevant context, invokes the responsible expert, and incorporates the resulting artifact back into the state. The initial Logical Model is checked by the 3NF Validator: failed evidence triggers a localized Logical Model repair, whereas a passing result enables Physical Design and Dialect Compilation. Runtime Testing then gathers DDL, SQL-test, and query-plan evidence through harness-mediated tools. Once the state is ready to finalize, the scheduler returns the validated DDL together with its Explanation.

The component invocation counts and outputs were as follows.

| Component                 |             Calls | Main result                                       |
| ------------------------- | ----------------: | ------------------------------------------------- |
| Requirement Analyst       |                 1 | Requirement Brief                                 |
| Conceptual Model Designer |                 1 | Conceptual Model                                  |
| Logical Model Designer    |                 2 | Initial model and one 3NF repair                  |
| Physical Design Expert    |                 1 | Physical Design                                   |
| Dialect Compiler          |                 1 | PostgreSQL DDL                                    |
| Test Expert               | 2 model responses | Test generation and tool-evidence interpretation  |
| Central Scheduler         | 8 scheduling steps (16 model calls) | Seven expert-routing decisions, including one 3NF repair, followed by finalization |
| 3NF Validator             |                 2 | Initial failure, followed by success after repair |
| DDL Executor              |                 1 | Schema materialized successfully in PostgreSQL    |
| SQL Test Runner           |                 1 | All 15 tests passed                               |
| Query Plan Tool           |                 1 | Seven EXPLAIN observations collected              |

Each Central Scheduler step comprised one context-selection call and one planning-and-reflection call.

### 2.1 Task Initialization

Before invoking the first expert, DBGenie initializes a Global Working State that maintains a unified, observable representation of the current task. It contains the original task, the six expert artifacts, artifact metadata, the action trace of each turn, expert warnings, unresolved issues, tool and test feedback, repair history, and the current validation status. Each expert output undergoes structural and reference validation before the harness stores it as the corresponding artifact. The Central Scheduler accesses this information through the state catalog and selective-context interface.

At each scheduling step, the Central Scheduler observes the Global Working State, selects the required context, reflects on current artifacts and validation evidence, and decides the next action.

The following excerpt shows the Global Working State after this run completed. The `logical_model` entry retains the actual record hierarchy to illustrate artifact metadata; other long payloads are abbreviated.

```json
{
  "task": {
    "id": "Donkie__Spoolman",
    "requirement": "The database must support ...",
    "workload": "15 access patterns",
    "target_dbms": "PostgreSQL"
  },
  "artifacts": {
    "requirement_brief": "validated artifact record",
    "conceptual_model": "validated artifact record",
    "logical_model": {
      "key": "logical_model",
      "status": "validated",
      "version": 2,
      "producer": "logical_model_designer",
      "validation": {"passed": true, "warnings": [], "errors": []},
      "depends_on_versions": {"requirement_brief": 1, "conceptual_model": 1},
      "stale": false,
      "payload": "schema_ir, normalization_spec, traceability, notes, and warnings"
    },
    "physical_plan": "validated artifact record",
    "dialect_report": "validated artifact record",
    "ddl": "validated artifact record",
    "test_report": "validated artifact record"
  },
  "turns": "15 trace records",
  "open_assumptions": [],
  "failure_events": [],
  "repair_history": "1 logical-model repair",
  "tool_request_proposals": "3 Test Expert proposals",
  "tool_results": "2 normalization results and 3 runtime results",
  "unresolved_problems":"...",
  "validation_status":"...",
  "warnings": [],
  "errors": [],
  "final_ddl": "...",
  "final_explanation": "..."
}
```

Artifact metadata records upstream dependencies, validation results, and stale status, allowing the scheduler to determine whether an artifact remains usable and whether downstream artifacts require regeneration. The harness derives readiness from current artifacts and tool results and exposes it through the state catalog. 

#### 2.1.1 Selective Context Manager

The Selective Context Manager constructs two distinct contexts during execution. First, it constructs the `decision_context` needed by the Central Scheduler. Second, after the scheduler decides to invoke an expert, it constructs a role-specific `execution_context` for that expert. Both contexts draw from the Global Working State, but they differ in selection purpose, consumer, and mandatory dependency injection.

For scheduler decisions, the scheduler first receives a lightweight state catalog rather than the complete working state. Its first model call selects which entries must be expanded for the current decision; it does not yet choose the next action.

**Context-selection prompt excerpt:**

```text
Before deciding the next action, select which working-memory context you need
to inspect this turn. You receive a lightweight catalog only; it intentionally
does not contain full artifacts, tool outputs, or long histories.

- Select only context needed to decide the next action.
- Use full only when exact content is necessary; otherwise use summary.
- Use readiness to inspect finalize blockers and execution evidence.
- If readiness.finalize_blockers is non-empty, inspect the most relevant
  blocker evidence before finalizing or choosing the next repair/tool action.
- Do not make the action decision in this response.
```

The harness expands the selected artifacts, tool results, readiness view, or history entries into a focused `decision_context`. In a second model call, the scheduler reads the catalog and this context to decide whether to invoke an expert, call a tool, terminate, or initiate a localized repair. The complete working state therefore does not have to be repeated in every scheduling prompt.

When producing an `invoke_expert` action, the scheduler also selects any additional `execution_context` useful to the target expert. Independently of this selection, the harness always injects the expert's mandatory direct upstream input with `view: "full"`:

```text
- requirement_analyst gets the task;
- conceptual_model_designer gets requirement_brief;
- logical_model_designer gets conceptual_model;
- physical_design_specialist gets logical_model;
- dialect_compiler gets logical_model and physical_plan;
- test_expert gets ddl.
```

#### 2.1.2 Planning and Reflection

The Planning and Reflection module converts the selected context into a concrete action. Reflection checks whether an expert respected its role boundary, whether an artifact contains the required information, whether it remains consistent with upstream inputs, and whether unresolved risks block downstream processing. Planning then chooses an expert invocation, repair instruction, tool call, or termination decision.

**Scheduler planning prompt excerpt:**

```text
You do not produce schema content yourself. Your job is to read the current
state catalog plus the decision_context you selected, then decide the next action.

You must:
- keep the full task state coherent,
- choose working-memory context for each invoked expert,
- choose which single expert to invoke next and what instruction to give,
- decide when to call tools,
- route failures to the most responsible role,
- decide downstream recomputation one expert at a time,
- decide when to terminate or finalize.
```

The scheduler prompt also defines the responsibility boundaries of all six experts. Structural defects are routed to the Logical Model Designer, DDL dialect errors to the Dialect Compiler, and index evidence is interpreted by the Test Expert before the scheduler decides whether the Physical Design Expert must revise the plan. The following stages show how these general mechanisms were applied to each expert invocation in this run.

### 2.2 Requirement Analysis

The Requirement Analyst reads the complete requirement together with all access patterns and distills their business semantics and usage information into a Requirement Brief.

**Role skill prompt excerpt:**

```text
Extract evidence-grounded design candidates from the natural language
requirement and workload.

Responsibilities:
- Read the full requirement and every workload description together.
- Identify candidate concepts, attributes, relationship hints, lifecycle
  semantics, ownership/deletion hints, and workload access intent.
- Populate workload_implications with traceable entries tied to workload ids.

Boundaries:
- Do not decide final entity boundaries.
- Do not output SchemaIR, table structures, indexes, DDL, or migration SQL.
```

**Scheduler decision and expert context.** Because the initialized state contained no design artifact, the Central Scheduler invoked the Requirement Analyst to produce the Requirement Brief. the scheduler injected the complete task, including the requirement, all 15 access patterns, and the PostgreSQL target. The resulting artifact identified concepts, candidate attributes, relationship clues, business rules, lifecycle semantics, ownership and deletion semantics, workload implications, and unresolved ambiguities. An excerpt follows.

```json
{
  "candidate_concepts": [
    "Manufacturer",
    "Filament",
    "Spool",
    "Setting",
    "CustomAttribute (ExtraField)"
  ],
  "relationship_hints": [
    "Filament belongs to Manufacturer (optional).",
    "Spool belongs to Filament (mandatory).",
    "CustomAttribute belongs to Manufacturer, Filament, or Spool."
  ],
  "latent_invariants": [
    "Every CustomAttribute key must be unique for each parent.",
    "Spool remaining_weight should equal total_weight - used_weight."
  ],
  "lifecycle_and_history": [
    "Spool is created with first_use_time initially NULL; first_use_time is set on first usage and last_use_time is updated on subsequent usage.",
    "Archived spools are excluded from active searches.",
    "Setting.updated_at is stored on creation or update."
  ],
  "ownership_and_deletion_semantics": [
    "Manufacturer and Filament deletion behavior is unspecified; the brief assumes RESTRICT.",
    "CustomAttribute should be deleted with its parent to avoid orphaned records."
  ],
  "ambiguities": [
    "The requirement does not specify CASCADE, SET NULL, or RESTRICT for related entities.",
    "It is unclear whether remaining_weight is stored or derived from total_weight and used_weight.",
    "Storage location may be free text or a controlled vocabulary."
  ]
}
```

For `w5`, the Requirement Brief further recorded the filtering, join, and ordering requirements:

```json
{
  "workload_id": "w5",
  "implied_concepts": ["Spool", "Filament"],
  "implied_relationships": ["Spool references Filament"],
  "filters_or_ordering": [
    "archived = false",
    "filament.material ILIKE '%phrase%'",
    "spool.storage_location = ?",
    "ORDER BY spool.last_use_time DESC",
    "LIMIT 20"
  ]
}
```

Together, these fields instantiate the Requirement Brief described in the paper: candidate concepts and relationship hints capture domain structure; latent invariants and deletion semantics capture business rules; lifecycle entries record state evolution; workload implications connect access patterns to downstream design; and ambiguities preserve unresolved issues for later agents.

### 2.3 Conceptual Modeling

The Conceptual Model Designer transforms the Requirement Brief into a conceptual model. It commits entity boundaries, relationship cardinalities, and business invariants without introducing tables, columns, SQL types, or indexes.

**Role skill prompt excerpt:**

```text
Convert the Requirement-to-Design Brief into a conceptual data model.
This is the first stage that commits entity boundaries and relationship semantics.

Responsibilities:
- Decide which candidate concepts become entities.
- Define entity boundaries, relationship cardinalities, weak entities,
  ownership, lifecycle semantics, and conceptual invariants.
- Use requirement_brief.workload_implications as design evidence.

Boundaries:
- Do not design tables, columns, indexes, physical plans, or DDL.
- Do not use DBMS-specific syntax.
```

**Scheduler decision and expert context.** Once the Requirement Brief was validated, the Central Scheduler invoked the Conceptual Model Designer to establish domain-level entities, relationships, and invariants. It selected the complete Requirement Brief as the context. The following raw artifact excerpt preserves the generated `entities`, `relationships`, `conceptual_invariants`, and `design_assumptions` structures.

```json
{
  "entities": [
    {
      "name": "Manufacturer",
      "attributes": [
        {"name": "id", "type": "integer", "notes": "Primary key, system-generated"},
        {"name": "name", "type": "string", "notes": "Manufacturer name, case-insensitive search required"},
        {"name": "notes", "type": "text", "notes": "Optional free-text notes"},"..."
      ],
      "identifier": "id"
    },
    {
      "name": "Filament",
      "attributes": [
        {"name": "id", "type": "integer", "notes": "Primary key"},
        {"name": "manufacturer_id", "type": "integer", "notes": "Foreign key to Manufacturer; nullable (optional)"},
        {"name": "material", "type": "string", "notes": "Free-text material name, used for filtering and distinct listing"},"..."
      ],
      "identifier": "id"
    }
  ],
  "relationships": [
    {
      "from_entity": "Manufacturer",
      "to_entity": "Filament",
      "from_cardinality": "0..*",
      "to_cardinality": "0..1",
      "description": "A Manufacturer may have zero or many Filaments; a Filament optionally belongs to zero or one Manufacturer (nullable foreign key)."
    },
    {
      "from_entity": "Filament",
      "to_entity": "Spool",
      "from_cardinality": "0..*",
      "to_cardinality": "1",
      "description": "A Filament may have zero or many Spools; a Spool must belong to exactly one Filament."
    },"..."
  ],
  "conceptual_invariants": [
    "For each parent entity (Manufacturer, Filament, Spool), every CustomAttribute key must be unique within that parent (i.e., no duplicate keys for the same parent).",
    "Spool.remaining_weight must always equal Spool.total_weight - Spool.used_weight. This invariant is maintained atomically on weight updates.","..."
  ],
  "design_assumptions": [
    "Deletion semantics: Manufacturer deletion: RESTRICT (prevent deletion if any Filaments reference it). Filament deletion: RESTRICT (prevent deletion if any Spools reference it). CustomAttribute deletion: CASCADE when parent entity is deleted (since they are weak entities). These choices minimize accidental data loss; the ambiguity is resolved by assuming safe defaults.","..."
  ]
}
```

### 2.4 Initial Logical Model

The Logical Model Designer translates the conceptual model into a Logical Schema IR.

**Role skill prompt excerpt:**

```text
Convert the reviewed conceptual model into logical SchemaIR.

Responsibilities:
- Design tables, columns, primary keys, foreign keys, unique constraints,
  check constraints, nullability, defaults, and state constraints.
- Produce a separate normalization_spec with exactly one entry for every table.
- Record semantic, non-trivial functional dependencies.
- When 3NF feedback identifies X -> A where X is not a superkey and A is
  non-prime, revise/decompose the logical model instead of hiding the dependency.

Boundaries:
- Do not output final DDL or migration SQL.
```

**Scheduler decision and expert context.** After observing that the Requirement Brief and Conceptual Model were validated and current, the Central Scheduler invoked the Logical Model Designer to create the Logical Schema IR. It selected the complete Conceptual Model as the mandatory direct input. The scheduler action was:

```json
{
  "action_type": "invoke_expert",
  "target_role": "logical_model_designer",
  "target_artifact": "logical_model",
  "instruction": "Create the logical model and normalization_spec from the conceptual model.",
  "explanation": "The requirement brief and conceptual model are validated; the next artifact is the logical model."
}
```

The initial output contained five tables: `manufacturer`, `filament`, `spool`, `setting`, and `custom_attribute`. The initial `spool` relation stored the following three weight attributes:

```json
{
  "name": "spool",
  "columns": [
    {"name": "id", "type": "integer", "nullable": false, "identity": true},
    {"name": "total_weight", "type": "numeric(10,3)", "nullable": false},
    {"name": "used_weight", "type": "numeric(10,3)", "nullable": false},
    {"name": "remaining_weight", "type": "numeric(10,3)", "nullable": false}
  ],
  "check_constraints": [
    {"expression": "remaining_weight = total_weight - used_weight"}
  ]
}
```

**3NF Validation Failure: **

After the Logical Model was produced, the harness automatically invoked the 3NF Validator under the scheduler policy. The validator iteratively computed attribute closures using Armstrong's axioms and returned its result to the Central Scheduler for reflection. The initial validation covered five tables and found one violation, yielding `passed=false`: the determinant of `{total_weight, used_weight} -> remaining_weight` was not a superkey, and `remaining_weight` was not a prime attribute.

### 2.5 Logical Model Repair

**Scheduler decision and expert context.** The Central Scheduler attributed the defect to the Logical Model Designer rather than proceeding to the Physical Design Expert. It re-invoked that expert with the harness-injected Conceptual Model and additionally selected the complete current Logical Model and the corresponding 3NF tool result:

```json
{
  "items": [
    {
      "source": "artifact",
      "key": "logical_model",
      "view": "full",
      "reason": "Current logical model to be revised."
    },
    {
      "source": "tool_result",
      "id": "tool_result_1",
      "view": "full",
      "reason": "3NF validation failure details for the spool table."
    }
  ]
}
```

The resulting repair context contained the harness-injected Conceptual Model, the current Logical Model selected by the scheduler, the specific violating functional dependency, and the localized repair instruction. The scheduler returned this repair action:

```json
{
  "action_type": "invoke_expert",
  "target_role": "logical_model_designer",
  "target_artifact": "logical_model",
  "instruction": "Remove the redundant remaining_weight column, its functional dependency, and the related CHECK constraint. Do not change other tables.",
  "explanation": "The reported dependency violates 3NF because its determinant is not a superkey; the logical model must be revised."
}
```

The revised Logical Model removed the derivable `remaining_weight` attribute, its CHECK constraint, and its functional dependency while preserving the remaining tables.

**3NF Validation Passed:**

The harness immediately revalidated the model, obtaining `passed=true` and `violation_count=0` across five tables. Only then did the next expert action target the Physical Design Expert. This trace demonstrates that the scheduler returns to the earliest affected stage in response to validation feedback and resumes downstream processing only after observing the repair, rather than following a fixed one-pass pipeline or restarting all experts.

The raw `schema_ir` table definitions from the revised Logical Model are shown below.

```json
{
  "schema_ir": {
    "tables": [
      {
        "name": "manufacturer",
        "columns": [
          {"name": "id", "type": "integer", "nullable": false, "identity": true},
          {"name": "name", "type": "text", "nullable": false},
          {"name": "notes", "type": "text", "nullable": true},
          {"name": "empty_spool_weight", "type": "numeric(10,3)", "nullable": true},
          {"name": "external_references", "type": "text", "nullable": true}
        ],
        "primary_key": ["id"],
        "foreign_keys": [],
        "unique_constraints": [],
        "check_constraints": [],
        "indexes": []
      },
      {
        "name": "filament",
        "columns": [
          {"name": "id", "type": "integer", "nullable": false, "identity": true},
          {"name": "manufacturer_id", "type": "integer", "nullable": true},
          {"name": "material", "type": "text", "nullable": false},
          {"name": "density", "type": "numeric(8,4)", "nullable": false},
          {"name": "diameter", "type": "numeric(8,4)", "nullable": false},
          {"name": "color", "type": "text", "nullable": false},
          {"name": "print_settings", "type": "text", "nullable": true},
          {"name": "price", "type": "numeric(10,2)", "nullable": true},
          {"name": "article_details", "type": "text", "nullable": true}
        ],
        "primary_key": ["id"],
        "foreign_keys": [
          {"columns": ["manufacturer_id"], "ref_table": "manufacturer", "ref_columns": ["id"]}
        ],
        "unique_constraints": [],
        "check_constraints": [],
        "indexes": [{"columns": ["manufacturer_id"], "unique": false}]
      },
      {
        "name": "spool",
        "columns": [
          {"name": "id", "type": "integer", "nullable": false, "identity": true},
          {"name": "filament_id", "type": "integer", "nullable": false},
          {"name": "total_weight", "type": "numeric(10,3)", "nullable": false},
          {"name": "used_weight", "type": "numeric(10,3)", "nullable": false, "default": 0},
          {"name": "empty_spool_weight", "type": "numeric(10,3)", "nullable": true},
          {"name": "first_use_time", "type": "timestamp", "nullable": true},
          {"name": "last_use_time", "type": "timestamp", "nullable": true},
          {"name": "storage_location", "type": "text", "nullable": true},
          {"name": "lot_number", "type": "text", "nullable": true},
          {"name": "purchase_price", "type": "numeric(10,2)", "nullable": true},
          {"name": "comments", "type": "text", "nullable": true},
          {"name": "archived", "type": "boolean", "nullable": false, "default": false}
        ],
        "primary_key": ["id"],
        "foreign_keys": [
          {"columns": ["filament_id"], "ref_table": "filament", "ref_columns": ["id"]}
        ],
        "unique_constraints": [],
        "check_constraints": [
          {"expression": "total_weight >= 0"},
          {"expression": "used_weight >= 0"}
        ],
        "indexes": [{"columns": ["filament_id"], "unique": false}]
      },
      {
        "name": "setting",
        "columns": [
          {"name": "setting_key", "type": "text", "nullable": false},
          {"name": "setting_value", "type": "text", "nullable": false},
          {"name": "updated_at", "type": "timestamp", "nullable": false}
        ],
        "primary_key": ["setting_key"],
        "foreign_keys": [],
        "unique_constraints": [],
        "check_constraints": [],
        "indexes": []
      },
      {
        "name": "custom_attribute",
        "columns": [
          {"name": "parent_type", "type": "text", "nullable": false},
          {"name": "parent_id", "type": "integer", "nullable": false},
          {"name": "key", "type": "text", "nullable": false},
          {"name": "value", "type": "text", "nullable": false}
        ],
        "primary_key": ["parent_type", "parent_id", "key"],
        "foreign_keys": [],
        "unique_constraints": [],
        "check_constraints": [],
        "indexes": [{"columns": ["parent_type", "parent_id"], "unique": false}]
      }
    ]
  }
}
```

### 2.6 Physical Design

The Physical Design Expert derives a canonical index plan from filtering, join, ordering, and update patterns without changing the logical schema.

**Role skill prompt excerpt:**

```text
Design workload-aware physical support from Logical SchemaIR and workload descriptions.

Responsibilities:
- Identify filters, joins, ordering, pagination, aggregation, and write patterns.
- Recommend normal, composite, unique, filtered, and covering indexes when supported.
- Explain workload-to-index traceability and avoid unsupported over-indexing.

Boundaries:
- Do not rewrite business semantics or table structure.
- Do not output final DDL.
```

**Scheduler decision and expert context.** After the revised Logical Model passed 3NF validation, the Central Scheduler invoked the Physical Design Expert to generate workload-oriented indexes. The scheduler selected the access-pattern descriptions and the complete revised Logical Model. The output contained four physical indexes:

| Index | Key columns | INCLUDE columns | Filter predicate |
|---|---|---|---|
| `IX_spool_archived_false` | `storage_location` | `filament_id, used_weight, total_weight` | `archived = false` |
| `IX_spool_last_use_time` | `last_use_time` | `filament_id, used_weight` | None |
| `IX_filament_material_color` | `material, color` | `manufacturer_id, diameter, density` | None |
| `IX_custom_attribute_key` | `key` | `parent_type, parent_id, value` | None |

### 2.7 Dialect Compilation

The Dialect Compiler translates the existing Logical Schema IR and Physical Design Plan into DDL for the target DBMS. It performs dialect lowering rather than design: it cannot introduce entities, constraint semantics, or physical structures absent from the upstream artifacts.

**Role skill prompt excerpt:**

```text
Compile the current SchemaIR and declared physical index plan into
target-DBMS DDL. This role is a compiler, not a designer.

Responsibilities:
- Compile only the tables, columns, keys, constraints, and logical indexes
  present in logical_model.schema_ir, plus indexes in physical_plan.indexes.
- Ignore logical_model.normalization_spec; it is validation metadata.
- Treat retrieved dialect knowledge as executor-grounded.

Boundaries:
- Do not add, remove, rename, split, merge, or denormalize schema objects.
- Do not add physical features absent from physical_plan.indexes.
```

**Scheduler decision and expert context.** Once the Logical Model and Physical Design Plan were validated and no pending issue remained, the Central Scheduler invoked the Dialect Compiler to produce PostgreSQL DDL. the scheduler additionally selected the complete Logical Model, Physical Design Plan, summaries of the task, Requirement Brief, and Conceptual Model.

DBGenie maintains a static Dialect Knowledge Base. It constructs a retrieval query from the role, scheduler instruction, and visible context, and uses local BM25 retrieval over the PostgreSQL dialect card. High-weight terms directly related to dialect compilation in this invocation included `type`, `key`, `index`, `column`, `constraint`, `unique`, and `table`. In addition to the mandatory executor/runtime chunk, the retrieved evidence included:

```text
[postgresql.executor_runtime.001]
- Executor: Docker postgres:16-alpine through AgentToolbox.
- Runtime version: detected at execution time and recorded in runtime evidence.
- Enabled extensions are not assumed unless the final DDL creates them.

[postgresql.core_rules.002]
- Prefer GENERATED BY DEFAULT AS IDENTITY for DB-managed integer surrogate keys.

[postgresql.core_rules.004]
- PostgreSQL supports table-level CHECK, UNIQUE, PRIMARY KEY, and foreign keys.

[postgresql.core_rules.005]
- PostgreSQL supports partial indexes with WHERE and covering indexes with INCLUDE.

[postgresql.core_rules.006]
- CREATE INDEX ... INCLUDE (...) WHERE ... is valid when include columns and
  a predicate are both needed.
```

Using this evidence, the Dialect Compiler lowered logical identity columns to `GENERATED BY DEFAULT AS IDENTITY`, mapped temporal attributes to `TIMESTAMP`, and rendered partial and covering indexes from the Physical Plan. Its complete artifact is a `dialect_report` containing the DDL together with type-mapping, syntax-adaptation, and dialect-limitation notes. To avoid repetition, only the generated `spool` table and the index supporting `w5` are shown here.

```sql
CREATE TABLE spool (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY,
    filament_id INTEGER NOT NULL,
    total_weight NUMERIC(10,3) NOT NULL,
    used_weight NUMERIC(10,3) NOT NULL DEFAULT 0,
    empty_spool_weight NUMERIC(10,3),
    first_use_time TIMESTAMP,
    last_use_time TIMESTAMP,
    storage_location TEXT,
    lot_number TEXT,
    purchase_price NUMERIC(10,2),
    comments TEXT,
    archived BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (id),
    FOREIGN KEY (filament_id) REFERENCES filament(id),
    CHECK (total_weight >= 0),
    CHECK (used_weight >= 0)
);

CREATE INDEX IX_spool_archived_false
    ON spool (storage_location)
    INCLUDE (filament_id, used_weight, total_weight)
    WHERE archived = false;
```

### 2.8 Runtime Testing

The Test Expert dynamically constructs tests from the current DDL and relevant design artifacts and interprets the evidence returned by execution tools. It does not directly modify the Logical Model, Physical Plan, or DDL.

**Role skill prompt excerpt:**

```text
Generate dynamic tests and structured feedback from current artifacts,
DDL execution result, requirement, workload, and target DBMS.

Responsibilities:
- Generate tests with explicit expected outcomes.
- Request ddl_executor when current DDL lacks execution evidence.
- Request sql_test_runner for non-empty generated tests without current evidence.
- Request query_plan_tool when physical indexes and workload checks exist.
- Interpret tool reports and route diagnosed failures to the responsible role.

Boundaries:
- Do not introspect the database schema.
- Do not modify DDL, SchemaIR, conceptual model, or physical plan.
```

**Scheduler decision and expert context.** After all design artifacts were validated, the readiness state still lacked real DDL execution and test evidence. The Central Scheduler therefore invoked the Test Expert to generate tests and request the three runtime tools. The scheduler selected the complete DDL and Requirement Brief plus a Logical Model summary. The Test Expert generated 15 tests covering positive invariants, negative constraints, workload smoke tests, and query-plan checks. Three representative tests follow.

**Positive invariant test:**

```json
{
  "id": "positive_insert_spool",
  "kind": "invariant",
  "expect_success": true,
  "sql": [
    "INSERT INTO manufacturer ...",
    "INSERT INTO filament ...",
    "INSERT INTO spool (id, filament_id, total_weight, used_weight, storage_location) VALUES (300, 300, 1000, 0, 'Shelf A');"
  ]
}
```

**Negative constraint test:**

```json
{
  "id": "negative_unique_custom_attribute",
  "kind": "negative_invariant",
  "should_fail": true,
  "sql": [
    "INSERT INTO custom_attribute (...) VALUES ('manufacturer', 500, 'color', 'blue');",
    "INSERT INTO custom_attribute (...) VALUES ('manufacturer', 500, 'color', 'red');"
  ]
}
```

**Query-plan test:**

```json
{
   "id": "queryplan_w5_partial_index",
   "kind": "query_plan",
   "setup_sql": [
     "INSERT INTO manufacturer (id, name) VALUES (900, 'Manu6');",
     "INSERT INTO filament (id, manufacturer_id, material, density, diameter, color) VALUES (900, 900, 'PLA', 1.24, 1.75, 'Red');","..."
   ],
   "query": "SELECT s.id, s.storage_location, s.last_use_time, f.material FROM spool s JOIN filament f ON s.filament_id = f.id WHERE s.archived = false AND f.material ILIKE '%pla%' AND s.storage_location = 'Shelf A' ORDER BY s.last_use_time DESC LIMIT 20;",
   "expected_index": "IX_spool_archived_false"
}
```

The initial Test Report proposed three tool calls: `ddl_executor`, `sql_test_runner`, and `query_plan_tool`. The harness executed them in an isolated Docker environment in DDL, SQL-test, and query-plan order, then automatically made the second Test Expert model call within the same scheduler action. This interpretation context contained the complete initial Test Report, the current readiness view, and all three tool results; it did not require another scheduler context-selection decision. The interpreted evidence showed that the DDL created five tables successfully, all 15 tests passed, and seven raw query plans were collected; the plan for `w5` used the intended partial index. The final `test_report.passed` value was `true`.

The DDL Executor submitted the final DDL unchanged to the real PostgreSQL environment and returned the following evidence:

```json
{
  "success": true,
  "executor": "docker_postgresql",
  "real_execution": true,
  "table_count_runtime": 5,
  "runtime_version": "postgresql 16.14"
}
```

The SQL Test Runner executed all 15 tests under the same runtime, with 15 passes and no failures. The negative test for a duplicate custom attribute produced the following database error, confirming enforcement of the composite primary key:

```text
ERROR: duplicate key value violates unique constraint "custom_attribute_pkey"
DETAIL: Key (parent_type, parent_id, key)=(manufacturer, 500, color) already exists.
```

The Query Plan Tool executed `EXPLAIN` on workload queries. The relevant portion of the `w5` plan was:

```text
Limit
  -> Sort
       Sort Key: s.last_use_time DESC
       -> Nested Loop
            -> Index Scan using ix_spool_archived_false on spool s
                 Index Cond: (storage_location = 'Shelf A'::text)
            -> Index Scan using filament_pkey on filament f
                 Index Cond: (id = s.filament_id)
```

The Query Plan Tool provides raw plan evidence rather than a design verdict. The Test Expert interpreted this evidence in the context of the workload, fixture, and Physical Plan, confirming that PostgreSQL used `IX_spool_archived_false` and finding no issue that required routing to the Physical Design Expert.

### 2.9 Finalization

After Runtime Testing, the readiness summary showed current passing 3NF evidence, successful materialization of five tables under PostgreSQL 16.14, 15 passing SQL tests, seven raw query-plan observations, and no finalize blocker. The scheduler therefore issued `finalize`, returning the final DDL and Explanation shown below. This satisfies the termination condition that the DDL must be materialized successfully and pass the required validation tests.

#### 2.9.1 Final DDL

```sql
CREATE TABLE manufacturer (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY,
    name TEXT NOT NULL,
    notes TEXT,
    empty_spool_weight NUMERIC(10,3),
    external_references TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE filament (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY,
    manufacturer_id INTEGER,
    material TEXT NOT NULL,
    density NUMERIC(8,4) NOT NULL,
    diameter NUMERIC(8,4) NOT NULL,
    color TEXT NOT NULL,
    print_settings TEXT,
    price NUMERIC(10,2),
    article_details TEXT,
    PRIMARY KEY (id),
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturer(id)
);

CREATE TABLE spool (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY,
    filament_id INTEGER NOT NULL,
    total_weight NUMERIC(10,3) NOT NULL,
    used_weight NUMERIC(10,3) NOT NULL DEFAULT 0,
    empty_spool_weight NUMERIC(10,3),
    first_use_time TIMESTAMP,
    last_use_time TIMESTAMP,
    storage_location TEXT,
    lot_number TEXT,
    purchase_price NUMERIC(10,2),
    comments TEXT,
    archived BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (id),
    FOREIGN KEY (filament_id) REFERENCES filament(id),
    CHECK (total_weight >= 0),
    CHECK (used_weight >= 0)
);

CREATE TABLE setting (
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (setting_key)
);

CREATE TABLE custom_attribute (
    parent_type TEXT NOT NULL,
    parent_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (parent_type, parent_id, key)
);

CREATE INDEX ON filament (manufacturer_id);
CREATE INDEX ON spool (filament_id);
CREATE INDEX ON custom_attribute (parent_type, parent_id);

CREATE INDEX IX_spool_archived_false
    ON spool (storage_location)
    INCLUDE (filament_id, used_weight, total_weight)
    WHERE archived = false;

CREATE INDEX IX_spool_last_use_time
    ON spool (last_use_time)
    INCLUDE (filament_id, used_weight);

CREATE INDEX IX_filament_material_color
    ON filament (material, color)
    INCLUDE (manufacturer_id, diameter, density);

CREATE INDEX IX_custom_attribute_key
    ON custom_attribute (key)
    INCLUDE (parent_type, parent_id, value);
```

#### 2.9.2 Final Explanation

The following is the original Explanation generated by the Central Scheduler in the successful `finalize` action:

> The design supports the Donkie/Spoolman filament inventory management system for PostgreSQL. The requirement brief identified five core concepts—Manufacturer, Filament, Spool, Setting, and CustomAttribute—which the conceptual model refined into entities and invariants. The logical model (version 2, after correcting a 3NF violation by removing a redundant `remaining_weight` column) comprises five tables: `manufacturer` (surrogate key, name, notes, empty_spool_weight, external_references), `filament` (surrogate key, FK to manufacturer, material, density, diameter, color, print_settings, price, article_details), `spool` (surrogate key, FK to filament, total/used weight with non-negative checks, timestamps, storage_location, lot, purchase_price, comments, archived flag), `setting` (natural key setting_key, value, updated_at), and `custom_attribute` (composite PK of parent_type, parent_id, key, with value). The physical index plan adds four workload-driven indexes: a partial filtered index `IX_spool_archived_false` on `storage_location` for active-spool queries by location, `IX_spool_last_use_time` for recency-ordered retrieval, `IX_filament_material_color` for material/color searches, and `IX_custom_attribute_key` for key-based attribute lookups. The dialect compiler emitted PostgreSQL-compliant DDL with `GENERATED BY DEFAULT AS IDENTITY`, foreign keys, check constraints, and all indexes. The 3NF validator passed with zero violations on version 2. The DDL executed successfully on a live PostgreSQL 16.14 container, creating all five tables. All 15 generated tests (positive inserts, negative uniqueness/check/FK violations, workload smoke tests, and query plan verification) passed on the same container. The query plan tool confirmed that the `IX_spool_archived_false` partial index is used in the w5 workload query (`Index Scan using ix_spool_archived_false`), and other queries rely on primary-key or composite indexes efficiently. A known limitation is that the `custom_attribute` table cannot enforce a polymorphic foreign key to multiple parent tables; referential integrity is delegated to the application. All readiness criteria are satisfied and finalize blockers are empty.
