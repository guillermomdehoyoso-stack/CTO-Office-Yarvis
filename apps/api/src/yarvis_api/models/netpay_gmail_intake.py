"""Tenant-scoped, read-only Gmail Intake D1 persistence."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class NetpayGmailConnection(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_gmail_connections"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider_account_id", name="uq_netpay_gmail_connections_org_account"),
        CheckConstraint(
            "state IN ("
            "'disconnected','connected','validating','ready','running',"
            "'succeeded','partially_failed','failed','revoked')",
            name="ck_netpay_gmail_connections_state",
        ),
        Index("ix_netpay_gmail_connections_org_state", "organization_id", "state"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="fake")
    credential_secret_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    label_id: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    cursor: Mapped[str | None] = mapped_column(String(255))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    mailbox_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manifest_status: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    manifest_entries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    manifest_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )


class NetpayGmailSyncRun(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_gmail_sync_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running','succeeded','partially_failed','failed')",
            name="ck_netpay_gmail_sync_runs_status",
        ),
        Index("ix_netpay_gmail_sync_runs_org_created", "organization_id", "created_at"),
        Index("ix_netpay_gmail_sync_runs_connection_created", "connection_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_gmail_connections.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cursor_before: Mapped[str | None] = mapped_column(String(255))
    cursor_after: Mapped[str | None] = mapped_column(String(255))
    captured_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deduplicated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NetpayGmailSourceItem(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_gmail_source_items"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "connection_id",
            "provider_account_id",
            "gmail_message_id",
            name="uq_netpay_gmail_source_items_identity",
        ),
        Index("ix_netpay_gmail_source_items_org_received", "organization_id", "provider_received_at"),
        Index("ix_netpay_gmail_source_items_thread", "organization_id", "gmail_thread_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_gmail_connections.id", ondelete="CASCADE"), nullable=False
    )
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gmail_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gmail_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synchronized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sender: Mapped[str | None] = mapped_column(String(255))
    recipient: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(500))
    plain_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    attachment_metadata: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    conflict_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conflict_fingerprint: Mapped[str | None] = mapped_column(String(64))


class NetpayGmailCommandReceipt(Base):
    __tablename__ = "netpay_gmail_command_receipts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "command_type",
            "idempotency_key",
            name="uq_netpay_gmail_receipts_org_command_key",
        ),
    )

    command_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    command_type: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    result_response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayGmailOAuthAttempt(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_gmail_oauth_attempts"
    __table_args__ = (
        UniqueConstraint("state_digest", name="uq_netpay_gmail_oauth_attempt_state_digest"),
        Index("ix_netpay_gmail_oauth_attempt_org_expiry", "organization_id", "expires_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    state_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    secret_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NetpayIntakeCandidate(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_intake_candidates"
    __table_args__ = (
        UniqueConstraint("organization_id", "source_item_id", name="uq_netpay_intake_candidates_org_source"),
        CheckConstraint(
            "state IN ('new','needs_review','pending_link','accepted','rejected','duplicate','linked')",
            name="ck_netpay_intake_candidates_state",
        ),
        CheckConstraint("priority IN ('urgent','high','normal','low')", name="ck_netpay_intake_candidates_priority"),
        Index("ix_netpay_intake_candidates_org_attention", "organization_id", "state", "priority"),
        Index("ix_netpay_intake_candidates_org_correlation", "organization_id", "correlation_key"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    source_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_gmail_source_items.id", ondelete="CASCADE"), nullable=False
    )
    connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_gmail_connections.id", ondelete="CASCADE"), nullable=False
    )
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="new")
    request_type: Mapped[str] = mapped_column(String(64), nullable=False, default="unclassified")
    product: Mapped[str] = mapped_column(String(32), nullable=False, default="not_applicable")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ticket_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    commerce_hints: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    terminal_serials: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    shipment_facts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    facts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    inferences: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    contradictions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    missing_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    correlation_key: Mapped[str | None] = mapped_column(String(255))
    client_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_clients.id", ondelete="RESTRICT")
    )
    company_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_companies.id", ondelete="RESTRICT")
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_branches.id", ondelete="RESTRICT")
    )
    store_reference_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT")
    )
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    suggested_responsible_principal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT")
    )
    suggested_next_action: Mapped[str | None] = mapped_column(Text)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extraction_method: Mapped[str] = mapped_column(String(32), nullable=False, default="deterministic")
    extraction_version: Mapped[str] = mapped_column(String(32), nullable=False, default="d2-rules-v1")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reviewed_by_principal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disposition_reason: Mapped[str | None] = mapped_column(String(255))
    owner_type: Mapped[str | None] = mapped_column(String(32))
    owner_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class NetpayCandidateHumanFollowUp(Base):
    __tablename__ = "netpay_candidate_human_follow_ups"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('meeting','call','agreement','pending_item','general_follow_up')",
            name="ck_netpay_candidate_follow_ups_kind",
        ),
        CheckConstraint("provenance_kind = 'operator_reported'", name="ck_netpay_candidate_follow_ups_provenance"),
        Index(
            "ix_netpay_candidate_follow_ups_org_candidate_recorded",
            "organization_id",
            "candidate_id",
            "recorded_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_intake_candidates.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="operator_reported")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)


class NetpayCandidateQualification(Base):
    __tablename__ = "netpay_candidate_qualifications"
    __table_args__ = (UniqueConstraint("candidate_id", "sequence", name="uq_netpay_candidate_qualification_sequence"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_intake_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provenance_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="operator_reported")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)


class NetpayCandidateCommercialIntakeTrace(Base):
    __tablename__ = "netpay_candidate_commercial_intake_traces"
    __table_args__ = (
        UniqueConstraint("organization_id", "candidate_id", name="uq_netpay_candidate_commercial_intake_trace"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_intake_candidates.id", ondelete="RESTRICT"), nullable=False
    )
    qualification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_candidate_qualifications.id", ondelete="RESTRICT"), nullable=False
    )
    commercial_intake_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_commercial_intake_items.id", ondelete="RESTRICT"), nullable=False
    )
    branch_drafts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)


class NetpayCandidateOnboardingDossier(Base):
    __tablename__ = "netpay_candidate_onboarding_dossiers"
    __table_args__ = (
        UniqueConstraint("organization_id", "candidate_id", name="uq_netpay_candidate_onboarding_dossier"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_intake_candidates.id", ondelete="RESTRICT"), nullable=False
    )
    commercial_intake_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_commercial_intake_items.id", ondelete="RESTRICT"), nullable=False
    )
    qualification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_candidate_qualifications.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_version: Mapped[str] = mapped_column(String(32), nullable=False)
    catalog_effective_date: Mapped[str] = mapped_column(String(10), nullable=False)
    catalog_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    catalog_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    applicant_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    products: Mapped[list] = mapped_column(JSONB, nullable=False)
    branch_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False)
    requirement_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)


class NetpayDossierEvidenceReference(Base):
    __tablename__ = "netpay_dossier_evidence_references"
    __table_args__ = (
        UniqueConstraint(
            "dossier_id", "source_item_id", "attachment_index", name="uq_netpay_dossier_evidence_metadata"
        ),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dossier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("netpay_candidate_onboarding_dossiers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_gmail_source_items.id", ondelete="RESTRICT"), nullable=False
    )
    attachment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(String(128))
    verification: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )


class NetpayDossierRequirementReview(Base):
    __tablename__ = "netpay_dossier_requirement_reviews"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending','attachment_detected','under_review','validated','observed','not_applicable')",
            name="ck_netpay_dossier_requirement_review_state",
        ),
        CheckConstraint("provenance_kind = 'operator_reported'", name="ck_netpay_dossier_review_provenance"),
        UniqueConstraint("dossier_id", "sequence", name="uq_netpay_dossier_review_sequence"),
        Index("ix_netpay_dossier_reviews_dossier_recorded", "dossier_id", "recorded_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dossier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("netpay_candidate_onboarding_dossiers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_snapshot_key: Mapped[str] = mapped_column(String(255), nullable=False)
    prior_state: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_reference_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_dossier_evidence_references.id", ondelete="RESTRICT")
    )
    review_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    comment: Mapped[str | None] = mapped_column(String(1000))
    provenance_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="operator_reported")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
