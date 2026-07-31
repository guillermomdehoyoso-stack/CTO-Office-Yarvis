"""Read-only, organization-scoped Operational Workspace overview DTOs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OperationalWorkspaceContextRead(BaseModel):
    organization_id: UUID
    organization_name: str | None
    site_id: UUID | None
    site_reference: str | None
    project_id: UUID | None
    project_reference: str | None


class OperationalWorkspaceSummaryRead(BaseModel):
    active_task_count: int
    blocked_task_count: int
    overdue_task_count: int
    unassigned_task_count: int
    active_process_count: int
    recent_activity_count: int


class OperationalWorkspaceTaskRead(BaseModel):
    id: UUID
    title: str
    status: str
    priority: str
    assignee_subject_id: str | None
    due_at: datetime | None
    version: int
    project_id: UUID | None
    site_id: UUID | None
    is_blocked: bool


class OperationalWorkspaceProcessRead(BaseModel):
    id: UUID
    process_definition_id: UUID
    process_definition_name: str
    lifecycle: str
    started_at: datetime
    updated_at: datetime
    project_id: UUID | None
    site_id: UUID | None


class OperationalWorkspaceActivityRead(BaseModel):
    id: UUID
    work_item_id: UUID
    event_type: str
    occurred_at: datetime
    actor_subject_id: str | None


class OperationalWorkspaceOverviewRead(BaseModel):
    context: OperationalWorkspaceContextRead
    summary: OperationalWorkspaceSummaryRead
    active_tasks: list[OperationalWorkspaceTaskRead]
    blocked_tasks: list[OperationalWorkspaceTaskRead]
    active_processes: list[OperationalWorkspaceProcessRead]
    recent_activity: list[OperationalWorkspaceActivityRead]
