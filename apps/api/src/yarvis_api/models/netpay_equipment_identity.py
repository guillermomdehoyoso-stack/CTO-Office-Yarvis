"""Tenant-scoped Store, terminal, MID and serial identity evidence."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class NetpayEquipmentIdentity(Base):
    __tablename__ = "netpay_equipment_identities"
    __table_args__ = (
        CheckConstraint("identity_kind IN ('terminal','mid','serial')", name="ck_netpay_equipment_identity_kind"),
        UniqueConstraint("organization_id", "id", name="uq_netpay_equipment_identity_org_id"),
        UniqueConstraint(
            "organization_id", "identity_kind", "normalized_value", name="uq_netpay_equipment_identity_value"
        ),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    identity_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    original_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalization_method: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NetpayEquipmentEvidence(Base):
    __tablename__ = "netpay_equipment_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        UniqueConstraint(
            "organization_id",
            "source_hash",
            "source_sheet",
            "source_row_reference",
            "identity_id",
            name="uq_netpay_equipment_evidence_source",
        ),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    identity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_profile: Mapped[str] = mapped_column(String(64), nullable=False)
    source_batch_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sheet: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_period: Mapped[str | None] = mapped_column(String(16))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    original_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalization_method: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NetpayStoreEquipmentLink(Base):
    __tablename__ = "netpay_store_equipment_links"
    __table_args__ = (
        CheckConstraint(
            "resolution_status IN ('pending','confirmed','ambiguous','contradictory','superseded')",
            name="ck_netpay_equipment_link_status",
        ),
        CheckConstraint(
            "terminal_identity_id IS NOT NULL OR mid_identity_id IS NOT NULL OR serial_identity_id IS NOT NULL",
            name="ck_netpay_equipment_link_identity",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_netpay_equipment_link_dates"
        ),
        ForeignKeyConstraint(
            ["organization_id", "terminal_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "mid_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        ForeignKeyConstraint(
            ["organization_id", "serial_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        Index("ix_netpay_equipment_link_org_store", "organization_id", "store_reference_id"),
        Index("ix_netpay_equipment_link_org_serial", "organization_id", "serial_identity_id", "valid_from", "valid_to"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    store_reference_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT")
    )
    terminal_identity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    mid_identity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    serial_identity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_equipment_evidence.id"), nullable=False
    )
    candidate_store_reference_ids: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    predecessor_link_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_equipment_links.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NetpayEquipmentIdentityDecision(Base):
    __tablename__ = "netpay_equipment_identity_decisions"
    __table_args__ = (UniqueConstraint("link_id", "aggregate_version", name="uq_netpay_equipment_decision_version"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    link_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_equipment_links.id"), nullable=False
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prior_status: Mapped[str | None] = mapped_column(String(20))
    resulting_status: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NetpayEquipmentIdentityReceipt(Base):
    __tablename__ = "netpay_equipment_identity_receipts"
    __table_args__ = (UniqueConstraint("organization_id", "idempotency_key", name="uq_netpay_equipment_receipt_key"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result_link_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_equipment_links.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
