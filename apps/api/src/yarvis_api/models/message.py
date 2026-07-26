from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("intake_items.id"), nullable=False, index=True)
    external_source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    connector_delivery_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    sender: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    recipients: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    trace_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
