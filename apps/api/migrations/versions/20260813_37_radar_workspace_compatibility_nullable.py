"""Retain legacy Radar workspace values while allowing canonical writes to omit them."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_37"
down_revision = "20260813_36"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("radar_merchants", "radar_requests", "radar_activities"):
        op.alter_column(table, "workspace_id", existing_type=sa.String(length=100), nullable=True)


def downgrade():
    for table in ("radar_activities", "radar_requests", "radar_merchants"):
        op.alter_column(table, "workspace_id", existing_type=sa.String(length=100), nullable=False)
