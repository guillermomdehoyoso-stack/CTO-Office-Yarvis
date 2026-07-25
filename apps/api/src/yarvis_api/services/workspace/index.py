from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from yarvis_api.services.workspace.io import safe_read_text
from yarvis_api.services.workspace.models import RepositoryFile

_TEXT_EXTENSIONS = {".md", ".txt", ".py", ".ts", ".tsx", ".json", ".yml", ".yaml"}


class SearchStrategy(Protocol):
    def search(self, root: Path, files: list[RepositoryFile], query: str, limit: int) -> list[dict[str, str | int]]:
        ...


@dataclass(slots=True)
class LightweightSearchStrategy:
    def search(self, root: Path, files: list[RepositoryFile], query: str, limit: int) -> list[dict[str, str | int]]:
        term = query.strip().lower()
        if not term:
            return []

        results: list[dict[str, str | int]] = []
        for file in files:
            score = 0
            snippet = ""
            if term in file.path.lower():
                score += 7

            if file.extension in _TEXT_EXTENSIONS:
                content = safe_read_text(root / file.path)
                content_lower = content.lower()
                index = content_lower.find(term)
                if index >= 0:
                    score += 5
                    begin = max(index - 80, 0)
                    end = min(index + 120, len(content))
                    snippet = content[begin:end].replace("\n", " ").strip()

            if score > 0:
                results.append({"path": file.path, "score": score, "snippet": snippet})

        results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
        return results[:limit]


class RepositoryIndex:
    def __init__(self, repository_root: Path, strategy: SearchStrategy | None = None):
        self._root = repository_root
        self._strategy = strategy or LightweightSearchStrategy()

    def search(self, files: list[RepositoryFile], query: str, limit: int = 20) -> list[dict[str, str | int]]:
        return self._strategy.search(self._root, files, query, limit)
