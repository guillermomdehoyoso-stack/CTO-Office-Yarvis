"""API contracts for the read-only Netpay Gmail Intake D1 slice."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GmailConnectionCreate(BaseModel):
    provider_account_id: str = Field(min_length=1, max_length=255)
    label_id: str = Field(min_length=1, max_length=255)
    query: str = Field(default="", max_length=500)
    credential_secret_ref: str = Field(min_length=1, max_length=255)


class GmailConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    provider_account_id: str
    provider_kind: str
    label_id: str
    query: str
    state: str
    cursor: str | None
    last_sync_at: datetime | None
    last_error_code: str | None
    mailbox_verified_at: datetime | None
    manifest_status: str
    manifest_entries: list[dict]
    manifest_approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GmailSyncRequest(BaseModel):
    backfill_days: int = Field(default=30, ge=1, le=30)


class GmailSyncRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    connection_id: UUID
    status: str
    window_start: datetime
    window_end: datetime
    cursor_before: str | None
    cursor_after: str | None
    captured_count: int
    deduplicated_count: int
    conflict_count: int
    failed_count: int
    failure_code: str | None
    correlation_id: UUID
    started_at: datetime
    completed_at: datetime | None


class GmailSourceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    connection_id: UUID
    provider_account_id: str
    gmail_message_id: str
    gmail_thread_id: str
    provider_received_at: datetime
    synchronized_at: datetime
    sender: str | None
    recipient: str | None
    subject: str | None
    plain_excerpt: str
    source_fingerprint: str
    attachment_metadata: list[dict]
    provenance: dict
    conflict_detected_at: datetime | None
    conflict_fingerprint: str | None
    created_at: datetime
    updated_at: datetime


class GmailSourcePage(BaseModel):
    items: list[GmailSourceItemRead]
    offset: int
    limit: int
    total: int


class GmailSyncPage(BaseModel):
    items: list[GmailSyncRead]
    offset: int
    limit: int
    total: int


class GmailOAuthStartRead(BaseModel):
    authorization_url: str
    expires_at: datetime


class GmailPilotManifestRead(BaseModel):
    connection_id: UUID
    status: str
    entries: list[dict]
    approved_at: datetime | None


class GmailCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    source_item_id: UUID
    connection_id: UUID
    received_at: datetime
    state: str
    request_type: str
    product: str
    description: str
    ticket_references: list[str]
    commerce_hints: list[dict]
    terminal_serials: list[str]
    shipment_facts: dict
    facts: list[dict]
    inferences: list[dict]
    contradictions: list[dict]
    missing_data: list[str]
    correlation_key: str | None
    client_id: UUID | None
    company_id: UUID | None
    branch_id: UUID | None
    store_reference_id: UUID | None
    priority: str
    suggested_responsible_principal_id: UUID | None
    suggested_next_action: str | None
    follow_up_at: datetime | None
    follow_up_basis: str = "derived_follow_up_threshold"
    explicit_deadline_at: datetime | None = None
    extraction_method: str
    extraction_version: str
    confidence: float
    extraction_reasons: list[str]
    reviewed_by_principal_id: UUID | None
    reviewed_at: datetime | None
    disposition_reason: str | None
    owner_type: str | None
    owner_id: UUID | None
    immutable: bool
    created_at: datetime
    updated_at: datetime
    age_days: int = 0
    overdue: bool = False
    related_candidate_ids: list[UUID] = Field(default_factory=list)


class GmailCandidatePage(BaseModel):
    items: list[GmailCandidateRead]
    offset: int
    limit: int
    total: int


class GmailCandidateReview(BaseModel):
    action: str = Field(pattern="^(edit|accept|reject|duplicate|link)$")
    request_type: str | None = Field(default=None, max_length=64)
    priority: str | None = Field(default=None, pattern="^(urgent|high|normal|low)$")
    suggested_next_action: str | None = Field(default=None, max_length=2000)
    follow_up_at: datetime | None = None
    owner_type: str | None = Field(default=None, pattern="^(case|commercial_intake)$")
    owner_id: UUID | None = None
    reason: str | None = Field(default=None, max_length=255)


class CandidateHumanFollowUpCreate(BaseModel):
    kind: str = Field(pattern="^(meeting|call|agreement|pending_item|general_follow_up)$")
    note: str = Field(min_length=1, max_length=4000)
    occurred_at: datetime | None = None


class CandidateHumanFollowUpRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    candidate_id: UUID
    kind: str
    note: str
    provenance_kind: str
    occurred_at: datetime | None
    recorded_at: datetime
    created_by_principal_id: UUID
    correlation_id: UUID


class CandidateHumanFollowUpPage(BaseModel):
    items: list[CandidateHumanFollowUpRead]
    offset: int
    limit: int
    total: int


class QualifiedValue(BaseModel):
    value: str = Field(min_length=1, max_length=255)
    verification: str = Field(pattern="^(operator_confirmed|operator_reported|unresolved)$")
    source_field: str | None = Field(default=None, max_length=128)


class QualifiedBranch(BaseModel):
    draft_key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    requested_products: list[str] = Field(min_length=1, max_length=2)
    verification: str = Field(pattern="^(operator_confirmed|operator_reported|unresolved)$")
    source_field: str | None = Field(default=None, max_length=128)


class CandidateQualificationWrite(BaseModel):
    applicant_kind: str = Field(pattern="^(persona_moral|persona_fisica|unresolved)$")
    legal_person_name: QualifiedValue | None = None
    representative_name: QualifiedValue | None = None
    brand_name: QualifiedValue | None = None
    requested_products: list[str] = Field(min_length=1, max_length=2)
    branches: list[QualifiedBranch] = Field(default_factory=list, max_length=50)
    rationale: str | None = Field(default=None, max_length=1000)


class CandidateQualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    candidate_id: UUID
    sequence: int
    payload: dict
    provenance_kind: str
    recorded_at: datetime
    created_by_principal_id: UUID


class CandidateCommercialIntakeCreate(BaseModel):
    qualification_id: UUID
    provisional_company_name: str = Field(min_length=1, max_length=255)
    provisional_contact_name: str | None = Field(default=None, max_length=255)
    product_interest: str = Field(pattern="^(tpv|ecommerce|mixed|other)$")
    summary: str = Field(min_length=1, max_length=4000)
    priority: str = Field(pattern="^(urgent|high|normal|low)$")
    next_action: str | None = Field(default=None, max_length=2000)


class CandidateDossierCreate(BaseModel):
    qualification_id: UUID
    catalog_sha256: str = Field(min_length=64, max_length=64)
    confirmed: bool


class DossierEvidenceMetadataReference(BaseModel):
    source_item_id: UUID
    attachment_index: int = Field(ge=0)
    suggestion: str | None = Field(default=None, max_length=128)


class CandidateDossierRequirementReviewWrite(BaseModel):
    requirement_snapshot_key: str = Field(min_length=1, max_length=255)
    state: str = Field(pattern="^(pending|attachment_detected|under_review|validated|observed|not_applicable)$")
    evidence: DossierEvidenceMetadataReference | None = None
    review_data: dict = Field(default_factory=dict)
    comment: str | None = Field(default=None, max_length=1000)
