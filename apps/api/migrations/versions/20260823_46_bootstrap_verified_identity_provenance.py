"""Persist prospective provenance for bootstrap-verified identity handoffs.

Revision ID: 20260823_46
Revises: 20260823_45
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260823_46"
down_revision = "20260823_45"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bootstrap_verified_identities", sa.Column("provenance", sa.String(length=32), nullable=True))
    op.add_column(
        "bootstrap_verified_identities",
        sa.Column("provenance_receipt_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_bootstrap_verified_identity_provenance_receipt",
        "bootstrap_verified_identities",
        ["provenance_receipt_id"],
    )
    op.create_check_constraint(
        "ck_bootstrap_verified_identity_provenance",
        "bootstrap_verified_identities",
        "(provenance IS NULL AND provenance_receipt_id IS NULL) "
        "OR (provenance = 'founder_bootstrap' AND provenance_receipt_id IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint(
        "ck_bootstrap_verified_identity_provenance", "bootstrap_verified_identities", type_="check"
    )
    op.drop_constraint(
        "uq_bootstrap_verified_identity_provenance_receipt",
        "bootstrap_verified_identities",
        type_="unique",
    )
    op.drop_column("bootstrap_verified_identities", "provenance_receipt_id")
    op.drop_column("bootstrap_verified_identities", "provenance")
