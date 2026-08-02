"""Minimal DI-003 Opportunity aggregate persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_opportunities_id_organization"),
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_opportunities_organization"),
        CheckConstraint("lifecycle_status IN ('proposed','confirmed','closed')", name="ck_opportunities_lifecycle"),
        CheckConstraint("aggregate_version > 0", name="ck_opportunities_aggregate_version_positive"),
        CheckConstraint(
            "(lifecycle_status = 'proposed' AND confirmed_at IS NULL AND confirmed_by_subject_id IS NULL) "
            "OR (lifecycle_status IN ('confirmed','closed') AND confirmed_at IS NOT NULL AND confirmed_by_subject_id IS NOT NULL)",
            name="ck_opportunities_confirmation_state",
        ),
        Index("ix_opportunities_org_lifecycle_created", "organization_id", "lifecycle_status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    business_intent: Mapped[str] = mapped_column(Text, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False, default="proposed")
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by_subject_id: Mapped[str | None] = mapped_column(String(255))


class OpportunityCommandIdempotency(Base):
    """Tenant-scoped durable replay record for DI-003 Opportunity commands."""

    __tablename__ = "opportunity_command_idempotency"
    __table_args__ = (
        UniqueConstraint("organization_id", "contract_id", "idempotency_key", name="uq_opportunity_command_idempotency"),
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_opportunity_command_idempotency_organization"),
        CheckConstraint("char_length(request_fingerprint) = 64", name="ck_opportunity_command_idempotency_fingerprint"),
        Index("ix_opportunity_command_idempotency_aggregate", "organization_id", "aggregate_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    contract_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    response_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="opportunity")
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
