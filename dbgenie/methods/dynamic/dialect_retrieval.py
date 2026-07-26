from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


DIALECT_KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "agents" / "dialect_cards"
DIALECT_RETRIEVAL_ROLES = {
    "logical_model_designer",
    "physical_design_specialist",
    "dialect_compiler",
    "test_expert",
}
DYNAMIC_CHUNK_LIMIT = 6
BM25_K1 = 1.5
BM25_B = 0.75
HARD_RULE_MARKERS = (
    "avoid ",
    "do not ",
    "does not ",
    "must ",
    "must not ",
    "not support",
    "not assume",
    "rejects ",
    "unsupported",
)

ROLE_SEEDS = {
    "logical_model_designer": (
        "type data type identity autoincrement primary key foreign key unique "
        "check nullability default json uuid array"
    ),
    "physical_design_specialist": (
        "index unique index composite index partial filtered include covering "
        "predicate ordering pagination"
    ),
    "dialect_compiler": (
        "ddl syntax quote identifier type mapping identity autoincrement constraint "
        "foreign key check index include filter extension"
    ),
    "test_expert": (
        "executor runtime enforcement constraint foreign key unique check negative "
        "test query plan explain index extension"
    ),
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "with",
}

TOKEN_SYNONYMS = {
    "autoincrement": {"auto_increment", "identity"},
    "auto_increment": {"autoincrement", "identity"},
    "identity": {"autoincrement", "auto_increment"},
    "filtered": {"partial"},
    "partial": {"filtered"},
    "covering": {"include"},
    "include": {"covering"},
    "fk": {"foreign", "key"},
    "foreign": {"fk"},
    "mssql": {"sqlserver", "sql", "server"},
    "sqlserver": {"mssql", "sql", "server"},
    "postgres": {"postgresql"},
    "postgresql": {"postgres"},
    "jsonb": {"json"},
    "json": {"jsonb"},
}

TOKEN_NORMALIZATION = {
    "actions": "action",
    "columns": "column",
    "constraints": "constraint",
    "extensions": "extension",
    "identifiers": "identifier",
    "indexes": "index",
    "keys": "key",
    "queries": "query",
    "rules": "rule",
    "tables": "table",
    "tests": "test",
    "types": "type",
}

SECTION_LABELS = {
    "executor/runtime": "executor_runtime",
    "core rules": "core_rules",
    "review checklist": "review_checklist",
}


@dataclass(frozen=True)
class DialectKnowledgeChunk:
    chunk_id: str
    dialect: str
    section: str
    text: str
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedDialectChunk:
    chunk: DialectKnowledgeChunk
    score: float | None
    mandatory: bool = False


@dataclass(frozen=True)
class DialectRetrievalResult:
    backend: str
    dialect: str
    role: str
    query_chars: int
    query_terms: tuple[str, ...]
    chunks: tuple[RetrievedDialectChunk, ...]
    warnings: tuple[str, ...] = ()

    def prompt_text(self) -> str:
        if not self.chunks:
            return ""
        parts = [
            "# Retrieved Dialect Knowledge",
            "",
            f"Dialect: `{self.dialect}`",
            f"Retrieval backend: `{self.backend}`",
            "",
            (
                "These are executor-grounded retrieved snippets, not a complete DBMS manual. "
                "Follow the retrieved constraints and do not invent unsupported behavior."
            ),
        ]
        for item in self.chunks:
            parts.extend(
                [
                    "",
                    f"## [{item.chunk.chunk_id} | {item.chunk.section}]",
                    item.chunk.text,
                ]
            )
        return "\n".join(parts)

    def metadata(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "dialect": self.dialect,
            "role": self.role,
            "query_chars": self.query_chars,
            "query_terms": list(self.query_terms),
            "chunks": [
                {
                    "chunk_id": item.chunk.chunk_id,
                    "section": item.chunk.section,
                    "score": None if item.score is None else round(item.score, 4),
                    "mandatory": item.mandatory,
                }
                for item in self.chunks
            ],
            "warnings": list(self.warnings),
        }


def normalize_dialect_id(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    aliases = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "mysql": "mysql",
        "mariadb": "mariadb",
        "maria db": "mariadb",
        "sqlite": "sqlite",
        "sqlite3": "sqlite",
        "duckdb": "duckdb",
        "duck db": "duckdb",
        "sql server": "sqlserver",
        "mssql": "sqlserver",
        "sqlserver": "sqlserver",
    }
    return aliases.get(normalized, normalized.replace(" ", ""))


def parse_dialect_card(dialect: str, text: str) -> tuple[DialectKnowledgeChunk, ...]:
    sections: dict[str, list[str]] = {value: [] for value in SECTION_LABELS.values()}
    current_section = ""
    for raw_line in str(text or "").splitlines():
        line = raw_line.rstrip()
        label = line.strip().rstrip(":").casefold()
        if label in SECTION_LABELS:
            current_section = SECTION_LABELS[label]
            continue
        if current_section:
            sections[current_section].append(line)

    chunks: list[DialectKnowledgeChunk] = []
    runtime_text = _join_nonempty_lines(sections["executor_runtime"])
    if runtime_text:
        chunks.append(_make_chunk(dialect, "executor_runtime", 1, runtime_text))

    for section in ("core_rules", "review_checklist"):
        for index, chunk_text in enumerate(_bullet_chunks(sections[section]), start=1):
            chunks.append(_make_chunk(dialect, section, index, chunk_text))
    return tuple(chunks)


def retrieve_dialect_knowledge(
    role: str,
    target_dbms: str,
    *,
    execution_context: Any = None,
    revision_request: Any = None,
    knowledge_dir: Path | None = None,
) -> DialectRetrievalResult | None:
    if role not in DIALECT_RETRIEVAL_ROLES:
        return None
    dialect = normalize_dialect_id(target_dbms)
    directory = (knowledge_dir or DIALECT_KNOWLEDGE_DIR).resolve()
    warnings: list[str] = []
    try:
        chunks = _load_dialect_chunks(dialect, directory.as_posix())
    except OSError as exc:
        chunks = ()
        warnings.append(f"dialect_card_read_failed: {type(exc).__name__}: {exc}")
    if not chunks:
        path = directory / f"{dialect}.md"
        warning = "dialect_card_not_found" if not path.exists() else "dialect_card_parse_failed"
        warnings.append(f"{warning}: {dialect}")
    elif not any(chunk.section == "executor_runtime" for chunk in chunks):
        warnings.append(f"dialect_runtime_chunk_missing: {dialect}")

    query_weights, query_chars = _build_query_weights(
        role,
        dialect,
        revision_request=revision_request,
        execution_context=execution_context,
    )
    query_terms = tuple(
        term
        for term, _weight in sorted(query_weights.items(), key=lambda item: (-item[1], item[0]))[:20]
    )
    mandatory_chunks = [chunk for chunk in chunks if _is_mandatory_chunk(chunk)]
    mandatory_ids = {chunk.chunk_id for chunk in mandatory_chunks}
    candidates = [chunk for chunk in chunks if chunk.chunk_id not in mandatory_ids]
    scored = _bm25_scores(candidates, query_weights)
    selected = [
        RetrievedDialectChunk(chunk=chunk, score=score, mandatory=False)
        for chunk, score in sorted(scored, key=lambda item: (-item[1], item[0].chunk_id))
        if score > 0
    ][:DYNAMIC_CHUNK_LIMIT]
    retrieved = [
        *(
            RetrievedDialectChunk(chunk=chunk, score=None, mandatory=True)
            for chunk in mandatory_chunks
        ),
        *selected,
    ]
    return DialectRetrievalResult(
        backend="local_bm25",
        dialect=dialect,
        role=role,
        query_chars=query_chars,
        query_terms=query_terms,
        chunks=tuple(retrieved),
        warnings=tuple(warnings),
    )


def _is_mandatory_chunk(chunk: DialectKnowledgeChunk) -> bool:
    if chunk.section in {"executor_runtime", "review_checklist"}:
        return True
    text = chunk.text.casefold()
    return any(marker in text for marker in HARD_RULE_MARKERS)


@lru_cache(maxsize=32)
def _load_dialect_chunks(dialect: str, directory: str) -> tuple[DialectKnowledgeChunk, ...]:
    path = Path(directory) / f"{dialect}.md"
    if not path.exists():
        return ()
    return parse_dialect_card(dialect, path.read_text(encoding="utf-8"))


def _make_chunk(dialect: str, section: str, index: int, text: str) -> DialectKnowledgeChunk:
    return DialectKnowledgeChunk(
        chunk_id=f"{dialect}.{section}.{index:03d}",
        dialect=dialect,
        section=section,
        text=text,
        tokens=tuple(_tokenize(text)),
    )


def _bullet_chunks(lines: list[str]) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current:
                chunks.append(" ".join(current))
            current = [stripped]
        elif current:
            current.append(stripped)
        else:
            current = [stripped]
    if current:
        chunks.append(" ".join(current))
    return chunks


def _join_nonempty_lines(lines: list[str]) -> str:
    return "\n".join(line.strip() for line in lines if line.strip())


def _build_query_weights(
    role: str,
    dialect: str,
    *,
    revision_request: Any,
    execution_context: Any,
) -> tuple[Counter[str], int]:
    revision_text = _json_text(revision_request)
    context_text = _json_text(
        execution_context.to_dict() if hasattr(execution_context, "to_dict") else execution_context
    )
    sources = [
        (ROLE_SEEDS.get(role, ""), 2),
        (revision_text, 2),
        (context_text, 1),
        (dialect, 1),
    ]
    weights: Counter[str] = Counter()
    for source_text, weight in sources:
        for token in _tokenize(source_text):
            weights[token] += weight
            for synonym in TOKEN_SYNONYMS.get(token, ()):
                weights[synonym] += weight
    return weights, sum(len(text) for text, _weight in sources)


def _bm25_scores(
    chunks: list[DialectKnowledgeChunk],
    query_weights: Counter[str],
) -> list[tuple[DialectKnowledgeChunk, float]]:
    if not chunks or not query_weights:
        return []
    document_count = len(chunks)
    average_length = sum(len(chunk.tokens) for chunk in chunks) / document_count
    document_frequency: Counter[str] = Counter()
    for chunk in chunks:
        document_frequency.update(set(chunk.tokens))

    scored: list[tuple[DialectKnowledgeChunk, float]] = []
    for chunk in chunks:
        frequencies = Counter(chunk.tokens)
        document_length = len(chunk.tokens)
        score = 0.0
        for term, query_weight in query_weights.items():
            frequency = frequencies.get(term, 0)
            if frequency <= 0:
                continue
            term_documents = document_frequency.get(term, 0)
            inverse_frequency = math.log(
                1 + (document_count - term_documents + 0.5) / (term_documents + 0.5)
            )
            normalization = frequency + BM25_K1 * (
                1 - BM25_B + BM25_B * document_length / max(average_length, 1)
            )
            score += query_weight * inverse_frequency * frequency * (BM25_K1 + 1) / normalization
        scored.append((chunk, score))
    return scored


def _tokenize(value: Any) -> list[str]:
    tokens: list[str] = []
    for raw_token in re.findall(r"[a-z0-9_]+", str(value or "").casefold()):
        candidates = [raw_token]
        if "_" in raw_token:
            candidates.extend(part for part in raw_token.split("_") if part)
        for token in candidates:
            token = TOKEN_NORMALIZATION.get(token, token)
            if len(token) > 1 and token not in STOP_WORDS:
                tokens.append(token)
    return tokens


def _json_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        return str(value)
