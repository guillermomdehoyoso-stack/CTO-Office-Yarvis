"""Append-only operational evidence for Mission Work lifecycle activity."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class MissionWorkEvent(Base):
    """An immutable, tenant-owned record of an observed Mission Work action."""

    __tablename__ = "mission_work_events"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "work_item_id",
            "sequence_number",
            name="uq_mission_work_events_work_sequence",
        ),
        CheckConstraint("sequence_number > 0", name="ck_mission_work_events_sequence_positive"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), ForeignKey("mission_work_items.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
