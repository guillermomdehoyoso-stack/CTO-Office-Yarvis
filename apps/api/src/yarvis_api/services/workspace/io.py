from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


class WorkspaceRepositoryRootError(ValueError):
    """Raised when the governed Workspace corpus root is unsafe or incomplete."""


def resolve_workspace_repository_root(configured_root: Path | None, fallback_start: Path) -> Path:
    """Resolve the explicitly configured corpus root or a local-development fallback."""

    candidate = configured_root if configured_root is not None else locate_repository_root(fallback_start)
    return validate_workspace_repository_root(candidate)


def validate_workspace_repository_root(candidate: Path) -> Path:
    """Return one canonical, contained Workspace corpus root or fail explicitly."""

    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise WorkspaceRepositoryRootError("workspace repository root does not exist") from error

    if not root.is_dir():
        raise WorkspaceRepositoryRootError("workspace repository root must be a directory")
    if root == root.parent:
        raise WorkspaceRepositoryRootError("workspace repository root cannot be a filesystem root")

    required_markers = (
        (root / "AGENTS.md", False),
        (root / "docs" / "development", True),
        (root / "docs" / "engineering", True),
    )
    for marker, directory in required_markers:
        _validate_contained_marker(root, marker, directory)
    return root


def _validate_contained_marker(root: Path, marker: Path, directory: bool) -> None:
    try:
        resolved_marker = marker.resolve(strict=True)
    except OSError as error:
        raise WorkspaceRepositoryRootError(f"workspace repository root is missing required marker: {marker.name}") from error
    if not resolved_marker.is_relative_to(root):
        raise WorkspaceRepositoryRootError("workspace repository marker escapes the configured root")
    if directory and not resolved_marker.is_dir():
        raise WorkspaceRepositoryRootError(f"workspace repository marker must be a directory: {marker.name}")
    if not directory and not resolved_marker.is_file():
        raise WorkspaceRepositoryRootError(f"workspace repository marker must be a file: {marker.name}")


def to_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def locate_repository_root(start: Path) -> Path:
    candidates = (start, *start.parents)
    for candidate in candidates:
        if (candidate / "AGENTS.md").exists() and (candidate / "docs").exists():
            return candidate
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "yarvis_api").exists():
            return candidate
    return start


def safe_read_text(path: Path, max_chars: int = 5000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""
