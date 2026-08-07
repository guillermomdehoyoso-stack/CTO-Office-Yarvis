"""F-011 F1 durable Radar command receipts, without handler migration."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260806_35"
down_revision = "20260806_34"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "radar_command_receipts",
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_type", sa.String(length=100), nullable=False),
        sa.Column("contract_version", sa.String(length=20), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_status_code", sa.Integer(), nullable=False),
        sa.Column("result_resource_type", sa.String(length=100), nullable=False),
        sa.Column("result_resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="succeeded"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("char_length(request_fingerprint) = 64", name="ck_radar_command_receipts_fingerprint"),
        sa.CheckConstraint("status = 'succeeded'", name="ck_radar_command_receipts_status"),
        sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], name="fk_radar_command_receipts_actor_principal", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_radar_command_receipts_organization", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("command_id", name="pk_radar_command_receipts"),
        sa.UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_radar_command_receipts_organization_command_key"),
    )
    op.create_index("ix_radar_command_receipts_actor_principal_id", "radar_command_receipts", ["actor_principal_id"])
    op.create_index("ix_radar_command_receipts_correlation_id", "radar_command_receipts", ["correlation_id"])


def downgrade():
    op.drop_index("ix_radar_command_receipts_correlation_id", table_name="radar_command_receipts")
    op.drop_index("ix_radar_command_receipts_actor_principal_id", table_name="radar_command_receipts")
    op.drop_table("radar_command_receipts")
