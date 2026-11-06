"""IG-016A C3 minimized protection cases; contact values are never persisted."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class NetpayProtectionCase(Base):
    __tablename__ = "netpay_protection_cases"
    __table_args__ = (
        Index(
            "uq_netpay_protection_active_source_cause",
            "organization_id",
            "source_kind",
            "source_id",
            "cause_code",
            unique=True,
            postgresql_where=text("terminal_at IS NULL"),
        ),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    store_reference_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id")
    )
    cause_code: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    assigned_principal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    next_action_code: Mapped[str | None] = mapped_column(String(48))
    commitment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contact_available: Mapped[bool] = mapped_column(nullable=False, default=False)
    terminal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersedes_case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id")
    )
    closure_kind: Mapped[str | None] = mapped_column(String(48))
    closure_evidence_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    closure_snapshot_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionCaseHistory(Base):
    __tablename__ = "netpay_protection_case_history"
    __table_args__ = (UniqueConstraint("case_id", "aggregate_version", name="uq_netpay_protection_history_version"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"), nullable=False
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prior_status: Mapped[str | None] = mapped_column(String(32))
    resulting_status: Mapped[str] = mapped_column(String(32), nullable=False)
    action_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(48), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(64))
    evidence_reference: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionCommandReceipt(Base):
    __tablename__ = "netpay_protection_command_receipts"
    __table_args__ = (UniqueConstraint("organization_id", "idempotency_key", name="uq_netpay_protection_receipt_key"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    command_id: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"))
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionSensitiveAccess(Base):
    __tablename__ = "netpay_protection_sensitive_access"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"), nullable=False
    )
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(48), nullable=False)
    master_version: Mapped[str] = mapped_column(String(64), nullable=False)
    opaque_reference: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionOutcomeEvidence(Base):
    __tablename__ = "netpay_protection_outcome_evidence"
    __table_args__ = (UniqueConstraint("supersedes_evidence_id", name="uq_netpay_outcome_evidence_successor"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"), nullable=False
    )
    evidence_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_authority: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    identity_scope: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_key: Mapped[str | None] = mapped_column(String(16))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    currency: Mapped[str | None] = mapped_column(String(3))
    supersedes_evidence_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_outcome_evidence.id")
    )
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionOutcomeAssessment(Base):
    __tablename__ = "netpay_protection_outcome_assessments"
    __table_args__ = (UniqueConstraint("supersedes_assessment_id", name="uq_netpay_outcome_assessment_successor"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"), nullable=False
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_outcome_evidence.id"), nullable=False
    )
    assessment_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    certainty: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(48), nullable=False)
    supersedes_assessment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_outcome_assessments.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionFinancialSnapshot(Base):
    __tablename__ = "netpay_protection_financial_snapshots"
    __table_args__ = (UniqueConstraint("supersedes_snapshot_id", name="uq_netpay_financial_snapshot_successor"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"), nullable=False
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_outcome_evidence.id"), nullable=False
    )
    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_outcome_assessments.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    certainty: Mapped[str] = mapped_column(String(16), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    period_key: Mapped[str | None] = mapped_column(String(16))
    components: Mapped[list] = mapped_column(JSONB, nullable=False)
    supersedes_snapshot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_protection_financial_snapshots.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayProtectionOutcomeReceipt(Base):
    __tablename__ = "netpay_protection_outcome_receipts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "idempotency_key", "request_fingerprint", name="uq_netpay_outcome_receipt_attempt"
        ),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    command_id: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_protection_cases.id"))
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
