"""Scope Radar Merchant store uniqueness to canonical organization."""

from alembic import op


revision = "20260813_36"
down_revision = "20260806_35"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_radar_merchants_workspace_store", "radar_merchants", type_="unique")
    op.create_unique_constraint(
        "uq_radar_merchants_organization_store",
        "radar_merchants",
        ["organization_id", "store_id"],
    )


def downgrade():
    op.drop_constraint("uq_radar_merchants_organization_store", "radar_merchants", type_="unique")
    op.create_unique_constraint(
        "uq_radar_merchants_workspace_store",
        "radar_merchants",
        ["workspace_id", "store_id"],
    )
