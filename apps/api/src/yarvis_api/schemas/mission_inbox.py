"""Governed DTOs for Mission Inbox read access."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MissionInboxItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    source_id: UUID
    intake_item_id: UUID
    site_id: UUID | None
    project_id: UUID | None
    connector_mapping_id: UUID | None
    title: str
    summary: str | None
    status: str
    priority: str
    received_at: datetime
    last_activity_at: datetime
    projected_at: datetime
    projection_version: int


class MissionInboxPage(BaseModel):
    items: list[MissionInboxItemRead]
    total: int
    limit: int
    offset: int
