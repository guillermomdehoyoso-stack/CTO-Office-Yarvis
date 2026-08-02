"""Add the minimal DI-003 Opportunity aggregate.

Revision ID: 20260802_24
Revises: 20260801_23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260802_24"
down_revision = "20260801_23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("business_intent", sa.Text(), nullable=False), sa.Column("lifecycle_status", sa.String(length=16), nullable=False), sa.Column("aggregate_version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("confirmed_by_subject_id", sa.String(length=255), nullable=True),
        sa.CheckConstraint("lifecycle_status IN ('proposed','confirmed','closed')", name="ck_opportunities_lifecycle"), sa.CheckConstraint("aggregate_version > 0", name="ck_opportunities_aggregate_version_positive"), sa.CheckConstraint("(lifecycle_status = 'proposed' AND confirmed_at IS NULL AND confirmed_by_subject_id IS NULL) OR (lifecycle_status IN ('confirmed','closed') AND confirmed_at IS NOT NULL AND confirmed_by_subject_id IS NOT NULL)", name="ck_opportunities_confirmation_state"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_opportunities_organization"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("id", "organization_id", name="uq_opportunities_id_organization"))
    op.create_index("ix_opportunities_org_lifecycle_created", "opportunities", ["organization_id", "lifecycle_status", "created_at"])
    op.create_table("opportunity_command_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("contract_id", sa.String(length=64), nullable=False), sa.Column("idempotency_key", sa.String(length=255), nullable=False), sa.Column("request_fingerprint", sa.String(length=64), nullable=False), sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("response_kind", sa.String(length=32), nullable=False), sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("char_length(request_fingerprint) = 64", name="ck_opportunity_command_idempotency_fingerprint"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_opportunity_command_idempotency_organization"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("organization_id", "contract_id", "idempotency_key", name="uq_opportunity_command_idempotency"))
    op.create_index("ix_opportunity_command_idempotency_aggregate", "opportunity_command_idempotency", ["organization_id", "aggregate_id"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_command_idempotency_aggregate", table_name="opportunity_command_idempotency")
    op.drop_table("opportunity_command_idempotency")
    op.drop_index("ix_opportunities_org_lifecycle_created", table_name="opportunities")
    op.drop_table("opportunities")
