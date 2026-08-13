"""Persistent, workspace-scoped records for the manual Netpay operational radar."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class RadarMerchant(TimestampedUUIDMixin, Base):
    __tablename__ = "radar_merchants"
    __table_args__ = (UniqueConstraint("organization_id", "store_id", name="uq_radar_merchants_organization_store"),)

    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    trade_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    store_id: Mapped[str | None] = mapped_column(String(100))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(40))
    products: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)


class RadarRequest(TimestampedUUIDMixin, Base):
    __tablename__ = "radar_requests"
    __table_args__ = (
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_radar_requests_workspace_idempotency"),
        CheckConstraint("status IN ('open', 'closed')", name="ck_radar_requests_status"),
        CheckConstraint("priority IN ('low', 'normal', 'high')", name="ck_radar_requests_priority"),
    )

    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    merchant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("radar_merchants.id"), nullable=False, index=True)
    free_text: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="normal", index=True)
    owner: Mapped[str | None] = mapped_column(String(255))
    next_action: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))


class RadarChecklistItem(Base):
    __tablename__ = "radar_checklist_items"
    __table_args__ = (UniqueConstraint("request_id", "item_code", name="uq_radar_checklist_request_code"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("radar_requests.id"), nullable=False, index=True)
    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    received_by: Mapped[str | None] = mapped_column(String(255))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RadarActivity(Base):
    __tablename__ = "radar_activities"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    merchant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("radar_merchants.id"), nullable=False, index=True)
    request_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("radar_requests.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class RadarCommandReceipt(Base):
    """Durable, organization-scoped replay receipt for future Radar commands.

    F1 intentionally stores a safe result reference rather than a command payload
    or a serialized public response.  Future handlers own response hydration.
    """

    __tablename__ = "radar_command_receipts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "command_type",
            "idempotency_key",
            name="uq_radar_command_receipts_organization_command_key",
        ),
        CheckConstraint("char_length(request_fingerprint) = 64", name="ck_radar_command_receipts_fingerprint"),
        CheckConstraint("status = 'succeeded'", name="ck_radar_command_receipts_status"),
    )

    command_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    command_type: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(20), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    causation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    result_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    result_resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    result_resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="succeeded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
