"""Minimal canonical operational-context references and Inbox association state."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base, TimestampedUUIDMixin


class Site(TimestampedUUIDMixin, Base):
    __tablename__ = "sites"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_sites_id_organization_id"),
        UniqueConstraint("organization_id", "reference", name="uq_sites_organization_id_reference"),
    )

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)


class Project(TimestampedUUIDMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_projects_id_organization_id"),
        UniqueConstraint("id", "site_id", "organization_id", name="uq_projects_id_site_id_organization_id"),
        UniqueConstraint("site_id", "reference", name="uq_projects_site_id_reference"),
        ForeignKeyConstraint(
            ("site_id", "organization_id"),
            ("sites.id", "sites.organization_id"),
            name="fk_projects_site_org",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    site_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)


class ConnectorMapping(TimestampedUUIDMixin, Base):
    __tablename__ = "connector_mappings"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_connector_mappings_id_organization_id"),
        UniqueConstraint("id", "project_id", "organization_id", name="uq_connector_mappings_id_project_id_organization_id"),
        UniqueConstraint("project_id", "connector_reference", name="uq_connector_mappings_project_id_connector_reference"),
        ForeignKeyConstraint(
            ("project_id", "organization_id"),
            ("projects.id", "projects.organization_id"),
            name="fk_connector_mappings_project_org",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    connector_reference: Mapped[str] = mapped_column(String(255), nullable=False)


class IntakeOperationalContextAssociation(Base):
    __tablename__ = "intake_operational_context_associations"
    __table_args__ = (
        UniqueConstraint("intake_item_id", name="uq_intake_operational_context_associations_intake_item_id"),
        UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_ioca_org_idempotency_key",
        ),
        ForeignKeyConstraint(
            ("intake_item_id", "organization_id"),
            ("intake_items.id", "intake_items.organization_id"),
            name="fk_ioca_intake_org",
        ),
        ForeignKeyConstraint(
            ("site_id", "organization_id"),
            ("sites.id", "sites.organization_id"),
            name="fk_ioca_site_org",
        ),
        ForeignKeyConstraint(
            ("project_id", "site_id", "organization_id"),
            ("projects.id", "projects.site_id", "projects.organization_id"),
            name="fk_ioca_project_site_org",
        ),
        ForeignKeyConstraint(
            ("connector_mapping_id", "project_id", "organization_id"),
            ("connector_mappings.id", "connector_mappings.project_id", "connector_mappings.organization_id"),
            name="fk_ioca_mapping_project_org",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    intake_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    site_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    connector_mapping_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    causation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    associated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
