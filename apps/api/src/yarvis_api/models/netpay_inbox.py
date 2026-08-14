"""Tenant-owned Netpay service Inbox aggregate; deliberately separate from legacy cases."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class _Audit:
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    updated_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)


class NetpayCaseType(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_types"
    __table_args__ = (UniqueConstraint("organization_id", "semantic_key", name="uq_netpay_case_types_org_key"),)
    semantic_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_products: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    default_template_version: Mapped[int | None] = mapped_column(Integer)
    completion_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class NetpayChecklistTemplate(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_checklist_templates"
    __table_args__ = (UniqueConstraint("organization_id", "case_type_key", "version", name="uq_netpay_templates_org_type_version"),)
    case_type_key: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    product: Mapped[str | None] = mapped_column(String(32))
    requirements: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NetpayServiceCase(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_inbox_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "folio", name="uq_netpay_inbox_cases_org_folio"),
        ForeignKeyConstraint(["organization_id", "client_id"], ["netpay_clients.organization_id", "netpay_clients.id"], name="fk_netpay_inbox_case_client_tenant"),
        ForeignKeyConstraint(["organization_id", "company_id"], ["netpay_companies.organization_id", "netpay_companies.id"], name="fk_netpay_inbox_case_company_tenant"),
        ForeignKeyConstraint(["organization_id", "branch_id"], ["netpay_branches.organization_id", "netpay_branches.id"], name="fk_netpay_inbox_case_branch_tenant"),
        CheckConstraint("state IN ('received','triage','information_pending','ready','in_progress','submitted','blocked','completed','cancelled')", name="ck_netpay_inbox_case_state"),
        CheckConstraint("product IN ('tpv','ecommerce','mixed','not_applicable')", name="ck_netpay_inbox_case_product"),
        CheckConstraint("priority IN ('urgent','high','normal','low')", name="ck_netpay_inbox_case_priority"),
        Index("ix_netpay_inbox_cases_org_attention", "organization_id", "state", "priority"),
    )
    folio: Mapped[str] = mapped_column(String(64), nullable=False)
    client_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    branch_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    store_reference_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_store_references.id", ondelete="RESTRICT"))
    case_type_key: Mapped[str] = mapped_column(String(64), nullable=False)
    original_description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_outcome: Mapped[str | None] = mapped_column(Text)
    product: Mapped[str] = mapped_column(String(32), nullable=False, default="not_applicable")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    responsible_principal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"))
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_channel: Mapped[str | None] = mapped_column(String(64))
    source_reference: Mapped[str | None] = mapped_column(String(255))
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    checklist_template_version: Mapped[int | None] = mapped_column(Integer)


class NetpayCaseChecklistItem(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_checklist_items"
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_inbox_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="missing")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    safe_evidence_reference: Mapped[str | None] = mapped_column(String(255))


class NetpayCaseStep(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_steps"
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_inbox_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")


class NetpayCaseNextAction(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_next_actions"
    __table_args__ = (Index("uq_netpay_case_next_action_open", "case_id", unique=True, postgresql_where=text("status = 'open'")),)
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_inbox_cases.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_principal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="human")
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class NetpayCaseActivity(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_activities"
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_inbox_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    safe_summary: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    causation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class NetpayCaseDocumentReference(_Audit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_case_document_references"
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("netpay_inbox_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    document_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    external_evidence_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")


class NetpayInboxCommandReceipt(Base):
    __tablename__ = "netpay_inbox_command_receipts"
    __table_args__ = (UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_inbox_receipts_org_command_key"),)
    command_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    command_type: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    result_response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
