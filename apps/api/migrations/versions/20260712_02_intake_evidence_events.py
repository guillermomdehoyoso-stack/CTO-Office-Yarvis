"""intake evidence and immutable domain events

Revision ID: 20260712_02
Revises: 20260711_01
Create Date: 2026-07-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260712_02"
down_revision = "20260711_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intake_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intake_number", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("text_content IS NOT NULL OR original_filename IS NOT NULL", name="ck_intake_items_content_present"),
        sa.CheckConstraint("source_type IN ('manual_upload', 'manual_text', 'email', 'whatsapp', 'photo', 'other')", name="ck_intake_items_source_type"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("intake_number"),
    )
    op.create_index("ix_intake_items_intake_number", "intake_items", ["intake_number"])
    op.create_index("ix_intake_items_organization_id", "intake_items", ["organization_id"])
    op.create_index("ix_intake_items_person_id", "intake_items", ["person_id"])
    op.create_index("ix_intake_items_case_id", "intake_items", ["case_id"])
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intake_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("evidence_type IN ('document', 'photo', 'message', 'measurement', 'receipt', 'confirmation', 'other')", name="ck_evidence_type"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["intake_item_id"], ["intake_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_case_id", "evidence", ["case_id"])
    op.create_index("ix_evidence_intake_item_id", "evidence", ["intake_item_id"])
    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_events_event_type", "domain_events", ["event_type"])
    op.create_index("ix_domain_events_aggregate_id", "domain_events", ["aggregate_id"])
    op.create_index("ix_domain_events_organization_id", "domain_events", ["organization_id"])
    op.create_index("ix_domain_events_case_id", "domain_events", ["case_id"])
    op.create_index("ix_domain_events_occurred_at", "domain_events", ["occurred_at"])
    op.create_index("ix_domain_events_correlation_id", "domain_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_table("domain_events")
    op.drop_table("evidence")
    op.drop_table("intake_items")
