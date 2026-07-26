from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvidenceFile:
    path: str
    evidence_type: str
    content: str


class EvidenceCollector:
    """Collects local evidence files from a cloned or exported repository."""

    TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".py", ".rb", ".js", ".ts", ".java", ".go", ".php", ".cs", ".sql", ".yml", ".yaml", ".json"}

    def collect_from_directory(self, repo_dir: str | Path) -> list[EvidenceFile]:
        root = Path(repo_dir)
        files: list[EvidenceFile] = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in self.TEXT_EXTENSIONS:
                continue
            relative = path.relative_to(root).as_posix()
            evidence_type = self._classify_path(relative)
            if not evidence_type:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            files.append(EvidenceFile(path=relative, evidence_type=evidence_type, content=content))
        return files

    def _classify_path(self, path: str) -> str:
        lower = path.lower()
        if "readme" in lower:
            return "readme"
        if lower.startswith(("docs/", "doc/")) or "api" in lower:
            return "docs"
        if "controller" in lower or "route" in lower:
            return "route"
        if "service" in lower:
            return "service"
        if "repository" in lower or "dao" in lower or "mapper" in lower:
            return "repository"
        if "test" in lower or "fixture" in lower:
            return "test"
        if "migration" in lower or "migrate" in lower:
            return "migration"
        if "changelog" in lower or "release" in lower:
            return "changelog"
        return ""

