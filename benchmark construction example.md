# Benchmark Construction Example

This appendix provides a concrete construction trace for one DevDB-Bench instance. 

## 1. Data Collection and Screening

In the data collection stage, candidate repositories are retrieved through the GitHub REST API, and repository metadata is retained for subsequent screening and manual verification.

| Field | Value |
| --- | --- |
| Repository | `davidfowl/TodoApp` |
| GitHub URL | `https://github.com/davidfowl/TodoApp` |
| Stars | 3104 |
| Forks | 458 |
| License | MIT |
| Last pushed | 2026-02-12T09:29:50Z |
| Framework | Entity Framework Core |
| Target DBMS | SQLite |

This repository satisfies the basic requirements for dataset construction: it is a public, non-fork, non-archived application repository with an explicit open-source license. It contains EF Core migration and snapshot files as schema evidence, and it also provides README, API tests, and application code as requirement and access-pattern evidence.

---

## 2. Reference Database Design Construction

Reference Database Design Construction aims to construct a normalized Design IR from schema evidence in a real repository and generate an executable reference DDL in the target DBMS dialect.

For this sample, the database design is mainly represented by EF Core migration files and a model snapshot. The construction process is:

```text
EF Core migration / snapshot evidence
    -> static EF Core extractor
    -> normalized Design IR
    -> SQLite DDL Construction
```

### 2.1 Schema Evidence Excerpt

The selected schema evidence files are:

```text
Todo.Api/Migrations/20221123071234_Initial.cs
Todo.Api/Migrations/20221123165051_RemoveIsAdmin.cs
Todo.Api/Migrations/20230714032431_ForeignKeyChange.cs
Todo.Api/Migrations/TodoDbContextModelSnapshot.cs
Todo.Api/TodoDbContext.cs
```

The `xxxxModelSnapshot.cs` and `Migrations/*.cs` paths indicate that this repository uses the EF Core schema construction mechanism.

The file `20221123071234_Initial.cs` defines the relevant user tables, the Todo table, foreign keys, and indexes. The following excerpt shows representative schema operations:

```csharp
migrationBuilder.CreateTable(
    name: "AspNetUsers",
    columns: table => new
    {
        Id = table.Column<string>(type: "TEXT", nullable: false),
        UserName = table.Column<string>(type: "TEXT", maxLength: 256, nullable: false),
        NormalizedUserName = table.Column<string>(type: "TEXT", maxLength: 256, nullable: true),
        Email = table.Column<string>(type: "TEXT", maxLength: 256, nullable: true),
        NormalizedEmail = table.Column<string>(type: "TEXT", maxLength: 256, nullable: true),
        EmailConfirmed = table.Column<bool>(type: "INTEGER", nullable: false),
        PasswordHash = table.Column<string>(type: "TEXT", nullable: true),
        SecurityStamp = table.Column<string>(type: "TEXT", nullable: true),
        PhoneNumber = table.Column<string>(type: "TEXT", nullable: true),
        AccessFailedCount = table.Column<int>(type: "INTEGER", nullable: false)
    },
    constraints: table =>
    {
        table.PrimaryKey("PK_AspNetUsers", x => x.Id);
    });

migrationBuilder.CreateTable(
    name: "Todos",
    columns: table => new
    {
        Id = table.Column<int>(type: "INTEGER", nullable: false),
        Title = table.Column<string>(type: "TEXT", nullable: false),
        IsComplete = table.Column<bool>(type: "INTEGER", nullable: false),
        OwnerId = table.Column<string>(type: "TEXT", nullable: false)
    },
    constraints: table =>
    {
        table.PrimaryKey("PK_Todos", x => x.Id);
        table.ForeignKey(
            name: "FK_Todos_AspNetUsers_OwnerId",
            column: x => x.OwnerId,
            principalTable: "AspNetUsers",
            principalColumn: "UserName",
            onDelete: ReferentialAction.Cascade);
    });

migrationBuilder.CreateIndex(
    name: "UserNameIndex",
    table: "AspNetUsers",
    column: "NormalizedUserName",
    unique: true);

migrationBuilder.CreateIndex(
    name: "IX_Todos_OwnerId",
    table: "Todos",
    column: "OwnerId");
```

This evidence exposes:

- user tables and the Todo item table;
- the ownership relationship between Todo items and users;
- indexes used for authentication-related lookup and foreign-key access.

### 2.2 Static Extractor

This sample uses the EF Core static extractor to identify EF Core schema construction patterns.

The key dispatch logic is:

```python
def extract_ef_core_schema(schema_files):
    tables = {}
    for item in sorted(schema_files, key=lambda file: file.repo_path.lower()):
        if not item.repo_path.lower().endswith(".cs"):
            continue
        text = _safe_read(item)
        migration_text = _ef_up_method_body(text) or text

        for match in re.finditer(r"migrationBuilder\.CreateTable\s*\(", migration_text):
            block = _call_block(migration_text, match.end() - 1)
            table_name = _ef_named_string(block, "name")
            if not table_name:
                continue
            table = _parse_ef_create_table(table_name, block)
            tables[table.name] = _merge_table(tables.get(table.name), table)
```

For migration-based artifacts, multiple files are read in path order. In this example, EF Core migration files are named with timestamps, so sorting them by path preserves the intended migration order. Earlier migrations are processed first, later migrations are applied afterward, and incremental changes are accumulated without losing previous structure.

Table and column extraction is performed by reading `migrationBuilder.CreateTable` blocks and extracting `table.Column<T>` declarations:

```python
def _parse_ef_create_table(table_name, block):
    columns = []
    primary_key = []

    for line in columns_body.splitlines():
        match = re.search(
            r"(\w+)\s*=\s*table\.Column<([^>]+)>\(([^)]*)\)",
            line,
        )
        if match:
            columns.append(
                ColumnIR(
                    name=match.group(1),
                    type=match.group(2),
                    nullable="nullable: true" in match.group(3),
                )
            )

    pk_match = re.search(r"table\.PrimaryKey\([^,]+,\s*x\s*=>\s*x\.(\w+)", block)
    if pk_match:
        primary_key.append(pk_match.group(1))
```

### 2.3 Design IR Result

The final Design IR for this sample has the following size:

| Metric | Value |
| --- | ---: |
| Tables | 8 |
| Columns | 41 |
| Foreign keys | 7 |
| Unique constraints | 0 |
| Indexes | 8 |

The following excerpt shows part of the Design IR:

```json
{
  "tables": [
    {
      "name": "AspNetUsers",
      "columns": [
        {"name": "Id", "type": "TEXT", "nullable": false},
        {"name": "UserName", "type": "TEXT", "nullable": true},
        {"name": "NormalizedUserName", "type": "TEXT", "nullable": true},
        {"name": "Email", "type": "TEXT", "nullable": true},
        {"name": "NormalizedEmail", "type": "TEXT", "nullable": true},
        {"name": "PasswordHash", "type": "TEXT", "nullable": true},
        {"name": "AccessFailedCount", "type": "INTEGER", "nullable": false}
      ],
      "primary_key": ["Id"],
      "indexes": [
        {"columns": ["NormalizedEmail"], "unique": false},
        {"columns": ["NormalizedUserName"], "unique": true}
      ]
    },
    {
      "name": "Todos",
      "columns": [
        {"name": "Id", "type": "INTEGER", "nullable": false},
        {"name": "Title", "type": "TEXT", "nullable": false},
        {"name": "IsComplete", "type": "INTEGER", "nullable": false},
        {"name": "OwnerId", "type": "TEXT", "nullable": false}
      ],
      "primary_key": ["Id"],
      "foreign_keys": [
        {
          "columns": ["OwnerId"],
          "ref_table": "AspNetUsers",
          "ref_columns": ["Id"]
        }
      ],
      "indexes": [
        {"columns": ["OwnerId"], "unique": false}
      ]
    }
  ]
}
```

### 2.4 DDL Generation

After the Design IR is constructed, a SQLite reference DDL is generated for the target DBMS.

```text
Target DBMS: SQLite
Input: normalized Design IR
Output: executable SQLite DDL
```

We use DeepSeek-v4-flash for DDL generation. The prompt is:

```text
Given a normalized database Design IR and a target DBMS dialect:

1. Emit only executable DDL for the target dialect.
2. Preserve every table, column, primary key, foreign key, unique constraint,
   check constraint, and index in the Design IR.
3. Map framework-specific or abstract types to target-dialect types.
   For SQLite:
   - string / TEXT-like types -> TEXT
   - int / INTEGER-like types -> INTEGER
   - bool / Boolean-like types -> INTEGER
   - DateTimeOffset-like values -> TEXT
4. Use dialect-correct identifier quoting.
5. Emit indexes after table definitions when they are not inline constraints.
6. Do not invent additional tables, columns, constraints, or indexes.
```

### 2.5 Final Reference DDL

The final SQLite reference DDL is:

```sql
CREATE TABLE "AspNetRoles" (
  "Id" TEXT NOT NULL,
  "ConcurrencyStamp" TEXT,
  "Name" TEXT,
  "NormalizedName" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "AspNetRoleClaims" (
  "Id" INTEGER NOT NULL,
  "ClaimType" TEXT,
  "ClaimValue" TEXT,
  "RoleId" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("RoleId") REFERENCES "AspNetRoles" ("Id")
);

CREATE TABLE "AspNetUserClaims" (
  "Id" INTEGER NOT NULL,
  "ClaimType" TEXT,
  "ClaimValue" TEXT,
  "UserId" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUserLogins" (
  "LoginProvider" TEXT NOT NULL,
  "ProviderKey" TEXT NOT NULL,
  "ProviderDisplayName" TEXT,
  "UserId" TEXT NOT NULL,
  PRIMARY KEY ("LoginProvider", "ProviderKey"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUserRoles" (
  "UserId" TEXT NOT NULL,
  "RoleId" TEXT NOT NULL,
  PRIMARY KEY ("UserId", "RoleId"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id"),
  FOREIGN KEY ("RoleId") REFERENCES "AspNetRoles" ("Id")
);

CREATE TABLE "AspNetUserTokens" (
  "UserId" TEXT NOT NULL,
  "LoginProvider" TEXT NOT NULL,
  "Name" TEXT NOT NULL,
  "Value" TEXT,
  PRIMARY KEY ("UserId", "LoginProvider", "Name"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUsers" (
  "Id" TEXT NOT NULL,
  "AccessFailedCount" INTEGER NOT NULL,
  "ConcurrencyStamp" TEXT,
  "Email" TEXT,
  "EmailConfirmed" INTEGER NOT NULL,
  "LockoutEnabled" INTEGER NOT NULL,
  "LockoutEnd" TEXT,
  "NormalizedEmail" TEXT,
  "NormalizedUserName" TEXT,
  "PasswordHash" TEXT,
  "PhoneNumber" TEXT,
  "PhoneNumberConfirmed" INTEGER NOT NULL,
  "SecurityStamp" TEXT,
  "TwoFactorEnabled" INTEGER NOT NULL,
  "UserName" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "Todos" (
  "Id" INTEGER NOT NULL,
  "IsComplete" INTEGER NOT NULL,
  "OwnerId" TEXT NOT NULL,
  "Title" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("OwnerId") REFERENCES "AspNetUsers" ("Id")
);

CREATE UNIQUE INDEX "uidx_AspNetRoles_NormalizedName_1" ON "AspNetRoles" ("NormalizedName");
CREATE INDEX "idx_AspNetRoleClaims_RoleId_1" ON "AspNetRoleClaims" ("RoleId");
CREATE INDEX "idx_AspNetUserClaims_UserId_1" ON "AspNetUserClaims" ("UserId");
CREATE INDEX "idx_AspNetUserLogins_UserId_1" ON "AspNetUserLogins" ("UserId");
CREATE INDEX "idx_AspNetUserRoles_RoleId_1" ON "AspNetUserRoles" ("RoleId");
CREATE INDEX "idx_AspNetUsers_NormalizedEmail_1" ON "AspNetUsers" ("NormalizedEmail");
CREATE UNIQUE INDEX "uidx_AspNetUsers_NormalizedUserName_2" ON "AspNetUsers" ("NormalizedUserName");
CREATE INDEX "idx_Todos_OwnerId_1" ON "Todos" ("OwnerId");
```

## 3. Requirement & Access-pattern Construction

We implement this step with two agents, an Analysis Agent and a Writing Agent, both using DeepSeek-v4-flash as the base model.

This step does not reverse-engineer natural-language inputs from the reference DDL or Schema IR. Instead, it uses README files, configuration files, API implementations, tests, and application code that expose business semantics and access behavior. 

### 3.1 Analysis Agent

The key evidence used for this sample includes:

| Evidence type | File |
| --- | --- |
| Requirement evidence | `README.md` |
| Requirement evidence | `Todo.Api/appsettings.json` |
| Access-pattern evidence | `Todo.Api.Tests/TodoApiTests.cs` |
| Access-pattern evidence | `Todo.Api.Tests/UserApiTests.cs` |
| Access-pattern evidence | `Todo.Api/Program.cs` |
| Access-pattern evidence | `Todo.Api/TodoDbContext.cs` |

The `README.md` file describes the application goal and functionality:

```text
This is a Todo application that features:
- Todo.Web: an ASP.NET Core hosted Blazor WASM front end application
- Todo.Api: an ASP.NET Core REST API backend using minimal APIs

It showcases:
- Using EntityFramework and SQLite for data access
- User management with ASP.NET Core Identity
- Cookie authentication
- Bearer authentication
- Writing integration tests for your REST API

Before executing any requests, you need to create a user and get an auth token.
To create a new user, POST to /users/register.
To get a token, hit /users/login with the user email and password.
You should be able to use the accessToken to make authenticated requests to the todo endpoints.
```

This evidence supports the following business interpretation:

- the application is an authenticated Todo REST API;
- users register, log in, and obtain tokens;
- Todo endpoints require authenticated requests;
- persistent information includes user identity and authentication data, role/claim/login/token-related records, and Todo items owned by users.

`Todo.Api.Tests/TodoApiTests.cs` shows the main access behavior for Todo items:

```csharp
[Fact]
public async Task GetTodos()
{
    var userId = "34";
    await application.CreateUserAsync(userId);

    db.Todos.Add(new Todo { Title = "Thing one I have to do", OwnerId = userId });
    await db.SaveChangesAsync();

    var client = application.CreateClient(userId);
    var todos = await client.GetFromJsonAsync<List<TodoItem>>("/todos");
    var todo = Assert.Single(todos);
    Assert.Equal("Thing one I have to do", todo.Title);
}
```

This test supports the access pattern of listing Todo items owned by the current user.

The Analysis Agent receives only repository metadata, requirement evidence, and access-pattern evidence. It does not receive the reference DDL or table/column lists. The prompt is:

```text
You are the Analysis Agent for a benchmark construction pipeline.

Your task is to analyze repository evidence and produce a structured
summary for requirement and access-pattern construction.

Input:
- repository_metadata: GitHub metadata, framework/ecosystem hints,
  target DBMS hints, and selected evidence paths.
- requirement_evidence: README, documentation, API docs, controllers,
  routes, services, forms, admin interfaces, tests, or fixtures that
  reveal business semantics.
- access_pattern_evidence: repositories, DAO/mapper code, explicit
  query files, ORM queries, controllers, routes, API endpoints, tests,
  search/filter/report code, and UI paths that reveal data usage.

Rules:
1. Use only the provided evidence. Do not use reference DDL,
   table lists, column lists, indexes, constraints, or SQL tests.
2. Do not write the final requirement paragraph or final access-pattern
   descriptions. Produce structured analysis only.
3. For requirement construction, record business objects, persistent
   information, relationships, business rules, and lifecycle-related
   evidence.
4. For access-pattern construction, record operation targets, operation
   kinds, actors, filter conditions, sorting or pagination requirements,
   aggregations, and representative creation, update, and deletion
   scenarios.
5. Prefer application-level concepts over code-level identifiers.
6. If evidence is weak or ambiguous, mark the item as uncertain instead
   of inventing functionality.
```

### 3.2 Writing Agent

The Writing Agent converts the structured summary into a natural-language requirement and access-pattern descriptions. Its input is the structured output of the Analysis Agent and the necessary evidence paths; it does not receive the Schema IR or reference DDL. The prompt is:

```text
You are the Writing Agent for a benchmark construction pipeline.

Your task is to convert the structured analysis into:
1. one natural-language application requirement, and
2. a set of natural-language access-pattern descriptions.

Input:
- repository_metadata
- requirement_analysis
- access_pattern_analysis
- evidence paths for traceability

Rules for the requirement:
1. Write one English paragraph.
2. Describe what persistent business information the application must
   store and manage.
3. Cover important business objects, relationships, ownership,
   lifecycle states, authorization rules, and historical/configuration
   information when supported by evidence.
4. Keep the language product-facing or developer-facing, not SQL-facing.

Rules for access-pattern descriptions:
1. Write each access pattern as a natural application operation.
2. Preserve the operation target, actor, filters, sorting/pagination,
   aggregation, and mutation intent from the structured analysis.
3. Do not write SQL, pseudo-SQL, query templates, table names, column
   names, index names, foreign keys, ORM terms, file paths, or test
   fixture details.
4. Replace code-level identifiers with natural business concepts.
5. Keep each description specific enough to guide physical design, but
   avoid revealing the reference schema.
```

### 3.3 Output

The Analysis Agent first compresses the evidence into a structured summary rather than directly producing the final benchmark input. For this sample, the analysis output can be summarized as follows:

```json
  "requirement_analysis": {
    "target_users": [
      "end users managing their own todo items",
      "administrators with elevated privileges"
    ],
    "business_objects": [
      {
        "object": "user account",
        "persistent_information": [
          "login identity",
          "authentication credential material",
          "security token state",
          "role and claim assignments",
          "external login bindings"
        ],
        "relationships": [
          "a user may own multiple todo items",
          "a user may have roles, claims, external logins, and tokens"
        ]
      },
      {
        "object": "todo item",
        "persistent_information": [
          "short text title",
          "completion state",
          "owning user"
        ],
        "relationships": [
          "each todo item belongs to one user"
        ]
      }
    ],
    "main_flows": [
      "user registration",
      "user login and token generation",
      "authenticated users create, read, update, and delete their own todo items",
      "administrators delete or update todo items regardless of owner"
    ],
    "business_rules": [
      "normal users can only access todo items they own",
      "administrators have elevated access to todo items"
    ],
    "lifecycle_evidence": [
      "a user is created before authenticated todo requests",
      "a todo item can be created, read, updated, and deleted",
      "a login flow produces a token used by later authenticated requests"
    ]
  }
```

```json
  "access_pattern_analysis": [
    {
      "operation_target": "todo items",
      "operation_kind": "list/read",
      "actor": "authenticated end user",
      "filter_conditions": [
        "only records owned by the current user"
      ],
      "sorting_or_pagination": null,
      "aggregation": null,
      "evidence_file": "Todo.Api.Tests/TodoApiTests.cs"
    },
    {
      "operation_target": "one todo item",
      "operation_kind": "detail/read",
      "actor": "authenticated end user",
      "filter_conditions": [
        "match a specific item identifier",
        "require ownership by the current user"
      ],
      "sorting_or_pagination": null,
      "aggregation": null,
      "evidence_file": "Todo.Api.Tests/TodoApiTests.cs"
    }
  ]
```

This intermediate representation has two roles:

1. It compresses the business semantics in the README and API tests into an auditable summary.
2. It provides a natural-language construction basis for the Writing Agent while avoiding direct copying of source-code identifiers, table names, column names, or database structures.

Based on the structured summary and evidence, the Writing Agent generates the final requirement:

```text
The system must support a user-authenticated todo application where registered users can manage their own todo items. User accounts should include the authentication and identity information needed for login, roles, claims, external logins, and security tokens. Todo items should store a title, completion state, and owner relationship so each item can be associated with the user who created or manages it. The stored user, role, and ownership data should support application-level authorization rules such as users managing their own todos and privileged roles performing administrative actions.
```

This requirement covers:

- user authentication and identity information;
- roles, claims, external logins, and tokens;
- the title, completion state, and ownership relationship of Todo items;
- the authorization difference between normal users and administrators.

It does not directly expose concrete table names, column names, primary keys, foreign keys, or indexes from the reference DDL.

The final access-pattern descriptions are:

| id | Access-pattern description |
| --- | --- |
| w1 | List all todo items that belong to a specific user. |
| w2 | Retrieve a specific todo item by its identifier, but only if it is owned by the current logged-in user. |
| w3 | Create a new todo item with a title and assign it to the currently authenticated user. |
| w4 | Update the title or completion status of an existing todo item that belongs to the current user. |
| w5 | Delete a todo item that is owned by the current user. |
| w6 | Admin deletes any todo item by its identifier, regardless of ownership. |
| w7 | Register a new user account by providing an email and password. |
| w8 | Authenticate a user by their username to verify their password and generate a session token. |

These access patterns express application-level operations rather than SQL query templates. For example, `w1` is written as "List all todo items that belong to a specific user" rather than as a query over a concrete table and owner column. This preserves the access intent while reducing schema-answer leakage.

## 4. Quality Control

After construction, the instance is reviewed before being included in the benchmark. The review follows the same three quality-control aspects used in the annotation guidelines: reference executability, consistency validation, and answer leakage with linguistic quality.

For **reference executability**, the generated SQLite DDL is executed under the target DBMS and then parsed back into a schema representation. The reviewer checks that the executed schema preserves the expected table, column, foreign-key, and index counts. For this sample, the DDL execution and round-trip validation both pass, with 8 tables, 41 columns, 7 foreign keys, and 8 indexes.

For **consistency validation**, the reviewer records four sub-aspects for this sample.

First, for reference design consistency, the reviewer compares the Schema IR and generated DDL against the EF Core migrations, model snapshot, and `TodoDbContext.cs`. The Identity-related tables, Todo table, primary keys, foreign keys, and indexes are all supported by schema evidence. The later foreign-key migration is especially important: it changes the Todo ownership relationship from the earlier `UserName` reference to the final user `Id` reference, and the final reference design follows the later evidence.

Second, for requirement-evidence consistency, the reviewer checks that the requirement is supported by README and application behavior. The requirement mentions a user-authenticated Todo application, user registration and login, identity information, Todo ownership, and privileged administrative actions. These concepts are supported by the README and the API tests.

Third, for access-pattern-evidence consistency, the reviewer checks each workload item against retained tests or application code. In this sample, the Todo API tests support listing, retrieving, creating, updating, and deleting Todo items under ownership constraints, including administrator deletion. The User API tests support user registration and login/token generation.

Fourth, for benchmark input sufficiency, the reviewer checks whether the requirement and access patterns provide enough application-level information to motivate the essential reference design. For this sample, the input is sufficient because it explains why the database needs user identity data, authentication-related records, Todo items, an ownership relationship, and access paths for owner-scoped Todo operations. 

For **answer leakage and linguistic quality**, the reviewer inspects the final requirement and workload descriptions as written for this sample. The accepted version uses application-level phrases such as "registered users", "manage their own todo items", "privileged roles", and "session token". It does not expose concrete table names, column names, primary keys, foreign keys, index names, or SQL fragments. Leakage-prone drafts such as "retrieve todos by filtering on the owner identifier" are rewritten as "List all todo items that belong to a specific user", preserving the access intent without revealing the reference schema.

The final review decision is assigned as follows:

| Aspect | Decision for this sample |
| --- | --- |
| Reference executability |  Pass |
| Reference consistency | Pass |
| Requirement-evidence consistency  | Pass |
| Access-pattern-evidence consistency | Pass |
| Benchmark input sufficiency | Pass |
| Leakage and language | Pass |

