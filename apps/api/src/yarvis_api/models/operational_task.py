"""Tenant-owned, neutral operational commitments and direct prerequisites."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class OperationalTask(Base):
    __tablename__ = "operational_tasks"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_operational_tasks_id_organization"),
        UniqueConstraint(
            "organization_id",
            "create_idempotency_key",
            name="uq_operational_tasks_create_idempotency",
        ),
        ForeignKeyConstraint(
            ("organization_id",),
            ("organizations.id",),
            name="fk_operational_tasks_organization",
        ),
        ForeignKeyConstraint(
            ("mission_work_item_id",),
            ("mission_work_items.id",),
            name="fk_operational_tasks_work",
        ),
        ForeignKeyConstraint(
            ("process_instance_id", "organization_id"),
            ("process_instances.id", "process_instances.organization_id"),
            name="fk_operational_tasks_process_organization",
        ),
        CheckConstraint(
            "status IN ('planned', 'ready', 'in_progress', 'completed', 'cancelled')",
            name="ck_operational_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name="ck_operational_tasks_priority",
        ),
        CheckConstraint("version > 0", name="ck_operational_tasks_version_positive"),
        CheckConstraint(
            "status <> 'cancelled' OR cancellation_reason IS NOT NULL",
            name="ck_operational_tasks_cancel_reason",
        ),
        Index(
            "ix_operational_tasks_org_work_created",
            "organization_id",
            "mission_work_item_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    mission_work_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    process_instance_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    process_stage_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    assignee_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    create_idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    create_request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "predecessor_task_id",
            "successor_task_id",
            name="uq_task_dependencies_direct_edge",
        ),
        ForeignKeyConstraint(
            ("predecessor_task_id", "organization_id"),
            ("operational_tasks.id", "operational_tasks.organization_id"),
            name="fk_task_dependencies_predecessor",
        ),
        ForeignKeyConstraint(
            ("successor_task_id", "organization_id"),
            ("operational_tasks.id", "operational_tasks.organization_id"),
            name="fk_task_dependencies_successor",
        ),
        CheckConstraint("predecessor_task_id <> successor_task_id", name="ck_task_dependencies_no_self_edge"),
        Index("ix_task_dependencies_org_successor", "organization_id", "successor_task_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    predecessor_task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    successor_task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OperationalTaskEvent(Base):
    __tablename__ = "operational_task_events"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "task_id",
            "idempotency_key",
            name="uq_operational_task_events_idempotency",
        ),
        UniqueConstraint(
            "organization_id",
            "task_id",
            "sequence_number",
            name="uq_operational_task_events_sequence",
        ),
        ForeignKeyConstraint(
            ("task_id", "organization_id"),
            ("operational_tasks.id", "operational_tasks.organization_id"),
            name="fk_operational_task_events_task_organization",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
