from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from yarvis_api.api.workspace_access import require_workspace_access
from yarvis_api.services.workspace.platform import WorkspacePlatform

router = APIRouter(
    prefix="/api/v1",
    tags=["workspace-platform"],
    dependencies=[Depends(require_workspace_access)],
)


def _workspace_platform(request: Request) -> WorkspacePlatform:
    return request.app.state.yarvis.workspace_platform


def _resolve_workspace_id(platform: WorkspacePlatform, requested_workspace_id: str | None) -> str:
    if requested_workspace_id is not None and requested_workspace_id.strip():
        return requested_workspace_id
    return platform.default_workspace_id()


@router.get("/workspaces")
def list_workspaces(request: Request) -> dict[str, object]:
    platform = _workspace_platform(request)
    workspaces = [
        {
            "workspace_id": workspace.workspace_id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
        }
        for workspace in platform.workspace_registry.list_workspaces()
    ]
    return {"count": len(workspaces), "items": workspaces}


@router.get("/workspaces/{workspace_id}")
def get_workspace(workspace_id: str, request: Request) -> dict[str, object]:
    platform = _workspace_platform(request)
    workspace = platform.workspace_registry.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace not found")

    snapshot = platform.snapshot(workspace_id)
    return {
        "workspace": snapshot["workspace"],
        "dashboard": snapshot["dashboard"],
        "state": snapshot["state"],
        "observer": snapshot["observer"],
    }


@router.get("/dashboard")
def get_dashboard(request: Request, workspace_id: str | None = Query(default=None)) -> dict[str, object]:
    platform = _workspace_platform(request)
    try:
        snapshot = platform.snapshot(_resolve_workspace_id(platform, workspace_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return snapshot["dashboard"]


@router.get("/repository")
def get_repository(request: Request, workspace_id: str | None = Query(default=None)) -> dict[str, object]:
    platform = _workspace_platform(request)
    try:
        resolved_workspace_id = _resolve_workspace_id(platform, workspace_id)
        snapshot = platform.snapshot(resolved_workspace_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "workspace_id": resolved_workspace_id,
        "health": snapshot["repository"],
        "document_reference_graph": {
            "node_count": snapshot["document_reference_graph"]["node_count"],
            "edge_count": snapshot["document_reference_graph"]["edge_count"],
        },
    }


@router.get("/timeline")
def get_timeline(request: Request, workspace_id: str | None = Query(default=None)) -> dict[str, object]:
    platform = _workspace_platform(request)
    try:
        resolved_workspace_id = _resolve_workspace_id(platform, workspace_id)
        snapshot = platform.snapshot(resolved_workspace_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "workspace_id": resolved_workspace_id,
        "current_sprint": snapshot["state"]["current_sprint"],
        "current_gate": snapshot["state"]["current_gate"],
        "events": snapshot["timeline"],
    }


@router.get("/search")
def search_repository(
    request: Request,
    q: str = Query(min_length=1, max_length=120),
    workspace_id: str | None = Query(default=None),
) -> dict[str, object]:
    platform = _workspace_platform(request)
    try:
        return platform.search(query=q, workspace_id=_resolve_workspace_id(platform, workspace_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/health")
def workspace_health(request: Request, workspace_id: str | None = Query(default=None)) -> dict[str, object]:
    platform = _workspace_platform(request)
    try:
        return platform.health_snapshot(_resolve_workspace_id(platform, workspace_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
