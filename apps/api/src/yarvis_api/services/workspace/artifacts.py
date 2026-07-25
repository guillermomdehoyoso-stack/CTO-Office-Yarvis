from __future__ import annotations

from pathlib import Path
import re

from yarvis_api.services.workspace.io import safe_read_text
from yarvis_api.services.workspace.models import RepositoryArtifact, RepositoryFile, WorkspaceState


class ArtifactCatalog:
    def __init__(self, repository_root: Path):
        self._root = repository_root

    def discover(self, files: list[RepositoryFile]) -> list[RepositoryArtifact]:
        artifact_paths = {
            "docs/development/CURRENT_STATE.md",
            "docs/development/CURRENT_SPRINT.md",
            "docs/engineering/GOVERNANCE_BASELINE_V1.md",
        }
        indexed = {item.path for item in files}
        artifacts: list[RepositoryArtifact] = []
        for path in artifact_paths:
            if path in indexed:
                artifacts.append(
                    RepositoryArtifact(
                        path=path,
                        content=safe_read_text(self._root / path, max_chars=30000),
                    )
                )
        return artifacts


class ArtifactStateProjector:
    def project_workspace_state(self, artifacts: list[RepositoryArtifact]) -> WorkspaceState:
        mapped = {artifact.path: artifact.content for artifact in artifacts}
        current_state = mapped.get("docs/development/CURRENT_STATE.md", "")
        current_sprint = mapped.get("docs/development/CURRENT_SPRINT.md", "")
        baseline = mapped.get("docs/engineering/GOVERNANCE_BASELINE_V1.md", "")

        return WorkspaceState(
            current_sprint=self._extract_first_field(current_state, "Current sprint"),
            current_gate=self._extract_first_field(current_state, "Current engineering gate"),
            work_package=self._extract_bullet_value(current_sprint, "Work package"),
            governance_mode=self._extract_mode_from_baseline(baseline),
        )

    def _extract_first_field(self, content: str, field_name: str) -> str:
        pattern = re.compile(rf"\|\s*{re.escape(field_name)}\s*\|\s*([^|]+?)\s*\|", re.IGNORECASE)
        match = pattern.search(content)
        return match.group(1).strip() if match else "UNKNOWN"

    def _extract_bullet_value(self, content: str, label: str) -> str:
        pattern = re.compile(rf"^-\s*{re.escape(label)}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(content)
        return match.group(1).strip() if match else "UNKNOWN"

    def _extract_mode_from_baseline(self, content: str) -> str:
        if "Governance is now in Maintenance Mode" in content:
            return "Maintenance Mode"
        return "UNKNOWN"
