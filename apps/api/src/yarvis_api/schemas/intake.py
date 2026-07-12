from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IntakeSourceType(str, Enum):
    manual_upload = "manual_upload"
    manual_text = "manual_text"
    email = "email"
    whatsapp = "whatsapp"
    photo = "photo"
    other = "other"


class IntakeCreate(BaseModel):
    source_type: IntakeSourceType
    content_type: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=255)
    text_content: str | None = None
    original_filename: str | None = Field(default=None, max_length=500)
    mime_type: str | None = Field(default=None, max_length=255)
    organization_id: UUID | None = None
    person_id: UUID | None = None
    case_id: UUID | None = None
    received_at: datetime | None = None

    @model_validator(mode="after")
    def require_content(self):
        if not self.text_content and not self.original_filename:
            raise ValueError("text_content or original_filename is required")
        return self


class IntakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    intake_number: str
    source_type: IntakeSourceType
    content_type: str
    title: str | None
    text_content: str | None
    original_filename: str | None
    mime_type: str | None
    organization_id: UUID | None
    person_id: UUID | None
    case_id: UUID | None
    received_at: datetime
    created_at: datetime
