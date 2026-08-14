from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class CaseCreate(BaseModel):
    client_id: UUID
    company_id: UUID
    branch_id: UUID | None = None
    store_reference_id: UUID | None = None
    case_type_key: str = Field(min_length=1, max_length=64)
    original_description: str = Field(min_length=1)
    expected_outcome: str | None = None
    product: str = Field(default="not_applicable", pattern="^(tpv|ecommerce|mixed|not_applicable)$")
    priority: str = Field(default="normal", pattern="^(urgent|high|normal|low)$")
    source_channel: str | None = Field(default=None, max_length=64)
    source_reference: str | None = Field(default=None, max_length=255)
    provenance: dict = Field(default_factory=dict)

class CaseClassify(BaseModel):
    case_type_key: str = Field(min_length=1, max_length=64)
    product: str = Field(pattern="^(tpv|ecommerce|mixed|not_applicable)$")
    expected_outcome: str | None = None
    priority: str = Field(pattern="^(urgent|high|normal|low)$")
    branch_id: UUID | None = None
    store_reference_id: UUID | None = None

class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; folio: str; client_id: UUID; company_id: UUID; branch_id: UUID | None; store_reference_id: UUID | None
    case_type_key: str; original_description: str; expected_outcome: str | None; product: str; state: str; priority: str
    responsible_principal_id: UUID | None; source_channel: str | None; source_reference: str | None; checklist_template_version: int | None
    created_at: datetime; updated_at: datetime
    requires_attention: bool = False
    checklist: list[dict] = Field(default_factory=list); steps: list[dict] = Field(default_factory=list); next_actions: list[dict] = Field(default_factory=list); activities: list[dict] = Field(default_factory=list); document_references: list[dict] = Field(default_factory=list)

class InboxPage(BaseModel):
    items: list[CaseRead]; offset: int; limit: int; total: int
