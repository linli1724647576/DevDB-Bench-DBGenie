# DBGenie

DBGenie generates database DDL from natural-language requirements and
workloads. This artifact also contains the 51-sample DevDB-Bench dataset,
baseline implementations, ablation variants, evaluation code, and dataset
construction utilities.

## Supported environment

This artifact is tested on:

- Windows 10 or Windows 11
- Windows PowerShell 5.1 or PowerShell 7
- CPython 3.10 (validated with Python 3.10.11)
- Docker Desktop using Linux containers for database execution

Linux and macOS are not supported by this release. Docker is not needed for the
artifact verification dry-run, but it is required for real PostgreSQL, MySQL,
MariaDB, and SQL Server execution.

Run every command below from the repository root, meaning the directory that
contains this README and `pyproject.toml`. The checkout directory can have any
name.

## Install

Create a clean virtual environment and install all method and evaluation
dependencies:

```powershell
py -3.10 --version
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[method,evaluation]"
.\.venv\Scripts\python.exe -m nltk.downloader wordnet omw-1.4
.\.venv\Scripts\python.exe -m spacy download en_core_web_sm
```

The NLTK command intentionally uses NLTK's default data directory so the
runtime can find the downloaded corpora without an additional `NLTK_DATA`
setting.

## Verify without API keys or Docker

Run the artifact verifier immediately after installation:

```powershell
.\.venv\Scripts\python.exe scripts\verify_artifact.py
```

The verifier checks the release layout, the full DevDB-Bench dataset, all
reference DDL paths, and the runtime task loader. It then runs one DBGenie task
with `--dry-run` in a temporary directory. It removes DBGenie API variables from
the child process, does not contact an LLM, does not invoke Docker, and does not
leave output files in the repository.

A successful run ends with a summary containing:

```text
Artifact verification PASSED: 51 samples, 379 workloads, 51 reference DDL files; dry-run status=dry_run.
```

## LLM configuration

Experiments select a model with `--llm-profile`. The available profiles and
their default models are defined in `configs/default.toml`:

- `deepseek`: `deepseek-v4-flash`
- `qwen`: `qwen3-coder-plus`
- `gpt`: `gpt-5.4`

`.env.example` is a variable reference only. DBGenie does not automatically
load `.env` files. Set variables in the PowerShell session that will run the
experiment. For DeepSeek:

```powershell
$env:DBGENIE_LLM_DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DBGENIE_LLM_DEEPSEEK_API_KEY="your-api-key"
```

For OpenAI-compatible Qwen and GPT endpoints:

```powershell
$env:DBGENIE_LLM_QWEN_BASE_URL="https://your-qwen-compatible-endpoint/v1"
$env:DBGENIE_LLM_QWEN_API_KEY="your-api-key"

$env:DBGENIE_LLM_GPT_BASE_URL="https://your-gpt-compatible-endpoint/v1"
$env:DBGENIE_LLM_GPT_API_KEY="your-api-key"
```

Override a configured model with
`DBGENIE_LLM_<PROFILE>_MODEL`. Do not place real keys in
`configs/default.toml` or commit them to the artifact.

## Docker preparation

Start Docker Desktop in Linux-container mode and verify the engine before a
real run:

```powershell
docker version
```

DBGenie uses `postgres:16-alpine`, `mysql:8.4`, `mariadb:11.4`, and
`mcr.microsoft.com/mssql/server:2022-latest` as needed. Docker pulls an image on
its first use. SQLite and DuckDB tasks use local Python runtimes.

## Dataset

The formal dataset is `benchmark/devdb_bench.json`. It contains 51 samples and
379 workloads. Every `reference_ddl_path` points to a corresponding file under
`benchmark/reference_ddl/`.

## Run DBGenie

First run one real sample to verify the configured LLM and Docker environment:

```powershell
.\.venv\Scripts\python.exe -m dbgenie.cli run-method `
  benchmark\devdb_bench.json `
  --config configs\default.toml `
  --llm-profile deepseek `
  --output outputs\dbgenie_deepseek_limit1.json `
  --run-dir runs\dbgenie_deepseek_limit1 `
  --variant full `
  --limit 1 `
  --jobs 1 `
  --progress
```

After that succeeds, remove `--limit 1` and use the full-run output paths:

```powershell
.\.venv\Scripts\python.exe -m dbgenie.cli run-method `
  benchmark\devdb_bench.json `
  --config configs\default.toml `
  --llm-profile deepseek `
  --output outputs\dbgenie_deepseek.json `
  --run-dir runs\dbgenie_deepseek `
  --variant full `
  --jobs 1 `
  --progress
```

## Run baselines

The available baselines are `few-shot`, `mac-sql`, and `schema-agent`:

```powershell
.\.venv\Scripts\python.exe -m dbgenie.cli run-baseline `
  benchmark\devdb_bench.json `
  --config configs\default.toml `
  --llm-profile deepseek `
  --method few-shot `
  --output outputs\few_shot_deepseek.json `
  --run-dir runs\few_shot_deepseek `
  --jobs 1 `
  --progress
```

## Run ablations

The available ablations are `without_requirement_analyst`,
`without_test_expert`, and `without_scheduler`:

```powershell
.\.venv\Scripts\python.exe -m dbgenie.cli run-method `
  benchmark\devdb_bench.json `
  --config configs\default.toml `
  --llm-profile deepseek `
  --output outputs\without_scheduler_deepseek.json `
  --run-dir runs\without_scheduler_deepseek `
  --variant without_scheduler `
  --jobs 1 `
  --progress
```

## Evaluate a completed run

Static design evaluation consumes the per-sample files in the selected run
directory. The first invocation downloads the FastEmbed model into
`models/fastembed/`:

```powershell
.\.venv\Scripts\python.exe -m dbgenie.cli evaluate-design-static `
  benchmark\devdb_bench.json `
  --run-dir runs\dbgenie_deepseek `
  --output outputs\evaluation_dbgenie_deepseek.json `
  --embedding-backend fastembed `
  --embedding-cache-dir models\fastembed
```

## Generated directories

The release does not include generated artifacts. Commands create their parent
directories automatically:

- `outputs/`: aggregate command results and evaluation reports
- `runs/`: per-sample method traces and runtime-IR caches
- `models/fastembed/`: the downloaded embedding model cache

The local `.venv/` directory is also generated during installation and is not
part of the artifact.

Dataset collection and construction entry scripts are under
`benchmark/scripts/`; run any script with `--help` to inspect its arguments.

