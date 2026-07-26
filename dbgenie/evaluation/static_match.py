from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from dbgenie.core.io import read_json
from dbgenie.core.schema_ir import SchemaIR, TableIR
from dbgenie.evaluation.runtime_design import (
    DOCKER_DBMS,
    SUPPORTED_DBMS,
    build_index_inventory,
    cleanup_runtime_services,
    dump_json,
    execute_and_introspect_runtime,
    normalize_schema_ir,
    prepare_runtime_services,
)


REFERENCE_RUNTIME_CACHE_VERSION = 1
GENERATED_RUNTIME_CACHE_VERSION = 1
RUNTIME_INTROSPECTION_VERSION = 1
RUNTIME_NORMALIZATION_VERSION = 1
STATIC_MATCH_METRIC_VERSION = 4
EASY_MAX_REFERENCE_TABLES = 10
MEDIUM_MAX_REFERENCE_TABLES = 30


@dataclass(frozen=True)
class NameMatch:
    matched: bool
    method: str = ""
    score: float = 0.0

    @property
    def rank(self) -> int:
        return {
            "exact": 4,
            "synonym": 3,
            "similarity": 2,
            "string": 1,
        }.get(self.method, 0)


class EmbeddingBackend(Protocol):
    def similarity(self, left: str, right: str) -> float:
        ...


class NameMatcher(Protocol):
    def match(self, predicted: str, reference: str) -> NameMatch:
        ...


class MiniLMNameMatcher:
    def __init__(
        self,
        *,
        embedding_backend: EmbeddingBackend,
        similarity_threshold: float = 0.6,
        string_threshold: float = 0.75,
    ) -> None:
        self.embedding_backend = embedding_backend
        self.similarity_threshold = similarity_threshold
        self.string_threshold = string_threshold
        try:
            from nltk.corpus import wordnet as wordnet
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "WordNet matching requires nltk with the wordnet corpus installed."
            ) from exc
        try:
            wordnet.synsets("user")
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "NLTK is installed, but the WordNet corpus is unavailable. "
                "Run: python -m nltk.downloader -d .cache\\nltk_data wordnet omw-1.4"
            ) from exc
        self._wordnet = wordnet
        self._spacy_nlp = load_spacy_model()

    def match(self, predicted: str, reference: str) -> NameMatch:
        predicted_value = str(predicted)
        reference_value = str(reference)
        predicted_key = predicted_value.casefold()
        reference_key = reference_value.casefold()
        if predicted_key == reference_key:
            return NameMatch(True, "exact", 1.0)

        if self._is_wordnet_synonym(predicted_key, reference_key):
            return NameMatch(True, "synonym", 1.0)

        similarity = self.embedding_backend.similarity(predicted_value, reference_value)
        if similarity >= self.similarity_threshold:
            return NameMatch(True, "similarity", similarity)

        string_score = token_lcs_overlap_ratio(
            predicted_value,
            reference_value,
            self._spacy_nlp,
        )
        if string_score >= self.string_threshold:
            return NameMatch(True, "string", string_score)
        return NameMatch(False, "none", max(string_score, similarity))

    def _is_wordnet_synonym(self, predicted: str, reference: str) -> bool:
        predicted_tokens = normalize_wordnet_tokens(split_identifier_tokens(predicted))
        reference_tokens = normalize_wordnet_tokens(split_identifier_tokens(reference))
        if (
            not predicted_tokens
            or not reference_tokens
            or len(predicted_tokens) != len(reference_tokens)
        ):
            return False
        return all(
            left == right or are_wordnet_synonyms(self._wordnet, left, right)
            for left, right in zip(predicted_tokens, reference_tokens)
        )


class FastEmbedBackend:
    def __init__(self, model_name: str, cache_dir: str | Path | None = None) -> None:
        try:
            from fastembed import TextEmbedding
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "fastembed is required for --embedding-backend fastembed."
            ) from exc
        kwargs: dict[str, Any] = {"model_name": model_name}
        if cache_dir:
            kwargs["cache_dir"] = str(cache_dir)
        self._model = TextEmbedding(**kwargs)
        self._cache: dict[str, list[float]] = {}

    def similarity(self, left: str, right: str) -> float:
        left_vector, right_vector = self._embed([left, right])
        return cosine_similarity(left_vector, right_vector)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        missing = [text for text in texts if text not in self._cache]
        if missing:
            embeddings = list(self._model.embed(missing))
            for text, embedding in zip(missing, embeddings):
                self._cache[text] = [float(value) for value in embedding]
        return [self._cache[text] for text in texts]


class SentenceTransformersBackend:
    def __init__(self, model_name_or_path: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "sentence-transformers is required for "
                "--embedding-backend sentence-transformers."
            ) from exc
        self._model = SentenceTransformer(model_name_or_path)
        self._cache: dict[str, list[float]] = {}

    def similarity(self, left: str, right: str) -> float:
        left_vector, right_vector = self._embed([left, right])
        return cosine_similarity(left_vector, right_vector)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        missing = [text for text in texts if text not in self._cache]
        if missing:
            embeddings = self._model.encode(missing, convert_to_numpy=True)
            for text, embedding in zip(missing, embeddings):
                self._cache[text] = [float(value) for value in embedding]
        return [self._cache[text] for text in texts]


class HttpEmbeddingBackend:
    def __init__(self, url: str) -> None:
        if not url:
            raise RuntimeError("--embedding-url is required for --embedding-backend http.")
        self.url = url
        self._cache: dict[str, list[float]] = {}

    def similarity(self, left: str, right: str) -> float:
        left_vector, right_vector = self._embed([left, right])
        return cosine_similarity(left_vector, right_vector)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        missing = [text for text in texts if text not in self._cache]
        if missing:
            request = urllib.request.Request(
                self.url,
                data=json.dumps({"texts": missing}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            raw_embeddings = payload.get("embeddings")
            if raw_embeddings is None and isinstance(payload.get("data"), list):
                raw_embeddings = [item.get("embedding") for item in payload["data"]]
            if not isinstance(raw_embeddings, list) or len(raw_embeddings) != len(missing):
                raise RuntimeError("HTTP embedding response must contain one embedding per text.")
            for text, embedding in zip(missing, raw_embeddings):
                self._cache[text] = [float(value) for value in embedding]
        return [self._cache[text] for text in texts]


@dataclass(frozen=True)
class StaticMatchConfig:
    candidate_json: Path
    run_dir: Path
    generated_runtime_ir_dir: Path = Path("runs/evaluation/generated_runtime_ir")
    reference_runtime_ir_dir: Path = Path("runs/evaluation/reference_runtime_ir")
    embedding_backend: str = "fastembed"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_cache_dir: Path | None = Path("models/fastembed")
    embedding_url: str = ""
    similarity_threshold: float = 0.6
    string_threshold: float = 0.75
    accuracy_f1_threshold: float = 0.9
    accuracy_medium_f1_threshold: float = 0.8
    accuracy_hard_f1_threshold: float = 0.7
    limit: int | None = None
    task_ids: tuple[str, ...] = ()
    detail_limit: int = 25
    write_runtime_ir: bool = True
    keep_containers: bool = False
    refresh_reference_runtime_ir: bool = False
    refresh_generated_runtime_ir: bool = False
    accept_legacy_generated_runtime_ir: bool = False
    runtime_ir_cache_only: bool = False
    progress: bool = False


@dataclass(frozen=True)
class ReferenceRuntimeIRConfig:
    candidate_json: Path
    reference_runtime_ir_dir: Path = Path("runs/evaluation/reference_runtime_ir")
    limit: int | None = None
    task_ids: tuple[str, ...] = ()
    refresh: bool = False
    keep_containers: bool = False
    progress: bool = False


@dataclass(frozen=True)
class GeneratedRuntimeIRConfig:
    candidate_json: Path
    run_dir: Path
    generated_runtime_ir_dir: Path = Path("runs/evaluation/generated_runtime_ir")
    limit: int | None = None
    task_ids: tuple[str, ...] = ()
    refresh: bool = False
    accept_legacy: bool = False
    keep_containers: bool = False
    progress: bool = False


@dataclass
class AlignmentResult:
    mapping: dict[str, str] = field(default_factory=dict)
    details: list[dict[str, Any]] = field(default_factory=list)
    ambiguous: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StaticMatchCounters:
    table_tp: int = 0
    table_ref: int = 0
    table_gen: int = 0
    column_tp: int = 0
    column_ref: int = 0
    column_gen: int = 0
    pk_matched: int = 0
    pk_total: int = 0
    pk_gen: int = 0
    fk_matched: int = 0
    fk_total: int = 0
    fk_gen: int = 0
    datatype_matched: int = 0
    datatype_total: int = 0
    constraint_matched: int = 0
    constraint_total: int = 0
    index_matched: int = 0
    index_total: int = 0
    index_gen: int = 0

    def add(self, other: "StaticMatchCounters") -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, getattr(self, name) + getattr(other, name))


class StaticSchemaMatcher:
    def __init__(
        self,
        name_matcher: NameMatcher,
        accuracy_f1_threshold: float = 0.9,
        accuracy_medium_f1_threshold: float = 0.8,
        accuracy_hard_f1_threshold: float = 0.7,
    ) -> None:
        if not (
            0.0
            <= accuracy_hard_f1_threshold
            <= accuracy_medium_f1_threshold
            <= accuracy_f1_threshold
            <= 1.0
        ):
            raise ValueError(
                "accuracy thresholds must satisfy "
                "0 <= hard <= medium <= easy <= 1"
            )
        self.name_matcher = name_matcher
        self.accuracy_f1_threshold = accuracy_f1_threshold
        self.accuracy_medium_f1_threshold = accuracy_medium_f1_threshold
        self.accuracy_hard_f1_threshold = accuracy_hard_f1_threshold

    def evaluate(
        self,
        *,
        reference: SchemaIR,
        generated: SchemaIR,
        generated_indexes: list[dict[str, Any]] | None = None,
        reference_indexes: list[dict[str, Any]] | None = None,
        task_id: str,
        full_name: str,
        target_dbms: str,
        run_status: str,
        has_generated_schema_ir: bool,
        has_generated_indexes: bool,
        errors: list[str] | None = None,
    ) -> dict[str, Any]:
        reference_table_count = len(reference.tables)
        difficulty = self._accuracy_difficulty(reference_table_count)
        table_alignment = self._align_names(
            [table.name for table in reference.tables],
            [table.name for table in generated.tables],
        )
        table_pairs = {
            ref_name: (
                self._find_table(reference, ref_name),
                self._find_table(generated, gen_name),
            )
            for ref_name, gen_name in table_alignment.mapping.items()
        }
        column_alignments: dict[str, AlignmentResult] = {}
        for ref_name, (ref_table, gen_table) in table_pairs.items():
            if ref_table is None or gen_table is None:
                continue
            column_alignments[ref_name] = self._align_names(
                [column.name for column in ref_table.columns],
                [column.name for column in gen_table.columns],
            )

        counters = StaticMatchCounters(
            table_tp=len(table_alignment.mapping),
            table_ref=len(reference.tables),
            table_gen=len(generated.tables),
            column_ref=sum(len(table.columns) for table in reference.tables),
            column_gen=sum(len(table.columns) for table in generated.tables),
        )
        counters.column_tp = sum(len(alignment.mapping) for alignment in column_alignments.values())

        column_details = self._column_details(
            reference,
            table_pairs,
            column_alignments,
            difficulty,
        )
        pk_details = self._primary_key_details(reference, generated, table_alignment, column_alignments)
        fk_details = self._foreign_key_details(reference, generated, table_alignment, column_alignments)
        datatype_details = self._datatype_details(reference, table_pairs, column_alignments)
        constraint_details = self._constraint_details(reference, generated, table_alignment, column_alignments)
        reference_index_list = (
            reference_indexes if reference_indexes is not None else schema_index_records(reference)
        )
        generated_index_list = (
            generated_indexes if generated_indexes is not None else schema_index_records(generated)
        )
        index_details = self._index_details(
            reference,
            reference_index_list,
            generated_index_list,
            table_alignment,
            column_alignments,
            difficulty,
        )

        conditional_pk_items = [
            item
            for item in pk_details["reference_items"]
            if item["included_in_conditional_metrics"]
        ]
        counters.pk_matched = sum(1 for item in conditional_pk_items if item["matched"])
        counters.pk_total = len(conditional_pk_items)
        counters.pk_gen = pk_details["generated_count"]
        counters.fk_matched = sum(1 for item in fk_details["reference_items"] if item["matched"])
        counters.fk_total = len(fk_details["reference_items"])
        counters.fk_gen = fk_details["generated_count"]
        counters.datatype_matched = sum(1 for item in datatype_details if item["matched"])
        counters.datatype_total = len(datatype_details)
        counters.constraint_matched = sum(1 for item in constraint_details["reference_items"] if item["matched"])
        counters.constraint_total = len(constraint_details["reference_items"])
        counters.index_matched = sum(1 for item in index_details["reference_items"] if item["matched"])
        counters.index_total = len(index_details["reference_items"])
        counters.index_gen = index_details["generated_count"]

        table_f1 = f1(counters.table_tp, counters.table_ref, counters.table_gen)
        table_exact_match = counters.table_tp == counters.table_ref == counters.table_gen
        table_threshold_match = table_f1 >= difficulty["effective_accuracy_f1_threshold"]
        table_unadjusted_threshold_match = table_f1 >= self.accuracy_f1_threshold
        table_acc = float(table_threshold_match)
        matched_column_details = [
            item for item in column_details if item["included_in_conditional_metrics"]
        ]
        matched_table_count = len(matched_column_details)
        column_acc = accuracy(
            sum(1 for item in matched_column_details if item["threshold_match"]),
            matched_table_count,
        )
        column_f1 = (
            sum(float(item["f1"]) for item in matched_column_details) / matched_table_count
            if matched_table_count
            else 0.0
        )
        primary_key_acc = accuracy(counters.pk_matched, counters.pk_total)
        foreign_key_acc = empty_sensitive_accuracy(
            counters.fk_matched,
            counters.fk_total,
            fk_details["generated_count"],
        )
        datatype_acc = accuracy(counters.datatype_matched, counters.datatype_total, empty_value=0.0)
        constraint_acc = empty_sensitive_accuracy(
            counters.constraint_matched,
            counters.constraint_total,
            constraint_details["generated_count"],
        )
        matched_index_scores = [
            item
            for item in index_details["table_scores"]
            if item["included_in_conditional_metrics"]
        ]
        index_acc = accuracy(
            sum(1 for item in matched_index_scores if item["threshold_match"]),
            len(matched_index_scores),
        )
        index_f1_value = (
            sum(float(item["f1"]) for item in matched_index_scores)
            / len(matched_index_scores)
            if matched_index_scores
            else 0.0
        )
        diagnostic_metrics = {
            "table_high_fidelity_rate": float(table_unadjusted_threshold_match),
            "column_high_fidelity_rate": accuracy(
                sum(
                    1
                    for item in matched_column_details
                    if item["unadjusted_threshold_match"]
                ),
                matched_table_count,
            ),
            "column_coverage_adjusted_f1": (
                sum(float(item["f1"]) for item in column_details)
                / reference_table_count
                if reference_table_count
                else 0.0
            ),
            "column_coverage_adjusted_high_fidelity_rate": accuracy(
                sum(1 for item in column_details if item["unadjusted_threshold_match"]),
                reference_table_count,
            ),
            "index_high_fidelity_rate": accuracy(
                sum(
                    1
                    for item in matched_index_scores
                    if item["unadjusted_threshold_match"]
                ),
                len(matched_index_scores),
            ),
            "index_coverage_adjusted_f1": (
                sum(float(item["f1"]) for item in index_details["table_scores"])
                / reference_table_count
                if reference_table_count
                else 0.0
            ),
            "index_coverage_adjusted_high_fidelity_rate": accuracy(
                sum(
                    1
                    for item in index_details["table_scores"]
                    if item["unadjusted_threshold_match"]
                ),
                reference_table_count,
            ),
        }

        missing_tables = [
            table.name for table in reference.tables if table.name not in table_alignment.mapping
        ]
        matched_generated_tables = set(table_alignment.mapping.values())
        extra_tables = [
            table.name for table in generated.tables if table.name not in matched_generated_tables
        ]

        return {
            "task_id": task_id,
            "full_name": full_name,
            "target_dbms": target_dbms,
            "run_status": run_status,
            "has_generated_schema_ir": has_generated_schema_ir,
            "has_generated_indexes": has_generated_indexes,
            "difficulty_tier": difficulty["difficulty_tier"],
            "reference_table_count": reference_table_count,
            "effective_accuracy_f1_threshold": difficulty[
                "effective_accuracy_f1_threshold"
            ],
            "metrics": {
                "table_acc": table_acc,
                "table_f1": table_f1,
                "column_acc": column_acc,
                "column_f1": column_f1,
                "primary_key_acc": primary_key_acc,
                "foreign_key_acc": foreign_key_acc,
                "datatype_acc": datatype_acc,
                "constraint_acc": constraint_acc,
                "index_acc": index_acc,
                "index_f1": index_f1_value,
                "physical_static_score": index_f1_value,
            },
            "diagnostic_metrics": diagnostic_metrics,
            "counts": counters.__dict__,
            "details": {
                "table_score": {
                    "matched": counters.table_tp,
                    "reference_total": counters.table_ref,
                    "generated_total": counters.table_gen,
                    "precision": (
                        counters.table_tp / counters.table_gen
                        if counters.table_gen
                        else float(counters.table_ref == 0)
                    ),
                    "recall": (
                        counters.table_tp / counters.table_ref
                        if counters.table_ref
                        else float(counters.table_gen == 0)
                    ),
                    "f1": table_f1,
                    "exact_match": table_exact_match,
                    "threshold_match": table_threshold_match,
                    "unadjusted_threshold_match": table_unadjusted_threshold_match,
                    **difficulty,
                    "accuracy_f1_threshold": self.accuracy_f1_threshold,
                },
                "table_alignment": table_alignment.details,
                "column_alignment": {
                    table: alignment.details for table, alignment in column_alignments.items()
                },
                "column_scores": column_details,
                "ambiguous_alignments": [
                    *table_alignment.ambiguous,
                    *[
                        {"scope": f"column:{table}", **item}
                        for table, alignment in column_alignments.items()
                        for item in alignment.ambiguous
                    ],
                ],
                "missing_tables": missing_tables,
                "extra_tables": extra_tables,
                "missing_columns": self._missing_columns(reference, column_alignments),
                "extra_columns": self._extra_columns(table_pairs, column_alignments),
                "primary_keys": pk_details["reference_items"],
                "primary_key_set": pk_details,
                "foreign_keys": fk_details["reference_items"],
                "foreign_key_set": fk_details,
                "extra_foreign_keys": fk_details["extra_items"],
                "datatypes": datatype_details,
                "constraints": constraint_details["reference_items"],
                "extra_constraints": constraint_details["extra_items"],
                "indexes": index_details["reference_items"],
                "index_scores": index_details["table_scores"],
                "extra_indexes": index_details["extra_items"],
                "errors": errors or [],
            },
        }

    def _accuracy_difficulty(self, reference_table_count: int) -> dict[str, Any]:
        if reference_table_count <= EASY_MAX_REFERENCE_TABLES:
            tier = "easy"
            threshold = self.accuracy_f1_threshold
        elif reference_table_count <= MEDIUM_MAX_REFERENCE_TABLES:
            tier = "medium"
            threshold = self.accuracy_medium_f1_threshold
        else:
            tier = "hard"
            threshold = self.accuracy_hard_f1_threshold
        return {
            "difficulty_tier": tier,
            "reference_table_count": reference_table_count,
            "effective_accuracy_f1_threshold": threshold,
        }

    def _align_names(self, reference_names: list[str], generated_names: list[str]) -> AlignmentResult:
        edges: list[tuple[int, float, str, str, NameMatch]] = []
        for ref_name in reference_names:
            for gen_name in generated_names:
                match = self.name_matcher.match(gen_name, ref_name)
                if match.matched:
                    edges.append((match.rank, match.score, ref_name, gen_name, match))
        edges.sort(key=lambda item: (-item[0], -item[1], item[2].casefold(), item[3].casefold()))
        result = AlignmentResult()
        used_ref: set[str] = set()
        used_gen: set[str] = set()
        for rank, score, ref_name, gen_name, match in edges:
            if ref_name in used_ref or gen_name in used_gen:
                continue
            tie_edges = [
                item
                for item in edges
                if item[2] == ref_name
                and item[3] not in used_gen
                and item[0] == rank
                and math.isclose(item[1], score, rel_tol=1e-9, abs_tol=1e-9)
            ]
            if len(tie_edges) > 1:
                result.ambiguous.append(
                    {
                        "scope": "name",
                        "reference": ref_name,
                        "candidates": [
                            {"generated": item[3], "method": item[4].method, "score": item[4].score}
                            for item in tie_edges
                        ],
                    }
                )
                used_ref.add(ref_name)
                continue
            result.mapping[ref_name] = gen_name
            used_ref.add(ref_name)
            used_gen.add(gen_name)
            result.details.append(
                {
                    "reference": ref_name,
                    "generated": gen_name,
                    "method": match.method,
                    "score": match.score,
                }
            )
        return result

    def _primary_key_details(
        self,
        reference: SchemaIR,
        generated: SchemaIR,
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
    ) -> dict[str, Any]:
        reference_items: list[dict[str, Any]] = []
        missing_items: list[dict[str, Any]] = []
        extra_items: list[dict[str, Any]] = []
        for ref_table in reference.tables:
            generated_table_name = table_alignment.mapping.get(ref_table.name)
            gen_table = (
                self._find_table(generated, generated_table_name)
                if generated_table_name is not None
                else None
            )
            item: dict[str, Any] = {
                "table": ref_table.name,
                "reference": list(ref_table.primary_key),
                "generated_table": generated_table_name,
                "generated": list(gen_table.primary_key) if gen_table is not None else None,
                "mapped_generated": [],
                "matched": False,
                "included_in_conditional_metrics": gen_table is not None,
            }
            if gen_table is None:
                item["reason"] = "unmatched_table"
                if ref_table.primary_key:
                    missing_items.append(
                        {"table": ref_table.name, "primary_key": list(ref_table.primary_key)}
                    )
                reference_items.append(item)
                continue

            alignment = column_alignments.get(ref_table.name, AlignmentResult())
            gen_to_ref = {gen: ref for ref, gen in alignment.mapping.items()}
            mapped_pk = [
                gen_to_ref[column]
                for column in gen_table.primary_key
                if column in gen_to_ref
            ]
            item["mapped_generated"] = mapped_pk
            same_members = (
                len(mapped_pk) == len(gen_table.primary_key)
                and len(ref_table.primary_key) == len(gen_table.primary_key)
                and set(ref_table.primary_key) == set(mapped_pk)
            )
            item["matched"] = same_members
            item["reason"] = "matched" if same_members else "primary_key_mismatch"
            if not same_members:
                if ref_table.primary_key:
                    missing_items.append(
                        {"table": ref_table.name, "primary_key": list(ref_table.primary_key)}
                    )
                if gen_table.primary_key:
                    extra_items.append(
                        {
                            "table": gen_table.name,
                            "primary_key": list(gen_table.primary_key),
                            "mapped_primary_key": mapped_pk,
                            "reason": (
                                "unmatched_column"
                                if len(mapped_pk) != len(gen_table.primary_key)
                                else "member_mismatch"
                            ),
                        }
                    )
            reference_items.append(item)

        matched_generated_tables = set(table_alignment.mapping.values())
        for gen_table in generated.tables:
            if gen_table.name not in matched_generated_tables and gen_table.primary_key:
                extra_items.append(
                    {
                        "table": gen_table.name,
                        "primary_key": list(gen_table.primary_key),
                        "reason": "unmatched_table",
                    }
                )

        conditional_items = [
            item for item in reference_items if item["included_in_conditional_metrics"]
        ]
        return {
            "matched": bool(conditional_items)
            and all(item["matched"] for item in conditional_items),
            "reference_items": reference_items,
            "generated_items": [
                {"table": table.name, "primary_key": list(table.primary_key)}
                for table in generated.tables
                if table.primary_key
            ],
            "missing_items": missing_items,
            "extra_items": extra_items,
            "generated_count": sum(1 for table in generated.tables if table.primary_key),
        }

    def _column_details(
        self,
        reference: SchemaIR,
        table_pairs: dict[str, tuple[TableIR | None, TableIR | None]],
        column_alignments: dict[str, AlignmentResult],
        difficulty: dict[str, Any],
    ) -> list[dict[str, Any]]:
        details = []
        for ref_table in reference.tables:
            pair = table_pairs.get(ref_table.name)
            gen_table = pair[1] if pair is not None else None
            alignment = column_alignments.get(ref_table.name, AlignmentResult())
            matched = len(alignment.mapping)
            reference_total = len(ref_table.columns)
            generated_total = len(gen_table.columns) if gen_table is not None else 0
            precision = (
                matched / generated_total
                if generated_total
                else float(reference_total == 0 and gen_table is not None)
            )
            recall = matched / reference_total if reference_total else float(gen_table is not None)
            column_f1 = (
                f1(matched, reference_total, generated_total)
                if gen_table is not None
                else 0.0
            )
            included = gen_table is not None
            details.append(
                {
                    "reference_table": ref_table.name,
                    "generated_table": gen_table.name if gen_table is not None else None,
                    "matched": matched,
                    "reference_total": reference_total,
                    "generated_total": generated_total,
                    "precision": precision,
                    "recall": recall,
                    "f1": column_f1,
                    "exact_match": (
                        included
                        and matched == reference_total == generated_total
                    ),
                    "threshold_match": (
                        included
                        and column_f1
                        >= difficulty["effective_accuracy_f1_threshold"]
                    ),
                    "unadjusted_threshold_match": (
                        included and column_f1 >= self.accuracy_f1_threshold
                    ),
                    "included_in_conditional_metrics": included,
                    **difficulty,
                    "accuracy_f1_threshold": self.accuracy_f1_threshold,
                }
            )
        return details

    def _foreign_key_details(
        self,
        reference: SchemaIR,
        generated: SchemaIR,
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
    ) -> dict[str, Any]:
        ref_items = []
        gen_items, unmapped_gen_items = self._mapped_foreign_keys(
            generated,
            table_alignment,
            column_alignments,
        )
        unmatched_gen = list(gen_items)
        missing_items = []
        for ref_table in reference.tables:
            for fk in ref_table.foreign_keys:
                ref_key = (
                    ref_table.name,
                    tuple(fk.columns),
                    fk.ref_table,
                    tuple(fk.ref_columns),
                )
                matched = ref_key in unmatched_gen
                if matched:
                    unmatched_gen.remove(ref_key)
                else:
                    missing_items.append(ref_key)
                ref_items.append(
                    {
                        "table": ref_table.name,
                        "columns": fk.columns,
                        "ref_table": fk.ref_table,
                        "ref_columns": fk.ref_columns,
                        "matched": matched,
                    }
                )
        return {
            "reference_items": ref_items,
            "extra_items": [
                {
                    "table": item[0],
                    "columns": list(item[1]),
                    "ref_table": item[2],
                    "ref_columns": list(item[3]),
                }
                for item in unmatched_gen
            ] + unmapped_gen_items,
            "missing_items": [
                {
                    "table": item[0],
                    "columns": list(item[1]),
                    "ref_table": item[2],
                    "ref_columns": list(item[3]),
                }
                for item in missing_items
            ],
            "generated_count": len(gen_items) + len(unmapped_gen_items),
            "matched": not missing_items and not unmatched_gen and not unmapped_gen_items,
        }

    def _datatype_details(
        self,
        reference: SchemaIR,
        table_pairs: dict[str, tuple[TableIR | None, TableIR | None]],
        column_alignments: dict[str, AlignmentResult],
    ) -> list[dict[str, Any]]:
        details = []
        for ref_table in reference.tables:
            ref_name = ref_table.name
            _matched_ref_table, gen_table = table_pairs.get(ref_name, (ref_table, None))
            alignment = column_alignments.get(ref_name, AlignmentResult())
            gen_columns = {column.name: column for column in gen_table.columns} if gen_table else {}
            for ref_column in ref_table.columns:
                gen_name = alignment.mapping.get(ref_column.name)
                gen_column = gen_columns.get(gen_name or "")
                if not gen_column:
                    continue
                ref_type = logical_type(ref_column.type)
                gen_type = logical_type(gen_column.type)
                details.append(
                    {
                        "table": ref_name,
                        "column": ref_column.name,
                        "generated_column": gen_name,
                        "matched": ref_type == gen_type,
                        "reference_type": ref_column.type,
                        "generated_type": gen_column.type,
                        "reference_logical_type": ref_type,
                        "generated_logical_type": gen_type,
                    }
                )
        return details

    def _constraint_details(
        self,
        reference: SchemaIR,
        generated: SchemaIR,
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
    ) -> dict[str, Any]:
        ref_constraints = self._reference_constraints(reference, column_alignments)
        gen_constraints = self._mapped_constraints(generated, table_alignment, column_alignments)
        unmatched_gen = list(gen_constraints)
        ref_items = []
        for constraint in ref_constraints:
            matched = constraint in unmatched_gen
            if matched:
                unmatched_gen.remove(constraint)
            ref_items.append(constraint_to_dict(constraint, matched=matched))
        return {
            "reference_items": ref_items,
            "extra_items": [constraint_to_dict(item, matched=False) for item in unmatched_gen],
            "generated_count": len(gen_constraints),
        }

    def _index_details(
        self,
        reference: SchemaIR,
        reference_indexes: list[dict[str, Any]],
        generated_indexes: list[dict[str, Any]],
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
        difficulty: dict[str, Any],
    ) -> dict[str, Any]:
        reference_by_table: dict[str, list[dict[str, Any]]] = {}
        for index in reference_indexes:
            reference_by_table.setdefault(str(index.get("table") or ""), []).append(index)
        generated_by_table: dict[str, list[dict[str, Any]]] = {}
        for index in generated_indexes:
            generated_by_table.setdefault(str(index.get("table") or ""), []).append(index)

        reference_items: list[dict[str, Any]] = []
        extra_items: list[dict[str, Any]] = []
        table_scores: list[dict[str, Any]] = []
        generated_count = 0
        for ref_table in reference.tables:
            ref_table_name = ref_table.name
            generated_table_name = table_alignment.mapping.get(ref_table_name)
            ref_table_indexes = reference_by_table.get(ref_table_name, [])
            reference_total = len(ref_table_indexes)
            if generated_table_name is None:
                for index in ref_table_indexes:
                    reference_items.append(
                        {
                            "table": ref_table_name,
                            "columns": [str(column) for column in index.get("columns") or []],
                            "unique": bool(index.get("unique", False)),
                            "matched": False,
                        }
                    )
                table_scores.append(
                    {
                        "reference_table": ref_table_name,
                        "generated_table": None,
                        "matched": 0,
                        "reference_total": reference_total,
                        "generated_total": 0,
                        "precision": 0.0,
                        "recall": 0.0,
                        "f1": 0.0,
                        "exact_match": False,
                        "threshold_match": False,
                        "unadjusted_threshold_match": False,
                        "included_in_conditional_metrics": False,
                        **difficulty,
                        "accuracy_f1_threshold": self.accuracy_f1_threshold,
                    }
                )
                continue

            generated_table_indexes = generated_by_table.get(generated_table_name, [])
            generated_total = len(generated_table_indexes)
            generated_count += generated_total
            alignment = column_alignments.get(ref_table_name, AlignmentResult())
            gen_to_ref_column = {
                generated_column: reference_column
                for reference_column, generated_column in alignment.mapping.items()
            }
            generated_candidates = []
            for index in generated_table_indexes:
                generated_columns = [
                    str(column) for column in index.get("columns") or []
                ]
                mapped_columns = [
                    gen_to_ref_column[column]
                    for column in generated_columns
                    if column in gen_to_ref_column
                ]
                mapped = len(mapped_columns) == len(generated_columns)
                generated_candidates.append(
                    {
                        "key": (
                            tuple(mapped_columns),
                            bool(index.get("unique", False)),
                        )
                        if mapped
                        else None,
                        "generated_columns": generated_columns,
                        "mapped_columns": mapped_columns,
                        "unique": bool(index.get("unique", False)),
                    }
                )

            matched_count = 0
            for index in ref_table_indexes:
                columns = [str(column) for column in index.get("columns") or []]
                key = (tuple(columns), bool(index.get("unique", False)))
                candidate_index = next(
                    (
                        position
                        for position, candidate in enumerate(generated_candidates)
                        if candidate["key"] == key
                    ),
                    None,
                )
                matched = candidate_index is not None
                if candidate_index is not None:
                    generated_candidates.pop(candidate_index)
                    matched_count += 1
                reference_items.append(
                    {
                        "table": ref_table_name,
                        "columns": columns,
                        "unique": key[1],
                        "matched": matched,
                    }
                )

            for candidate in generated_candidates:
                mapped_columns = candidate["mapped_columns"]
                extra_items.append(
                    {
                        "table": ref_table_name,
                        "generated_table": generated_table_name,
                        "columns": (
                            mapped_columns
                            if candidate["key"] is not None
                            else candidate["generated_columns"]
                        ),
                        "generated_columns": candidate["generated_columns"],
                        "unique": candidate["unique"],
                        "reason": (
                            "unmatched_identity"
                            if candidate["key"] is not None
                            else "unmatched_column"
                        ),
                    }
                )

            table_f1 = f1(matched_count, reference_total, generated_total)
            table_scores.append(
                {
                    "reference_table": ref_table_name,
                    "generated_table": generated_table_name,
                    "matched": matched_count,
                    "reference_total": reference_total,
                    "generated_total": generated_total,
                    "precision": (
                        matched_count / generated_total
                        if generated_total
                        else float(reference_total == 0)
                    ),
                    "recall": (
                        matched_count / reference_total
                        if reference_total
                        else 1.0
                    ),
                    "f1": table_f1,
                    "exact_match": matched_count == reference_total == generated_total,
                    "threshold_match": (
                        table_f1 >= difficulty["effective_accuracy_f1_threshold"]
                    ),
                    "unadjusted_threshold_match": (
                        table_f1 >= self.accuracy_f1_threshold
                    ),
                    "included_in_conditional_metrics": True,
                    **difficulty,
                    "accuracy_f1_threshold": self.accuracy_f1_threshold,
                }
            )

        return {
            "reference_items": reference_items,
            "extra_items": extra_items,
            "table_scores": table_scores,
            "generated_count": generated_count,
        }

    def _mapped_foreign_keys(
        self,
        generated: SchemaIR,
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
    ) -> tuple[
        list[tuple[str, tuple[str, ...], str, tuple[str, ...]]],
        list[dict[str, Any]],
    ]:
        gen_to_ref_table = {gen: ref for ref, gen in table_alignment.mapping.items()}
        result = []
        unmapped = []
        for gen_table in generated.tables:
            ref_table_name = gen_to_ref_table.get(gen_table.name)
            if not ref_table_name:
                for fk in gen_table.foreign_keys:
                    unmapped.append(
                        {
                            "table": gen_table.name,
                            "columns": fk.columns,
                            "ref_table": fk.ref_table,
                            "ref_columns": fk.ref_columns,
                            "reason": "unmatched_table",
                        }
                    )
                continue
            alignment = column_alignments.get(ref_table_name, AlignmentResult())
            gen_to_ref_col = {gen: ref for ref, gen in alignment.mapping.items()}
            for fk in gen_table.foreign_keys:
                ref_target_table = gen_to_ref_table.get(fk.ref_table)
                if not ref_target_table:
                    unmapped.append(
                        {
                            "table": gen_table.name,
                            "columns": fk.columns,
                            "ref_table": fk.ref_table,
                            "ref_columns": fk.ref_columns,
                            "reason": "unmatched_ref_table",
                        }
                    )
                    continue
                target_alignment = column_alignments.get(ref_target_table, AlignmentResult())
                target_gen_to_ref_col = {
                    gen: ref for ref, gen in target_alignment.mapping.items()
                }
                mapped_columns = [gen_to_ref_col[column] for column in fk.columns if column in gen_to_ref_col]
                mapped_ref_columns = [
                    target_gen_to_ref_col[column]
                    for column in fk.ref_columns
                    if column in target_gen_to_ref_col
                ]
                if len(mapped_columns) != len(fk.columns) or len(mapped_ref_columns) != len(fk.ref_columns):
                    unmapped.append(
                        {
                            "table": gen_table.name,
                            "columns": fk.columns,
                            "mapped_columns": mapped_columns,
                            "ref_table": fk.ref_table,
                            "ref_columns": fk.ref_columns,
                            "mapped_ref_columns": mapped_ref_columns,
                            "reason": "unmatched_column",
                        }
                    )
                    continue
                result.append(
                    (
                        ref_table_name,
                        tuple(mapped_columns),
                        ref_target_table,
                        tuple(mapped_ref_columns),
                    )
                )
        return result, unmapped

    def _reference_constraints(
        self,
        schema: SchemaIR,
        column_alignments: dict[str, AlignmentResult],
    ) -> list[tuple[str, str, tuple[str, ...]]]:
        result = []
        for table in schema.tables:
            alignment = column_alignments.get(table.name)
            if alignment is None:
                continue
            for column in table.columns:
                if column.name in alignment.mapping and not column.nullable:
                    result.append((table.name, "not_null", (column.name,)))
            for unique in table.unique_constraints:
                if all(column in alignment.mapping for column in unique.columns):
                    result.append((table.name, "unique", tuple(sorted(unique.columns))))
        return result

    def _mapped_constraints(
        self,
        generated: SchemaIR,
        table_alignment: AlignmentResult,
        column_alignments: dict[str, AlignmentResult],
    ) -> list[tuple[str, str, tuple[str, ...]]]:
        gen_to_ref_table = {gen: ref for ref, gen in table_alignment.mapping.items()}
        result = []
        for gen_table in generated.tables:
            ref_table_name = gen_to_ref_table.get(gen_table.name)
            if not ref_table_name:
                continue
            alignment = column_alignments.get(ref_table_name, AlignmentResult())
            gen_to_ref_col = {gen: ref for ref, gen in alignment.mapping.items()}
            for column in gen_table.columns:
                ref_column = gen_to_ref_col.get(column.name)
                if ref_column and not column.nullable:
                    result.append((ref_table_name, "not_null", (ref_column,)))
            for unique in gen_table.unique_constraints:
                mapped = [gen_to_ref_col[column] for column in unique.columns if column in gen_to_ref_col]
                if len(mapped) == len(unique.columns):
                    result.append((ref_table_name, "unique", tuple(sorted(mapped))))
        return result

    def _missing_columns(
        self,
        reference: SchemaIR,
        column_alignments: dict[str, AlignmentResult],
    ) -> list[dict[str, str]]:
        missing = []
        for table in reference.tables:
            alignment = column_alignments.get(table.name, AlignmentResult())
            for column in table.columns:
                if column.name not in alignment.mapping:
                    missing.append({"table": table.name, "column": column.name})
        return missing

    def _extra_columns(
        self,
        table_pairs: dict[str, tuple[TableIR | None, TableIR | None]],
        column_alignments: dict[str, AlignmentResult],
    ) -> list[dict[str, str]]:
        extra = []
        for ref_name, (_ref_table, gen_table) in table_pairs.items():
            if gen_table is None:
                continue
            alignment = column_alignments.get(ref_name, AlignmentResult())
            matched_generated = set(alignment.mapping.values())
            for column in gen_table.columns:
                if column.name not in matched_generated:
                    extra.append({"table": gen_table.name, "column": column.name})
        return extra

    @staticmethod
    def _find_table(schema: SchemaIR, name: str) -> TableIR | None:
        for table in schema.tables:
            if table.name == name:
                return table
        return None


def emit_progress(enabled: bool, message: str) -> None:
    if enabled:
        print(message, file=sys.stderr, flush=True)


def select_candidates(
    candidate_json: Path,
    *,
    task_ids: tuple[str, ...] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    payload = read_json(candidate_json)
    candidates = list(payload.get("candidates", []))
    if task_ids:
        requested = set(task_ids)
        candidates = [
            candidate
            for candidate in candidates
            if repo_slug(str(candidate.get("full_name") or "")) in requested
            or str(candidate.get("full_name") or "") in requested
        ]
    if limit is not None:
        candidates = candidates[:limit]
    return candidates


def required_runtime_dbms_for_evaluation(
    candidates: list[dict[str, Any]],
    config: StaticMatchConfig,
) -> set[str]:
    if config.runtime_ir_cache_only:
        return set()
    required: set[str] = set()
    for candidate in candidates:
        full_name = str(candidate.get("full_name") or "")
        task_id = repo_slug(full_name)
        target_dbms = str(candidate.get("dbms_final") or "")
        _reference_path, reference_ddl, _reference_errors = read_reference_ddl(candidate)
        reference, _reference_diagnostic = load_reference_runtime_ir_cache(
            task_id=task_id,
            target_dbms=target_dbms,
            ddl=reference_ddl,
            runtime_ir_dir=config.reference_runtime_ir_dir,
            refresh=config.refresh_reference_runtime_ir,
            upgrade_legacy=False,
        )

        run_path = config.run_dir / f"{task_id}.json"
        run_payload, _run_errors = read_run_payload(run_path)
        generated_ddl = str(run_payload.get("final_ddl") or "")
        generated, _generated_diagnostic = load_generated_runtime_ir_cache(
            task_id=task_id,
            target_dbms=target_dbms,
            ddl=generated_ddl,
            runtime_ir_dir=config.generated_runtime_ir_dir,
            source_run_path=run_path.as_posix(),
            refresh=config.refresh_generated_runtime_ir,
            accept_legacy=config.accept_legacy_generated_runtime_ir,
            upgrade_cache=False,
        )
        if (reference is None or generated is None) and target_dbms:
            required.add(target_dbms)
    return required


def evaluate_static_match(config: StaticMatchConfig) -> dict[str, Any]:
    candidates = select_candidates(
        config.candidate_json,
        task_ids=config.task_ids,
        limit=config.limit,
    )
    emit_progress(
        config.progress,
        f"[evaluate] loading semantic matcher for {len(candidates)} samples",
    )
    name_matcher = build_name_matcher(config)
    matcher = StaticSchemaMatcher(
        name_matcher,
        accuracy_f1_threshold=config.accuracy_f1_threshold,
        accuracy_medium_f1_threshold=config.accuracy_medium_f1_threshold,
        accuracy_hard_f1_threshold=config.accuracy_hard_f1_threshold,
    )
    sample_results = []
    dbms_set = required_runtime_dbms_for_evaluation(candidates, config)
    service_message = ", ".join(sorted(dbms_set)) if dbms_set else "none (all cached)"
    emit_progress(
        config.progress,
        "[evaluate] preparing runtime services: " + service_message,
    )
    service_availability, started = prepare_runtime_services(dbms_set)
    try:
        for index, candidate in enumerate(candidates, start=1):
            task_id = repo_slug(str(candidate.get("full_name") or ""))
            target_dbms = str(candidate.get("dbms_final") or "")
            emit_progress(
                config.progress,
                f"[evaluate {index}/{len(candidates)}] {task_id} ({target_dbms})",
            )
            result = evaluate_static_match_candidate(
                candidate,
                config=config,
                matcher=matcher,
                service_availability=service_availability,
            )
            sample_results.append(result)
            reference_execution = result.get("reference_execution") or {}
            generated_execution = result.get("generated_execution") or {}
            reference_source = str(reference_execution.get("source") or "database")
            reference_cache = str(reference_execution.get("cache_status") or "")
            generated_source = str(generated_execution.get("source") or "database")
            generated_cache = str(generated_execution.get("cache_status") or "")
            reference_label = reference_source
            if reference_cache:
                reference_label += f":{reference_cache}"
            generated_label = generated_source
            if generated_cache:
                generated_label += f":{generated_cache}"
            emit_progress(
                config.progress,
                (
                    f"[evaluate {index}/{len(candidates)}] done {task_id} "
                    f"generated={generated_execution.get('status', 'unknown')}/{generated_label} "
                    f"reference={reference_execution.get('status', 'unknown')}/{reference_label} "
                    f"scored={'yes' if result.get('scored') else 'no'}"
                ),
            )
    finally:
        if not config.keep_containers:
            cleanup_runtime_services(started)

    scored_results = [item for item in sample_results if item.get("scored")]
    emit_progress(
        config.progress,
        f"[evaluate] complete: scored={len(scored_results)}/{len(sample_results)}",
    )
    grouped_results: dict[str, list[dict[str, Any]]] = {}
    for result in scored_results:
        grouped_results.setdefault(str(result["run_status"]), []).append(result)
    execution_summary = executability_summary(sample_results)
    logical_static_match = logical_summary(scored_results)
    physical_static_match = physical_summary(scored_results)
    diagnostics = diagnostic_summary(scored_results)
    return {
        "source": {
            "candidate_json": config.candidate_json.as_posix(),
            "run_dir": config.run_dir.as_posix(),
            "generated_runtime_ir_dir": config.generated_runtime_ir_dir.as_posix(),
            "reference_runtime_ir_dir": config.reference_runtime_ir_dir.as_posix(),
            "sample_count": len(sample_results),
            "scored_count": len(scored_results),
            "supported_dbms": sorted(SUPPORTED_DBMS),
            "docker_dbms": sorted(DOCKER_DBMS),
            "service_availability": service_availability,
            "embedding_backend": config.embedding_backend,
            "embedding_model": config.embedding_model,
            "similarity_threshold": config.similarity_threshold,
            "string_threshold": config.string_threshold,
            "metric_version": STATIC_MATCH_METRIC_VERSION,
            "accuracy_f1_threshold": config.accuracy_f1_threshold,
            "accuracy_difficulty_tiers": [
                {
                    "difficulty_tier": "easy",
                    "minimum_reference_tables": 1,
                    "maximum_reference_tables": EASY_MAX_REFERENCE_TABLES,
                    "f1_threshold": config.accuracy_f1_threshold,
                },
                {
                    "difficulty_tier": "medium",
                    "minimum_reference_tables": EASY_MAX_REFERENCE_TABLES + 1,
                    "maximum_reference_tables": MEDIUM_MAX_REFERENCE_TABLES,
                    "f1_threshold": config.accuracy_medium_f1_threshold,
                },
                {
                    "difficulty_tier": "hard",
                    "minimum_reference_tables": MEDIUM_MAX_REFERENCE_TABLES + 1,
                    "maximum_reference_tables": None,
                    "f1_threshold": config.accuracy_hard_f1_threshold,
                },
            ],
            "task_ids": list(config.task_ids),
            "refresh_reference_runtime_ir": config.refresh_reference_runtime_ir,
            "refresh_generated_runtime_ir": config.refresh_generated_runtime_ir,
            "accept_legacy_generated_runtime_ir": (
                config.accept_legacy_generated_runtime_ir
            ),
            "runtime_ir_cache_only": config.runtime_ir_cache_only,
        },
        "summary": {
            "sample_count": len(sample_results),
            "scored_count": len(scored_results),
            "executability": execution_summary,
            "reference_runtime_ir_cache": reference_cache_summary(sample_results),
            "generated_runtime_ir_cache": generated_cache_summary(sample_results),
            "logical_static_match": logical_static_match,
            "physical_static_match": physical_static_match,
            "diagnostics": diagnostics,
            "end_to_end": end_to_end_summary(
                logical_static_match,
                physical_static_match,
                execution_summary["generated_executability_rate"],
            ),
            "by_run_status": {
                status: {
                    "sample_count": len(items),
                    "logical_static_match": logical_summary(items),
                    "physical_static_match": physical_summary(items),
                    "diagnostics": diagnostic_summary(items),
                }
                for status, items in sorted(grouped_results.items())
            },
        },
        "samples": sample_results,
    }


def prepare_reference_runtime_ir(config: ReferenceRuntimeIRConfig) -> dict[str, Any]:
    candidates = select_candidates(
        config.candidate_json,
        task_ids=config.task_ids,
        limit=config.limit,
    )
    prepared: list[dict[str, Any]] = []
    dbms_set: set[str] = set()
    emit_progress(
        config.progress,
        f"[reference] scanning cache for {len(candidates)} samples",
    )
    for candidate in candidates:
        full_name = str(candidate.get("full_name") or "")
        task_id = repo_slug(full_name)
        target_dbms = str(candidate.get("dbms_final") or "")
        reference_path, ddl, errors = read_reference_ddl(candidate)
        normalized, _diagnostic = load_reference_runtime_ir_cache(
            task_id=task_id,
            target_dbms=target_dbms,
            ddl=ddl,
            runtime_ir_dir=config.reference_runtime_ir_dir,
            refresh=config.refresh,
            upgrade_legacy=False,
        )
        prepared.append(
            {
                "task_id": task_id,
                "full_name": full_name,
                "target_dbms": target_dbms,
                "reference_ddl_path": reference_path,
                "ddl": ddl,
                "errors": errors,
            }
        )
        if normalized is None and target_dbms:
            dbms_set.add(target_dbms)

    if dbms_set:
        service_message = ", ".join(sorted(dbms_set))
    else:
        service_message = "none (all samples cached)"
    emit_progress(
        config.progress,
        f"[reference] preparing runtime services: {service_message}",
    )
    service_availability, started = prepare_runtime_services(dbms_set)
    results = []
    try:
        for index, item in enumerate(prepared, start=1):
            emit_progress(
                config.progress,
                (
                    f"[reference {index}/{len(prepared)}] {item['task_id']} "
                    f"({item['target_dbms']})"
                ),
            )
            normalized, execution = load_or_execute_reference_runtime(
                task_id=item["task_id"],
                target_dbms=item["target_dbms"],
                ddl=item["ddl"],
                runtime_ir_dir=config.reference_runtime_ir_dir,
                write_runtime_ir=True,
                service_availability=service_availability,
                refresh=config.refresh,
            )
            results.append(
                {
                    "task_id": item["task_id"],
                    "full_name": item["full_name"],
                    "target_dbms": item["target_dbms"],
                    "reference_ddl_path": (
                        item["reference_ddl_path"].as_posix()
                        if item["reference_ddl_path"]
                        else ""
                    ),
                    "has_reference_runtime_ir": (
                        isinstance(normalized, dict) and bool(normalized.get("tables"))
                    ),
                    "reference_execution": execution,
                    "errors": item["errors"],
                }
            )
            emit_progress(
                config.progress,
                (
                    f"[reference {index}/{len(prepared)}] done {item['task_id']} "
                    f"status={execution.get('status', 'unknown')} "
                    f"cache={execution.get('cache_status', 'unknown')}"
                ),
            )
    finally:
        if not config.keep_containers:
            cleanup_runtime_services(started)

    passed_count = sum(
        1
        for item in results
        if item["reference_execution"].get("status") == "passed"
        and item["has_reference_runtime_ir"]
    )
    emit_progress(
        config.progress,
        f"[reference] complete: passed={passed_count}/{len(results)}",
    )
    return {
        "source": {
            "candidate_json": config.candidate_json.as_posix(),
            "reference_runtime_ir_dir": config.reference_runtime_ir_dir.as_posix(),
            "sample_count": len(results),
            "supported_dbms": sorted(SUPPORTED_DBMS),
            "docker_dbms": sorted(DOCKER_DBMS),
            "service_availability": service_availability,
            "task_ids": list(config.task_ids),
            "limit": config.limit,
            "refresh": config.refresh,
        },
        "summary": {
            "sample_count": len(results),
            "passed_count": passed_count,
            "failed_count": len(results) - passed_count,
            "reference_runtime_ir_cache": reference_cache_summary(results),
        },
        "samples": results,
    }


def prepare_generated_runtime_ir(config: GeneratedRuntimeIRConfig) -> dict[str, Any]:
    candidates = select_candidates(
        config.candidate_json,
        task_ids=config.task_ids,
        limit=config.limit,
    )
    prepared: list[dict[str, Any]] = []
    dbms_set: set[str] = set()
    emit_progress(
        config.progress,
        f"[generated] scanning cache for {len(candidates)} samples",
    )
    for candidate in candidates:
        full_name = str(candidate.get("full_name") or "")
        task_id = repo_slug(full_name)
        target_dbms = str(candidate.get("dbms_final") or "")
        run_path = config.run_dir / f"{task_id}.json"
        errors: list[str] = []
        run_payload, run_errors = read_run_payload(run_path)
        errors.extend(run_errors)
        ddl = str(run_payload.get("final_ddl") or "")
        if not ddl.strip():
            errors.append("missing_generated_ddl")
        normalized, _diagnostic = load_generated_runtime_ir_cache(
            task_id=task_id,
            target_dbms=target_dbms,
            ddl=ddl,
            runtime_ir_dir=config.generated_runtime_ir_dir,
            source_run_path=run_path.as_posix(),
            refresh=config.refresh,
            accept_legacy=config.accept_legacy,
            upgrade_cache=False,
        )
        prepared.append(
            {
                "task_id": task_id,
                "full_name": full_name,
                "target_dbms": target_dbms,
                "run_path": run_path,
                "ddl": ddl,
                "errors": errors,
            }
        )
        if normalized is None and target_dbms and ddl.strip():
            dbms_set.add(target_dbms)

    service_message = ", ".join(sorted(dbms_set)) if dbms_set else "none (all cached)"
    emit_progress(
        config.progress,
        f"[generated] preparing runtime services: {service_message}",
    )
    service_availability, started = prepare_runtime_services(dbms_set)
    results = []
    try:
        for index, item in enumerate(prepared, start=1):
            emit_progress(
                config.progress,
                (
                    f"[generated {index}/{len(prepared)}] {item['task_id']} "
                    f"({item['target_dbms']})"
                ),
            )
            normalized, execution = load_or_execute_generated_runtime(
                task_id=item["task_id"],
                target_dbms=item["target_dbms"],
                ddl=item["ddl"],
                runtime_ir_dir=config.generated_runtime_ir_dir,
                write_runtime_ir=True,
                service_availability=service_availability,
                source_run_path=item["run_path"].as_posix(),
                refresh=config.refresh,
                accept_legacy=config.accept_legacy,
            )
            results.append(
                {
                    "task_id": item["task_id"],
                    "full_name": item["full_name"],
                    "target_dbms": item["target_dbms"],
                    "run_path": item["run_path"].as_posix(),
                    "has_generated_runtime_ir": (
                        isinstance(normalized, dict) and bool(normalized.get("tables"))
                    ),
                    "generated_execution": execution,
                    "errors": item["errors"],
                }
            )
            emit_progress(
                config.progress,
                (
                    f"[generated {index}/{len(prepared)}] done {item['task_id']} "
                    f"status={execution.get('status', 'unknown')} "
                    f"cache={execution.get('cache_status', 'unknown')}"
                ),
            )
    finally:
        if not config.keep_containers:
            cleanup_runtime_services(started)

    passed_count = sum(
        1
        for item in results
        if item["generated_execution"].get("status") == "passed"
        and item["has_generated_runtime_ir"]
    )
    emit_progress(
        config.progress,
        f"[generated] complete: passed={passed_count}/{len(results)}",
    )
    return {
        "source": {
            "candidate_json": config.candidate_json.as_posix(),
            "run_dir": config.run_dir.as_posix(),
            "generated_runtime_ir_dir": config.generated_runtime_ir_dir.as_posix(),
            "sample_count": len(results),
            "supported_dbms": sorted(SUPPORTED_DBMS),
            "docker_dbms": sorted(DOCKER_DBMS),
            "service_availability": service_availability,
            "task_ids": list(config.task_ids),
            "limit": config.limit,
            "refresh": config.refresh,
            "accept_legacy": config.accept_legacy,
        },
        "summary": {
            "sample_count": len(results),
            "passed_count": passed_count,
            "failed_count": len(results) - passed_count,
            "generated_runtime_ir_cache": generated_cache_summary(results),
        },
        "samples": results,
    }


def evaluate_static_match_candidate(
    candidate: dict[str, Any],
    *,
    config: StaticMatchConfig,
    matcher: StaticSchemaMatcher,
    service_availability: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    full_name = str(candidate.get("full_name") or "")
    task_id = repo_slug(full_name)
    run_path = config.run_dir / f"{task_id}.json"
    errors: list[str] = []
    run_payload, run_errors = read_run_payload(run_path)
    errors.extend(run_errors)

    target_dbms = str(candidate.get("dbms_final") or dig(run_payload, "state", "task", "target_dbms") or "")
    run_status = str(run_payload.get("status") or "missing")
    reference_ddl_path, reference_ddl, reference_errors = read_reference_ddl(candidate)
    errors.extend(reference_errors)
    generated_ddl = str(run_payload.get("final_ddl") or "")

    reference_normalized, reference_execution = load_or_execute_reference_runtime(
        task_id=task_id,
        target_dbms=target_dbms,
        ddl=reference_ddl,
        runtime_ir_dir=config.reference_runtime_ir_dir,
        write_runtime_ir=config.write_runtime_ir,
        service_availability=service_availability,
        refresh=config.refresh_reference_runtime_ir,
        cache_only=config.runtime_ir_cache_only,
    )
    generated_normalized, generated_execution = load_or_execute_generated_runtime(
        task_id=task_id,
        target_dbms=target_dbms,
        ddl=generated_ddl,
        runtime_ir_dir=config.generated_runtime_ir_dir,
        write_runtime_ir=config.write_runtime_ir,
        service_availability=service_availability,
        source_run_path=run_path.as_posix(),
        refresh=config.refresh_generated_runtime_ir,
        accept_legacy=config.accept_legacy_generated_runtime_ir,
        cache_only=config.runtime_ir_cache_only,
    )
    has_reference_runtime_ir = isinstance(reference_normalized, dict) and bool(reference_normalized.get("tables"))
    has_generated_runtime_ir = isinstance(generated_normalized, dict) and bool(generated_normalized.get("tables"))
    if not has_reference_runtime_ir:
        errors.append("missing_reference_runtime_ir")
    if not has_generated_runtime_ir:
        errors.append("missing_generated_runtime_ir")

    base = {
        "task_id": task_id,
        "full_name": full_name,
        "target_dbms": target_dbms,
        "run_path": run_path.as_posix(),
        "reference_ddl_path": reference_ddl_path.as_posix() if reference_ddl_path else "",
        "run_status": run_status,
        "has_reference_runtime_ir": has_reference_runtime_ir,
        "has_generated_runtime_ir": has_generated_runtime_ir,
        "has_generated_schema_ir": has_generated_runtime_ir,
        "has_generated_indexes": False,
        "reference_execution": reference_execution,
        "generated_execution": generated_execution,
        "errors": errors,
    }
    if not has_reference_runtime_ir or not has_generated_runtime_ir:
        return {
            **base,
            "scored": False,
            "metrics": zero_metrics(),
            "diagnostic_metrics": zero_diagnostic_metrics(),
            "counts": StaticMatchCounters().__dict__,
            "details": {"errors": errors},
        }

    reference_schema = SchemaIR.from_dict(reference_normalized)
    generated_schema = SchemaIR.from_dict(generated_normalized)
    reference_indexes = index_records_from_schema(reference_normalized)
    generated_indexes = index_records_from_schema(generated_normalized)
    result = matcher.evaluate(
        reference=reference_schema,
        generated=generated_schema,
        reference_indexes=reference_indexes,
        generated_indexes=generated_indexes,
        task_id=task_id,
        full_name=full_name,
        target_dbms=target_dbms,
        run_status=run_status,
        has_generated_schema_ir=True,
        has_generated_indexes=bool(generated_indexes),
        errors=errors,
    )
    return {
        **result,
        "scored": True,
        "run_path": run_path.as_posix(),
        "reference_ddl_path": reference_ddl_path.as_posix() if reference_ddl_path else "",
        "has_reference_runtime_ir": True,
        "has_generated_runtime_ir": True,
        "reference_execution": reference_execution,
        "generated_execution": generated_execution,
    }


def runtime_ir_cache_path(runtime_ir_dir: Path, task_id: str, side: str) -> Path:
    return runtime_ir_dir / f"{task_id}.{side}.runtime_schema_ir.json"


def reference_ddl_hash(ddl: str) -> str:
    return hashlib.sha256(ddl.encode("utf-8")).hexdigest()


def generated_ddl_hash(ddl: str) -> str:
    return hashlib.sha256(ddl.encode("utf-8")).hexdigest()


def dump_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        dump_json(temporary, data)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_reference_runtime_ir_cache(
    *,
    task_id: str,
    target_dbms: str,
    ddl: str,
    runtime_ir_dir: Path,
    refresh: bool = False,
    upgrade_legacy: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    cache_path = runtime_ir_cache_path(runtime_ir_dir, task_id, "reference")
    diagnostic: dict[str, Any] = {
        "cache_hit": False,
        "cache_lookup_status": "refresh" if refresh else "miss",
        "runtime_ir_path": cache_path.as_posix(),
    }
    if refresh:
        return None, diagnostic
    if not cache_path.exists():
        return None, diagnostic

    try:
        payload = read_json(cache_path)
    except Exception as exc:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": f"{exc.__class__.__name__}: {exc}",
        }
    if not isinstance(payload, dict):
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "cache payload is not an object",
        }

    cache_version = payload.get("cache_version")
    if cache_version is not None and cache_version != REFERENCE_RUNTIME_CACHE_VERSION:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": f"unsupported cache_version:{cache_version}",
        }
    expected = {
        "task_id": task_id,
        "side": "reference",
        "target_dbms": target_dbms,
    }
    for key, value in expected.items():
        if str(payload.get(key) or "") != value:
            return None, {
                **diagnostic,
                "cache_lookup_status": "invalid",
                "cache_error": f"cache {key} mismatch",
            }

    cached_hash = str(payload.get("reference_ddl_sha256") or "")
    current_hash = reference_ddl_hash(ddl) if ddl else ""
    if cached_hash and current_hash and cached_hash != current_hash:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "reference DDL hash mismatch",
        }

    normalized = payload.get("normalized_runtime_schema_ir")
    if not isinstance(normalized, dict) or not normalized.get("tables"):
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "normalized runtime IR is missing or empty",
        }

    legacy = cache_version is None or not cached_hash
    cache_status = "legacy_hit" if legacy else "hit"
    upgrade_error = ""
    if legacy and upgrade_legacy and current_hash:
        upgraded = {
            **payload,
            "cache_version": REFERENCE_RUNTIME_CACHE_VERSION,
            "reference_ddl_sha256": current_hash,
        }
        try:
            dump_json_atomic(cache_path, upgraded)
        except Exception as exc:  # pragma: no cover - filesystem failure
            upgrade_error = f"{exc.__class__.__name__}: {exc}"

    execution = {
        "status": "passed",
        "executed": False,
        "introspected": False,
        "table_count_runtime": len(normalized.get("tables") or []),
        "error": None,
        "source": "cache",
        "cache_hit": True,
        "cache_status": cache_status,
        "cache_lookup_status": cache_status,
        "runtime_ir_path": cache_path.as_posix(),
    }
    if upgrade_error:
        execution["cache_upgrade_error"] = upgrade_error
    return normalized, execution


def load_generated_runtime_ir_cache(
    *,
    task_id: str,
    target_dbms: str,
    ddl: str,
    runtime_ir_dir: Path,
    source_run_path: str = "",
    refresh: bool = False,
    accept_legacy: bool = False,
    upgrade_cache: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    cache_path = runtime_ir_cache_path(runtime_ir_dir, task_id, "generated")
    diagnostic: dict[str, Any] = {
        "cache_hit": False,
        "cache_lookup_status": "refresh" if refresh else "miss",
        "runtime_ir_path": cache_path.as_posix(),
    }
    if refresh:
        return None, diagnostic
    if not ddl.strip():
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "generated DDL is empty",
        }
    if not cache_path.exists():
        return None, diagnostic

    try:
        payload = read_json(cache_path)
    except Exception as exc:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": f"{exc.__class__.__name__}: {exc}",
        }
    if not isinstance(payload, dict):
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "cache payload is not an object",
        }

    cache_version = payload.get("cache_version")
    if cache_version is not None and cache_version != GENERATED_RUNTIME_CACHE_VERSION:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": f"unsupported cache_version:{cache_version}",
        }
    expected = {
        "task_id": task_id,
        "side": "generated",
        "target_dbms": target_dbms,
    }
    for key, value in expected.items():
        if str(payload.get(key) or "") != value:
            return None, {
                **diagnostic,
                "cache_lookup_status": "invalid",
                "cache_error": f"cache {key} mismatch",
            }

    cached_hash = str(payload.get("generated_ddl_sha256") or "")
    current_hash = generated_ddl_hash(ddl) if ddl else ""
    if cached_hash and current_hash and cached_hash != current_hash:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "generated DDL hash mismatch",
        }

    raw = payload.get("raw_runtime_schema_ir")
    normalized = payload.get("normalized_runtime_schema_ir")
    if not isinstance(raw, dict) or not raw.get("tables"):
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "raw runtime IR is missing or empty",
        }
    if not isinstance(normalized, dict) or not normalized.get("tables"):
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "normalized runtime IR is missing or empty",
        }

    legacy = any(
        payload.get(key) is None
        for key in (
            "cache_version",
            "generated_ddl_sha256",
            "introspection_version",
            "normalization_version",
        )
    )
    if legacy and not accept_legacy:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "legacy generated cache requires explicit acceptance",
        }
    if not legacy and payload.get("introspection_version") != RUNTIME_INTROSPECTION_VERSION:
        return None, {
            **diagnostic,
            "cache_lookup_status": "invalid",
            "cache_error": "runtime introspection version mismatch",
        }

    renormalized = (
        not legacy
        and payload.get("normalization_version") != RUNTIME_NORMALIZATION_VERSION
    )
    if renormalized:
        normalized = normalize_schema_ir(raw, target_dbms)
        if not normalized.get("tables"):
            return None, {
                **diagnostic,
                "cache_lookup_status": "invalid",
                "cache_error": "renormalized runtime IR is empty",
            }

    cache_status = "legacy_hit" if legacy else "renormalized" if renormalized else "hit"
    upgrade_error = ""
    if (legacy or renormalized) and upgrade_cache and current_hash:
        upgraded = {
            **payload,
            "cache_version": GENERATED_RUNTIME_CACHE_VERSION,
            "introspection_version": RUNTIME_INTROSPECTION_VERSION,
            "normalization_version": RUNTIME_NORMALIZATION_VERSION,
            "generated_ddl_sha256": current_hash,
            "normalized_runtime_schema_ir": normalized,
        }
        if source_run_path:
            upgraded["source_run_path"] = source_run_path
        try:
            dump_json_atomic(cache_path, upgraded)
        except Exception as exc:  # pragma: no cover - filesystem failure
            upgrade_error = f"{exc.__class__.__name__}: {exc}"

    execution = {
        "status": "passed",
        "executed": False,
        "introspected": False,
        "table_count_runtime": len(normalized.get("tables") or []),
        "error": None,
        "source": "cache",
        "cache_hit": True,
        "cache_status": cache_status,
        "cache_lookup_status": cache_status,
        "runtime_ir_path": cache_path.as_posix(),
    }
    if upgrade_error:
        execution["cache_upgrade_error"] = upgrade_error
    return normalized, execution


def load_or_execute_reference_runtime(
    *,
    task_id: str,
    target_dbms: str,
    ddl: str,
    runtime_ir_dir: Path,
    write_runtime_ir: bool,
    service_availability: dict[str, dict[str, Any]],
    refresh: bool = False,
    cache_only: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    normalized, cache_diagnostic = load_reference_runtime_ir_cache(
        task_id=task_id,
        target_dbms=target_dbms,
        ddl=ddl,
        runtime_ir_dir=runtime_ir_dir,
        refresh=refresh,
        upgrade_legacy=write_runtime_ir,
    )
    if normalized is not None:
        return normalized, cache_diagnostic
    if cache_only:
        return None, {
            "status": "skipped",
            "executed": False,
            "introspected": False,
            "reason": "reference_runtime_ir_cache_miss",
            "source": "cache",
            "cache_hit": False,
            "cache_status": cache_diagnostic["cache_lookup_status"],
            **cache_diagnostic,
        }

    normalized, execution = execute_runtime_side(
        task_id=task_id,
        side="reference",
        target_dbms=target_dbms,
        ddl=ddl,
        runtime_ir_dir=runtime_ir_dir,
        write_runtime_ir=write_runtime_ir,
        service_availability=service_availability,
        runtime_ir_metadata={
            "cache_version": REFERENCE_RUNTIME_CACHE_VERSION,
            "reference_ddl_sha256": reference_ddl_hash(ddl),
        },
        atomic_runtime_ir_write=True,
    )
    if normalized is not None:
        cache_status = "built" if write_runtime_ir else "not_written"
    else:
        cache_status = "failed"
    return normalized, {
        **execution,
        "source": "database",
        "cache_hit": False,
        "cache_status": cache_status,
        "cache_lookup_status": cache_diagnostic["cache_lookup_status"],
        **(
            {"cache_error": cache_diagnostic["cache_error"]}
            if cache_diagnostic.get("cache_error")
            else {}
        ),
    }


def load_or_execute_generated_runtime(
    *,
    task_id: str,
    target_dbms: str,
    ddl: str,
    runtime_ir_dir: Path,
    write_runtime_ir: bool,
    service_availability: dict[str, dict[str, Any]],
    source_run_path: str = "",
    refresh: bool = False,
    accept_legacy: bool = False,
    cache_only: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    normalized, cache_diagnostic = load_generated_runtime_ir_cache(
        task_id=task_id,
        target_dbms=target_dbms,
        ddl=ddl,
        runtime_ir_dir=runtime_ir_dir,
        source_run_path=source_run_path,
        refresh=refresh,
        accept_legacy=accept_legacy,
        upgrade_cache=write_runtime_ir,
    )
    if normalized is not None:
        return normalized, cache_diagnostic
    if cache_only:
        return None, {
            "status": "skipped",
            "executed": False,
            "introspected": False,
            "reason": "generated_runtime_ir_cache_miss",
            "source": "cache",
            "cache_hit": False,
            "cache_status": cache_diagnostic["cache_lookup_status"],
            **cache_diagnostic,
        }

    normalized, execution = execute_runtime_side(
        task_id=task_id,
        side="generated",
        target_dbms=target_dbms,
        ddl=ddl,
        runtime_ir_dir=runtime_ir_dir,
        write_runtime_ir=write_runtime_ir,
        service_availability=service_availability,
        runtime_ir_metadata={
            "cache_version": GENERATED_RUNTIME_CACHE_VERSION,
            "introspection_version": RUNTIME_INTROSPECTION_VERSION,
            "normalization_version": RUNTIME_NORMALIZATION_VERSION,
            "generated_ddl_sha256": generated_ddl_hash(ddl),
            "source_run_path": source_run_path,
        },
        atomic_runtime_ir_write=True,
    )
    if normalized is not None:
        cache_status = "built" if write_runtime_ir else "not_written"
    else:
        cache_status = "failed"
    return normalized, {
        **execution,
        "source": "database",
        "cache_hit": False,
        "cache_status": cache_status,
        "cache_lookup_status": cache_diagnostic["cache_lookup_status"],
        **(
            {"cache_error": cache_diagnostic["cache_error"]}
            if cache_diagnostic.get("cache_error")
            else {}
        ),
    }


def execute_runtime_side(
    *,
    task_id: str,
    side: str,
    target_dbms: str,
    ddl: str,
    runtime_ir_dir: Path,
    write_runtime_ir: bool,
    service_availability: dict[str, dict[str, Any]],
    runtime_ir_metadata: dict[str, Any] | None = None,
    atomic_runtime_ir_write: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if target_dbms not in SUPPORTED_DBMS:
        return None, {
            "status": "skipped",
            "executed": False,
            "introspected": False,
            "reason": f"unsupported_dbms:{target_dbms}",
        }
    service = service_availability.get(target_dbms, {"available": True, "reason": ""})
    if not service.get("available", True):
        return None, {
            "status": "skipped",
            "executed": False,
            "introspected": False,
            "reason": f"runtime_unavailable:{service.get('reason')}",
        }
    if not ddl.strip():
        return None, {
            "status": "failed",
            "executed": False,
            "introspected": False,
            "error_type": f"missing_{side}_ddl",
            "error": f"{side} DDL is empty.",
        }
    try:
        raw_runtime, execution = execute_and_introspect_runtime(
            target_dbms,
            f"{task_id}_{side}",
            ddl,
        )
    except Exception as exc:
        return None, {
            "status": "failed",
            "executed": False,
            "introspected": False,
            "error_type": "runtime_exception",
            "exception_type": exc.__class__.__name__,
            "error": str(exc),
        }
    if raw_runtime is None:
        return None, execution
    normalized = normalize_schema_ir(raw_runtime, target_dbms)
    runtime_ir_path = runtime_ir_cache_path(runtime_ir_dir, task_id, side)
    if write_runtime_ir:
        runtime_payload = {
            "task_id": task_id,
            "side": side,
            "target_dbms": target_dbms,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "raw_runtime_schema_ir": raw_runtime,
            "normalized_runtime_schema_ir": normalized,
            **(runtime_ir_metadata or {}),
        }
        if atomic_runtime_ir_write:
            dump_json_atomic(runtime_ir_path, runtime_payload)
        else:
            dump_json(runtime_ir_path, runtime_payload)
    return normalized, {
        **execution,
        "runtime_ir_path": runtime_ir_path.as_posix() if write_runtime_ir else "",
    }


def reference_ddl_path_from_candidate(candidate: dict[str, Any]) -> Path | None:
    generation = candidate.get("reference_ddl_generation")
    if isinstance(generation, dict) and generation.get("ddl_path"):
        return Path(str(generation["ddl_path"]))
    if candidate.get("reference_ddl_path"):
        return Path(str(candidate["reference_ddl_path"]))
    return None


def read_reference_ddl(
    candidate: dict[str, Any],
) -> tuple[Path | None, str, list[str]]:
    path = reference_ddl_path_from_candidate(candidate)
    if path is None:
        return None, "", ["missing_reference_ddl_path"]
    if not path.exists():
        return path, "", [f"missing_reference_ddl:{path.as_posix()}"]
    return path, path.read_text(encoding="utf-8", errors="ignore"), []


def read_run_payload(run_path: Path) -> tuple[dict[str, Any], list[str]]:
    if not run_path.exists():
        return {}, [f"missing_run_file:{run_path.as_posix()}"]
    try:
        payload = read_json(run_path)
    except Exception as exc:
        return {}, [f"invalid_run_file:{exc.__class__.__name__}:{exc}"]
    if not isinstance(payload, dict):
        return {}, ["invalid_run_file:payload is not an object"]
    return payload, []


def index_records_from_schema(schema: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = build_index_inventory(schema)
    return [
        {
            "table": item["table"],
            "columns": item["columns"],
            "unique": item["unique"],
            "origins": item.get("origins", []),
            "names": item.get("names", []),
        }
        for _key, item in sorted(inventory.items(), key=lambda pair: repr(pair[0]))
    ]


def schema_index_records(schema: SchemaIR) -> list[dict[str, Any]]:
    return index_records_from_schema(schema.to_dict())


def zero_metrics() -> dict[str, float]:
    return {
        "table_acc": 0.0,
        "table_f1": 0.0,
        "column_acc": 0.0,
        "column_f1": 0.0,
        "primary_key_acc": 0.0,
        "foreign_key_acc": 0.0,
        "datatype_acc": 0.0,
        "constraint_acc": 0.0,
        "index_acc": 0.0,
        "index_f1": 0.0,
        "physical_static_score": 0.0,
    }


def zero_diagnostic_metrics() -> dict[str, float]:
    return {
        "table_high_fidelity_rate": 0.0,
        "column_high_fidelity_rate": 0.0,
        "column_coverage_adjusted_f1": 0.0,
        "column_coverage_adjusted_high_fidelity_rate": 0.0,
        "index_high_fidelity_rate": 0.0,
        "index_coverage_adjusted_f1": 0.0,
        "index_coverage_adjusted_high_fidelity_rate": 0.0,
    }


def executability_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    generated = Counter(
        str(item.get("generated_execution", {}).get("status") or "unknown")
        for item in results
    )
    reference = Counter(
        str(item.get("reference_execution", {}).get("status") or "unknown")
        for item in results
    )
    generated_passed_count = generated.get("passed", 0)
    sample_count = len(results)
    return {
        "generated_by_status": dict(sorted(generated.items())),
        "reference_by_status": dict(sorted(reference.items())),
        "generated_passed_count": generated_passed_count,
        "sample_count": sample_count,
        "generated_executability_rate": (
            generated_passed_count / sample_count if sample_count else 0.0
        ),
    }


def end_to_end_summary(
    logical_static_match: dict[str, float],
    physical_static_match: dict[str, float],
    generated_executability_rate: float,
) -> dict[str, Any]:
    return {
        "generated_executability_rate": generated_executability_rate,
        "logical_static_match": {
            name: value * generated_executability_rate
            for name, value in logical_static_match.items()
        },
        "physical_static_match": {
            name: value * generated_executability_rate
            for name, value in physical_static_match.items()
        },
    }


def reference_cache_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "hit": 0,
        "legacy_hit": 0,
        "built": 0,
        "invalid": 0,
        "failed": 0,
        "not_written": 0,
    }
    for item in results:
        execution = item.get("reference_execution") or {}
        cache_status = str(execution.get("cache_status") or "")
        if cache_status in summary:
            summary[cache_status] += 1
        if execution.get("cache_lookup_status") == "invalid" and cache_status != "invalid":
            summary["invalid"] += 1
    return summary


def generated_cache_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "hit": 0,
        "legacy_hit": 0,
        "renormalized": 0,
        "built": 0,
        "miss": 0,
        "invalid": 0,
        "failed": 0,
        "not_written": 0,
    }
    for item in results:
        execution = item.get("generated_execution") or {}
        cache_status = str(execution.get("cache_status") or "")
        if cache_status in summary:
            summary[cache_status] += 1
        if execution.get("cache_lookup_status") == "invalid" and cache_status != "invalid":
            summary["invalid"] += 1
    return summary


def logical_summary(results: list[dict[str, Any]]) -> dict[str, float]:
    macro = macro_average(results)
    names = [
        "table_acc",
        "table_f1",
        "column_acc",
        "column_f1",
        "primary_key_acc",
        "foreign_key_acc",
        "datatype_acc",
        "constraint_acc",
    ]
    return {name: macro[name] for name in names}


def physical_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"index_acc": 0.0, "index_f1": 0.0, "physical_static_score": 0.0}
    return {
        "index_acc": sum(float(item["metrics"]["index_acc"]) for item in results) / len(results),
        "index_f1": sum(float(item["metrics"]["index_f1"]) for item in results) / len(results),
        "physical_static_score": sum(
            float(item["metrics"]["physical_static_score"]) for item in results
        ) / len(results),
    }


def diagnostic_summary(results: list[dict[str, Any]]) -> dict[str, float]:
    names = list(zero_diagnostic_metrics())
    if not results:
        return zero_diagnostic_metrics()
    return {
        name: sum(float(item["diagnostic_metrics"][name]) for item in results)
        / len(results)
        for name in names
    }


def build_name_matcher(config: StaticMatchConfig) -> NameMatcher:
    return MiniLMNameMatcher(
        embedding_backend=build_embedding_backend(config),
        similarity_threshold=config.similarity_threshold,
        string_threshold=config.string_threshold,
    )


def build_embedding_backend(config: StaticMatchConfig) -> EmbeddingBackend:
    backend = config.embedding_backend.casefold()
    if backend == "fastembed":
        return FastEmbedBackend(config.embedding_model, config.embedding_cache_dir)
    if backend == "sentence-transformers":
        return SentenceTransformersBackend(config.embedding_model)
    if backend == "http":
        return HttpEmbeddingBackend(config.embedding_url)
    raise RuntimeError(f"Unsupported embedding backend: {config.embedding_backend}")


def extract_generated_indexes(
    run_payload: dict[str, Any],
    generated_schema: SchemaIR,
) -> tuple[list[dict[str, Any]], bool]:
    physical_plan = dig(run_payload, "state", "artifacts", "physical_plan", "payload", "physical_plan")
    indexes = []
    if isinstance(physical_plan, dict):
        raw_indexes = physical_plan.get("indexes")
        if raw_indexes is None:
            raw_indexes = physical_plan.get("index")
        if isinstance(raw_indexes, list):
            indexes.extend(item for item in raw_indexes if isinstance(item, dict))
    for table in generated_schema.tables:
        for index in table.indexes:
            indexes.append(
                {
                    "table": table.name,
                    "columns": index.columns,
                    "unique": index.unique,
                    "name": index.name,
                }
            )
    return dedupe_indexes(indexes), bool(indexes)


def macro_average(results: list[dict[str, Any]]) -> dict[str, float]:
    metric_names = [
        "table_acc",
        "table_f1",
        "column_acc",
        "column_f1",
        "primary_key_acc",
        "foreign_key_acc",
        "datatype_acc",
        "constraint_acc",
        "index_acc",
        "index_f1",
        "physical_static_score",
    ]
    if not results:
        return {name: 0.0 for name in metric_names}
    return {
        name: sum(float(item["metrics"][name]) for item in results) / len(results)
        for name in metric_names
    }


_SPACY_NLP: Any | None = None


def load_spacy_model() -> Any:
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "spaCy is required for token overlap matching. "
            "Run: .venv\\Scripts\\python.exe -m pip install -e \".[evaluation]\""
        ) from exc
    try:
        _SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "spaCy model en_core_web_sm is required. "
            "Run: .venv\\Scripts\\python.exe -m spacy download en_core_web_sm"
        ) from exc
    _SPACY_NLP.Defaults.stop_words.add("record")
    return _SPACY_NLP


def longest_common_substring_ratio(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    previous = [0] * (len(right) + 1)
    best = 0
    for left_index in range(1, len(left) + 1):
        current = [0] * (len(right) + 1)
        for right_index in range(1, len(right) + 1):
            if left[left_index - 1] == right[right_index - 1]:
                current[right_index] = previous[right_index - 1] + 1
                best = max(best, current[right_index])
        previous = current
    return best / min(len(left), len(right))


def split_identifier_tokens(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    text = text.replace("`", " ")
    text = text.replace('"', " ")
    text = text.replace("[", " ").replace("]", " ")
    text = text.replace(".", " ")
    text = text.replace("-", " ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    parts = re.split(r"[^A-Za-z0-9]+", text)
    return [part.casefold() for part in parts if part]


def normalize_wordnet_tokens(tokens: list[str]) -> list[str]:
    normalized = []
    for token in tokens:
        if token == "number":
            normalized.append("id")
        else:
            normalized.append(token)
    return normalized


def are_wordnet_synonyms(wordnet_module: Any, left: str, right: str) -> bool:
    synsets_left = wordnet_module.synsets(left)
    synsets_right = wordnet_module.synsets(right)
    for left_synset in synsets_left:
        for right_synset in synsets_right:
            if left_synset == right_synset:
                return True
    return False


def spacy_lemma_tokens(text: str, nlp: Any) -> list[str]:
    doc = nlp(text)
    tokens: list[str] = []
    for token in doc:
        if token.is_stop or token.is_punct:
            continue
        lemma = str(token.lemma_ or token.text).casefold().strip()
        if not lemma or lemma == "-pron-":
            lemma = str(token.text or "").casefold().strip()
        if lemma:
            tokens.append(lemma)
    return tokens


def token_lcs_overlap_ratio(left: str, right: str, nlp: Any) -> float:
    left_tokens = spacy_lemma_tokens(left, nlp)
    right_tokens = spacy_lemma_tokens(right, nlp)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    best = 0.0
    for left_token in left_tokens:
        for right_token in right_tokens:
            score = longest_common_substring_ratio(left_token, right_token)
            if score > best:
                best = score
    return best


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def f1(true_positive: int, reference_total: int, generated_total: int) -> float:
    if reference_total == 0 and generated_total == 0:
        return 1.0
    if reference_total == 0 or generated_total == 0 or true_positive == 0:
        return 0.0
    precision = true_positive / generated_total
    recall = true_positive / reference_total
    return 2 * precision * recall / (precision + recall)


def accuracy(matched: int, total: int, *, empty_value: float = 0.0) -> float:
    if total == 0:
        return empty_value
    return matched / total


def empty_sensitive_accuracy(matched: int, reference_total: int, generated_total: int) -> float:
    if reference_total == 0:
        return 1.0 if generated_total == 0 else 0.0
    return matched / reference_total


def dedupe_indexes(indexes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for index in indexes:
        table = str(index.get("table") or "")
        columns = tuple(str(column) for column in index.get("columns") or [])
        unique = bool(index.get("unique", False))
        key = (table, columns, unique)
        if not table or not columns or key in seen:
            continue
        seen.add(key)
        result.append(index)
    return result


def logical_type(raw_type: str) -> str:
    value = str(raw_type).casefold()
    if any(token in value for token in ("bool", "bit")):
        return "BOOL"
    if any(token in value for token in ("time", "date", "timestamp", "year")):
        return "DATETIME"
    if any(token in value for token in ("blob", "binary", "byte", "image", "varbinary")):
        return "BINARY"
    if any(
        token in value
        for token in (
            "int",
            "decimal",
            "numeric",
            "number",
            "real",
            "float",
            "double",
            "money",
            "serial",
        )
    ):
        return "NUMERIC"
    if any(token in value for token in ("char", "text", "uuid", "string", "json", "enum")):
        return "TEXT"
    return value.upper()


def constraint_to_dict(
    constraint: tuple[str, str, tuple[str, ...]],
    *,
    matched: bool,
) -> dict[str, Any]:
    return {
        "table": constraint[0],
        "kind": constraint[1],
        "columns": list(constraint[2]),
        "matched": matched,
    }


def repo_slug(full_name: str) -> str:
    return full_name.replace("/", "__")


def dig(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
