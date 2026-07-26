from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dbgenie.core.config import load_config
from dbgenie.core.io import read_json, write_json
from benchmark.construction.enrichment import CandidateEnricher


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_json")
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--checkpoint-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    payload = read_json(args.candidate_json)
    candidates = payload.get("candidates", [])
    checkpoint_path = Path(args.checkpoint_jsonl)
    existing = _read_checkpoint(checkpoint_path)
    processed = {item["full_name"] for item in existing if item.get("full_name")}
    remaining = [item for item in candidates if item.get("full_name") not in processed]
    if args.limit:
        remaining = remaining[: args.limit]

    config = load_config(args.config)
    enricher = CandidateEnricher(config.github, config.dataset)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    with checkpoint_path.open("a", encoding="utf-8") as checkpoint:
        for index, candidate in enumerate(remaining, start=1):
            if args.progress:
                print(
                    f"[{index}/{len(remaining)}] enrich {candidate.get('full_name')}",
                    file=sys.stderr,
                    flush=True,
                )
            result = enricher.enrich(candidate)
            item = {
                **candidate,
                "domain_enriched": result.domain,
                "ecosystem_enriched": result.ecosystem,
                "dialect_enriched": result.dialect,
                "dbms_enriched": result.dbms,
                "schema_artifact_enriched": result.schema_artifact,
                "enrichment_files": result.downloaded_files,
                "enrichment_evidence": result.evidence,
                "enrichment_errors": result.errors,
            }
            checkpoint.write(json.dumps(item, ensure_ascii=False) + "\n")
            checkpoint.flush()
            existing.append(item)

    output_payload = {
        "source_file": args.candidate_json,
        "candidate_count": len(existing),
        "remaining_count": max(0, len(candidates) - len({item['full_name'] for item in existing})),
        "candidates": existing,
    }
    write_json(args.output, output_payload)
    return 0


def _read_checkpoint(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        items.append(json.loads(line))
    deduped = {}
    for item in items:
        deduped[item["full_name"]] = item
    return list(deduped.values())


if __name__ == "__main__":
    raise SystemExit(main())

