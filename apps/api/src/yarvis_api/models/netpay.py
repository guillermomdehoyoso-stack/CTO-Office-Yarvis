from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class NetpayServiceCase(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_service_cases"

    folio: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="detected")
    source_email_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    source_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    source_sender: Mapped[str | None] = mapped_column(String(320), nullable=True)
    source_intake_item_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("intake_items.id"), nullable=True, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    investigation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    to_addresses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    cc_addresses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    reply_to_addresses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    delivered_to: Mapped[str | None] = mapped_column(String(320), nullable=True)
    x_original_to: Mapped[str | None] = mapped_column(String(320), nullable=True)
    original_recipient: Mapped[str | None] = mapped_column(String(320), nullable=True)
    recipient_addresses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    operational_recipient: Mapped[str | None] = mapped_column(String(320), nullable=True)
    recipient_resolution_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient_resolution_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    physical_destination_resolution_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    physical_destination_resolution_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    body_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments_metadata: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    operational_resolution: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class NetpayShipment(Base):
    __tablename__ = "netpay_shipments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_service_cases.id"), nullable=False, index=True)
    tracking_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    carrier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="detected")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiver_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_full: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    folio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NetpayDeviceAssignment(TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_device_assignments"

    device_serial: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    store_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="assigned")
    service_case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_service_cases.id"), nullable=True, index=True)
