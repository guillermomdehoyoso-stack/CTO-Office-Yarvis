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
