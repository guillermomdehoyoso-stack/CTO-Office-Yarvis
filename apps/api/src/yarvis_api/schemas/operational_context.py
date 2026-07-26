"""Explicit API DTOs for governed Intake operational-context association."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssociateIntakeOperationalContextCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: UUID
    project_id: UUID
    connector_mapping_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class IntakeOperationalContextAssociationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    association_id: UUID
    intake_item_id: UUID
    organization_id: UUID
    site_id: UUID
    project_id: UUID
    connector_mapping_id: UUID | None
    associated_at: datetime
    correlation_id: UUID
    causation_id: UUID | None
