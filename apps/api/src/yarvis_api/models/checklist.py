from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class CaseType(TimestampedUUIDMixin, Base):
    __tablename__ = "case_types"
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DocumentType(TimestampedUUIDMixin, Base):
    __tablename__ = "document_types"
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    validity_days: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"
    __table_args__ = (UniqueConstraint("case_type_id", "version", name="uq_checklist_template_version"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("case_types.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ChecklistRequirement(Base):
    __tablename__ = "checklist_requirements"
    __table_args__ = (UniqueConstraint("checklist_template_id", "code", name="uq_checklist_requirement_code"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    checklist_template_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("checklist_templates.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    document_type_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_types.id"), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    multiple_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CaseChecklist(Base):
    __tablename__ = "case_checklists"
    __table_args__ = (UniqueConstraint("case_id", "checklist_template_id", "template_version", name="uq_case_checklist_template_version"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    checklist_template_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("checklist_templates.id"), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RequirementFulfillment(TimestampedUUIDMixin, Base):
    __tablename__ = "requirement_fulfillments"
    case_checklist_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("case_checklists.id"), nullable=False, index=True)
    checklist_requirement_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("checklist_requirements.id"), nullable=False, index=True)
    intake_item_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("intake_items.id"))
    evidence_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("evidence.id"))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    expiration_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IntakeClassification(TimestampedUUIDMixin, Base):
    __tablename__ = "intake_classifications"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("intake_items.id"), nullable=False, index=True)
    document_type_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_types.id"))
    evidence_type: Mapped[str | None] = mapped_column(String(50))
    proposed_case_type_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("case_types.id"))
    confidence: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="proposed")
    confirmed_by: Mapped[str | None] = mapped_column(String(255))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
