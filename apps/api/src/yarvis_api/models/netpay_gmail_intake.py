"""Tenant-scoped, read-only Gmail Intake D1 persistence."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
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
    credential_secret_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    label_id: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    cursor: Mapped[str | None] = mapped_column(String(255))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
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
