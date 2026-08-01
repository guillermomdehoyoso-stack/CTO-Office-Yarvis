"""DI-002A Document Registry persistence baseline.

Revision ID: 20260731_21
Revises: 20260730_20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260731_21"
down_revision = "20260730_20"
branch_labels = None
depends_on = None

_RELATIVE_STORAGE_KEY = (
    "storage_key IS NULL OR (btrim(storage_key) <> '' "
    "AND storage_key !~ '^/' "
    "AND storage_key !~ '^\\\\\\\\' "
    "AND storage_key !~ '^[A-Za-z]:[/\\\\\\\\]' "
    "AND storage_key !~ '(^|[/\\\\\\\\])\\.\\.([/\\\\\\\\]|$)')"
)


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("lifecycle_status", sa.String(16), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_subject_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_documents_id_organization"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_documents_organization"),
        sa.CheckConstraint("classification IN ('general','contract','technical','regulatory','financial','evidence','correspondence','other')", name="ck_documents_classification"),
        sa.CheckConstraint("lifecycle_status IN ('active','archived')", name="ck_documents_lifecycle"),
        sa.CheckConstraint("version > 0", name="ck_documents_version_positive"),
    )
    op.create_index("ix_documents_org_lifecycle_updated", "documents", ["organization_id", "lifecycle_status", "updated_at"])
    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=True),
        sa.Column("checksum_algorithm", sa.String(32), nullable=False),
        sa.Column("checksum_value", sa.String(128), nullable=False),
        sa.Column("storage_provider", sa.String(32), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=True),
        sa.Column("external_reference", sa.Text(), nullable=True),
        sa.Column("source_kind", sa.String(64), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=True),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("created_by_subject_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_document_versions_id_organization"),
        sa.UniqueConstraint("id", "document_id", "organization_id", name="uq_document_versions_id_document_organization"),
        sa.UniqueConstraint("organization_id", "document_id", "sequence", name="uq_document_versions_sequence"),
        sa.ForeignKeyConstraint(["document_id", "organization_id"], ["documents.id", "documents.organization_id"], name="fk_document_versions_document_organization"),
        sa.ForeignKeyConstraint(["supersedes_version_id", "document_id", "organization_id"], ["document_versions.id", "document_versions.document_id", "document_versions.organization_id"], name="fk_document_versions_supersedes_document_organization"),
        sa.CheckConstraint("sequence > 0", name="ck_document_versions_sequence"),
        sa.CheckConstraint("byte_size IS NULL OR byte_size >= 0", name="ck_document_versions_byte_size"),
        sa.CheckConstraint("char_length(checksum_algorithm)>0 AND char_length(checksum_value)>0", name="ck_document_versions_checksum"),
        sa.CheckConstraint("storage_key IS NOT NULL OR external_reference IS NOT NULL", name="ck_document_versions_reference"),
        sa.CheckConstraint(_RELATIVE_STORAGE_KEY, name="ck_document_versions_relative_key"),
        sa.CheckConstraint("supersedes_version_id IS NULL OR supersedes_version_id <> id", name="ck_document_versions_not_self_superseding"),
    )
    op.create_index("ix_document_versions_org_document_sequence", "document_versions", ["organization_id", "document_id", "sequence"])
    op.create_foreign_key(
        "fk_documents_current_version_document_organization",
        "documents",
        "document_versions",
        ["current_version_id", "id", "organization_id"],
        ["id", "document_id", "organization_id"],
    )
    op.create_table(
        "document_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_by_subject_id", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_document_associations_organization"),
        sa.ForeignKeyConstraint(["document_id", "organization_id"], ["documents.id", "documents.organization_id"], name="fk_document_associations_document_organization"),
        sa.CheckConstraint("subject_type IN ('organization','site','project','mission_work_item','operational_task','process_instance')", name="ck_document_associations_subject_type"),
        sa.CheckConstraint("unlinked_at IS NULL OR unlinked_at >= linked_at", name="ck_document_associations_history"),
    )
    op.create_index("uq_document_associations_active", "document_associations", ["organization_id", "document_id", "subject_type", "subject_id"], unique=True, postgresql_where=sa.text("unlinked_at IS NULL"))
    op.create_index("ix_document_associations_subject_active", "document_associations", ["organization_id", "subject_type", "subject_id", "unlinked_at"])
    op.execute("CREATE FUNCTION document_versions_append_only_guard() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'document_versions are append-only'; END; $$ LANGUAGE plpgsql;")
    op.execute("CREATE TRIGGER document_versions_append_only BEFORE UPDATE OR DELETE ON document_versions FOR EACH ROW EXECUTE FUNCTION document_versions_append_only_guard();")


def downgrade() -> None:
    op.execute("DROP TRIGGER document_versions_append_only ON document_versions")
    op.execute("DROP FUNCTION document_versions_append_only_guard()")
    op.drop_table("document_associations")
    op.drop_constraint("fk_documents_current_version_document_organization", "documents", type_="foreignkey")
    op.drop_table("document_versions")
    op.drop_table("documents")
