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

class OpportunityDossierRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID; organization_id: UUID; opportunity_id: UUID; workspace_id: UUID; template_id: str; lifecycle_status: str; aggregate_version: int; created_at: datetime


class DossierTemplateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    stable_key: str
    business_type: str
    business_version: int
    display_name: str
    status: str
    created_at: datetime
    published_at: datetime
    retired_at: datetime | None
    aggregate_version: int
