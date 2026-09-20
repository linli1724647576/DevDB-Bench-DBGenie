# Dialect Card: MariaDB

Dialect id: `mariadb`

Executor/runtime:
- Executor: Docker `mariadb:11.4` through `AgentToolbox`.
- Runtime version: detected at execution time with `SELECT VERSION()` and recorded in `ddl_execution.runtime_version`.
- Treat this card as executor-grounded: generate for the configured Docker runtime and default MariaDB behavior, not for generic MySQL behavior when MariaDB differs.

Core rules:
- MariaDB is MySQL-like for this V1 pipeline.
- Quote identifiers with backticks when quoting is needed.
- Use `AUTO_INCREMENT` for DB-managed integer surrogate keys.
- Use `BOOLEAN`, `VARCHAR(n)`, `TEXT`, `BIGINT`, `INT`, `DATETIME`, `DATE`, `TIME`, `DECIMAL(p,s)`, and JSON-compatible text when needed.
- MariaDB does not support PostgreSQL-style partial indexes with `WHERE`.
- MariaDB does not support covering index `INCLUDE`.
- Avoid PostgreSQL-only identity syntax, `JSONB`, and SQL Server square brackets.

Review checklist:
- Indexed text/blob columns are bounded or intentionally narrowed.
- Generated table, index, constraint, and foreign-key identifiers must not exceed 64 characters; shorten derived names deterministically while preserving uniqueness.
- InnoDB index keys must fit the 3072-byte limit. Account for the encoded byte width of every indexed character column.
- Create referenced tables before foreign keys that target them, or add foreign keys with `ALTER TABLE` after all participating tables exist.
- Do not generate a `CHECK` constraint whose expression references an `AUTO_INCREMENT` column; MariaDB 11.4 rejects it at execution time.
- No `WHERE` or `INCLUDE` clause appears in `CREATE INDEX`.
- Foreign key column types match referenced key columns.
