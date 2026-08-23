"""Add durable founder bootstrap authorization receipts.

Revision ID: 20260822_44
Revises: 20260822_43
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260822_44"
down_revision = "20260822_43"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "founder_bootstrap_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("authorization_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("nonce_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("handoff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("outcome IN ('prepared','consumed')", name="ck_founder_bootstrap_receipt_outcome"),
        sa.ForeignKeyConstraint(["handoff_id"], ["bootstrap_verified_identities.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("idempotency_key_hash", name="uq_founder_bootstrap_idempotency_key"),
    )


def downgrade():
    op.drop_table("founder_bootstrap_receipts")
