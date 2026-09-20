from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "benchmark" / "devdb_bench.json"
CONFIG_PATH = REPO_ROOT / "configs" / "default.toml"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"

EXPECTED_SAMPLE_COUNT = 51
EXPECTED_WORKLOAD_COUNT = 379
EXPECTED_DDL_COUNT = 51

ROOT_FIELDS = {"dataset_name", "candidate_count", "candidates"}
SAMPLE_FIELDS = {
    "full_name",
    "url",
    "license",
    "stars",
    "forks",
    "pushed_at",
    "dbms_final",
    "schema_artifact_final",
    "ecosystem_final",
    "application_domain_final",
    "requirement",
    "workload",
    "reference_ddl_path",
}
WORKLOAD_FIELDS = {"id", "description"}
EXPECTED_ENV_NAMES = {
    "DBGENIE_LLM_DEEPSEEK_BASE_URL",
    "DBGENIE_LLM_DEEPSEEK_API_KEY",
    "DBGENIE_LLM_DEEPSEEK_MODEL",
    "DBGENIE_LLM_QWEN_BASE_URL",
    "DBGENIE_LLM_QWEN_API_KEY",
    "DBGENIE_LLM_QWEN_MODEL",
    "DBGENIE_LLM_GPT_BASE_URL",
    "DBGENIE_LLM_GPT_API_KEY",
    "DBGENIE_LLM_GPT_MODEL",
    "DBGENIE_GITHUB_TOKEN",
}


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read valid JSON from {path}: {exc}") from exc


def verify_release_layout() -> None:
    required_paths = (
        REPO_ROOT / "README.md",
        REPO_ROOT / "pyproject.toml",
        ENV_EXAMPLE_PATH,
        CONFIG_PATH,
        DATASET_PATH,
        REPO_ROOT / "benchmark" / "reference_ddl",
        REPO_ROOT / "dbgenie" / "cli.py",
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_paths if not path.exists()]
    require(not missing, "missing required artifact paths: " + ", ".join(missing))
    require(not (REPO_ROOT / ".env").exists(), ".env must not be present in the release")
    require(not (REPO_ROOT / "tests").exists(), "tests/ must not be present in the release")
    require(not (REPO_ROOT / ".gitignore").exists(), ".gitignore must not be present in the release")


def parse_env_example() -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        ENV_EXAMPLE_PATH.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        require("=" in line, f".env.example line {line_number} is not KEY=VALUE")
        name, value = line.split("=", 1)
        name = name.strip()
        require(name and name not in values, f"invalid or duplicate environment variable: {name!r}")
        values[name] = value.strip()

    require(
        set(values) == EXPECTED_ENV_NAMES,
        ".env.example variables differ from the expected DBGenie interface",
    )
    secret_names = [
        name for name in values if name.endswith("_API_KEY") or name.endswith("_TOKEN")
    ]
    populated = [name for name in secret_names if values[name]]
    require(not populated, ".env.example contains populated secrets: " + ", ".join(populated))
    return values


def verify_config_secrets() -> None:
    secret_fields: set[str] = set()
    for line_number, raw_line in enumerate(
        CONFIG_PATH.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        name, value = (part.strip() for part in line.split("=", 1))
        if name not in {"api_key", "token"}:
            continue
        secret_fields.add(name)
        require(
            value in {'""', "''"},
            f"configs/default.toml line {line_number} contains a populated {name}",
        )
    require(
        secret_fields == {"api_key", "token"},
        "configs/default.toml must declare empty api_key and token fields",
    )


def verify_dataset() -> tuple[dict[str, Any], int, int]:
    release = read_json(DATASET_PATH)
    require(isinstance(release, dict), "benchmark/devdb_bench.json must contain an object")
    require(set(release) == ROOT_FIELDS, "dataset root fields do not match the release schema")
    require(release["dataset_name"] == "DevDB-Bench", "dataset_name must be DevDB-Bench")

    candidates = release["candidates"]
    require(isinstance(candidates, list), "candidates must be a list")
    require(release["candidate_count"] == EXPECTED_SAMPLE_COUNT, "candidate_count must be 51")
    require(len(candidates) == EXPECTED_SAMPLE_COUNT, "dataset must contain 51 candidates")

    names: set[str] = set()
    ddl_paths: set[str] = set()
    workload_count = 0
    reference_root = (REPO_ROOT / "benchmark" / "reference_ddl").resolve()

    for index, candidate in enumerate(candidates, start=1):
        require(isinstance(candidate, dict), f"candidate {index} must be an object")
        require(set(candidate) == SAMPLE_FIELDS, f"candidate {index} fields do not match the schema")
        full_name = candidate["full_name"]
        require(isinstance(full_name, str) and full_name.strip(), f"candidate {index} has no full_name")
        require(full_name not in names, f"duplicate candidate full_name: {full_name}")
        names.add(full_name)

        require(isinstance(candidate["stars"], int), f"{full_name}: stars must be an integer")
        require(isinstance(candidate["forks"], int), f"{full_name}: forks must be an integer")
        require(str(candidate["requirement"]).strip(), f"{full_name}: requirement is empty")

        workload = candidate["workload"]
        require(isinstance(workload, list), f"{full_name}: workload must be a list")
        workload_ids: set[str] = set()
        for item in workload:
            require(
                isinstance(item, dict) and set(item) == WORKLOAD_FIELDS,
                f"{full_name}: workload fields do not match the schema",
            )
            workload_id = item["id"]
            require(workload_id not in workload_ids, f"{full_name}: duplicate workload id {workload_id}")
            workload_ids.add(workload_id)
            require(str(item["description"]).strip(), f"{full_name}: workload {workload_id} is empty")
        workload_count += len(workload)

        relative_ddl = candidate["reference_ddl_path"]
        require(
            isinstance(relative_ddl, str) and relative_ddl.startswith("benchmark/reference_ddl/"),
            f"{full_name}: invalid reference_ddl_path",
        )
        ddl_path = (REPO_ROOT / Path(relative_ddl)).resolve()
        require(
            ddl_path == reference_root or reference_root in ddl_path.parents,
            f"{full_name}: reference_ddl_path escapes benchmark/reference_ddl",
        )
        require(ddl_path.is_file(), f"{full_name}: missing reference DDL {relative_ddl}")
        require(ddl_path.stat().st_size > 0, f"{full_name}: reference DDL is empty")
        ddl_paths.add(relative_ddl)

    require(workload_count == EXPECTED_WORKLOAD_COUNT, "dataset must contain 379 workloads")
    require(len(ddl_paths) == EXPECTED_DDL_COUNT, "dataset must reference 51 unique DDL files")
    return release, workload_count, len(ddl_paths)


def verify_runtime_loader(release: dict[str, Any]) -> None:
    try:
        from dbgenie.agents.inputs import load_agent_tasks
    except ImportError as exc:
        raise VerificationError(
            "cannot import DBGenie; run the README installation commands first"
        ) from exc

    tasks = load_agent_tasks(DATASET_PATH, input_format="candidate")
    candidates = release["candidates"]
    require(len(tasks) == EXPECTED_SAMPLE_COUNT, "runtime loader did not produce 51 tasks")
    for task, candidate in zip(tasks, candidates, strict=True):
        require(task.source == candidate["full_name"], f"loader source mismatch for {task.id}")
        require(
            task.requirement == candidate["requirement"],
            f"loader requirement mismatch for {task.id}",
        )
        require(task.target_dbms == candidate["dbms_final"], f"loader DBMS mismatch for {task.id}")
        require(
            [item.to_dict() for item in task.workload] == candidate["workload"],
            f"loader workload mismatch for {task.id}",
        )


def verify_keyless_dry_run() -> None:
    child_env = os.environ.copy()
    for name in tuple(child_env):
        if name.startswith("DBGENIE_LLM_") or name == "DBGENIE_GITHUB_TOKEN":
            child_env.pop(name, None)

    with tempfile.TemporaryDirectory(prefix="dbgenie-artifact-") as temp_dir:
        temp_root = Path(temp_dir)
        output_path = temp_root / "outputs" / "dry_run.json"
        run_dir = temp_root / "runs" / "dry_run"
        command = [
            sys.executable,
            "-m",
            "dbgenie.cli",
            "run-method",
            str(DATASET_PATH),
            "--config",
            str(CONFIG_PATH),
            "--llm-profile",
            "deepseek",
            "--output",
            str(output_path),
            "--run-dir",
            str(run_dir),
            "--variant",
            "full",
            "--limit",
            "1",
            "--jobs",
            "1",
            "--dry-run",
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=REPO_ROOT,
                env=child_env,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise VerificationError("keyless dry-run timed out after 180 seconds") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "no process output").strip()
            raise VerificationError(
                f"keyless dry-run exited with {completed.returncode}: {detail}"
            )

        payload = read_json(output_path)
        require(payload.get("task_count") == 1, "dry-run task_count must be 1")
        require(payload.get("result_count") == 1, "dry-run result_count must be 1")
        results = payload.get("results")
        require(isinstance(results, list) and len(results) == 1, "dry-run must contain one result")
        require(results[0].get("status") == "dry_run", "dry-run result status must be dry_run")


def main() -> int:
    try:
        verify_release_layout()
        print("[1/5] Release layout: PASS")
        parse_env_example()
        verify_config_secrets()
        print("[2/5] Configuration templates: PASS")
        release, workload_count, ddl_count = verify_dataset()
        print("[3/5] DevDB-Bench dataset: PASS")
        verify_runtime_loader(release)
        print("[4/5] Runtime task loader: PASS")
        verify_keyless_dry_run()
        print("[5/5] Keyless temporary dry-run: PASS")
    except (VerificationError, OSError, ValueError, TypeError) as exc:
        print(f"Artifact verification FAILED: {exc}", file=sys.stderr)
        return 1

    print(
        "Artifact verification PASSED: "
        f"{EXPECTED_SAMPLE_COUNT} samples, {workload_count} workloads, "
        f"{ddl_count} reference DDL files; dry-run status=dry_run."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
