from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 fallback for the simple config used here.
    tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_seconds: int = 60
    name: str = "default"
    provider: str = "openai_compatible"
    temperature: float | None = None
    stream: bool = False
    max_retries: int = 0


@dataclass(frozen=True)
class GitHubConfig:
    token: str = ""
    per_page: int = 50


@dataclass(frozen=True)
class DatasetConfig:
    min_stars: int = 20
    min_forks: int = 3
    min_contributors: int = 3
    min_tables: int = 3
    active_within_days: int = 365
    materialization_mode: str = "selected_files"
    max_evidence_files_per_repo: int = 80
    max_file_bytes: int = 500000
    min_application_score: int = 4
    screening_queries: tuple[str, ...] = ()
    require_contributors_check: bool = False


@dataclass(frozen=True)
class EvaluationConfig:
    target_dbms: str = "postgresql"
    use_atlas: bool = True
    work_dir: str = "runs"


@dataclass(frozen=True)
class AppConfig:
    llm: LLMConfig
    llm_profiles: dict[str, LLMConfig]
    github: GitHubConfig
    dataset: DatasetConfig
    evaluation: EvaluationConfig


def load_config(path: str | Path = "configs/default.toml") -> AppConfig:
    config_path = Path(path)
    raw: dict[str, Any] = {}
    if config_path.exists():
        if tomllib is not None:
            with config_path.open("rb") as f:
                raw = tomllib.load(f)
        else:
            raw = _load_simple_toml(config_path)

    llm_raw = _as_dict(raw.get("llm", {}))
    github_raw = raw.get("github", {})
    dataset_raw = raw.get("dataset", {})
    evaluation_raw = raw.get("evaluation", {})

    llm_profiles = _load_llm_profiles(raw, llm_raw)
    llm = llm_profiles["default"]
    github = GitHubConfig(
        token=os.getenv("DBGENIE_GITHUB_TOKEN", github_raw.get("token", "")),
        per_page=int(github_raw.get("per_page", 50)),
    )
    dataset = DatasetConfig(
        min_stars=int(dataset_raw.get("min_stars", 20)),
        min_forks=int(dataset_raw.get("min_forks", 3)),
        min_contributors=int(dataset_raw.get("min_contributors", 3)),
        min_tables=int(dataset_raw.get("min_tables", 3)),
        active_within_days=int(dataset_raw.get("active_within_days", 365)),
        materialization_mode=dataset_raw.get("materialization_mode", "selected_files"),
        max_evidence_files_per_repo=int(dataset_raw.get("max_evidence_files_per_repo", 80)),
        max_file_bytes=int(dataset_raw.get("max_file_bytes", 500000)),
        min_application_score=int(dataset_raw.get("min_application_score", 4)),
        screening_queries=tuple(dataset_raw.get("screening_queries", ())),
        require_contributors_check=bool(dataset_raw.get("require_contributors_check", False)),
    )
    evaluation = EvaluationConfig(
        target_dbms=evaluation_raw.get("target_dbms", "postgresql"),
        use_atlas=bool(evaluation_raw.get("use_atlas", True)),
        work_dir=evaluation_raw.get("work_dir", "runs"),
    )
    return AppConfig(
        llm=llm,
        llm_profiles=llm_profiles,
        github=github,
        dataset=dataset,
        evaluation=evaluation,
    )


def get_llm_config(config: AppConfig, profile_name: str = "default") -> LLMConfig:
    try:
        return config.llm_profiles[profile_name]
    except KeyError as exc:
        available = ", ".join(sorted(config.llm_profiles)) or "none"
        raise KeyError(
            f"Unknown LLM profile '{profile_name}'. Available profiles: {available}."
        ) from exc


def _load_llm_profiles(raw: dict[str, Any], default_raw: dict[str, Any]) -> dict[str, LLMConfig]:
    profiles_raw = _llm_profile_sections(raw)
    default_profile_raw = {**default_raw, **profiles_raw.pop("default", {})}
    profiles: dict[str, LLMConfig] = {
        "default": _build_llm_config(
            default_profile_raw,
            name="default",
            use_legacy_env=True,
        )
    }
    for name, profile_raw in sorted(profiles_raw.items()):
        profiles[name] = _build_llm_config(profile_raw, name=name, use_legacy_env=False)
    return profiles


def _build_llm_config(
    raw: dict[str, Any],
    *,
    name: str,
    use_legacy_env: bool,
) -> LLMConfig:
    prefix = _profile_env_prefix(name)
    legacy = "DBGENIE_LLM_" if use_legacy_env else ""
    return LLMConfig(
        base_url=_env_value(prefix, "BASE_URL", raw.get("base_url", ""), legacy),
        api_key=_env_value(prefix, "API_KEY", raw.get("api_key", ""), legacy),
        model=_env_value(prefix, "MODEL", raw.get("model", ""), legacy),
        timeout_seconds=int(
            _env_value(prefix, "TIMEOUT_SECONDS", raw.get("timeout_seconds", 60), legacy)
        ),
        name=str(raw.get("name") or name),
        provider=str(
            _env_value(
                prefix,
                "PROVIDER",
                raw.get("provider", "openai_compatible"),
                legacy,
            )
        ),
        temperature=_optional_float(
            _env_value(prefix, "TEMPERATURE", raw.get("temperature"), legacy)
        ),
        stream=_optional_bool(_env_value(prefix, "STREAM", raw.get("stream", False), legacy)),
        max_retries=max(
            0,
            int(_env_value(prefix, "MAX_RETRIES", raw.get("max_retries", 0), legacy)),
        ),
    )


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _optional_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _llm_profile_sections(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    nested = raw.get("llm_profiles", {})
    if isinstance(nested, dict):
        for name, value in nested.items():
            if isinstance(value, dict):
                profiles[str(name)] = dict(value)
    for section_name, value in raw.items():
        if (
            isinstance(section_name, str)
            and section_name.startswith("llm_profiles.")
            and isinstance(value, dict)
        ):
            profiles[section_name.split(".", 1)[1]] = dict(value)
    return profiles


def _profile_env_prefix(name: str) -> str:
    clean = "".join(char if char.isalnum() else "_" for char in name.upper())
    return f"DBGENIE_LLM_{clean}_"


def _env_value(
    profile_prefix: str,
    suffix: str,
    default: Any,
    legacy_prefix: str = "",
) -> Any:
    profile_value = os.getenv(f"{profile_prefix}{suffix}")
    if profile_value is not None:
        return profile_value
    if legacy_prefix:
        legacy_value = os.getenv(f"{legacy_prefix}{suffix}")
        if legacy_value is not None:
            return legacy_value
    return default


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_simple_toml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    section: dict[str, Any] | None = None
    pending_array_key: str | None = None
    pending_array_values: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if pending_array_key is not None:
            if line.startswith("]"):
                if section is not None:
                    section[pending_array_key] = pending_array_values
                pending_array_key = None
                pending_array_values = []
                continue
            pending_array_values.append(_parse_simple_toml_value(line.rstrip(",")))
            continue
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            section = _ensure_simple_toml_section(data, section_name)
            continue
        if section is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        clean_key = key.strip()
        clean_value = value.strip()
        if clean_value == "[":
            pending_array_key = clean_key
            pending_array_values = []
            continue
        section[clean_key] = _parse_simple_toml_value(clean_value)
    return data


def _ensure_simple_toml_section(data: dict[str, Any], section_name: str) -> dict[str, Any]:
    current = data
    for part in section_name.split("."):
        next_section = current.setdefault(part, {})
        if not isinstance(next_section, dict):
            next_section = {}
            current[part] = next_section
        current = next_section
    return current


def _parse_simple_toml_value(value: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
