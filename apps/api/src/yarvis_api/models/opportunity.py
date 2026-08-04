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


class OpportunityWorkspace(Base):
    """Minimal persistent context owned by one confirmed Opportunity."""

    __tablename__ = "opportunity_workspaces"
    __table_args__ = (
        UniqueConstraint("opportunity_id", name="uq_opportunity_workspaces_opportunity"),
        ForeignKeyConstraint(("opportunity_id", "organization_id"), ("opportunities.id", "opportunities.organization_id"), name="fk_opportunity_workspaces_opportunity_organization"),
        CheckConstraint("lifecycle_status IN ('pending','active','closed')", name="ck_opportunity_workspaces_lifecycle"),
        CheckConstraint("aggregate_version > 0", name="ck_opportunity_workspaces_aggregate_version_positive"),
        Index("ix_opportunity_workspaces_organization", "organization_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    template_id: Mapped[str | None] = mapped_column(String(64))
    opportunity_type: Mapped[str | None] = mapped_column(String(32))
    template_version: Mapped[int | None] = mapped_column(Integer)
    template_display_name: Mapped[str | None] = mapped_column(String(255))

class OpportunityDossier(Base):
    __tablename__="opportunity_dossiers"
    __table_args__=(
        UniqueConstraint("workspace_id",name="uq_opportunity_dossiers_workspace"),
        ForeignKeyConstraint(("workspace_id",),("opportunity_workspaces.id",),name="fk_opportunity_dossiers_workspace"),
        ForeignKeyConstraint(("opportunity_id","organization_id"),("opportunities.id","opportunities.organization_id"),name="fk_opportunity_dossiers_opportunity_organization"),
        CheckConstraint("lifecycle_status IN ('pending','active','closed')",name="ck_opportunity_dossiers_lifecycle"),
        CheckConstraint("aggregate_version > 0",name="ck_opportunity_dossiers_aggregate_version_positive"),
    )
    id: Mapped[UUID]=mapped_column(PG_UUID(as_uuid=True),primary_key=True,default=uuid4)
    organization_id: Mapped[UUID]=mapped_column(PG_UUID(as_uuid=True),nullable=False)
    opportunity_id: Mapped[UUID]=mapped_column(PG_UUID(as_uuid=True),nullable=False)
    workspace_id: Mapped[UUID]=mapped_column(PG_UUID(as_uuid=True),nullable=False)
    template_id: Mapped[str]=mapped_column(String(64),nullable=False)
    lifecycle_status: Mapped[str]=mapped_column(String(16),nullable=False,default="active")
    aggregate_version: Mapped[int]=mapped_column(Integer,nullable=False,default=1)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=utc_now)


class DossierTemplateVersion(Base):
    """One immutable, published business-process blueprint version."""

    __tablename__ = "dossier_template_versions"
    __table_args__ = (
        UniqueConstraint("organization_id", "stable_key", "business_version", name="uq_dossier_template_versions_business_identity"),
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_dossier_template_versions_organization"),
        CheckConstraint("status IN ('published','retired')", name="ck_dossier_template_versions_status"),
        CheckConstraint("business_version > 0", name="ck_dossier_template_versions_business_version_positive"),
        CheckConstraint("aggregate_version > 0", name="ck_dossier_template_versions_aggregate_version_positive"),
        CheckConstraint("(status = 'published' AND retired_at IS NULL) OR (status = 'retired' AND retired_at IS NOT NULL)", name="ck_dossier_template_versions_retirement_state"),
        Index("ix_dossier_template_versions_published_lookup", "organization_id", "stable_key", "business_version"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    stable_key: Mapped[str] = mapped_column(String(64), nullable=False)
    business_type: Mapped[str] = mapped_column(String(128), nullable=False)
    business_version: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
