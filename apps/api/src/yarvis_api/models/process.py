"""Tenant-owned, versioned definitions for generic operational processes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
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
