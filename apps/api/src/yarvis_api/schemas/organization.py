from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    organization_type: str = Field(default="organization", min_length=1, max_length=50)
    status: str = Field(default="active", min_length=1, max_length=50)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    display_name: str
    organization_type: str
    status: str
    created_at: datetime
    updated_at: datetime
