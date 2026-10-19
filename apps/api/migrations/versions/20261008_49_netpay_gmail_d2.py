"""Add governed Gmail OAuth attempt and D2 candidate persistence.

Revision ID: 20261008_49
Revises: 20261008_48
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261008_49"
down_revision: str | None = "20261008_48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

U = postgresql.UUID(as_uuid=True)
J = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "netpay_gmail_connections",
        sa.Column("provider_kind", sa.String(16), nullable=False, server_default="fake"),
    )
    op.add_column("netpay_gmail_connections", sa.Column("mailbox_verified_at", sa.DateTime(timezone=True)))
    op.add_column(
        "netpay_gmail_connections",
        sa.Column("manifest_status", sa.String(16), nullable=False, server_default="none"),
    )
    op.add_column(
        "netpay_gmail_connections",
        sa.Column("manifest_entries", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column("netpay_gmail_connections", sa.Column("manifest_approved_at", sa.DateTime(timezone=True)))

    op.create_table(
        "netpay_gmail_oauth_attempts",
        sa.Column("id", U, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("principal_id", U, nullable=False),
        sa.Column("state_digest", sa.String(64), nullable=False),
        sa.Column("secret_ref", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_digest", name="uq_netpay_gmail_oauth_attempt_state_digest"),
    )
    op.create_index(
        "ix_netpay_gmail_oauth_attempt_org_expiry",
        "netpay_gmail_oauth_attempts",
        ["organization_id", "expires_at"],
    )

    op.create_table(
        "netpay_intake_candidates",
        sa.Column("id", U, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("source_item_id", U, nullable=False),
        sa.Column("connection_id", U, nullable=False),
        sa.Column("source_fingerprint", sa.String(64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="new"),
        sa.Column("request_type", sa.String(64), nullable=False, server_default="unclassified"),
        sa.Column("product", sa.String(32), nullable=False, server_default="not_applicable"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("ticket_references", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("commerce_hints", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("terminal_serials", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("shipment_facts", J, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("facts", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("inferences", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("contradictions", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("missing_data", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("correlation_key", sa.String(255)),
        sa.Column("client_id", U),
        sa.Column("company_id", U),
        sa.Column("branch_id", U),
        sa.Column("store_reference_id", U),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("suggested_responsible_principal_id", U),
        sa.Column("suggested_next_action", sa.Text()),
        sa.Column("follow_up_at", sa.DateTime(timezone=True)),
        sa.Column("extraction_method", sa.String(32), nullable=False, server_default="deterministic"),
        sa.Column("extraction_version", sa.String(32), nullable=False, server_default="d2-rules-v1"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("extraction_reasons", J, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reviewed_by_principal_id", U),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("disposition_reason", sa.String(255)),
        sa.Column("owner_type", sa.String(32)),
        sa.Column("owner_id", U),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_item_id"], ["netpay_gmail_source_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["netpay_gmail_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["netpay_clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["company_id"], ["netpay_companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["branch_id"], ["netpay_branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_reference_id"], ["netpay_store_references.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["suggested_responsible_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_item_id", name="uq_netpay_intake_candidates_org_source"),
        sa.CheckConstraint(
            "state IN ('new','needs_review','pending_link','accepted','rejected','duplicate','linked')",
            name="ck_netpay_intake_candidates_state",
        ),
        sa.CheckConstraint("priority IN ('urgent','high','normal','low')", name="ck_netpay_intake_candidates_priority"),
    )
    op.create_index(
        "ix_netpay_intake_candidates_org_attention",
        "netpay_intake_candidates",
        ["organization_id", "state", "priority"],
    )
    op.create_index(
        "ix_netpay_intake_candidates_org_correlation",
        "netpay_intake_candidates",
        ["organization_id", "correlation_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_netpay_intake_candidates_org_correlation", table_name="netpay_intake_candidates")
    op.drop_index("ix_netpay_intake_candidates_org_attention", table_name="netpay_intake_candidates")
    op.drop_table("netpay_intake_candidates")
    op.drop_index("ix_netpay_gmail_oauth_attempt_org_expiry", table_name="netpay_gmail_oauth_attempts")
    op.drop_table("netpay_gmail_oauth_attempts")
    op.drop_column("netpay_gmail_connections", "manifest_approved_at")
    op.drop_column("netpay_gmail_connections", "manifest_entries")
    op.drop_column("netpay_gmail_connections", "manifest_status")
    op.drop_column("netpay_gmail_connections", "mailbox_verified_at")
    op.drop_column("netpay_gmail_connections", "provider_kind")
