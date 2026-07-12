from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(str, Enum):
    document = "document"
    photo = "photo"
    message = "message"
    measurement = "measurement"
    receipt = "receipt"
    confirmation = "confirmation"
    other = "other"


class EvidenceCreate(BaseModel):
    intake_item_id: UUID | None = None
    evidence_type: EvidenceType
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    captured_at: datetime | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    intake_item_id: UUID | None
    evidence_type: EvidenceType
    title: str
    description: str | None
    captured_at: datetime | None
    created_at: datetime
