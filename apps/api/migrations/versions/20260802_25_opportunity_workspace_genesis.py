"""Add the minimal Opportunity Workspace.

Revision ID: 20260802_25
Revises: 20260802_24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260802_25"
down_revision = "20260802_24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunity_workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=16), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("lifecycle_status IN ('pending','active','closed')", name="ck_opportunity_workspaces_lifecycle"),
        sa.CheckConstraint("aggregate_version > 0", name="ck_opportunity_workspaces_aggregate_version_positive"),
        sa.ForeignKeyConstraint(["opportunity_id", "organization_id"], ["opportunities.id", "opportunities.organization_id"], name="fk_opportunity_workspaces_opportunity_organization"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", name="uq_opportunity_workspaces_opportunity"),
    )
    op.create_index("ix_opportunity_workspaces_organization", "opportunity_workspaces", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_workspaces_organization", table_name="opportunity_workspaces")
    op.drop_table("opportunity_workspaces")
