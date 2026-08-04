"""C05 published Dossier Template catalog.

Revision ID: 20260803_28
Revises: 20260802_27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260803_28"
down_revision = "20260802_27"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("dossier_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stable_key", sa.String(length=64), nullable=False), sa.Column("business_type", sa.String(length=128), nullable=False), sa.Column("business_version", sa.Integer(), nullable=False), sa.Column("display_name", sa.String(length=255), nullable=False), sa.Column("status", sa.String(length=16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True), nullable=False), sa.Column("retired_at", sa.DateTime(timezone=True)), sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('published','retired')", name="ck_dossier_template_versions_status"), sa.CheckConstraint("business_version > 0", name="ck_dossier_template_versions_business_version_positive"), sa.CheckConstraint("aggregate_version > 0", name="ck_dossier_template_versions_aggregate_version_positive"), sa.CheckConstraint("(status = 'published' AND retired_at IS NULL) OR (status = 'retired' AND retired_at IS NOT NULL)", name="ck_dossier_template_versions_retirement_state"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_dossier_template_versions_organization"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("organization_id", "stable_key", "business_version", name="uq_dossier_template_versions_business_identity"))
    op.create_index("ix_dossier_template_versions_published_lookup", "dossier_template_versions", ["organization_id", "stable_key", "business_version"])
    op.execute("""
    CREATE FUNCTION protect_dossier_template_version_immutability() RETURNS trigger AS $$
    BEGIN
      IF NEW.organization_id IS DISTINCT FROM OLD.organization_id
         OR NEW.stable_key IS DISTINCT FROM OLD.stable_key
         OR NEW.business_type IS DISTINCT FROM OLD.business_type
         OR NEW.business_version IS DISTINCT FROM OLD.business_version
         OR NEW.display_name IS DISTINCT FROM OLD.display_name
         OR NEW.created_at IS DISTINCT FROM OLD.created_at
         OR NEW.published_at IS DISTINCT FROM OLD.published_at THEN
        RAISE EXCEPTION 'published dossier template meaning is immutable';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_dossier_template_version_immutability
    BEFORE UPDATE ON dossier_template_versions FOR EACH ROW
    EXECUTE FUNCTION protect_dossier_template_version_immutability();
    """)
def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_dossier_template_version_immutability ON dossier_template_versions")
    op.execute("DROP FUNCTION IF EXISTS protect_dossier_template_version_immutability()")
    op.drop_index("ix_dossier_template_versions_published_lookup", table_name="dossier_template_versions")
    op.drop_table("dossier_template_versions")
