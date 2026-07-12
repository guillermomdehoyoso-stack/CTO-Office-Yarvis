from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    description: str | None
    active: bool


class DocumentTypeRead(CatalogRead):
    validity_days: int | None


class ClassificationCreate(BaseModel):
    document_type_id: UUID | None = None
    evidence_type: str | None = Field(default=None, max_length=50)
    proposed_case_type_id: UUID | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)


class ClassificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    intake_item_id: UUID
    document_type_id: UUID | None
    evidence_type: str | None
    proposed_case_type_id: UUID | None
    confidence: int | None
    status: str
    confirmed_by: str | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConfirmationInput(BaseModel):
    confirmed_by: str | None = Field(default=None, max_length=255)


class FulfillmentInput(BaseModel):
    intake_item_id: UUID | None = None
    evidence_id: UUID | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_reference(self):
        if self.intake_item_id is None and self.evidence_id is None:
            raise ValueError("intake_item_id or evidence_id is required")
        return self


class NotesInput(BaseModel):
    notes: str = Field(min_length=1)

class ReviewInput(BaseModel):
    reviewed_by: str | None = None
    document_date: datetime | None = None
    valid_from: datetime | None = None
    rejection_reason: str | None = None


class FulfillmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_checklist_id: UUID
    checklist_requirement_id: UUID
    intake_item_id: UUID | None
    evidence_id: UUID | None
    status: str
    notes: str | None
    validated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    document_date: datetime | None
    valid_from: datetime | None
    valid_until: datetime | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    expiration_evaluated_at: datetime | None


class RequirementRead(BaseModel):
    id: UUID
    code: str
    name: str
    required: bool
    multiple_allowed: bool
    display_order: int
    document_type_id: UUID | None
    fulfillment_statuses: list[str]


class CaseChecklistRead(BaseModel):
    id: UUID
    case_id: UUID
    checklist_template_id: UUID
    template_version: int
    created_at: datetime
    required_total: int
    required_complete: int
    progress_percent: float
    requirements: list[RequirementRead]
