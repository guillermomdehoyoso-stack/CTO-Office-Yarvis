"""Append-only, tenant-scoped operational economic facts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


class EconomicFact(Base):
    """One immutable assertion of an economic measure for one operational subject."""

    __tablename__ = "economic_facts"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_economic_facts_id_organization"),
        UniqueConstraint("organization_id", "idempotency_key", name="uq_economic_facts_org_idempotency"),
        ForeignKeyConstraint(
            ("supersedes_fact_id", "organization_id"),
            ("economic_facts.id", "economic_facts.organization_id"),
            name="fk_economic_facts_supersedes_organization",
        ),
        CheckConstraint(
            "fact_type IN ('revenue_expected', 'revenue_contracted', 'cost_estimated', "
            "'cost_committed', 'cost_incurred', 'labor_cost', 'cash_in', 'cash_out', "
            "'cost_to_complete')",
            name="ck_economic_facts_fact_type",
        ),
        CheckConstraint(
            "subject_type IN ('project', 'mission_work_item', 'process_instance', 'task')",
            name="ck_economic_facts_subject_type",
        ),
        CheckConstraint("amount > 0", name="ck_economic_facts_amount_positive"),
        CheckConstraint("char_length(currency) = 3", name="ck_economic_facts_currency_iso"),
        Index("ix_economic_facts_org_subject_effective", "organization_id", "subject_type", "subject_id", "effective_at"),
        Index("ix_economic_facts_org_subject_type", "organization_id", "subject_type", "subject_id", "fact_type"),
        Index("ix_economic_facts_org_supersedes", "organization_id", "supersedes_fact_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    fact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    actor_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    authority_scope: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    causation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    supersedes_fact_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
