from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryFile:
    path: str
    extension: str
    size_bytes: int
    modified_at: str
    is_documentation: bool


@dataclass(frozen=True)
class WorkspaceDefinition:
    workspace_id: str
    name: str
    description: str
    status: str
    capabilities: list[str]
    is_default: bool = False


@dataclass(frozen=True)
class WorkspaceState:
    current_sprint: str
    current_gate: str
    work_package: str
    governance_mode: str


@dataclass(frozen=True)
class RepositoryArtifact:
    path: str
    content: str
