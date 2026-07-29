"""Governed API DTOs for generic operational process definitions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessDefinitionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ProcessStageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    stage_type: str = Field(min_length=1, max_length=20)
    display_order: int = Field(ge=0)
    metadata_json: dict[str, Any] | None = None


class ProcessStageUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    stage_type: str = Field(min_length=1, max_length=20)
    display_order: int = Field(ge=0)
    metadata_json: dict[str, Any] | None = None


class ProcessTransitionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_stage_id: UUID
    to_stage_id: UUID
    name: str = Field(min_length=1, max_length=255)


class ProcessTransitionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


class ProcessStageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    stage_key: str
    name: str
    description: str | None
    stage_type: str
    display_order: int
    metadata_json: dict[str, Any] | None


class ProcessTransitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    from_stage_id: UUID
    to_stage_id: UUID
    name: str


class ProcessDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    version: int
    lifecycle: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    retired_at: datetime | None
    stages: list[ProcessStageRead]
    transitions: list[ProcessTransitionRead]


class ProcessDefinitionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    version: int
    lifecycle: str
    created_at: datetime
    updated_at: datetime


class StartProcessInstanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    process_definition_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class TransitionProcessInstanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transition_id: UUID
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class CancelProcessInstanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class LinkProcessInstanceToMissionWorkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_work_item_id: UUID
    relationship_type: str = Field(default="primary", min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class UnlinkProcessInstanceFromMissionWorkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class ProcessInstanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    process_definition_id: UUID
    process_definition_version: int
    current_stage_id: UUID
    lifecycle: str
    created_by_subject_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    version: int


class ProcessInstanceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    occurred_at: datetime
    event_type: str
    actor_subject_id: str | None
    payload: dict[str, Any] = Field(validation_alias="payload_json")
    sequence_number: int


class ProcessInstanceTimeline(BaseModel):
    items: list[ProcessInstanceEventRead]


class ProcessInstanceWorkLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    mission_work_item_id: UUID
    process_instance_id: UUID
    relationship_type: str
    linked_at: datetime
    unlinked_at: datetime | None
    created_by_authority_id: str | None


class ProcessInstanceWorkLinkHistory(BaseModel):
    items: list[ProcessInstanceWorkLinkRead]


class ProcessInstancePage(BaseModel):
    items: list[ProcessInstanceRead]
    total: int
    limit: int
    offset: int
