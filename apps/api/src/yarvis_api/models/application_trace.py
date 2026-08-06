"""Append-only technical trace entries; not canonical business state."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base


class ApplicationTrace(Base):
    __tablename__ = "application_traces"
    __table_args__ = (
        UniqueConstraint("trace_id", "sequence", name="uq_application_traces_trace_sequence"),
        CheckConstraint("sequence > 0", name="ck_application_traces_sequence_positive"),
        CheckConstraint(
            "entry_kind IN ('started', 'succeeded', 'failed')",
            name="ck_application_traces_entry_kind",
        ),
        CheckConstraint(
            "(entry_kind = 'started' AND sequence = 1) OR "
            "(entry_kind IN ('succeeded', 'failed') AND sequence = 2)",
            name="ck_application_traces_entry_sequence_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    trace_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    interaction_contract_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    contract_version: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_module_id: Mapped[str] = mapped_column(String(128), nullable=False)
    owning_context: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    correlation_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    causation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authorization_decision: Mapped[str] = mapped_column(String(32), nullable=False)
    object_reference: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_reference: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    event_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    provenance_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evidence_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    retry_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    compensation_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
