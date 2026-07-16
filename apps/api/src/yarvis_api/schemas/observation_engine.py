from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ObservationConfirmationStatus(str, Enum):
    observed = "observed"
    candidate = "candidate"
    confirmed = "confirmed"
    rejected = "rejected"
    superseded = "superseded"
    conflicted = "conflicted"


class ResolutionStatus(str, Enum):
    proposed = "proposed"
    confirmed = "confirmed"
    rejected = "rejected"
    conflicted = "conflicted"


class PolicyStatus(str, Enum):
    draft = "draft"
    active = "active"
    inactive = "inactive"


class PolicyEvaluationStatus(str, Enum):
    matched = "matched"
    not_matched = "not_matched"
    insufficient_data = "insufficient_data"
    conflict = "conflict"


class SourceCreate(BaseModel):
    source_type: str = Field(min_length=1, max_length=100)
    external_source_id: str | None = Field(default=None, max_length=255)
    source_name: str = Field(min_length=1, max_length=255)
    received_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
    classification: str | None = Field(default=None, max_length=100)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    external_source_id: str | None
    source_name: str
    received_at: datetime
    metadata: dict = Field(validation_alias="metadata_json")
    classification: str | None
    created_at: datetime


class DocumentCreate(BaseModel):
    source_id: UUID
    filename: str | None = Field(default=None, max_length=500)
    media_type: str = Field(min_length=1, max_length=255)
    file_hash: str | None = Field(default=None, max_length=128)
    file_content: str | None = None
    byte_size: int | None = None
    report_date: datetime | None = None
    storage_reference: str | None = Field(default=None, max_length=1000)
    extraction_status: str = Field(default="pending", min_length=1, max_length=50)
    classification: str | None = Field(default=None, max_length=100)
    metadata: dict = Field(default_factory=dict)
    allow_reprocess: bool = False


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    filename: str | None
    media_type: str
    file_hash: str
    byte_size: int | None
    report_date: datetime | None
    storage_reference: str | None
    extraction_status: str
    classification: str | None
    metadata: dict = Field(validation_alias="metadata_json")
    created_at: datetime
    processed_at: datetime | None


class DocumentRegisterResult(BaseModel):
    created: bool
    duplicate_by: str | None = None
    document: DocumentRead


class ObservationCreate(BaseModel):
    document_id: UUID | None = None
    source_id: UUID | None = None
    domain: str = Field(min_length=1, max_length=100)
    subject_type: str | None = Field(default=None, max_length=100)
    subject_reference: str | None = Field(default=None, max_length=255)
    field_name: str = Field(min_length=1, max_length=150)
    observed_value: dict
    normalized_value: dict | None = None
    identifier_type: str | None = Field(default=None, max_length=100)
    extraction_method: str = Field(min_length=1, max_length=100)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confirmation_status: ObservationConfirmationStatus = ObservationConfirmationStatus.observed
    source_reference: str | None = Field(default=None, max_length=500)
    observed_at: datetime | None = None
    provenance: dict = Field(default_factory=dict)


class ObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID | None
    source_id: UUID | None
    domain: str
    subject_type: str | None
    subject_reference: str | None
    field_name: str
    observed_value: dict
    normalized_value: dict | None
    identifier_type: str | None
    extraction_method: str
    confidence: float
    confirmation_status: ObservationConfirmationStatus
    source_reference: str | None
    observed_at: datetime
    confirmed_by: str | None
    confirmed_at: datetime | None
    supersedes_observation_id: UUID | None
    provenance: dict
    created_at: datetime


class ObservationStatusChange(BaseModel):
    actor: str = Field(min_length=1, max_length=255)
    reason: str | None = None


class ObservationSupersede(BaseModel):
    actor: str = Field(min_length=1, max_length=255)
    replacement_observation_id: UUID
    reason: str | None = None


class ResolutionProposalCreate(BaseModel):
    candidate_entity_type: str = Field(min_length=1, max_length=100)
    candidate_entity_id: str | None = Field(default=None, max_length=255)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)


class ResolutionDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: UUID
    candidate_entity_type: str
    candidate_entity_id: str | None
    decision_status: ResolutionStatus
    confidence: float
    explanation: str
    decided_by: str | None
    decided_at: datetime | None
    created_at: datetime


class ResolutionDecisionAction(BaseModel):
    actor: str = Field(min_length=1, max_length=255)


class OperationalPolicyCreate(BaseModel):
    policy_key: str = Field(min_length=1, max_length=150)
    domain: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    status: PolicyStatus = PolicyStatus.draft
    configuration: dict
    description: str = Field(min_length=1)
    severity: str = Field(min_length=1, max_length=20)
    requires_human_approval: bool = True
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class OperationalPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_key: str
    domain: str
    version: int
    status: PolicyStatus
    configuration: dict
    description: str
    severity: str
    requires_human_approval: bool
    effective_from: datetime | None
    effective_until: datetime | None
    created_at: datetime
    updated_at: datetime


class PolicyEvaluateRequest(BaseModel):
    policy_key: str = Field(min_length=1, max_length=150)
    subject_type: str = Field(min_length=1, max_length=100)
    subject_id: str = Field(min_length=1, max_length=255)
    facts: dict = Field(default_factory=dict)
    evidence_references: list[dict] = Field(default_factory=list)


class PolicyEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_id: UUID
    subject_type: str
    subject_id: str
    result_status: PolicyEvaluationStatus
    explanation: str
    input_snapshot: dict
    evidence_references: list
    evaluated_at: datetime
    created_at: datetime


class AttentionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_type: str
    subject_id: str
    policy_key: str
    severity: str
    explanation: str
    recommended_action: str
    requires_human_approval: bool
    status: str
    created_at: datetime
