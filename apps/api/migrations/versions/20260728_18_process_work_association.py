"""process work association and timeline source identity

Revision ID: 20260728_18
Revises: 20260728_17
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260728_18"
down_revision = "20260728_17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "process_instance_work_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mission_work_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_authority_id", sa.String(length=255), nullable=True),
        sa.Column("link_idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("link_request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("unlink_idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("unlink_request_fingerprint", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["process_instance_id", "organization_id"], ["process_instances.id", "process_instances.organization_id"], name="fk_process_work_links_instance_organization"),
        sa.ForeignKeyConstraint(["mission_work_item_id"], ["mission_work_items.id"], name="fk_process_work_links_work"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "link_idempotency_key", name="uq_process_work_links_link_idempotency"),
        sa.UniqueConstraint("organization_id", "unlink_idempotency_key", name="uq_process_work_links_unlink_idempotency"),
        sa.CheckConstraint("relationship_type <> ''", name="ck_process_work_links_relationship_type"),
    )
    op.create_index("uq_process_work_links_active_primary_instance", "process_instance_work_links", ["organization_id", "process_instance_id"], unique=True, postgresql_where=sa.text("unlinked_at IS NULL AND relationship_type = 'primary'"))
    op.create_index("uq_process_work_links_active_relationship", "process_instance_work_links", ["organization_id", "process_instance_id", "mission_work_item_id", "relationship_type"], unique=True, postgresql_where=sa.text("unlinked_at IS NULL"))
    op.create_index("ix_process_work_links_org_work_active", "process_instance_work_links", ["organization_id", "mission_work_item_id", "unlinked_at"])
    op.create_index("ix_process_work_links_org_instance_active", "process_instance_work_links", ["organization_id", "process_instance_id", "unlinked_at"])
    op.add_column("mission_work_events", sa.Column("source_domain_event_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("uq_mission_work_events_source_domain_event", "mission_work_events", ["organization_id", "work_item_id", "source_domain_event_id"], unique=True, postgresql_where=sa.text("source_domain_event_id IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("uq_mission_work_events_source_domain_event", table_name="mission_work_events")
    op.drop_column("mission_work_events", "source_domain_event_id")
    op.drop_index("ix_process_work_links_org_instance_active", table_name="process_instance_work_links")
    op.drop_index("ix_process_work_links_org_work_active", table_name="process_instance_work_links")
    op.drop_index("uq_process_work_links_active_relationship", table_name="process_instance_work_links")
    op.drop_index("uq_process_work_links_active_primary_instance", table_name="process_instance_work_links")
    op.drop_table("process_instance_work_links")
