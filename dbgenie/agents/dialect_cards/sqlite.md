# Dialect Card: SQLite

Dialect id: `sqlite`

Executor/runtime:
- Executor: Python `sqlite3` package through `AgentToolbox` in an in-memory database.
- Runtime version: detected from `sqlite3.sqlite_version` and recorded in `ddl_execution.runtime_version`.
- Execution enables `PRAGMA foreign_keys = ON`.
- Treat this card as executor-grounded: generate for the SQLite library linked to the active Python runtime, not for arbitrary SQLite builds.

Core rules:
- SQLite accepts double-quoted identifiers.
- Prefer `INTEGER` primary keys for rowid-backed surrogate keys; generic identity clauses are usually omitted in this V1 generator.
- Use SQLite type affinity: `INTEGER`, `REAL`, `TEXT`, `BLOB`, `NUMERIC`, `BOOLEAN`, `DATETIME`, and `DATE` are acceptable declarations.
- Foreign keys must be inline in `CREATE TABLE` or otherwise compatible with SQLite limitations; execution should enable `PRAGMA foreign_keys = ON`.
- SQLite supports simple indexes and unique indexes.
- SQLite does not support PostgreSQL/SQL Server `INCLUDE` indexes.
- SQLite partial indexes exist, but V1 physical lowering currently treats filtered physical indexes as unsupported unless explicitly implemented.
- Avoid MySQL backticks, `AUTO_INCREMENT`, SQL Server `IDENTITY(1,1)`, and PostgreSQL identity syntax.

Review checklist:
- Generated DDL can run through an in-memory SQLite executor.
- No unsupported `ALTER TABLE ... ADD CONSTRAINT` foreign key statements are introduced.
- No `INCLUDE` clause appears in indexes.
