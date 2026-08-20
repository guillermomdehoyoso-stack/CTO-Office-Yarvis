"""Tenant-owned D1 operational dataset aggregates; never stores source binaries."""

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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class OperationalDataBatch(Base):
    __tablename__ = "netpay_operational_data_batches"
    __table_args__ = (
        UniqueConstraint("organization_id", "dataset_type", "source_hash", name="uq_netpay_data_batch_hash"),
        CheckConstraint(
            "dataset_type IN ('monthly_store_profitability','no_usage_campaign')", name="ck_netpay_data_batch_dataset"
        ),
        CheckConstraint(
            "status IN ('uploaded','validating','needs_review','accepted','rejected')",
            name="ck_netpay_data_batch_status",
        ),
        Index("ix_netpay_data_batches_org_type_period", "organization_id", "dataset_type", "reporting_period"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    dataset_type: Mapped[str] = mapped_column(String(48), nullable=False)
    reporting_period: Mapped[str | None] = mapped_column(String(16))
    selected_sheet: Mapped[str] = mapped_column(String(255), nullable=False)
    sanitized_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    preview_token: Mapped[str] = mapped_column(String(64), nullable=False)
    store_state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    row_counts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source_discarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    uploaded_by_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class OperationalDataRow(Base):
    __tablename__ = "netpay_operational_data_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_row_number", name="uq_netpay_data_row_source"),
        CheckConstraint(
            "validation_status IN ('valid','invalid','needs_review')", name="ck_netpay_data_row_validation"
        ),
        CheckConstraint("match_status IN ('matched','unmatched','ambiguous')", name="ck_netpay_data_row_match"),
        Index("ix_netpay_data_rows_batch_match", "batch_id", "match_status"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_operational_data_batches.id", ondelete="RESTRICT"), nullable=False
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    controlled_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    validation_status: Mapped[str] = mapped_column(String(16), nullable=False)
    match_status: Mapped[str] = mapped_column(String(16), nullable=False)
    store_reference_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT")
    )
    error_codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    row_key: Mapped[str] = mapped_column(String(64), nullable=False)
    row_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    projected_action: Mapped[str] = mapped_column(String(16), nullable=False)
    resolved_by_principal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class StoreProfitabilityFact(Base):
    __tablename__ = "netpay_store_profitability_facts"
    __table_args__ = (
        UniqueConstraint("batch_id", "store_reference_id", name="uq_netpay_profitability_batch_store"),
        Index("ix_netpay_profitability_org_store_period", "organization_id", "store_reference_id", "reporting_period"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_operational_data_batches.id", ondelete="RESTRICT"), nullable=False
    )
    store_reference_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT"), nullable=False
    )
    client_external_reference: Mapped[str | None] = mapped_column(String(100))
    reporting_period: Mapped[str] = mapped_column(String(16), nullable=False)
    product_uen: Mapped[str | None] = mapped_column(String(128))
    volume: Mapped[float | None] = mapped_column(Float)
    transaction_count: Mapped[int | None] = mapped_column(Integer)
    income: Mapped[float | None] = mapped_column(Float)
    cost: Mapped[float | None] = mapped_column(Float)
    commissions: Mapped[float | None] = mapped_column(Float)
    profitability: Mapped[float | None] = mapped_column(Float)
    no_use_indicator: Mapped[bool | None] = mapped_column(Boolean)
    row_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NoUsageCampaignEntry(Base):
    __tablename__ = "netpay_no_usage_campaign_entries"
    __table_args__ = (
        UniqueConstraint("batch_id", "store_reference_id", name="uq_netpay_no_usage_batch_store"),
        Index("ix_netpay_no_usage_org_store_period", "organization_id", "store_reference_id", "campaign_period"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_operational_data_batches.id", ondelete="RESTRICT"), nullable=False
    )
    store_reference_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_period: Mapped[str] = mapped_column(String(16), nullable=False)
    months_without_usage: Mapped[int | None] = mapped_column(Integer)
    merchant_status: Mapped[str | None] = mapped_column(String(64))
    alert_code: Mapped[str | None] = mapped_column(String(64))
    outcome_code: Mapped[str | None] = mapped_column(String(64))
    follow_up_code: Mapped[str | None] = mapped_column(String(64))
    row_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OperationalDataCommandReceipt(Base):
    __tablename__ = "netpay_operational_data_command_receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_data_receipt_key"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    result_batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_operational_data_batches.id", ondelete="RESTRICT"), nullable=False
    )
    result_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    result_response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
