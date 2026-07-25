from __future__ import annotations

from datetime import UTC, datetime

from yarvis_api.services.workspace.models import RepositoryFile, WorkspaceDefinition, WorkspaceState


class ReadModelBuilder:
    def build_repository_health(self, files: list[RepositoryFile]) -> dict[str, object]:
        by_extension: dict[str, int] = {}
        for file in files:
            key = file.extension or "(none)"
            by_extension[key] = by_extension.get(key, 0) + 1

        docs_files = [file for file in files if file.is_documentation]
        return {
            "total_files": len(files),
            "documentation_files": len(docs_files),
            "python_files": by_extension.get(".py", 0),
            "typescript_files": by_extension.get(".ts", 0) + by_extension.get(".tsx", 0),
            "by_extension": by_extension,
            "read_only_authority": "repository",
            "generated_at": datetime.now(tz=UTC).isoformat(),
        }

    def build_dashboard(
        self,
        workspace: WorkspaceDefinition,
        repository_health: dict[str, object],
        state: WorkspaceState,
        timeline: list[dict[str, str | int]],
    ) -> dict[str, object]:
        return {
            "workspace_id": workspace.workspace_id,
            "workspace_name": workspace.name,
            "repository_health": repository_health,
            "current_sprint": state.current_sprint,
            "current_gate": state.current_gate,
            "timeline_preview": timeline[:8],
            "updated_at": datetime.now(tz=UTC).isoformat(),
        }
