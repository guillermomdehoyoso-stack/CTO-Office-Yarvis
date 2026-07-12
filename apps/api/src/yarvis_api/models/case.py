from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yarvis_api.models.base import Base, TimestampedUUIDMixin


def generate_case_number() -> str:
    return f"CAS-{uuid4().hex[:12].upper()}"


class Case(TimestampedUUIDMixin, Base):
    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True, default=generate_case_number)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="intake")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    owner_organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    primary_person_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("people.id"), nullable=True, index=True)
    next_action_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blocked_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    owner_organization = relationship("Organization", back_populates="cases")
    primary_person = relationship("Person", back_populates="primary_cases")
