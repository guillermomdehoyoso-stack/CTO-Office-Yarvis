"""deterministic inbound intake slice

Revision ID: 20260716_10
Revises: 20260716_09
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260716_10"
down_revision = "20260716_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "intake_items",
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "intake_items",
        sa.Column("trace_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "domain_events",
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_domain_events_causation_id", "domain_events", ["causation_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intake_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_source", sa.String(length=100), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=False),
        sa.Column("connector_delivery_id", sa.String(length=255), nullable=True),
        sa.Column("sender", sa.String(length=320), nullable=False),
        sa.Column("recipients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trace_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["intake_item_id"], ["intake_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_intake_item_id", "messages", ["intake_item_id"])
    op.create_index("ix_messages_external_source", "messages", ["external_source"])
    op.create_index("ix_messages_external_message_id", "messages", ["external_message_id"])
    op.create_index("ix_messages_connector_delivery_id", "messages", ["connector_delivery_id"])
    op.create_index("ix_messages_sender", "messages", ["sender"])


def downgrade() -> None:
    op.drop_index("ix_messages_sender", table_name="messages")
    op.drop_index("ix_messages_connector_delivery_id", table_name="messages")
    op.drop_index("ix_messages_external_message_id", table_name="messages")
    op.drop_index("ix_messages_external_source", table_name="messages")
    op.drop_index("ix_messages_intake_item_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_domain_events_causation_id", table_name="domain_events")
    op.drop_column("domain_events", "causation_id")

    op.drop_column("intake_items", "trace_metadata")
    op.drop_column("intake_items", "source_metadata")
