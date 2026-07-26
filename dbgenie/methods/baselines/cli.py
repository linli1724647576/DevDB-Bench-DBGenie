from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from dbgenie.agents.inputs import load_agent_tasks
from dbgenie.agents.types import AgentTaskInput
from dbgenie.core.config import get_llm_config, load_config
from dbgenie.core.io import write_json
from dbgenie.llm.client import LLMClient

from .contracts import BaselineMethod, BaselineRunOutcome, BaselineRunResult
from .registry import available_baseline_methods, get_baseline_method


ProgressCallback = Callable[[str], None]


def run_baseline(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dbgenie run-baseline")
    parser.add_argument("input_json")
    parser.add_argument("--method", choices=available_baseline_methods(), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--input-format", choices=["auto", "candidate", "task"], default="auto")
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--llm-profile", default="default")
    parser.add_argument("--run-dir", default="runs/baseline")
    parser.add_argument("--trace-dir")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--preview-prompt", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args(argv)
    previous_sigint_handler = _install_fast_sigint_handler()

    try:
        method = get_baseline_method(args.method)
        tasks = load_agent_tasks(args.input_json, input_format=args.input_format, limit=args.limit)
        if args.preview_prompt:
            _write_prompt_preview(
                output=Path(args.output),
                source_file=args.input_json,
                input_format=args.input_format,
                method=method,
                tasks=tasks,
            )
            return 0

        config = load_config(args.config)
        llm_config = get_llm_config(config, args.llm_profile)
        jobs = max(1, int(args.jobs or 1))
        trace_dir = Path(args.trace_dir) if args.trace_dir else Path(args.run_dir) / "_traces"
        print_lock = threading.Lock()

        def run_one(index: int, task: AgentTaskInput) -> dict[str, str]:
            progress = _progress_callback(
                args.progress,
                task_index=index + 1,
                task_count=len(tasks),
                task_id=task.id,
                print_lock=print_lock,
            )
            try:
                progress("generating")
                outcome = method.execute(
                    task,
                    llm_config,
                    llm_client_factory=LLMClient,
                    progress=progress,
                )
            except Exception as exc:  # pragma: no cover - integration safeguard
                progress(f"failed error={type(exc).__name__}: {exc}")
                outcome = BaselineRunOutcome(
                    result=BaselineRunResult(task_id=task.id, status="failed", final_ddl=""),
                    trace={
                        "task_id": task.id,
                        "method": method.name,
                        "status": "failed",
                        "errors": [f"{type(exc).__name__}: {exc}"],
                    },
                )
            result = outcome.result
            write_json(Path(args.run_dir) / f"{task.id}.json", result.to_dict())
            if outcome.trace is not None:
                write_json(trace_dir / f"{task.id}.json", outcome.trace)
            progress(f"done status={result.status}")
            return result.to_dict()

        results = _run_tasks(tasks, jobs=jobs, run_one=run_one)
        payload = {
            "source_file": args.input_json,
            "input_format": args.input_format,
            "method": method.name,
            "prompt_version": method.prompt_version,
            "example_ids": list(method.example_ids),
            "llm_profile": args.llm_profile,
            "llm": LLMClient(llm_config).metadata(),
            "run_dir": args.run_dir,
            "trace_dir": trace_dir.as_posix(),
            "jobs": jobs,
            "task_count": len(tasks),
            "result_count": len(results),
            "results": results,
        }
        write_json(args.output, payload)
        return 0
    except KeyboardInterrupt:  # pragma: no cover - terminal behavior
        _exit_after_keyboard_interrupt()
        return 130
    finally:
        _restore_sigint_handler(previous_sigint_handler)


def _write_prompt_preview(
    *,
    output: Path,
    source_file: str,
    input_format: str,
    method: BaselineMethod,
    tasks: list[AgentTaskInput],
) -> None:
    write_json(
        output,
        {
            "mode": "prompt_preview",
            "source_file": source_file,
            "input_format": input_format,
            "method": method.name,
            "prompt_version": method.prompt_version,
            "example_ids": list(method.example_ids),
            "task_count": len(tasks),
            "prompts": [
                {
                    "task_id": task.id,
                    **method.preview(task),
                }
                for task in tasks
            ],
        },
    )


def _run_tasks(
    tasks: list[AgentTaskInput],
    *,
    jobs: int,
    run_one: Callable[[int, AgentTaskInput], dict[str, str]],
) -> list[dict[str, str]]:
    if jobs == 1 or len(tasks) <= 1:
        return [run_one(index, task) for index, task in enumerate(tasks)]
    results: list[dict[str, str] | None] = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(run_one, index, task): index
            for index, task in enumerate(tasks)
        }
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return [item for item in results if item is not None]


def _progress_callback(
    enabled: bool,
    *,
    task_index: int,
    task_count: int,
    task_id: str,
    print_lock: threading.Lock,
) -> ProgressCallback:
    if not enabled:
        return lambda message: None

    def emit(message: str) -> None:
        with print_lock:
            print(f"[{task_index}/{task_count} {task_id}] {message}", flush=True)

    return emit


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
        sys.stderr.write("\n[run-baseline] interrupted by Ctrl+C; exiting immediately.\n")
        sys.stderr.flush()
    finally:
        os._exit(130)
