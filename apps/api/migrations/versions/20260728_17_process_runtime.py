"""process runtime backend

Revision ID: 20260728_17
Revises: 20260727_16
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260728_17"
down_revision = "20260727_16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "process_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_definition_version", sa.Integer(), nullable=False),
        sa.Column("current_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lifecycle", sa.String(length=20), nullable=False),
        sa.Column("created_by_subject_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("start_idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("start_request_fingerprint", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["process_definition_id", "organization_id"],
            ["process_definitions.id", "process_definitions.organization_id"],
            name="fk_process_instances_definition_organization",
        ),
        sa.ForeignKeyConstraint(
            ["current_stage_id", "process_definition_id", "organization_id"],
            ["process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"],
            name="fk_process_instances_current_stage",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_process_instances_id_organization"),
        sa.UniqueConstraint("organization_id", "start_idempotency_key", name="uq_process_instances_start_idempotency"),
        sa.CheckConstraint("lifecycle IN ('active', 'completed', 'cancelled')", name="ck_process_instances_lifecycle"),
        sa.CheckConstraint("version > 0", name="ck_process_instances_version_positive"),
        sa.CheckConstraint("lifecycle <> 'cancelled' OR cancellation_reason IS NOT NULL", name="ck_process_instances_cancel_reason"),
    )
    op.create_index("ix_process_instances_organization_id", "process_instances", ["organization_id"])
    op.create_index("ix_process_instances_definition_id", "process_instances", ["process_definition_id"])
    op.create_index("ix_process_instances_org_lifecycle_updated", "process_instances", ["organization_id", "lifecycle", "updated_at"])
    op.create_index("ix_process_instances_org_definition", "process_instances", ["organization_id", "process_definition_id"])
    op.create_table(
        "process_instance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_subject_id", sa.String(length=255), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["process_instance_id", "organization_id"],
            ["process_instances.id", "process_instances.organization_id"],
            name="fk_process_instance_events_instance_organization",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "process_instance_id", "sequence_number", name="uq_process_instance_events_sequence"),
        sa.UniqueConstraint("organization_id", "process_instance_id", "idempotency_key", name="uq_process_instance_events_idempotency"),
        sa.CheckConstraint("sequence_number > 0", name="ck_process_instance_events_sequence_positive"),
    )
    op.create_index("ix_process_instance_events_org_instance_sequence", "process_instance_events", ["organization_id", "process_instance_id", "sequence_number"])
    op.execute(
        """
        CREATE FUNCTION prevent_process_instance_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'process_instance_events are append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER process_instance_events_append_only
        BEFORE UPDATE OR DELETE ON process_instance_events
        FOR EACH ROW EXECUTE FUNCTION prevent_process_instance_event_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER process_instance_events_append_only ON process_instance_events")
    op.execute("DROP FUNCTION prevent_process_instance_event_mutation()")
    op.drop_index("ix_process_instance_events_org_instance_sequence", table_name="process_instance_events")
    op.drop_table("process_instance_events")
    op.drop_index("ix_process_instances_org_definition", table_name="process_instances")
    op.drop_index("ix_process_instances_org_lifecycle_updated", table_name="process_instances")
    op.drop_index("ix_process_instances_definition_id", table_name="process_instances")
    op.drop_index("ix_process_instances_organization_id", table_name="process_instances")
    op.drop_table("process_instances")
