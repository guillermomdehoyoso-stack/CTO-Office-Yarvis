from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


def generate_intake_number() -> str:
    return f"INT-{uuid4().hex[:12].upper()}"


class IntakeItem(Base):
    __tablename__ = "intake_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True, default=generate_intake_number)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    person_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("people.id"), nullable=True, index=True)
    case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
