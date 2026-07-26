"""deterministic inbound intake idempotency

Revision ID: 20260716_11
Revises: 20260716_10
Create Date: 2026-07-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260716_11"
down_revision = "20260716_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("intake_items", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.add_column("intake_items", sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_intake_items_organization_id_idempotency_key",
        "intake_items",
        ["organization_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_intake_items_organization_id_idempotency_key",
        "intake_items",
        type_="unique",
    )
    op.drop_column("intake_items", "idempotency_fingerprint")
    op.drop_column("intake_items", "idempotency_key")
