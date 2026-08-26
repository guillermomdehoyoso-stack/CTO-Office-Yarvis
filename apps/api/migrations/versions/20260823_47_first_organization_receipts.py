"""Persist durable receipts for one governed first-Organization creation.

Revision ID: 20260823_47
Revises: 20260823_46
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260823_47"
down_revision = "20260823_46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "first_organization_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("authorization_digest", sa.String(length=64), nullable=False),
        sa.Column("nonce_hash", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False, server_default="created"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("authorization_digest", name="uq_first_organization_receipt_authorization"),
        sa.UniqueConstraint("nonce_hash", name="uq_first_organization_receipt_nonce"),
        sa.UniqueConstraint("idempotency_key_hash", name="uq_first_organization_receipt_idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("first_organization_receipts")
