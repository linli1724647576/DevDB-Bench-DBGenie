from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PASSWORD = "dbgenie_pass"
PG_NAME = "dbgenie_refddl_pg_20260602"
MY_NAME = "dbgenie_refddl_mysql_20260602"
MA_NAME = "dbgenie_refddl_mariadb_20260602"
SS_NAME = "dbgenie_refddl_sqlserver_20260602"
SQLSERVER_PASSWORD = "DBGenie_Strong_Pass_2026!"


def run(cmd: list[str], input_text: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True, timeout=timeout)


def docker_rm(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_postgres() -> None:
    docker_rm(PG_NAME)
    cp = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            PG_NAME,
            "-e",
            f"POSTGRES_PASSWORD={PASSWORD}",
            "postgres:16-alpine",
        ],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr)
    for _ in range(60):
        ok = run(["docker", "exec", PG_NAME, "pg_isready", "-U", "postgres"], timeout=10)
        if ok.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("postgres did not become ready")


def start_mysql_like(name: str, image: str, env_name: str, admin_bin: str = "mysqladmin") -> None:
    docker_rm(name)
    cp = run(
        ["docker", "run", "-d", "--name", name, "-e", f"{env_name}={PASSWORD}", image],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr)
    for _ in range(90):
        ok = run(
            [
                "docker",
                "exec",
                name,
                admin_bin,
                "ping",
                "-h127.0.0.1",
                "--protocol=tcp",
                "-uroot",
                f"-p{PASSWORD}",
            ],
            timeout=10,
        )
        if ok.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"{image} did not become ready")


def start_sqlserver() -> None:
    docker_rm(SS_NAME)
    cp = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            SS_NAME,
            "-e",
            "ACCEPT_EULA=Y",
            "-e",
            f"MSSQL_SA_PASSWORD={SQLSERVER_PASSWORD}",
            "mcr.microsoft.com/mssql/server:2022-latest",
        ],
        timeout=60,
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr)
    for _ in range(90):
        ok = _sqlserver_query("master", "SELECT 1", timeout=20)
        if ok.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("SQL Server did not become ready")


def db_name(full_name: str) -> str:
    return ("t2d_" + re.sub(r"[^a-zA-Z0-9_]", "_", full_name).lower())[:48]


def ddl_path(root: Path, candidate: dict[str, Any]) -> Path | None:
    path = candidate.get("reference_ddl_path")
    if not path:
        path = (candidate.get("reference_ddl_generation") or {}).get("ddl_path")
    if path:
        return root / path
    return None


def validate_sqlite(ddl: str) -> dict[str, Any]:
    try:
        con = sqlite3.connect(":memory:")
        con.execute("PRAGMA foreign_keys = ON;")
        con.executescript(ddl)
        rows = con.execute("SELECT count(*) FROM sqlite_master WHERE type='table';").fetchone()[0]
        con.close()
        return {"status": "passed", "executed": True, "table_count_runtime": rows, "error": None}
    except Exception as exc:
        return {"status": "failed", "executed": True, "error": str(exc)}


def validate_duckdb(ddl: str) -> dict[str, Any]:
    if not importlib.util.find_spec("duckdb"):
        return {
            "status": "skipped",
            "executed": False,
            "reason": "duckdb Python package is not installed",
        }
    import duckdb  # type: ignore[import-not-found]

    try:
        con = duckdb.connect(database=":memory:")
        con.execute(ddl)
        rows = con.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'main';"
        ).fetchone()[0]
        con.close()
        return {"status": "passed", "executed": True, "table_count_runtime": int(rows), "error": None}
    except Exception as exc:
        return {"status": "failed", "executed": True, "error": str(exc)}


def validate_postgres(candidate: dict[str, Any], ddl: str) -> dict[str, Any]:
    database = db_name(candidate["full_name"])
    run(
        ["docker", "exec", PG_NAME, "psql", "-U", "postgres", "-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {database};"],
        timeout=30,
    )
    create = run(
        ["docker", "exec", PG_NAME, "psql", "-U", "postgres", "-d", "postgres", "-c", f"CREATE DATABASE {database};"],
        timeout=30,
    )
    if create.returncode != 0:
        return {"status": "failed", "executed": False, "error": create.stderr}
    cp = run(
        ["docker", "exec", "-i", PG_NAME, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", database],
        input_text=ddl,
        timeout=180,
    )
    if cp.returncode != 0:
        return {"status": "failed", "executed": True, "error": (cp.stderr or cp.stdout)[-4000:]}
    count = run(
        [
            "docker",
            "exec",
            PG_NAME,
            "psql",
            "-U",
            "postgres",
            "-d",
            database,
            "-tAc",
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';",
        ],
        timeout=30,
    )
    return {
        "status": "passed",
        "executed": True,
        "table_count_runtime": int(count.stdout.strip() or 0),
        "error": None,
    }


def validate_mysql_like(
    container: str,
    candidate: dict[str, Any],
    ddl: str,
    client_bin: str = "mysql",
) -> dict[str, Any]:
    database = db_name(candidate["full_name"])
    init = f"DROP DATABASE IF EXISTS `{database}`; CREATE DATABASE `{database}`;"
    connection_args = [client_bin, "-h127.0.0.1", "--protocol=tcp", "-uroot", f"-p{PASSWORD}"]
    cp = run(["docker", "exec", "-i", container, *connection_args], input_text=init, timeout=60)
    if cp.returncode != 0:
        return {"status": "failed", "executed": False, "error": (cp.stderr or cp.stdout)[-4000:]}
    cp = run(
        ["docker", "exec", "-i", container, *connection_args, database],
        input_text=ddl,
        timeout=180,
    )
    if cp.returncode != 0:
        return {"status": "failed", "executed": True, "error": (cp.stderr or cp.stdout)[-4000:]}
    count = run(
        [
            "docker",
            "exec",
            "-i",
            container,
            *connection_args,
            "-N",
            "-B",
            database,
            "-e",
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE();",
        ],
        timeout=30,
    )
    try:
        table_count = int((count.stdout or "0").strip().splitlines()[-1])
    except Exception:
        table_count = None
    return {
        "status": "passed",
        "executed": True,
        "table_count_runtime": table_count,
        "error": None,
    }


def validate_sqlserver(candidate: dict[str, Any], ddl: str) -> dict[str, Any]:
    database = db_name(candidate["full_name"])
    init = (
        f"IF DB_ID(N'{database}') IS NOT NULL BEGIN ALTER DATABASE [{database}] "
        f"SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]; END; "
        f"CREATE DATABASE [{database}];"
    )
    cp = _sqlserver_query("master", init, timeout=120)
    if cp.returncode != 0:
        return {"status": "failed", "executed": False, "error": (cp.stderr or cp.stdout)[-4000:]}
    cp = _sqlserver_script(database, ddl, timeout=240)
    if cp.returncode != 0:
        return {"status": "failed", "executed": True, "error": (cp.stderr or cp.stdout)[-4000:]}
    count = _sqlserver_query(
        database,
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';",
        timeout=60,
    )
    table_count = None
    for line in (count.stdout or "").splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            table_count = int(stripped)
            break
    return {
        "status": "passed",
        "executed": True,
        "table_count_runtime": table_count,
        "error": None,
    }


def _sqlserver_query(database: str, query: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            f"container:{SS_NAME}",
            "mcr.microsoft.com/mssql-tools",
            "/opt/mssql-tools/bin/sqlcmd",
            "-S",
            "localhost",
            "-U",
            "sa",
            "-P",
            SQLSERVER_PASSWORD,
            "-d",
            database,
            "-b",
            "-Q",
            query,
        ],
        timeout=timeout,
    )


def _sqlserver_script(database: str, script: str, timeout: int) -> subprocess.CompletedProcess[str]:
    command = (
        "cat > /tmp/dbgenie_ddl.sql && "
        f"/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{SQLSERVER_PASSWORD}' "
        f"-d '{database}' -b -i /tmp/dbgenie_ddl.sql"
    )
    return run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            f"container:{SS_NAME}",
            "mcr.microsoft.com/mssql-tools",
            "/bin/bash",
            "-lc",
            command,
        ],
        input_text=script,
        timeout=timeout,
    )


def validate_candidate(root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    dbms = candidate.get("dbms_final")
    path = ddl_path(root, candidate)
    if not path or not path.exists():
        result = {"status": "failed", "executed": False, "error": f"missing ddl path: {path}"}
    else:
        ddl = path.read_text(encoding="utf-8", errors="ignore")
        if dbms == "SQLite":
            result = validate_sqlite(ddl)
        elif dbms == "DuckDB":
            result = validate_duckdb(ddl)
        elif dbms == "PostgreSQL":
            result = validate_postgres(candidate, ddl)
        elif dbms == "MySQL":
            result = validate_mysql_like(MY_NAME, candidate, ddl)
        elif dbms == "MariaDB":
            result = validate_mysql_like(MA_NAME, candidate, ddl, client_bin="mariadb")
        elif dbms == "SQL Server":
            result = validate_sqlserver(candidate, ddl)
        else:
            result = {"status": "skipped", "executed": False, "reason": f"unsupported dbms {dbms}"}
    return {
        "full_name": candidate["full_name"],
        "dbms_final": dbms,
        "ddl_path": path.as_posix() if path else "",
        **result,
    }


def build_report(source: Path, candidate_count: int, results: list[dict[str, Any]]) -> str:
    by_status = Counter(result["status"] for result in results)
    by_dbms_status: dict[str, Counter[str]] = {}
    for result in results:
        by_dbms_status.setdefault(result["dbms_final"], Counter())[result["status"]] += 1
    lines = [
        "# Reference DDL Runtime Validation Report",
        "",
        f"- 输入样本：`{source.as_posix()}`",
        f"- 样本数：{candidate_count}",
        "",
        "## 状态统计",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(by_status.items()))
    lines.extend(["", "## DBMS 分布与执行结果", ""])
    for dbms, counts in sorted(by_dbms_status.items()):
        lines.append(f"- {dbms}: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    failed = [result for result in results if result["status"] == "failed"]
    skipped = [result for result in results if result["status"] == "skipped"]
    lines.extend(["", "## 失败样本", ""])
    if not failed:
        lines.append("- 无")
    else:
        for result in failed:
            error = (result.get("error") or "").replace("\n", " ")[:500]
            lines.append(f"- `{result['full_name']}` | DBMS={result['dbms_final']} | {error}")
    lines.extend(["", "## 跳过样本", ""])
    if not skipped:
        lines.append("- 无")
    else:
        for result in skipped:
            lines.append(f"- `{result['full_name']}` | DBMS={result['dbms_final']} | {result.get('reason')}")
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- SQLite 使用 Python 内存数据库执行。",
            "- PostgreSQL 使用 `postgres:16-alpine` 临时容器执行。",
            "- MySQL 使用 `mysql:8.4` 临时容器执行。",
            "- MariaDB 使用 `mariadb:11.4` 临时容器执行。",
            "- SQL Server 本轮未配置 runtime 容器，因此仅标记 skipped。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    root = Path(".").resolve()
    source = Path(args.candidate_json)
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    candidates = payload.get("candidates", [])
    if args.limit:
        candidates = candidates[: args.limit]

    results: list[dict[str, Any]] = []
    dbms_set = {candidate.get("dbms_final") for candidate in candidates}
    if "PostgreSQL" in dbms_set:
        start_postgres()
    if "MySQL" in dbms_set:
        start_mysql_like(MY_NAME, "mysql:8.4", "MYSQL_ROOT_PASSWORD")
    if "MariaDB" in dbms_set:
        start_mysql_like(MA_NAME, "mariadb:11.4", "MARIADB_ROOT_PASSWORD", admin_bin="mariadb-admin")
    if "SQL Server" in dbms_set:
        start_sqlserver()
    try:
        for index, candidate in enumerate(candidates, start=1):
            if args.progress:
                print(f"[{index}/{len(candidates)}] {candidate['full_name']} {candidate.get('dbms_final')}", flush=True)
            results.append(validate_candidate(root, candidate))
    finally:
        if "PostgreSQL" in dbms_set:
            docker_rm(PG_NAME)
        if "MySQL" in dbms_set:
            docker_rm(MY_NAME)
        if "MariaDB" in dbms_set:
            docker_rm(MA_NAME)
        if "SQL Server" in dbms_set:
            docker_rm(SS_NAME)

    by_status = Counter(result["status"] for result in results)
    by_dbms_status: dict[str, Counter[str]] = {}
    for result in results:
        by_dbms_status.setdefault(result["dbms_final"], Counter())[result["status"]] += 1
    output_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": source.as_posix(),
        "candidate_count": len(candidates),
        "summary": {
            "by_status": dict(by_status),
            "by_dbms_status": {key: dict(value) for key, value in sorted(by_dbms_status.items())},
        },
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = Path(args.report_output)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(build_report(source, len(candidates), results), encoding="utf-8")
    print(json.dumps(output_payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
