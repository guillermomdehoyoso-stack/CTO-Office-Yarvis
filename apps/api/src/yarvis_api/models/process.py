"""Tenant-owned, versioned definitions for generic operational processes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class ProcessDefinition(Base):
    __tablename__ = "process_definitions"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_process_definitions_id_organization_id"),
        UniqueConstraint("organization_id", "name", "version", name="uq_process_definitions_organization_name_version"),
        CheckConstraint("lifecycle IN ('draft', 'published', 'retired')", name="ck_process_definitions_lifecycle"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessStage(Base):
    __tablename__ = "process_stages"
    __table_args__ = (
        UniqueConstraint("id", "process_definition_id", "organization_id", name="uq_process_stages_id_definition_organization"),
        UniqueConstraint("process_definition_id", "stage_key", name="uq_process_stages_definition_key"),
        UniqueConstraint("process_definition_id", "display_order", name="uq_process_stages_definition_display_order"),
        ForeignKeyConstraint(
            ("process_definition_id", "organization_id"),
            ("process_definitions.id", "process_definitions.organization_id"),
            name="fk_process_stages_definition_organization",
        ),
        CheckConstraint("stage_type IN ('start', 'work', 'wait', 'decision', 'terminal')", name="ck_process_stages_type"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    process_definition_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    stage_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_type: Mapped[str] = mapped_column(String(20), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class ProcessTransition(Base):
    __tablename__ = "process_transitions"
    __table_args__ = (
        UniqueConstraint("id", "process_definition_id", "organization_id", name="uq_process_transitions_id_definition_organization"),
        UniqueConstraint("process_definition_id", "from_stage_id", "to_stage_id", name="uq_process_transitions_definition_edge"),
        ForeignKeyConstraint(
            ("process_definition_id", "organization_id"),
            ("process_definitions.id", "process_definitions.organization_id"),
            name="fk_process_transitions_definition_organization",
        ),
        ForeignKeyConstraint(
            ("from_stage_id", "process_definition_id", "organization_id"),
            ("process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"),
            name="fk_process_transitions_from_stage",
        ),
        ForeignKeyConstraint(
            ("to_stage_id", "process_definition_id", "organization_id"),
            ("process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"),
            name="fk_process_transitions_to_stage",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    process_definition_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    from_stage_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    to_stage_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class ProcessInstance(Base):
    """Tenant-owned runtime state for one immutable Process Definition version."""

    __tablename__ = "process_instances"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_process_instances_id_organization"),
        UniqueConstraint("organization_id", "start_idempotency_key", name="uq_process_instances_start_idempotency"),
        ForeignKeyConstraint(
            ("process_definition_id", "organization_id"),
            ("process_definitions.id", "process_definitions.organization_id"),
            name="fk_process_instances_definition_organization",
        ),
        ForeignKeyConstraint(
            ("current_stage_id", "process_definition_id", "organization_id"),
            ("process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"),
            name="fk_process_instances_current_stage",
        ),
        CheckConstraint("lifecycle IN ('active', 'completed', 'cancelled')", name="ck_process_instances_lifecycle"),
        CheckConstraint("version > 0", name="ck_process_instances_version_positive"),
        CheckConstraint("lifecycle <> 'cancelled' OR cancellation_reason IS NOT NULL", name="ck_process_instances_cancel_reason"),
        Index("ix_process_instances_org_lifecycle_updated", "organization_id", "lifecycle", "updated_at"),
        Index("ix_process_instances_org_definition", "organization_id", "process_definition_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    process_definition_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    process_definition_version: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stage_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_by_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    start_request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)


class ProcessInstanceEvent(Base):
    """Append-only, ordered evidence for Process Instance lifecycle operations."""

    __tablename__ = "process_instance_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "process_instance_id", "sequence_number", name="uq_process_instance_events_sequence"),
        UniqueConstraint("organization_id", "process_instance_id", "idempotency_key", name="uq_process_instance_events_idempotency"),
        ForeignKeyConstraint(
            ("process_instance_id", "organization_id"),
            ("process_instances.id", "process_instances.organization_id"),
            name="fk_process_instance_events_instance_organization",
        ),
        CheckConstraint("sequence_number > 0", name="ck_process_instance_events_sequence_positive"),
        Index("ix_process_instance_events_org_instance_sequence", "organization_id", "process_instance_id", "sequence_number"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    process_instance_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
