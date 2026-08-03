"""Add fixed Opportunity Workspace specialization metadata.

Revision ID: 20260802_26
Revises: 20260802_25
"""
from alembic import op
import sqlalchemy as sa
revision="20260802_26"; down_revision="20260802_25"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("opportunity_workspaces",sa.Column("template_id",sa.String(length=64),nullable=True))
    op.add_column("opportunity_workspaces",sa.Column("opportunity_type",sa.String(length=32),nullable=True))
    op.add_column("opportunity_workspaces",sa.Column("template_version",sa.Integer(),nullable=True))
    op.add_column("opportunity_workspaces",sa.Column("template_display_name",sa.String(length=255),nullable=True))
def downgrade():
    op.drop_column("opportunity_workspaces","template_display_name");op.drop_column("opportunity_workspaces","template_version");op.drop_column("opportunity_workspaces","opportunity_type");op.drop_column("opportunity_workspaces","template_id")
