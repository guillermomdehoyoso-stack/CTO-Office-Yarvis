"""Tenant-owned Netpay Client, Company, Branch, and optional Store Reference."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class _MasterAudit:
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    updated_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)


class NetpayClient(_MasterAudit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_clients"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_netpay_clients_organization_id"),
        Index("ix_netpay_clients_organization_name", "organization_id", "normalized_name"),
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(100))
    primary_contact_name: Mapped[str | None] = mapped_column(String(255))
    primary_email: Mapped[str | None] = mapped_column(String(320))
    primary_phone: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class NetpayCompany(_MasterAudit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_companies"
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "client_id"], ["netpay_clients.organization_id", "netpay_clients.id"], name="fk_netpay_companies_client_tenant", ondelete="RESTRICT"),
        UniqueConstraint("organization_id", "id", name="uq_netpay_companies_organization_id"),
        UniqueConstraint("organization_id", "tax_identifier", name="uq_netpay_companies_organization_tax"),
        Index("ix_netpay_companies_client_name", "organization_id", "client_id", "normalized_legal_name"),
    )
    client_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_identifier: Mapped[str | None] = mapped_column(String(64))
    legal_address: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class NetpayBranch(_MasterAudit, TimestampedUUIDMixin, Base):
    __tablename__ = "netpay_branches"
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "company_id"], ["netpay_companies.organization_id", "netpay_companies.id"], name="fk_netpay_branches_company_tenant", ondelete="RESTRICT"),
        UniqueConstraint("organization_id", "id", name="uq_netpay_branches_organization_id"),
        UniqueConstraint("organization_id", "company_id", "branch_match_key", name="uq_netpay_branches_company_match"),
    )
    company_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    commercial_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_commercial_name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_match_key: Mapped[str] = mapped_column(String(512), nullable=False)
    branch_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    locality: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class NetpayStoreReference(_MasterAudit, Base):
    __tablename__ = "netpay_store_references"
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "branch_id"], ["netpay_branches.organization_id", "netpay_branches.id"], name="fk_netpay_store_references_branch_tenant", ondelete="RESTRICT"),
        CheckConstraint("source_type <> ''", name="ck_netpay_store_references_source_type"),
        Index("uq_netpay_store_references_active_branch", "organization_id", "branch_id", unique=True, postgresql_where=text("active")),
        Index("uq_netpay_store_references_active_store", "organization_id", "normalized_store_id", unique=True, postgresql_where=text("active")),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_store_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by_principal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"))
    created_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    updated_by_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class NetpayMasterCommandReceipt(Base):
    __tablename__ = "netpay_master_command_receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_master_receipts_org_command_key"),
        CheckConstraint("char_length(request_fingerprint) = 64", name="ck_netpay_master_receipts_fingerprint"),
    )
    command_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    command_type: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_principal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    result_resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    result_status_code: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
