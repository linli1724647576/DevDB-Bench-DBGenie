# DBGenie

DBGenie generates database DDL from natural-language requirements and workloads.
This repository also contains the DevDB-Bench dataset, baseline implementations,
ablation variants, evaluation code, and dataset-construction utilities.

## Environment

Requirements:

- Python 3.10 or newer
- Docker Engine for PostgreSQL, MySQL, MariaDB, and SQL Server execution

Install the project and all experiment dependencies:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[method,evaluation,dev]"
.venv\Scripts\python.exe -m nltk.downloader -d .cache/nltk_data wordnet omw-1.4
.venv\Scripts\python.exe -m spacy download en_core_web_sm
```

Run all commands below from the `DBGenie_release` directory. The commands use
the virtual environment's Python directly, so activating the environment is not
required.

## LLM configuration

Experiments select a model with `--llm-profile`. The available profiles and
their default models are defined in `configs/default.toml`:

- `deepseek`: `deepseek-v4-flash`
- `qwen`: `qwen3-coder-plus`
- `gpt`: `gpt-5.4`

Set the variables for the profile that will be used. For example, DeepSeek in
PowerShell:

```powershell
$env:DBGENIE_LLM_DEEPSEEK_API_KEY="your-api-key"
```

Qwen and GPT also require the OpenAI-compatible API endpoint used by the local
environment:

```powershell
$env:DBGENIE_LLM_QWEN_BASE_URL="https://your-qwen-compatible-endpoint/v1"
$env:DBGENIE_LLM_QWEN_API_KEY="your-api-key"

$env:DBGENIE_LLM_GPT_BASE_URL="https://your-gpt-compatible-endpoint/v1"
$env:DBGENIE_LLM_GPT_API_KEY="your-api-key"
```

The model names can be overridden with `DBGENIE_LLM_<PROFILE>_MODEL`. The
`.env.example` file is a variable reference only; the project does not
automatically load `.env` files. Keys may alternatively be placed in the matching
profile in `configs/default.toml`, but they must not be committed.

## Dataset

The formal 51-sample dataset is `benchmark/devdb_bench.json`. Its
`reference_ddl_path` values point to files under `benchmark/reference_ddl/`.

## Run

Main DBGenie method:

```powershell
.venv\Scripts\python.exe -m dbgenie.cli run-method `
  benchmark/devdb_bench.json `
  --config configs/default.toml `
  --llm-profile deepseek `
  --output outputs/dbgenie_deepseek.json `
  --run-dir runs/dbgenie_deepseek `
  --variant full `
  --jobs 1 `
  --progress
```

Baselines (`few-shot`, `mac-sql`, or `schema-agent`):

```powershell
.venv\Scripts\python.exe -m dbgenie.cli run-baseline `
  benchmark/devdb_bench.json `
  --config configs/default.toml `
  --llm-profile deepseek `
  --method few-shot `
  --output outputs/few_shot_deepseek.json `
  --run-dir runs/few_shot_deepseek `
  --jobs 1 `
  --progress
```

Ablations (`without_requirement_analyst`, `without_test_expert`, or
`without_scheduler`):

```powershell
.venv\Scripts\python.exe -m dbgenie.cli run-method `
  benchmark/devdb_bench.json `
  --config configs/default.toml `
  --llm-profile deepseek `
  --output outputs/without_scheduler_deepseek.json `
  --run-dir runs/without_scheduler_deepseek `
  --variant without_scheduler `
  --jobs 1 `
  --progress
```

Static design evaluation:

```powershell
.venv\Scripts\python.exe -m dbgenie.cli evaluate-design-static `
  benchmark/devdb_bench.json `
  --run-dir runs/dbgenie_deepseek `
  --output outputs/evaluation_dbgenie_deepseek.json `
  --embedding-backend fastembed `
  --embedding-cache-dir models/fastembed
```

Dataset collection and construction entry scripts are under
`benchmark/scripts/`; run any script with `--help` to inspect its arguments.
