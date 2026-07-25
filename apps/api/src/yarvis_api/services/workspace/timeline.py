from __future__ import annotations

from typing import Protocol

from yarvis_api.services.workspace.models import RepositoryFile


class TimelineProvider(Protocol):
    def build(self, files: list[RepositoryFile], limit: int = 25) -> list[dict[str, str | int]]:
        ...


class FilesystemTimelineProvider:
    def build(self, files: list[RepositoryFile], limit: int = 25) -> list[dict[str, str | int]]:
        timeline = [
            {
                "path": file.path,
                "modified_at": file.modified_at,
                "size_bytes": file.size_bytes,
                "kind": "documentation" if file.is_documentation else "implementation",
            }
            for file in files
            if file.path.startswith(("docs/", "apps/", "README.md", "AGENTS.md"))
        ]
        timeline.sort(key=lambda item: str(item["modified_at"]), reverse=True)
        return timeline[:limit]
