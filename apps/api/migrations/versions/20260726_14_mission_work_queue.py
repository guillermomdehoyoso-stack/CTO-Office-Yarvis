"""mission work queue

Revision ID: 20260726_14
Revises: 20260726_13
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260726_14"
down_revision = "20260726_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mission_work_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Inbox rows are rebuildable; this durable reference is intentionally not an FK.
        sa.Column("inbox_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("assignee_subject_id", sa.String(length=255), nullable=True),
        sa.Column("created_by_subject_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "inbox_item_id", name="uq_mission_work_items_inbox_identity"),
        sa.UniqueConstraint("organization_id", "source_type", "source_id", name="uq_mission_work_items_source_identity"),
        sa.CheckConstraint("status IN ('open', 'assigned', 'in_progress', 'waiting', 'resolved', 'cancelled')", name="ck_mission_work_items_status"),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="ck_mission_work_items_priority"),
    )
    op.create_index("ix_mission_work_items_org_status_updated", "mission_work_items", ["organization_id", "status", "updated_at"])
    op.create_index("ix_mission_work_items_org_assignee_status", "mission_work_items", ["organization_id", "assignee_subject_id", "status"])
    op.create_index("ix_mission_work_items_org_priority_updated", "mission_work_items", ["organization_id", "priority", "updated_at"])
    op.create_index("ix_mission_work_items_org_source", "mission_work_items", ["organization_id", "source_type", "source_id"])
    op.create_index("ix_mission_work_items_org_inbox", "mission_work_items", ["organization_id", "inbox_item_id"])


def downgrade() -> None:
    op.drop_table("mission_work_items")
