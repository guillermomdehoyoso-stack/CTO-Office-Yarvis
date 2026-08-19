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
    responsible_principal_id: UUID | None; target_date: datetime | None; source_channel: str | None; source_reference: str | None; checklist_template_version: int | None
    created_at: datetime; updated_at: datetime
    requires_attention: bool = False
    checklist: list[dict] = Field(default_factory=list); steps: list[dict] = Field(default_factory=list); next_actions: list[dict] = Field(default_factory=list); activities: list[dict] = Field(default_factory=list); document_references: list[dict] = Field(default_factory=list)

class InboxPage(BaseModel):
    items: list[CaseRead]; offset: int; limit: int; total: int

class ChecklistUpdate(BaseModel):
    status: str = Field(pattern="^(missing|received|under_review|confirmed|rejected|not_applicable|expired)$")
    safe_evidence_reference: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=1000)
class AssignmentUpdate(BaseModel): responsible_principal_id: UUID | None = None
class NextActionUpdate(BaseModel):
    description: str | None = None; responsible_principal_id: UUID | None = None; due_date: datetime | None = None; status: str = Field(default="open", pattern="^(open|done|cancelled)$"); origin: str = Field(default="human", pattern="^(human|suggested)$")
class StateTransition(BaseModel): state: str; reason: str | None = None
class ActivityWrite(BaseModel): activity_type: str = Field(min_length=1,max_length=64); safe_summary: str = Field(min_length=1); external_reference: str | None = Field(default=None,max_length=255)

class CommercialIntakeCreate(BaseModel):
    kind: str = Field(pattern="^(initial_contact|rfq|commercial_opportunity|unclassified)$")
    channel: str = Field(pattern="^(call|email|whatsapp|referral|manual)$")
    received_at: datetime
    provisional_company_name: str | None = Field(default=None, max_length=255)
    provisional_contact_name: str | None = Field(default=None, max_length=255)
    product_interest: str = Field(pattern="^(tpv|ecommerce|other)$")
    summary: str = Field(min_length=1, max_length=4000)
    priority: str = Field(default="normal", pattern="^(urgent|high|normal|low)$")
    assignee_principal_id: UUID | None = None
    assign_to_self: bool = False
    next_action: str | None = Field(default=None, max_length=4000)
    due_date: datetime | None = None

class CommercialIntakeUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(qualifying|qualified)$")
    assignee_principal_id: UUID | None = None
    next_action: str | None = Field(default=None, max_length=4000)
    due_date: datetime | None = None
    assign_to_self: bool = False

class CommercialIntakeConvert(BaseModel):
    existing_client_id: UUID | None = None
    company_id: UUID | None = None
    branch_id: UUID | None = None
    create_master: dict | None = None
    case_type_key: str = Field(default="tpv_activation", max_length=64)
    expected_outcome: str | None = Field(default=None, max_length=4000)

class CommercialIntakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; kind: str; channel: str; received_at: datetime; provisional_company_name: str | None; provisional_contact_name: str | None; product_interest: str; summary: str; priority: str; assignee_principal_id: UUID | None; next_action: str | None; due_date: datetime | None; status: str; master_client_id: UUID | None; master_company_id: UUID | None; master_branch_id: UUID | None; converted_case_id: UUID | None; created_at: datetime; updated_at: datetime
    requires_attention: bool = False
    timeline: list[dict] = Field(default_factory=list)

class CommercialIntakePage(BaseModel):
    items: list[CommercialIntakeRead]; offset: int; limit: int; total: int
