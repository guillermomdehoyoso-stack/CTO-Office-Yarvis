import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from yarvis_api.bootstrap import create_app
from yarvis_api.config import Settings
from yarvis_api.services.workspace.io import WorkspaceRepositoryRootError, resolve_workspace_repository_root


WORKSPACE_TOKEN = "workspace-test-token"


@pytest.fixture
def workspace_repository(tmp_path: Path) -> Path:
    repository_root = tmp_path / "workspace-repository"
    (repository_root / "docs" / "development").mkdir(parents=True)
    (repository_root / "docs" / "engineering").mkdir(parents=True)
    (repository_root / "apps" / "workspaces").mkdir(parents=True)
    (repository_root / "AGENTS.md").write_text("workspace fixture", encoding="utf-8")
    (repository_root / "docs" / "development" / "CURRENT_STATE.md").write_text(
        "| Current sprint | WS-000 - Development Workspace Bootstrap |\n"
        "| Current engineering gate | EOS Foundation Documentation |\n",
        encoding="utf-8",
    )
    (repository_root / "docs" / "development" / "CURRENT_SPRINT.md").write_text(
        "- Work package: WS-000 - Development Workspace Bootstrap\n",
        encoding="utf-8",
    )
    (repository_root / "docs" / "engineering" / "GOVERNANCE_BASELINE_V1.md").write_text(
        "Governance is now in Maintenance Mode\n",
        encoding="utf-8",
    )
    (repository_root / "apps" / "workspaces" / "ws000.json").write_text(
        json.dumps(
            {
                "workspace_id": "ws000",
                "name": "Development Workspace",
                "description": "fixture workspace",
                "status": "active",
                "default": True,
                "capabilities": ["dashboard"],
            }
        ),
        encoding="utf-8",
    )
    return repository_root


def build_workspace_app(repository_root: Path):
    return create_app(
        settings=Settings(
            environment="test",
            workspace_access_token_secret=SecretStr(WORKSPACE_TOKEN),
            workspace_repository_root=repository_root,
        )
    )


def workspace_headers() -> dict[str, str]:
    return {"x-yarvis-workspace-token": WORKSPACE_TOKEN}


def test_workspace_routes_reject_unauthenticated_requests(workspace_repository: Path) -> None:
    response = TestClient(build_workspace_app(workspace_repository)).get("/api/v1/workspaces")

    assert response.status_code == 401
    assert response.json() == {"detail": "workspace authentication required"}


def test_workspace_registry_exposes_ws000(workspace_repository: Path) -> None:
    response = TestClient(build_workspace_app(workspace_repository)).get(
        "/api/v1/workspaces",
        headers=workspace_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["workspace_id"] == "ws000"


def test_workspace_platform_uses_an_explicit_repository_root(workspace_repository: Path) -> None:
    nested_start = workspace_repository / "apps" / "api" / "src" / "yarvis_api"
    nested_start.mkdir(parents=True)

    resolved_root = resolve_workspace_repository_root(workspace_repository, nested_start)
    app = build_workspace_app(workspace_repository)

    assert resolved_root == workspace_repository.resolve()
    assert app.state.yarvis.workspace_platform.repository_root == workspace_repository.resolve()


def test_workspace_rejects_a_missing_configured_root(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceRepositoryRootError, match="does not exist"):
        build_workspace_app(tmp_path / "missing-workspace-repository")


def test_workspace_rejects_marker_symlink_escaping_the_configured_root(tmp_path: Path) -> None:
    repository_root = tmp_path / "workspace-repository"
    repository_root.mkdir()
    outside_agents = tmp_path / "outside-agents.md"
    outside_agents.write_text("outside", encoding="utf-8")
    (repository_root / "AGENTS.md").symlink_to(outside_agents)
    (repository_root / "docs" / "development").mkdir(parents=True)
    (repository_root / "docs" / "engineering").mkdir(parents=True)

    with pytest.raises(WorkspaceRepositoryRootError, match="escapes"):
        build_workspace_app(repository_root)


def test_workspace_platform_projects_repository_state(workspace_repository: Path) -> None:
    app = build_workspace_app(workspace_repository)

    response = TestClient(app).get("/api/v1/workspaces/ws000", headers=workspace_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace"]["workspace_id"] == "ws000"
    assert payload["state"]["current_sprint"] == "WS-000 - Development Workspace Bootstrap"
    assert payload["state"]["current_gate"] == "EOS Foundation Documentation"


def test_workspace_platform_is_isolated_per_application(workspace_repository: Path) -> None:
    first_app = build_workspace_app(workspace_repository)
    second_app = build_workspace_app(workspace_repository)

    assert first_app.state.yarvis.workspace_platform is not second_app.state.yarvis.workspace_platform
    assert first_app.state.yarvis.workspace_platform.repository_root == second_app.state.yarvis.workspace_platform.repository_root


def test_workspace_core_endpoints_are_authenticated_and_operational(workspace_repository: Path) -> None:
    client = TestClient(build_workspace_app(workspace_repository))

    dashboard = client.get("/api/v1/dashboard", headers=workspace_headers())
    repository = client.get("/api/v1/repository", headers=workspace_headers())
    timeline = client.get("/api/v1/timeline", headers=workspace_headers())
    search = client.get("/api/v1/search", params={"q": "sprint"}, headers=workspace_headers())
    health = client.get("/api/v1/health", headers=workspace_headers())

    assert dashboard.status_code == 200
    assert repository.status_code == 200
    assert timeline.status_code == 200
    assert search.status_code == 200
    assert health.status_code == 200

    assert repository.json()["health"]["read_only_authority"] == "repository"
    assert isinstance(timeline.json()["events"], list)
    assert search.json()["query"] == "sprint"
    assert health.json()["services"]["engineering_observer"] == "ok"


def test_workspace_uses_the_configured_container_corpus() -> None:
    app = create_app(settings=Settings())

    assert app.state.yarvis.workspace_platform.repository_root == Path("/workspace-repository").resolve()
    snapshot = app.state.yarvis.workspace_platform.snapshot("ws000")
    current_state = (Path("/workspace-repository") / "docs" / "development" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    expected_sprint = next(line.split("|")[2].strip() for line in current_state.splitlines() if "| Current sprint |" in line)
    assert snapshot["state"]["current_sprint"] == expected_sprint
