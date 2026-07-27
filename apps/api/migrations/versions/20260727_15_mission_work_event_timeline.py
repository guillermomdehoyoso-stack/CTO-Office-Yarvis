"""mission work event timeline

Revision ID: 20260727_15
Revises: 20260726_14
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260727_15"
down_revision = "20260726_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mission_work_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_subject_id", sa.String(length=255), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["work_item_id"], ["mission_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "work_item_id", "sequence_number", name="uq_mission_work_events_work_sequence"),
        sa.CheckConstraint("sequence_number > 0", name="ck_mission_work_events_sequence_positive"),
    )
    op.create_index(
        "ix_mission_work_events_org_work_sequence",
        "mission_work_events",
        ["organization_id", "work_item_id", "sequence_number"],
    )
    op.execute(
        """
        CREATE FUNCTION prevent_mission_work_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'mission_work_events are append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER mission_work_events_append_only
        BEFORE UPDATE OR DELETE ON mission_work_events
        FOR EACH ROW EXECUTE FUNCTION prevent_mission_work_event_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER mission_work_events_append_only ON mission_work_events")
    op.execute("DROP FUNCTION prevent_mission_work_event_mutation()")
    op.drop_table("mission_work_events")
