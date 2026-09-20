from __future__ import annotations

import json
import re
from collections import defaultdict
from itertools import combinations
from typing import Annotated, Any


def _split_attributes(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,&]", value) if item.strip()]


def _dependencies(value: dict[str, list[str]]) -> list[tuple[set[str], set[str]]]:
    return [
        (set(_split_attributes(determinant)), {str(item) for item in dependents})
        for determinant, dependents in value.items()
    ]


def _closure(base: set[str], dependencies: list[tuple[set[str], set[str]]]) -> set[str]:
    result = set(base)
    changed = True
    while changed:
        changed = False
        for determinant, dependents in dependencies:
            if determinant <= result and not dependents <= result:
                result.update(dependents)
                changed = True
    return result


def _candidate_keys(
    attributes: list[str],
    dependencies: list[tuple[set[str], set[str]]],
) -> list[list[str]]:
    all_attributes = set(attributes)
    candidates: list[list[str]] = []
    for size in range(1, len(attributes) + 1):
        for combo in combinations(attributes, size):
            candidate = set(combo)
            if any(set(existing) <= candidate for existing in candidates):
                continue
            if _closure(candidate, dependencies) == all_attributes:
                candidates.append(list(combo))
    return candidates


async def get_attribute_keys_by_arm_strong(
    dependencies_json: Annotated[
        str,
        "JSON functional dependencies: {relation: {determinant: [dependents]}}",
    ],
) -> dict[str, Any]:
    """Identify candidate keys from functional dependencies."""
    raw = json.loads(dependencies_json)
    attributes_all: dict[str, list[str]] = {}
    keys: dict[str, list[list[str]]] = {}
    for relation, relation_dependencies in raw.items():
        dependencies = _dependencies(relation_dependencies)
        attributes = sorted(
            set().union(*(left | right for left, right in dependencies))
            if dependencies
            else set()
        )
        attributes_all[str(relation)] = attributes
        keys[str(relation)] = _candidate_keys(attributes, dependencies)
    return {"attributes_all": attributes_all, "entity_primary_keys": keys}


def _stable_relation_name(
    source_name: str,
    candidate_keys: list[list[str]],
    index: int,
    used_names: set[str],
) -> str:
    key_part = "_".join(candidate_keys[0]) if candidate_keys else f"part_{index}"
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", key_part).strip("_") or f"part_{index}"
    base = f"{source_name}_{clean}"
    name = base
    suffix = 2
    while name in used_names:
        name = f"{base}_{suffix}"
        suffix += 1
    used_names.add(name)
    return name


async def confirm_to_third_normal_form(
    dependencies_json: Annotated[
        str,
        "JSON functional dependencies: {relation: {determinant: [dependents]}}",
    ],
    entity_primary_keys: Annotated[
        str,
        "JSON candidate keys: {relation: [[key attributes]]}",
    ],
    attributes_all: Annotated[
        str,
        "JSON relation attributes: {relation: [attributes]}",
    ],
) -> dict[str, Any]:
    """Apply SchemaAgent's original dependency-based 3NF decomposition."""
    dependency_maps: dict[str, dict[str, list[str]]] = json.loads(dependencies_json)
    keys_by_name: dict[str, list[list[str]]] = json.loads(entity_primary_keys)
    attributes_by_name: dict[str, list[str]] = json.loads(attributes_all)

    decompositions: dict[str, list[set[str]]] = defaultdict(list)
    for relation, dependency_map in dependency_maps.items():
        for determinant, dependents in _dependencies(dependency_map):
            part = determinant | dependents
            if part not in decompositions[relation]:
                decompositions[relation].append(part)
        for key in keys_by_name.get(relation, []):
            key_set = set(key)
            if not any(key_set <= part for part in decompositions[relation]):
                decompositions[relation].append(key_set)
        decompositions[relation] = [part for part in decompositions[relation] if len(part) > 1]

    output_attributes: dict[str, dict[str, Any]] = {}
    output_keys: dict[str, list[list[str]]] = {}
    used_names: set[str] = set()
    for relation, parts in decompositions.items():
        if len(parts) <= 1:
            fallback = sorted(parts[0]) if parts else []
            output_attributes[relation] = {
                "Attribute": list(attributes_by_name.get(relation, fallback))
            }
            output_keys[relation] = list(keys_by_name.get(relation, []))
            used_names.add(relation)
            continue

        original_dependencies = _dependencies(dependency_maps[relation])
        for index, part in enumerate(parts, start=1):
            part_dependencies = [
                (left, right & part)
                for left, right in original_dependencies
                if left <= part and right & part
            ]
            part_keys = _candidate_keys(sorted(part), part_dependencies)
            name = _stable_relation_name(relation, part_keys, index, used_names)
            output_attributes[name] = {
                "Attribute": sorted(part),
                "Foreign key": {},
            }
            output_keys[name] = part_keys

    return {
        "entity_attributes_all": output_attributes,
        "entity_keys_and_attribute_map": output_keys,
    }
