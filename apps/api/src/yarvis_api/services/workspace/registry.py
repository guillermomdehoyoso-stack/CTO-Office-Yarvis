from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from yarvis_api.services.workspace.models import WorkspaceDefinition


@dataclass(frozen=True)
class WorkspaceManifest:
    workspace_id: str
    name: str
    description: str
    status: str
    capabilities: list[str]
    is_default: bool = False


class WorkspaceRegistry:
    def __init__(self, repository_root: Path):
        self._root = repository_root

    def list_workspaces(self) -> list[WorkspaceDefinition]:
        manifests = self._load_manifests()
        return [
            WorkspaceDefinition(
                workspace_id=item.workspace_id,
                name=item.name,
                description=item.description,
                status=item.status,
                capabilities=item.capabilities,
                is_default=item.is_default,
            )
            for item in manifests
        ]

    def get_workspace(self, workspace_id: str) -> WorkspaceDefinition | None:
        for workspace in self.list_workspaces():
            if workspace.workspace_id == workspace_id:
                return workspace
        return None

    def default_workspace_id(self) -> str:
        workspaces = self.list_workspaces()
        for workspace in workspaces:
            if workspace.is_default:
                return workspace.workspace_id
        if workspaces:
            return workspaces[0].workspace_id
        raise ValueError("no workspace manifests found")

    def _load_manifests(self) -> list[WorkspaceManifest]:
        manifests: list[WorkspaceManifest] = []
        manifest_dirs = [
            self._root / "apps" / "workspaces",
            self._root / "workspaces",
            self._root.parent / "apps" / "workspaces",
        ]

        loaded_paths: set[Path] = set()
        for manifest_dir in manifest_dirs:
            if not manifest_dir.exists():
                continue
            for path in sorted(manifest_dir.glob("*.json")):
                if path in loaded_paths:
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                manifests.append(
                    WorkspaceManifest(
                        workspace_id=str(data["workspace_id"]),
                        name=str(data["name"]),
                        description=str(data["description"]),
                        status=str(data.get("status", "active")),
                        capabilities=[str(item) for item in data.get("capabilities", [])],
                        is_default=bool(data.get("default", False)),
                    )
                )
                loaded_paths.add(path)

        return manifests
