"""Governed API DTOs for Mission Work."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateMissionWorkItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inbox_item_id: UUID


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignee_subject_id: str | None = Field(default=None, min_length=1, max_length=255)


class StatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(min_length=1, max_length=50)


class PriorityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: str = Field(min_length=1, max_length=50)


class CommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comment: str = Field(min_length=1, max_length=4000)


class MissionWorkItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inbox_item_id: UUID
    source_type: str
    source_id: UUID
    title: str
    summary: str | None
    status: str
    priority: str
    assignee_subject_id: str | None
    created_by_subject_id: str
    created_at: datetime
    updated_at: datetime
    assigned_at: datetime | None
    started_at: datetime | None
    resolved_at: datetime | None
    version: int


class MissionWorkItemPage(BaseModel):
    items: list[MissionWorkItemRead]
    total: int
    limit: int
    offset: int


class MissionWorkEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    occurred_at: datetime
    event_type: str
    actor_subject_id: str | None
    payload: dict = Field(validation_alias="payload_json")
    sequence_number: int


class MissionWorkTimeline(BaseModel):
    items: list[MissionWorkEventRead]
