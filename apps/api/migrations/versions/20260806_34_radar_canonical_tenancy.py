"""F-011 E/F nullable Radar tenancy, without historical backfill."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260806_34"
down_revision = "20260806_32"
branch_labels = None
depends_on = None

def upgrade():
    for table in ("radar_merchants", "radar_requests", "radar_activities"):
        op.add_column(table, sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(f"fk_{table}_organization", table, "organizations", ["organization_id"], ["id"])
        op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])

def downgrade():
    for table in ("radar_activities", "radar_requests", "radar_merchants"):
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        op.drop_constraint(f"fk_{table}_organization", table, type_="foreignkey")
        op.drop_column(table, "organization_id")
