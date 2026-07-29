"""Read-only DTOs for a consolidated Mission Work operational workspace."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from yarvis_api.schemas.mission_work import MissionWorkEventRead, MissionWorkItemRead, MissionWorkTimeline
from yarvis_api.schemas.operational_economics import EconomicSummary


class OperationalWorkspaceProcessLink(BaseModel):
    id: UUID
    relationship_type: str
    linked_at: datetime
    unlinked_at: datetime | None


class OperationalWorkspaceProcessInstance(BaseModel):
    id: UUID
    lifecycle: str
    process_definition_id: UUID
    process_definition_name: str
    process_definition_version: int
    current_stage_id: UUID
    current_stage_key: str
    current_stage_name: str
    current_stage_type: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    last_transition: MissionWorkEventRead | None
    links: list[OperationalWorkspaceProcessLink]
    economic_summary: EconomicSummary


class OperationalWorkspaceRead(BaseModel):
    work_item: MissionWorkItemRead
    participants: list[str]
    process_instances: list[OperationalWorkspaceProcessInstance]
    timeline: MissionWorkTimeline
    economic_summary: EconomicSummary
    active_process_instance_count: int
    historical_process_instance_count: int
    last_activity_at: datetime
