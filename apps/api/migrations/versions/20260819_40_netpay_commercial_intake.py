"""Add tenant-owned Netpay commercial intake before Master conversion.

Revision ID: 20260819_40
Revises: 20260814_39
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260819_40"
down_revision = "20260814_39"
branch_labels = None
depends_on = None

U = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    audit = [sa.Column("organization_id", U, nullable=False), sa.Column("created_by_principal_id", U, nullable=False), sa.Column("updated_by_principal_id", U, nullable=False), sa.Column("id", U, primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)]
    op.create_table(
        "netpay_commercial_intake_items",
        sa.Column("kind", sa.String(32), nullable=False), sa.Column("channel", sa.String(16), nullable=False), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provisional_company_name", sa.String(255)), sa.Column("provisional_contact_name", sa.String(255)), sa.Column("product_interest", sa.String(16), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("assignee_principal_id", U), sa.Column("next_action", sa.Text()), sa.Column("due_date", sa.DateTime(timezone=True)), sa.Column("status", sa.String(16), nullable=False, server_default="new"),
        sa.Column("master_client_id", U), sa.Column("master_company_id", U), sa.Column("master_branch_id", U), sa.Column("converted_case_id", U, unique=True), *audit,
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["assignee_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["master_client_id"], ["netpay_clients.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["master_company_id"], ["netpay_companies.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["master_branch_id"], ["netpay_branches.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["converted_case_id"], ["netpay_inbox_cases.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("kind IN ('initial_contact','rfq','commercial_opportunity','unclassified')", name="ck_netpay_commercial_intake_kind"), sa.CheckConstraint("channel IN ('call','email','whatsapp','referral','manual')", name="ck_netpay_commercial_intake_channel"), sa.CheckConstraint("product_interest IN ('tpv','ecommerce','other')", name="ck_netpay_commercial_intake_product"), sa.CheckConstraint("priority IN ('urgent','high','normal','low')", name="ck_netpay_commercial_intake_priority"), sa.CheckConstraint("status IN ('new','qualifying','qualified','discarded')", name="ck_netpay_commercial_intake_status"),
    )
    op.create_index("ix_netpay_commercial_intake_org_attention", "netpay_commercial_intake_items", ["organization_id", "status", "priority"])
    op.create_table("netpay_commercial_intake_command_receipts", sa.Column("command_id", U, primary_key=True), sa.Column("organization_id", U, nullable=False), sa.Column("command_type", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("actor_principal_id", U, nullable=False), sa.Column("correlation_id", U, nullable=False), sa.Column("result_resource_id", U, nullable=False), sa.Column("result_status_code", sa.Integer(), nullable=False), sa.Column("result_response_body", postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_commercial_intake_receipts_org_command_key"))


def downgrade() -> None:
    op.drop_table("netpay_commercial_intake_command_receipts")
    op.drop_index("ix_netpay_commercial_intake_org_attention", table_name="netpay_commercial_intake_items")
    op.drop_table("netpay_commercial_intake_items")
