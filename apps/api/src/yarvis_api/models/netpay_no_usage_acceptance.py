"""IG-016A C2 minimized acceptance state; no source bytes or PII."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class NetpayNoUsageCheckpoint(Base):
    __tablename__ = "netpay_no_usage_checkpoints"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(16), nullable=False)
    preview_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayNoUsageBatch(Base):
    __tablename__ = "netpay_no_usage_batches"
    __table_args__ = (
        UniqueConstraint("organization_id", "source_set_fingerprint", name="uq_no_usage_batch_source_set"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    checkpoint_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_no_usage_checkpoints.id"), nullable=False
    )
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_set_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    preview_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    counts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayNoUsageSource(Base):
    __tablename__ = "netpay_no_usage_sources"
    __table_args__ = (UniqueConstraint("batch_id", "profile", name="uq_no_usage_source_profile"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_no_usage_batches.id"), nullable=False
    )
    profile: Mapped[str] = mapped_column(String(80), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(16), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    sheet: Mapped[str] = mapped_column(String(64), nullable=False)
    structural_signature: Mapped[str] = mapped_column(String(64), nullable=False)


class NetpayNoUsageException(Base):
    __tablename__ = "netpay_no_usage_exceptions"
    __table_args__ = (UniqueConstraint("batch_id", "classification", name="uq_no_usage_exception_class"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_no_usage_batches.id"), nullable=False
    )
    classification: Mapped[str] = mapped_column(String(48), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)


class NetpayNoUsageHistory(Base):
    __tablename__ = "netpay_no_usage_history"
    __table_args__ = (UniqueConstraint("batch_id", "aggregate_version", name="uq_no_usage_history_version"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_no_usage_batches.id"), nullable=False
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    safe_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NetpayNoUsageReceipt(Base):
    __tablename__ = "netpay_no_usage_receipts"
    __table_args__ = (UniqueConstraint("organization_id", "idempotency_key", name="uq_no_usage_receipt_key"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("netpay_no_usage_batches.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
