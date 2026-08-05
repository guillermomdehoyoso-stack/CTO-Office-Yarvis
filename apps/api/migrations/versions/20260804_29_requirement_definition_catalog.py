"""C06 immutable Requirement Definition catalog."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260804_29"
down_revision = "20260803_28"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "requirement_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dossier_template_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semantic_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("semantic_subject", sa.String(32), nullable=False),
        sa.Column("fulfillment_mode", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False),
        sa.Column("provenance", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "dossier_template_version_id",
            "semantic_key",
            name="uq_requirement_definitions_template_key",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_requirement_definitions_organization",
        ),
        sa.ForeignKeyConstraint(
            ["dossier_template_version_id"],
            ["dossier_template_versions.id"],
            name="fk_requirement_definitions_template",
        ),
        sa.CheckConstraint(
            "semantic_subject IN ('identity','evidence','business_data','derived_knowledge','human_decision')",
            name="ck_requirement_definitions_subject",
        ),
        sa.CheckConstraint(
            "fulfillment_mode IN ('provided','derived','verified','confirmed')",
            name="ck_requirement_definitions_mode",
        ),
        sa.CheckConstraint(
            "classification IN ('required','optional')",
            name="ck_requirement_definitions_classification",
        ),
        sa.CheckConstraint(
            "aggregate_version > 0",
            name="ck_requirement_definitions_aggregate_version_positive",
        ),
    )
    op.create_index(
        "ix_requirement_definitions_template_key",
        "requirement_definitions",
        ["organization_id", "dossier_template_version_id", "semantic_key"],
    )
    op.create_table(
        "requirement_definition_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "requirement_definition_id",
            "depends_on_definition_id",
            name="uq_requirement_definition_dependency",
        ),
        sa.ForeignKeyConstraint(
            ["requirement_definition_id"],
            ["requirement_definitions.id"],
            name="fk_requirement_definition_dependencies_definition",
        ),
        sa.ForeignKeyConstraint(
            ["depends_on_definition_id"],
            ["requirement_definitions.id"],
            name="fk_requirement_definition_dependencies_depends_on",
        ),
        sa.CheckConstraint(
            "requirement_definition_id <> depends_on_definition_id",
            name="ck_requirement_definition_dependencies_not_self",
        ),
    )
    op.execute(
        """
    CREATE FUNCTION protect_requirement_definition_immutability() RETURNS trigger AS $$
    BEGIN
      IF NEW.organization_id IS DISTINCT FROM OLD.organization_id
         OR NEW.dossier_template_version_id IS DISTINCT FROM OLD.dossier_template_version_id
         OR NEW.semantic_key IS DISTINCT FROM OLD.semantic_key
         OR NEW.title IS DISTINCT FROM OLD.title
         OR NEW.purpose IS DISTINCT FROM OLD.purpose
         OR NEW.semantic_subject IS DISTINCT FROM OLD.semantic_subject
         OR NEW.fulfillment_mode IS DISTINCT FROM OLD.fulfillment_mode
         OR NEW.classification IS DISTINCT FROM OLD.classification
         OR NEW.provenance IS DISTINCT FROM OLD.provenance
         OR NEW.created_at IS DISTINCT FROM OLD.created_at
         OR NEW.aggregate_version IS DISTINCT FROM OLD.aggregate_version THEN
        RAISE EXCEPTION 'requirement definition meaning is immutable';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_requirement_definition_immutability
    BEFORE UPDATE ON requirement_definitions FOR EACH ROW
    EXECUTE FUNCTION protect_requirement_definition_immutability();
    """
    )
    op.execute(
        """
    CREATE FUNCTION protect_requirement_definition_dependency_insert() RETURNS trigger AS $$
    DECLARE
      parent_xmin bigint;
    BEGIN
      SELECT xmin::text::bigint
      INTO parent_xmin
      FROM requirement_definitions
      WHERE id = NEW.requirement_definition_id;

      IF parent_xmin IS NOT NULL AND parent_xmin <> txid_current() THEN
        RAISE EXCEPTION 'requirement definition dependencies are immutable';
      END IF;

      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_requirement_definition_dependency_insert
    BEFORE INSERT ON requirement_definition_dependencies FOR EACH ROW
    EXECUTE FUNCTION protect_requirement_definition_dependency_insert();
    """
    )
    op.execute(
        """
    CREATE FUNCTION protect_requirement_definition_dependency_immutability() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'requirement definition dependencies are immutable';
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_requirement_definition_dependency_immutability
    BEFORE UPDATE OR DELETE ON requirement_definition_dependencies FOR EACH ROW
    EXECUTE FUNCTION protect_requirement_definition_dependency_immutability();
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS trg_requirement_definition_dependency_immutability ON requirement_definition_dependencies"
    )
    op.execute("DROP FUNCTION IF EXISTS protect_requirement_definition_dependency_immutability()")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_requirement_definition_dependency_insert ON requirement_definition_dependencies"
    )
    op.execute("DROP FUNCTION IF EXISTS protect_requirement_definition_dependency_insert()")
    op.drop_table("requirement_definition_dependencies")
    op.execute("DROP TRIGGER IF EXISTS trg_requirement_definition_immutability ON requirement_definitions")
    op.execute("DROP FUNCTION IF EXISTS protect_requirement_definition_immutability()")
    op.drop_index("ix_requirement_definitions_template_key", table_name="requirement_definitions")
    op.drop_table("requirement_definitions")
