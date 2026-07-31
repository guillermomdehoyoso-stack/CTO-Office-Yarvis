"""Operational Task runtime foundation.

Revision ID: 20260730_20
Revises: 20260729_19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260730_20"
down_revision = "20260729_19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operational_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mission_work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("process_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("assignee_subject_id", sa.String(length=255), nullable=True),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_subject_id", sa.String(length=255), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by_subject_id", sa.String(length=255), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("create_idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("create_request_fingerprint", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_operational_tasks_organization"),
        sa.ForeignKeyConstraint(["mission_work_item_id"], ["mission_work_items.id"], name="fk_operational_tasks_work"),
        sa.ForeignKeyConstraint(
            ["process_instance_id", "organization_id"],
            ["process_instances.id", "process_instances.organization_id"],
            name="fk_operational_tasks_process_organization",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_operational_tasks_id_organization"),
        sa.UniqueConstraint("organization_id", "create_idempotency_key", name="uq_operational_tasks_create_idempotency"),
        sa.CheckConstraint("status IN ('planned', 'ready', 'in_progress', 'completed', 'cancelled')", name="ck_operational_tasks_status"),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="ck_operational_tasks_priority"),
        sa.CheckConstraint("version > 0", name="ck_operational_tasks_version_positive"),
        sa.CheckConstraint("status <> 'cancelled' OR cancellation_reason IS NOT NULL", name="ck_operational_tasks_cancel_reason"),
    )
    op.create_index("ix_operational_tasks_org_work_created", "operational_tasks", ["organization_id", "mission_work_item_id", "created_at", "id"])

    op.create_table(
        "task_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("predecessor_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("successor_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["predecessor_task_id", "organization_id"],
            ["operational_tasks.id", "operational_tasks.organization_id"],
            name="fk_task_dependencies_predecessor",
        ),
        sa.ForeignKeyConstraint(
            ["successor_task_id", "organization_id"],
            ["operational_tasks.id", "operational_tasks.organization_id"],
            name="fk_task_dependencies_successor",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "predecessor_task_id", "successor_task_id", name="uq_task_dependencies_direct_edge"),
        sa.CheckConstraint("predecessor_task_id <> successor_task_id", name="ck_task_dependencies_no_self_edge"),
    )
    op.create_index("ix_task_dependencies_org_successor", "task_dependencies", ["organization_id", "successor_task_id"])

    op.create_table(
        "operational_task_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id", "organization_id"],
            ["operational_tasks.id", "operational_tasks.organization_id"],
            name="fk_operational_task_events_task_organization",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "task_id", "idempotency_key", name="uq_operational_task_events_idempotency"),
        sa.UniqueConstraint("organization_id", "task_id", "sequence_number", name="uq_operational_task_events_sequence"),
    )


def downgrade() -> None:
    op.drop_table("operational_task_events")
    op.drop_index("ix_task_dependencies_org_successor", table_name="task_dependencies")
    op.drop_table("task_dependencies")
    op.drop_index("ix_operational_tasks_org_work_created", table_name="operational_tasks")
    op.drop_table("operational_tasks")
