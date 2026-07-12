from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    organization_id: UUID | None = None
    person_id: UUID | None = None
    case_id: UUID | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    organization_id: UUID | None
    person_id: UUID | None
    case_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationMessageCreate(BaseModel):
    role: str = "user"
    text_content: str | None = None


class ConversationMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    text_content: str | None
    intake_item_id: UUID | None
    created_at: datetime


class ConversationDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation: ConversationRead
    messages: list[ConversationMessageRead]
