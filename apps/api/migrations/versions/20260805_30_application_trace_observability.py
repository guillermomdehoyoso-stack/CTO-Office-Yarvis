"""F-012 append-only technical application trace."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260805_30"
down_revision = "20260804_29"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "application_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("entry_kind", sa.String(16), nullable=False),
        sa.Column("interaction_contract_id", sa.String(128), nullable=False),
        sa.Column("contract_version", sa.String(32), nullable=False),
        sa.Column("owner_module_id", sa.String(128), nullable=False),
        sa.Column("owning_context", sa.String(255), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", sa.String(255), nullable=False),
        sa.Column("causation_id", sa.String(255), nullable=True),
        sa.Column("authorization_decision", sa.String(32), nullable=False),
        sa.Column("object_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("event_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provenance_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retry_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("compensation_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_type", sa.String(128), nullable=True),
        sa.Column("failure_summary", sa.String(512), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id", "sequence", name="uq_application_traces_trace_sequence"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_application_traces_organization"),
        sa.CheckConstraint("sequence > 0", name="ck_application_traces_sequence_positive"),
        sa.CheckConstraint("entry_kind IN ('started', 'succeeded', 'failed')", name="ck_application_traces_entry_kind"),
        sa.CheckConstraint(
            "(entry_kind = 'started' AND sequence = 1) OR "
            "(entry_kind IN ('succeeded', 'failed') AND sequence = 2)",
            name="ck_application_traces_entry_sequence_kind",
        ),
    )
    op.create_index("ix_application_traces_trace_id", "application_traces", ["trace_id"])
    op.create_index("ix_application_traces_contract_id", "application_traces", ["interaction_contract_id"])
    op.create_index("ix_application_traces_organization_id", "application_traces", ["organization_id"])
    op.create_index("ix_application_traces_correlation_id", "application_traces", ["correlation_id"])
    op.execute(
        """
    CREATE FUNCTION protect_application_trace_immutability() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'application traces are append-only';
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_application_traces_immutability
    BEFORE UPDATE OR DELETE ON application_traces FOR EACH ROW
    EXECUTE FUNCTION protect_application_trace_immutability();

    CREATE FUNCTION validate_application_trace_transition() RETURNS trigger AS $$
    BEGIN
      IF NEW.entry_kind = 'started' THEN
        IF NEW.sequence <> 1 THEN
          RAISE EXCEPTION 'started application traces require sequence 1';
        END IF;
      ELSIF NEW.entry_kind IN ('succeeded', 'failed') THEN
        IF NEW.sequence <> 2 OR NOT EXISTS (
          SELECT 1 FROM application_traces
          WHERE trace_id = NEW.trace_id AND sequence = 1 AND entry_kind = 'started'
        ) THEN
          RAISE EXCEPTION 'terminal application traces require a started entry';
        END IF;
      ELSE
        RAISE EXCEPTION 'invalid application trace entry kind';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_application_traces_transition
    BEFORE INSERT ON application_traces FOR EACH ROW
    EXECUTE FUNCTION validate_application_trace_transition();
    """
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_application_traces_transition ON application_traces")
    op.execute("DROP FUNCTION IF EXISTS validate_application_trace_transition()")
    op.execute("DROP TRIGGER IF EXISTS trg_application_traces_immutability ON application_traces")
    op.execute("DROP FUNCTION IF EXISTS protect_application_trace_immutability()")
    op.drop_index("ix_application_traces_correlation_id", table_name="application_traces")
    op.drop_index("ix_application_traces_organization_id", table_name="application_traces")
    op.drop_index("ix_application_traces_contract_id", table_name="application_traces")
    op.drop_index("ix_application_traces_trace_id", table_name="application_traces")
    op.drop_table("application_traces")
