from __future__ import annotations

from pathlib import Path
import re

from yarvis_api.services.workspace.io import safe_read_text
from yarvis_api.services.workspace.models import RepositoryFile


class DocumentReferenceGraphBuilder:
    """Builds a document-reference graph from markdown links."""

    def __init__(self, repository_root: Path):
        self._root = repository_root

    def build(self, files: list[RepositoryFile]) -> dict[str, object]:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []

        for file in files:
            if not file.is_documentation:
                continue

            nodes.append({"id": file.path, "type": "markdown" if file.extension == ".md" else "document"})
            if file.extension != ".md":
                continue

            content = safe_read_text(self._root / file.path, max_chars=10000)
            for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", content):
                target = match.group(1).strip()
                if target.startswith("http"):
                    continue
                normalized_target = target.split("#", 1)[0].strip()
                if normalized_target.endswith(".md"):
                    edges.append({"from": file.path, "to": normalized_target, "relation": "references"})

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}
