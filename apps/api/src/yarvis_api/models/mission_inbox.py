"""Mission Inbox read-model persistence owned by projection infrastructure."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base
from yarvis_api.clock import utc_now


class MissionInboxItem(Base):
    __tablename__ = "mission_inbox_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "source_type", "source_id", name="uq_mission_inbox_items_source_identity"),
        Index("ix_mission_inbox_items_status", "status"),
        Index("ix_mission_inbox_items_priority", "priority"),
        Index("ix_mission_inbox_items_received_at", "received_at"),
        Index("ix_mission_inbox_items_last_activity_at", "last_activity_at"),
        Index("ix_mission_inbox_items_project_id", "project_id"),
        Index("ix_mission_inbox_items_site_id", "site_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    intake_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("intake_items.id"), nullable=False)
    site_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    project_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    connector_mapping_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("connector_mappings.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    projected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    source_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("domain_events.id"), nullable=True)
    projection_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ProjectionCheckpoint(Base):
    __tablename__ = "projection_checkpoints"
    __table_args__ = (UniqueConstraint("projection_name", name="uq_projection_checkpoints_projection_name"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    projection_name: Mapped[str] = mapped_column(String(100), nullable=False)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    last_event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    projection_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
