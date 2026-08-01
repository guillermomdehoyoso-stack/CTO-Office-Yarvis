"""Canonical DI-002 Document Registry persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.clock import utc_now
from yarvis_api.models.base import Base


_SUBJECTS = "'organization','site','project','mission_work_item','operational_task','process_instance'"
_RELATIVE_STORAGE_KEY = (
    "storage_key IS NULL OR (btrim(storage_key) <> '' "
    "AND storage_key !~ '^/' "
    "AND storage_key !~ '^\\\\\\\\' "
    "AND storage_key !~ '^[A-Za-z]:[/\\\\\\\\]' "
    "AND storage_key !~ '(^|[/\\\\\\\\])\\.\\.([/\\\\\\\\]|$)')"
)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_documents_id_organization"),
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_documents_organization"),
        ForeignKeyConstraint(
            ("current_version_id", "id", "organization_id"),
            ("document_versions.id", "document_versions.document_id", "document_versions.organization_id"),
            name="fk_documents_current_version_document_organization",
        ),
        CheckConstraint(
            "classification IN ('general','contract','technical','regulatory','financial','evidence','correspondence','other')",
            name="ck_documents_classification",
        ),
        CheckConstraint("lifecycle_status IN ('active','archived')", name="ck_documents_lifecycle"),
        CheckConstraint("version > 0", name="ck_documents_version_positive"),
        Index("ix_documents_org_lifecycle_updated", "organization_id", "lifecycle_status", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="organization")
    current_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_document_versions_id_organization"),
        UniqueConstraint("id", "document_id", "organization_id", name="uq_document_versions_id_document_organization"),
        UniqueConstraint("organization_id", "document_id", "sequence", name="uq_document_versions_sequence"),
        ForeignKeyConstraint(
            ("document_id", "organization_id"),
            ("documents.id", "documents.organization_id"),
            name="fk_document_versions_document_organization",
        ),
        ForeignKeyConstraint(
            ("supersedes_version_id", "document_id", "organization_id"),
            ("document_versions.id", "document_versions.document_id", "document_versions.organization_id"),
            name="fk_document_versions_supersedes_document_organization",
        ),
        CheckConstraint("sequence > 0", name="ck_document_versions_sequence"),
        CheckConstraint("byte_size IS NULL OR byte_size >= 0", name="ck_document_versions_byte_size"),
        CheckConstraint(
            "char_length(checksum_algorithm)>0 AND char_length(checksum_value)>0",
            name="ck_document_versions_checksum",
        ),
        CheckConstraint("storage_key IS NOT NULL OR external_reference IS NOT NULL", name="ck_document_versions_reference"),
        CheckConstraint(_RELATIVE_STORAGE_KEY, name="ck_document_versions_relative_key"),
        CheckConstraint(
            "supersedes_version_id IS NULL OR supersedes_version_id <> id",
            name="ck_document_versions_not_self_superseding",
        ),
        Index("ix_document_versions_org_document_sequence", "organization_id", "document_id", "sequence"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    document_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(500))
    byte_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum_value: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(1000))
    external_reference: Mapped[str | None] = mapped_column(Text)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(1000))
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    supersedes_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class DocumentAssociation(Base):
    __tablename__ = "document_associations"
    __table_args__ = (
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_document_associations_organization"),
        ForeignKeyConstraint(
            ("document_id", "organization_id"),
            ("documents.id", "documents.organization_id"),
            name="fk_document_associations_document_organization",
        ),
        CheckConstraint("subject_type IN (" + _SUBJECTS + ")", name="ck_document_associations_subject_type"),
        CheckConstraint("unlinked_at IS NULL OR unlinked_at >= linked_at", name="ck_document_associations_history"),
        Index(
            "uq_document_associations_active",
            "organization_id",
            "document_id",
            "subject_type",
            "subject_id",
            unique=True,
            postgresql_where=text("unlinked_at IS NULL"),
        ),
        Index("ix_document_associations_subject_active", "organization_id", "subject_type", "subject_id", "unlinked_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    document_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    linked_by_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)


class DocumentCommandIdempotency(Base):
    """Tenant-scoped durable replay record for DI-002B commands."""

    __tablename__ = "document_command_idempotency"
    __table_args__ = (
        UniqueConstraint("organization_id", "contract_id", "idempotency_key", name="uq_document_command_idempotency"),
        ForeignKeyConstraint(("organization_id",), ("organizations.id",), name="fk_document_command_idempotency_organization"),
        CheckConstraint("char_length(request_fingerprint) = 64", name="ck_document_command_idempotency_fingerprint"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    contract_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    response_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
