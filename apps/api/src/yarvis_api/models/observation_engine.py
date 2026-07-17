from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("source_records.id"), nullable=False, index=True)
    filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    byte_size: Mapped[int | None] = mapped_column(nullable=True)
    report_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_reference: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    detected_file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_report_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    parser_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_count: Mapped[int | None] = mapped_column(nullable=True)
    observation_count: Mapped[int | None] = mapped_column(nullable=True)
    duplicate_of_document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True, index=True)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True, index=True)
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("source_records.id"), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subject_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    field_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    observed_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    identifier_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confirmation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="observed", index=True)
    source_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_observation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("observations.id"), nullable=True, index=True)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ResolutionDecision(Base):
    __tablename__ = "resolution_decisions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    observation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("observations.id"), nullable=False, index=True)
    candidate_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    candidate_entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OperationalPolicy(Base):
    __tablename__ = "operational_policies"
    __table_args__ = (UniqueConstraint("policy_key", "version", name="uq_operational_policy_key_version"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PolicyEvaluation(Base):
    __tablename__ = "policy_evaluations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("operational_policies.id"), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    result_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AttentionItem(Base):
    __tablename__ = "attention_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    policy_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
