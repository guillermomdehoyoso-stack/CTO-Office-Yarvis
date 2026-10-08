"""Add the bounded, read-only Netpay Gmail Intake D1 source boundary.

This is an explicit merge revision because the reviewed Alembic graph has four
heads. It creates no candidate, owner, scheduler, OAuth or Gmail mutation
state.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261008_48"
down_revision = ("20260712_04", "20260802_25", "20260802_26", "20260823_47")
branch_labels = None
depends_on = None

U = postgresql.UUID(as_uuid=True)
J = postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        "netpay_gmail_connections",
        sa.Column("id", U, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("credential_secret_ref", sa.String(255), nullable=False),
        sa.Column("label_id", sa.String(255), nullable=False),
        sa.Column("query", sa.String(500), nullable=False, server_default=""),
        sa.Column("state", sa.String(32), nullable=False, server_default="connected"),
        sa.Column("cursor", sa.String(255)),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_code", sa.String(64)),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("updated_by_principal_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "provider_account_id", name="uq_netpay_gmail_connections_org_account"),
        sa.CheckConstraint(
            "state IN ('disconnected','connected','validating','ready','running','succeeded','partially_failed','failed','revoked')",
            name="ck_netpay_gmail_connections_state",
        ),
    )
    op.create_index("ix_netpay_gmail_connections_organization_id", "netpay_gmail_connections", ["organization_id"])
    op.create_index("ix_netpay_gmail_connections_org_state", "netpay_gmail_connections", ["organization_id", "state"])

    op.create_table(
        "netpay_gmail_sync_runs",
        sa.Column("id", U, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("connection_id", U, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cursor_before", sa.String(255)),
        sa.Column("cursor_after", sa.String(255)),
        sa.Column("captured_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deduplicated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflict_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_code", sa.String(64)),
        sa.Column("correlation_id", U, nullable=False),
        sa.Column("actor_principal_id", U, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["connection_id"], ["netpay_gmail_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('running','succeeded','partially_failed','failed')", name="ck_netpay_gmail_sync_runs_status"),
    )
    op.create_index("ix_netpay_gmail_sync_runs_org_created", "netpay_gmail_sync_runs", ["organization_id", "created_at"])
    op.create_index("ix_netpay_gmail_sync_runs_connection_created", "netpay_gmail_sync_runs", ["connection_id", "created_at"])

    op.create_table(
        "netpay_gmail_source_items",
        sa.Column("id", U, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("connection_id", U, nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("gmail_message_id", sa.String(255), nullable=False),
        sa.Column("gmail_thread_id", sa.String(255), nullable=False),
        sa.Column("provider_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synchronized_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sender", sa.String(255)),
        sa.Column("recipient", sa.String(255)),
        sa.Column("subject", sa.String(500)),
        sa.Column("plain_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_fingerprint", sa.String(64), nullable=False),
        sa.Column("attachment_metadata", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("provenance", J, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("conflict_detected_at", sa.DateTime(timezone=True)),
        sa.Column("conflict_fingerprint", sa.String(64)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["connection_id"], ["netpay_gmail_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "connection_id",
            "provider_account_id",
            "gmail_message_id",
            name="uq_netpay_gmail_source_items_identity",
        ),
    )
    op.create_index("ix_netpay_gmail_source_items_org_received", "netpay_gmail_source_items", ["organization_id", "provider_received_at"])
    op.create_index("ix_netpay_gmail_source_items_thread", "netpay_gmail_source_items", ["organization_id", "gmail_thread_id"])

    op.create_table(
        "netpay_gmail_command_receipts",
        sa.Column("command_id", U, nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("command_type", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("actor_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.Column("result_resource_id", U, nullable=False),
        sa.Column("result_status_code", sa.Integer(), nullable=False),
        sa.Column("result_response_body", J, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("command_id"),
        sa.UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_gmail_receipts_org_command_key"),
    )


def downgrade() -> None:
    op.drop_table("netpay_gmail_command_receipts")
    op.drop_index("ix_netpay_gmail_source_items_thread", table_name="netpay_gmail_source_items")
    op.drop_index("ix_netpay_gmail_source_items_org_received", table_name="netpay_gmail_source_items")
    op.drop_table("netpay_gmail_source_items")
    op.drop_index("ix_netpay_gmail_sync_runs_connection_created", table_name="netpay_gmail_sync_runs")
    op.drop_index("ix_netpay_gmail_sync_runs_org_created", table_name="netpay_gmail_sync_runs")
    op.drop_table("netpay_gmail_sync_runs")
    op.drop_index("ix_netpay_gmail_connections_org_state", table_name="netpay_gmail_connections")
    op.drop_index("ix_netpay_gmail_connections_organization_id", table_name="netpay_gmail_connections")
    op.drop_table("netpay_gmail_connections")
