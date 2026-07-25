from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from yarvis_api.services.workspace.artifacts import ArtifactCatalog, ArtifactStateProjector
from yarvis_api.services.workspace.document_reference_graph import DocumentReferenceGraphBuilder
from yarvis_api.services.workspace.health import HealthService
from yarvis_api.services.workspace.index import RepositoryIndex
from yarvis_api.services.workspace.observer import EngineeringObserver
from yarvis_api.services.workspace.read_models import ReadModelBuilder
from yarvis_api.services.workspace.registry import WorkspaceRegistry
from yarvis_api.services.workspace.scanner import RepositoryScanner
from yarvis_api.services.workspace.timeline import FilesystemTimelineProvider, TimelineProvider


class WorkspacePlatform:
    def __init__(self, repository_root: Path, timeline_provider: TimelineProvider | None = None):
        self.repository_root = repository_root
        self.repository_scanner = RepositoryScanner(repository_root)
        self.repository_index = RepositoryIndex(repository_root)
        self.document_reference_graph_builder = DocumentReferenceGraphBuilder(repository_root)
        self.artifact_catalog = ArtifactCatalog(repository_root)
        self.artifact_state_projector = ArtifactStateProjector()
        self.read_model_builder = ReadModelBuilder()
        self.workspace_registry = WorkspaceRegistry(repository_root)
        self.timeline_provider = timeline_provider or FilesystemTimelineProvider()
        self.observer = EngineeringObserver()
        self.health_service = HealthService()

    def default_workspace_id(self) -> str:
        return self.workspace_registry.default_workspace_id()

    def snapshot(self, workspace_id: str | None = None) -> dict[str, object]:
        resolved_workspace_id = workspace_id or self.default_workspace_id()
        workspace = self.workspace_registry.get_workspace(resolved_workspace_id)
        if workspace is None:
            raise KeyError(f"workspace not found: {resolved_workspace_id}")

        files = self.repository_scanner.scan()
        artifacts = self.artifact_catalog.discover(files)
        workspace_state = self.artifact_state_projector.project_workspace_state(artifacts)
        repository_health = self.read_model_builder.build_repository_health(files)
        document_reference_graph = self.document_reference_graph_builder.build(files)
        timeline = self.timeline_provider.build(files)
        dashboard = self.read_model_builder.build_dashboard(workspace, repository_health, workspace_state, timeline)
        observer_output = self.observer.observe(repository_health, workspace_state, timeline)

        return {
            "workspace": asdict(workspace),
            "repository": repository_health,
            "document_reference_graph": document_reference_graph,
            "state": asdict(workspace_state),
            "timeline": timeline,
            "dashboard": dashboard,
            "observer": observer_output,
        }

    def search(self, query: str, workspace_id: str | None = None) -> dict[str, object]:
        resolved_workspace_id = workspace_id or self.default_workspace_id()
        workspace = self.workspace_registry.get_workspace(resolved_workspace_id)
        if workspace is None:
            raise KeyError(f"workspace not found: {resolved_workspace_id}")

        files = self.repository_scanner.scan()
        results = self.repository_index.search(files, query)
        return {
            "workspace_id": resolved_workspace_id,
            "query": query,
            "count": len(results),
            "results": results,
        }

    def health_snapshot(self, workspace_id: str | None = None) -> dict[str, object]:
        snapshot = self.snapshot(workspace_id)
        services = self.health_service.evaluate(snapshot)
        return {
            "workspace_id": snapshot["workspace"]["workspace_id"],
            "status": "ok",
            "services": services,
            "engineering_health": snapshot["observer"]["engineering_health"],
            "generated_at": snapshot["observer"]["generated_at"],
        }
