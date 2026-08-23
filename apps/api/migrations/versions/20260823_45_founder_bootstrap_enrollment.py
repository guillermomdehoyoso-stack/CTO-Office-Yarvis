"""Persist founder enrollment result references without signed payload material.

Revision ID: 20260823_45
Revises: 20260822_44
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260823_45"
down_revision = "20260822_44"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_founder_bootstrap_receipt_outcome", "founder_bootstrap_receipts", type_="check")
    op.create_check_constraint(
        "ck_founder_bootstrap_receipt_outcome",
        "founder_bootstrap_receipts",
        "outcome IN ('prepared','consumed','enrolled')",
    )
    for name, target in (
        ("person_id", "people.id"),
        ("principal_id", "principals.id"),
        ("membership_id", "principal_memberships.id"),
    ):
        op.add_column("founder_bootstrap_receipts", sa.Column(name, postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_founder_bootstrap_{name}",
            "founder_bootstrap_receipts",
            target.split(".")[0],
            [name],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade():
    for name in ("membership_id", "principal_id", "person_id"):
        op.drop_constraint(f"fk_founder_bootstrap_{name}", "founder_bootstrap_receipts", type_="foreignkey")
        op.drop_column("founder_bootstrap_receipts", name)
    op.drop_constraint("ck_founder_bootstrap_receipt_outcome", "founder_bootstrap_receipts", type_="check")
    op.create_check_constraint(
        "ck_founder_bootstrap_receipt_outcome", "founder_bootstrap_receipts", "outcome IN ('prepared','consumed')"
    )
