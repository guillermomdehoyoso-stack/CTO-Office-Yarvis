"""Transactional Mission Work source-of-truth aggregate."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class MissionWorkItem(Base):
    """Independent work aggregate with a durable reference to its Inbox origin.

    ``inbox_item_id`` deliberately is not a foreign key: Mission Inbox is a
    rebuildable projection whose rows can be deleted and replayed. Creation
    validates the tenant-scoped Inbox item and snapshots its governed identity.
    """

    __tablename__ = "mission_work_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "inbox_item_id", name="uq_mission_work_items_inbox_identity"),
        UniqueConstraint("organization_id", "source_type", "source_id", name="uq_mission_work_items_source_identity"),
        CheckConstraint("status IN ('open', 'assigned', 'in_progress', 'waiting', 'resolved', 'cancelled')", name="ck_mission_work_items_status"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="ck_mission_work_items_priority"),
        Index("ix_mission_work_items_org_status_updated", "organization_id", "status", "updated_at"),
        Index("ix_mission_work_items_org_assignee_status", "organization_id", "assignee_subject_id", "status"),
        Index("ix_mission_work_items_org_priority_updated", "organization_id", "priority", "updated_at"),
        Index("ix_mission_work_items_org_source", "organization_id", "source_type", "source_id"),
        Index("ix_mission_work_items_org_inbox", "organization_id", "inbox_item_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    inbox_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    assignee_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
