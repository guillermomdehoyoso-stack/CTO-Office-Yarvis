"""Add the minimal Opportunity Dossier.

Revision ID: 20260802_27
Revises: 20260802_26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="20260802_27";down_revision="20260802_26";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("opportunity_dossiers",sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("organization_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("opportunity_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("workspace_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("template_id",sa.String(length=64),nullable=False),sa.Column("lifecycle_status",sa.String(length=16),nullable=False),sa.Column("aggregate_version",sa.Integer(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint("lifecycle_status IN ('pending','active','closed')",name="ck_opportunity_dossiers_lifecycle"),sa.CheckConstraint("aggregate_version > 0",name="ck_opportunity_dossiers_aggregate_version_positive"),sa.ForeignKeyConstraint(["workspace_id"],["opportunity_workspaces.id"],name="fk_opportunity_dossiers_workspace"),sa.ForeignKeyConstraint(["opportunity_id","organization_id"],["opportunities.id","opportunities.organization_id"],name="fk_opportunity_dossiers_opportunity_organization"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("workspace_id",name="uq_opportunity_dossiers_workspace"))
def downgrade(): op.drop_table("opportunity_dossiers")
