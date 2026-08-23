"""Add one-use encrypted OIDC bootstrap identity handoff.

Revision ID: 20260822_43
Revises: 20260820_42
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260822_43"
down_revision = "20260820_42"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bootstrap_verified_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("oidc_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issuer_hash", sa.String(64), nullable=False),
        sa.Column("subject_encrypted", sa.String(1024), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["oidc_attempt_id"], ["oidc_authentication_attempts.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("oidc_attempt_id", name="uq_bootstrap_verified_identity_attempt"),
    )
    op.create_index("ix_bootstrap_verified_identities_expires", "bootstrap_verified_identities", ["expires_at"])


def downgrade():
    op.drop_index("ix_bootstrap_verified_identities_expires", table_name="bootstrap_verified_identities")
    op.drop_table("bootstrap_verified_identities")
