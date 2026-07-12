from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseType(str, Enum):
    cfe = "cfe"
    netpay = "netpay"
    general = "general"


class CaseStatus(str, Enum):
    open = "open"
    closed = "closed"


class CaseStage(str, Enum):
    intake = "intake"
    in_progress = "in_progress"
    complete = "complete"


class CasePriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    case_type: CaseType
    case_type_id: UUID | None = None
    status: CaseStatus = CaseStatus.open
    stage: CaseStage = CaseStage.intake
    priority: CasePriority = CasePriority.normal
    owner_organization_id: UUID
    primary_person_id: UUID | None = None
    next_action_summary: str | None = Field(default=None, max_length=500)
    blocked: bool = False
    blocked_reason: str | None = Field(default=None, max_length=500)
    target_date: date | None = None

    @model_validator(mode="after")
    def validate_blocked_reason(self):
        if not self.blocked and self.blocked_reason is not None:
            raise ValueError("blocked_reason requires blocked to be true")
        return self


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: str | None
    case_type: CaseType
    case_type_id: UUID | None
    status: CaseStatus
    stage: CaseStage
    priority: CasePriority
    owner_organization_id: UUID
    primary_person_id: UUID | None
    next_action_summary: str | None
    blocked: bool
    blocked_reason: str | None
    target_date: date | None
    created_at: datetime
    updated_at: datetime
