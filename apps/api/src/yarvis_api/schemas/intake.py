from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from yarvis_api.application.inbound_intake import InboundSourceType
from yarvis_api.schemas.event import DomainEventRead


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
class DeterministicInboundIntakeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_source: InboundSourceType
    external_message_id: str = Field(min_length=1, max_length=255)
    connector_delivery_id: str | None = Field(default=None, max_length=255)
    sender: str = Field(min_length=1, max_length=320)
    recipients: list[str] = Field(default_factory=list)
    subject: str = Field(min_length=1, max_length=500)
    text_body: str = Field(min_length=1)
    html_body: str | None = None
    content_type: str = Field(default="message/rfc822", min_length=1, max_length=100)
    source_timestamp: datetime
    received_timestamp: datetime
    headers: dict[str, str] = Field(default_factory=dict)
    correlation_id: UUID
    causation_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_recipients_and_body(self):
        if not self.recipients or any(not recipient.strip() for recipient in self.recipients):
            raise ValueError("recipients must contain at least one nonblank recipient")
        if self.html_body is not None and not self.html_body.strip():
            raise ValueError("html_body must be nonblank when provided")
        return self


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    intake_item_id: UUID
    external_source: str
    external_message_id: str
    connector_delivery_id: str | None
    sender: str
    recipients: list[str]
    subject: str
    text_body: str
    html_body: str | None
    source_timestamp: datetime
    received_at: datetime
    headers: dict[str, str]
    trace_metadata: dict
    created_at: datetime


class IntakeDetailRead(IntakeRead):
    source_metadata: dict
    trace_metadata: dict
    message: MessageRead | None = None
    events: list[DomainEventRead] = Field(default_factory=list)
