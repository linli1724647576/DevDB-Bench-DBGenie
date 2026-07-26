from __future__ import annotations

import argparse
import os
import signal
import sys
import traceback
import threading
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Callable

from dbgenie.agents.inputs import load_agent_tasks
from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import get_llm_config, load_config
from dbgenie.core.io import read_json, write_json
from dbgenie.llm.client import LLMClient
from dbgenie.methods.ablations.registry import (
    available_method_variants,
    get_method_definition,
)

from .definition import FULL_METHOD_DEFINITION, DynamicMethodDefinition
from .pipeline import DynamicMethodOptions, DynamicMethodPipeline
from .tools import DynamicMethodToolbox


def run_method(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dbgenie run-method")
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--input-format", choices=["auto", "candidate", "task"], default="auto")
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--llm-profile", default="default")
    parser.add_argument("--variant", choices=available_method_variants(), default="full")
    parser.add_argument("--run-dir")
    parser.add_argument("--ddl-executor", choices=["docker"], default="docker")
    parser.add_argument(
        "--max-turns",
        "--max-scheduler-steps",
        dest="max_turns",
        type=int,
        default=20,
        help=(
            "maximum normal scheduler decisions; trace events do not consume this budget; "
            "retained but ignored by fixed-pipeline variants"
        ),
    )
    parser.add_argument("--max-repairs", type=int, default=3)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args(argv)
    previous_sigint_handler = _install_fast_sigint_handler()

    try:
        config = load_config(args.config)
        llm_config = get_llm_config(config, args.llm_profile)
        method_definition = get_method_definition(args.variant)
        run_dir = _resolve_run_dir(args.run_dir, method_definition)
        tasks = load_agent_tasks(args.input_json, input_format=args.input_format, limit=args.limit)
        jobs = max(1, int(args.jobs or 1))
        print_lock = threading.Lock()

        def run_one(index: int, task):
            progress = _progress_callback(
                args.progress,
                task_index=index + 1,
                task_count=len(tasks),
                task_id=task.id,
                print_lock=print_lock,
            )
            llm_client: LLMClient | None = None
            try:
                llm_client = LLMClient(llm_config)
                toolbox = DynamicMethodToolbox(execution_mode=args.ddl_executor)
                pipeline = DynamicMethodPipeline(
                    llm_client,
                    DynamicMethodOptions(
                        run_dir=run_dir,
                        dry_run=bool(args.dry_run),
                        max_turns=int(args.max_turns),
                        max_repairs=int(args.max_repairs),
                        ddl_executor=args.ddl_executor,
                        progress_callback=progress,
                    ),
                    toolbox=toolbox,
                    method_definition=method_definition,
                )
                return pipeline.run(task).to_dict()
            except Exception as exc:  # pragma: no cover - exercised through CLI integration paths
                result = _write_failed_run_result(
                    task,
                    run_dir=run_dir,
                    llm=llm_client.metadata() if llm_client else {},
                    error=exc,
                    method_definition=method_definition,
                )
                if callable(progress):
                    progress("done status=failed")
                return result

        if jobs == 1 or len(tasks) <= 1:
            results = [run_one(index, task) for index, task in enumerate(tasks)]
        else:
            results = _run_tasks_with_worker_pool(tasks, jobs, run_one)

        payload = {
            "source_file": args.input_json,
            "input_format": args.input_format,
            "variant": method_definition.name,
            "dry_run": bool(args.dry_run),
            "run_dir": run_dir.as_posix(),
            "ddl_executor": args.ddl_executor,
            "jobs": jobs,
            "task_count": len(tasks),
            "result_count": len(results),
            "results": results,
        }
        write_json(args.output, payload)
        return 0
    except KeyboardInterrupt:  # pragma: no cover - depends on terminal signal delivery
        _exit_after_keyboard_interrupt()
        return 130
    finally:
        _restore_sigint_handler(previous_sigint_handler)


def _run_tasks_with_worker_pool(
    tasks: list[Any],
    jobs: int,
    run_one: Callable[[int, Any], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run at most `jobs` samples concurrently and refill only after completion."""
    if jobs <= 1 or len(tasks) <= 1:
        return [run_one(index, task) for index, task in enumerate(tasks)]

    results_by_index: list[dict[str, Any] | None] = [None] * len(tasks)
    next_index = 0
    in_flight: dict[Future, int] = {}

    def submit_next(executor: ThreadPoolExecutor) -> None:
        nonlocal next_index
        if next_index >= len(tasks):
            return
        index = next_index
        in_flight[executor.submit(run_one, index, tasks[index])] = index
        next_index += 1

    executor = ThreadPoolExecutor(max_workers=min(jobs, len(tasks)))
    try:
        for _ in range(min(jobs, len(tasks))):
            submit_next(executor)
        while in_flight:
            done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in done:
                index = in_flight.pop(future)
                results_by_index[index] = future.result()
                submit_next(executor)
    except KeyboardInterrupt:
        for future in in_flight:
            future.cancel()
        _shutdown_executor(executor, wait=False, cancel_futures=True)
        raise
    except Exception:
        _shutdown_executor(executor, wait=False, cancel_futures=True)
        raise
    else:
        _shutdown_executor(executor, wait=True, cancel_futures=False)

    return [item for item in results_by_index if item is not None]


def _shutdown_executor(
    executor: ThreadPoolExecutor,
    *,
    wait: bool,
    cancel_futures: bool,
) -> None:
    try:
        executor.shutdown(wait=wait, cancel_futures=cancel_futures)
    except TypeError:  # pragma: no cover - compatibility with older Python versions
        executor.shutdown(wait=wait)


def _install_fast_sigint_handler():
    try:
        previous = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, _sigint_fast_exit)
        return previous
    except ValueError:
        return None


def _restore_sigint_handler(previous) -> None:
    if previous is None:
        return
    try:
        signal.signal(signal.SIGINT, previous)
    except ValueError:
        pass


def _sigint_fast_exit(signum, frame) -> None:  # pragma: no cover - terminal behavior
    del signum, frame
    _exit_after_keyboard_interrupt()


def _exit_after_keyboard_interrupt() -> None:  # pragma: no cover - terminal behavior
    try:
        sys.stderr.write("\n[run-method] interrupted by Ctrl+C; exiting immediately.\n")
        sys.stderr.flush()
    finally:
        os._exit(130)


def _write_failed_run_result(
    task: AgentTaskInput,
    *,
    run_dir: Path,
    llm: dict[str, Any],
    error: Exception,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> dict[str, Any]:
    run_path = run_dir / f"{task.id}.json"
    error_message = f"unhandled_exception: {type(error).__name__}: {error}"
    if run_path.exists():
        try:
            existing = _append_failure_to_existing_run(
                run_path,
                task=task,
                llm=llm,
                error=error,
                error_message=error_message,
                method_definition=method_definition,
            )
        except Exception:
            existing = None
        if existing is not None:
            write_json(run_path, existing)
            return existing
    state = {
        **method_definition.to_metadata(),
        "task": task.to_dict(),
        "current_phase": "failed",
        "artifacts": {},
        "turns": [
            {
                "index": 1,
                "speaker": "harness",
                "kind": "unhandled_exception",
                "status": "failed",
                "action": {},
                "output": {
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "traceback": traceback.format_exc(),
                },
                "warnings": [],
                "errors": [error_message],
            }
        ],
        "open_assumptions": [],
        "failure_events": [],
        "repair_history": [],
        "tool_request_proposals": [],
        "tool_results": [],
        "warnings": [],
        "errors": [error_message],
        "final_ddl": "",
        "final_explanation": "",
    }
    payload = {
        "task_id": task.id,
        **method_definition.to_metadata(),
        "status": "failed",
        "final_ddl": "",
        "final_explanation": "",
        "evaluation_metrics": _failed_evaluation_metrics(
            f"sample failed before method metrics could be collected: {error_message}"
        ),
        "state": state,
        "run_path": run_path.as_posix(),
        "llm": llm,
        "warnings": [],
        "errors": [error_message],
    }
    write_json(run_path, payload)
    return payload


def _append_failure_to_existing_run(
    run_path: Path,
    *,
    task: AgentTaskInput,
    llm: dict[str, Any],
    error: Exception,
    error_message: str,
    method_definition: DynamicMethodDefinition = FULL_METHOD_DEFINITION,
) -> dict[str, Any] | None:
    payload = read_json(run_path)
    if not isinstance(payload, dict):
        return None
    state = payload.get("state")
    if not isinstance(state, dict):
        return None

    state["current_phase"] = "failed"
    state.update(method_definition.to_metadata())
    turns = state.get("turns")
    if not isinstance(turns, list):
        turns = []
        state["turns"] = turns
    turns.append(
        {
            "index": len(turns) + 1,
            "speaker": "harness",
            "kind": "unhandled_exception",
            "status": "failed",
            "action": {},
            "output": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
            },
            "warnings": [],
            "errors": [error_message],
        }
    )

    state_errors = state.get("errors")
    if not isinstance(state_errors, list):
        state_errors = []
        state["errors"] = state_errors
    state_errors.append(error_message)

    payload_errors = payload.get("errors")
    if not isinstance(payload_errors, list):
        payload_errors = []
    payload_errors.append(error_message)

    payload["task_id"] = payload.get("task_id") or task.id
    payload.update(method_definition.to_metadata())
    payload["status"] = "failed"
    payload["state"] = state
    payload["run_path"] = run_path.as_posix()
    payload["llm"] = payload.get("llm") or llm
    payload["errors"] = payload_errors
    payload["warnings"] = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
    payload["final_ddl"] = payload.get("final_ddl") or state.get("final_ddl") or ""
    final_explanation = payload.get("final_explanation") or state.get("final_explanation") or ""
    state["final_explanation"] = final_explanation
    payload["final_explanation"] = final_explanation
    payload["evaluation_metrics"] = _metrics_with_sample_failed(payload.get("evaluation_metrics"))
    return payload


def _resolve_run_dir(
    value: str | None,
    method_definition: DynamicMethodDefinition,
) -> Path:
    if value:
        return Path(value)
    base = Path("runs/method")
    if method_definition.name == FULL_METHOD_DEFINITION.name:
        return base
    return base / method_definition.name


def _metrics_with_sample_failed(metrics: Any) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        return _failed_evaluation_metrics("sample failed before method metrics could be collected")
    updated = dict(metrics)
    final_state = dict(updated.get("final_state") or {})
    blockers = final_state.get("status_blockers")
    if not isinstance(blockers, list):
        blockers = []
    if "sample_failed" not in blockers:
        blockers.append("sample_failed")
    final_state["ready_evidence"] = False
    final_state["status_blockers"] = blockers
    updated["final_state"] = final_state
    return updated


def _failed_evaluation_metrics(warning: str) -> dict[str, Any]:
    del warning
    return {
        "ddl": {
            "present": False,
            "length": 0,
            "executable": False,
            "execution_evidence": "none",
            "real_execution": False,
        },
        "tests": {
            "generated": 0,
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": None,
            "real_execution": False,
        },
        "query_plan": {
            "required": False,
            "executed": 0,
            "failed": 0,
            "has_raw_evidence": False,
        },
        "final_state": {
            "ready_evidence": False,
            "pending_tool_requests": 0,
            "pending_sql_test_requests": 0,
            "stale_artifacts": [],
            "status_blockers": ["sample_failed"],
        },
    }


def _progress_callback(
    enabled: bool,
    *,
    task_index: int,
    task_count: int,
    task_id: str,
    print_lock,
):
    if not enabled:
        return None

    def emit(message: str) -> None:
        with print_lock:
            print(f"[{task_index}/{task_count} {task_id}] {message}", flush=True)

    return emit
