from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from yarvis_api.services.workspace.io import to_iso
from yarvis_api.services.workspace.models import RepositoryFile

_ALLOWED_ROOT_FILES = {"AGENTS.md"}
_ALLOWED_PREFIXES = ("docs/development/", "docs/engineering/", "apps/workspaces/")
_ALLOWED_EXTENSIONS = {".json", ".md", ".txt", ".yaml", ".yml"}
_BLOCKED_FILENAMES = {".env", ".env.local", ".env.production"}
_MAX_FILE_SIZE_BYTES = 256_000


class RepositoryScanStrategy(Protocol):
    def scan(self, root: Path) -> list[RepositoryFile]:
        ...


@dataclass(slots=True)
class FullRepositoryScanStrategy:
    skip_dirs: set[str]

    def scan(self, root: Path) -> list[RepositoryFile]:
        files: list[RepositoryFile] = []
        for path in root.rglob("*"):
            if any(part in self.skip_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue

            try:
                resolved_path = path.resolve(strict=True)
                relative = path.relative_to(root).as_posix()
                if not resolved_path.is_relative_to(root):
                    continue
                stat = resolved_path.stat()
            except OSError:
                continue
            if not _is_allowed_workspace_path(relative, stat.st_size):
                continue
            files.append(
                RepositoryFile(
                    path=relative,
                    extension=path.suffix.lower(),
                    size_bytes=stat.st_size,
                    modified_at=to_iso(stat.st_mtime),
                    is_documentation=relative.startswith("docs/"),
                )
            )

        files.sort(key=lambda item: item.path)
        return files


class RepositoryScanner:
    def __init__(self, repository_root: Path, strategy: RepositoryScanStrategy | None = None):
        self._root = repository_root
        self._strategy = strategy or FullRepositoryScanStrategy(
            skip_dirs={".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        )

    def scan(self) -> list[RepositoryFile]:
        return self._strategy.scan(self._root)


def _is_allowed_workspace_path(relative_path: str, size_bytes: int) -> bool:
    if size_bytes > _MAX_FILE_SIZE_BYTES:
        return False
    path = Path(relative_path)
    if path.name.lower() in _BLOCKED_FILENAMES or path.name.lower().startswith(".env."):
        return False
    if relative_path in _ALLOWED_ROOT_FILES:
        return True
    return relative_path.startswith(_ALLOWED_PREFIXES) and path.suffix.lower() in _ALLOWED_EXTENSIONS
