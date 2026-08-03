from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    business_intent: str
    lifecycle_status: str
    aggregate_version: int
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None
    confirmed_by_subject_id: str | None


class OpportunityWorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    opportunity_id: UUID
    organization_id: UUID
    lifecycle_status: str
    aggregate_version: int
    created_at: datetime

class OpportunityTemplateRead(BaseModel):
    template_id: str
    business_type: str
    version: int
    display_name: str
