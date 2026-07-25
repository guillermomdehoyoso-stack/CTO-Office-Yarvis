"""Minimal authenticated access boundary for the Development Workspace."""

from __future__ import annotations

from fastapi import HTTPException, Request, status


def require_workspace_access(request: Request) -> None:
    """Deny Workspace access unless its explicitly configured token is presented."""

    expected_token = request.app.state.yarvis.settings.workspace_access_token
    supplied_token = request.headers.get("x-yarvis-workspace-token")
    if expected_token is None or supplied_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="workspace authentication required",
        )
