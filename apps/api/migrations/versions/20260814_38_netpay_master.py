"""Create tenant-owned Netpay Client, Company, Branch, and Store master."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260814_38"
down_revision = "20260813_37"
branch_labels = None
depends_on = None


def _audit_columns():
    return [
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade():
    op.create_table("netpay_clients", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), *_audit_columns(), sa.Column("display_name", sa.String(255), nullable=False), sa.Column("normalized_name", sa.String(255), nullable=False), sa.Column("external_reference", sa.String(100)), sa.Column("primary_contact_name", sa.String(255)), sa.Column("primary_email", sa.String(320)), sa.Column("primary_phone", sa.String(40)), sa.Column("status", sa.String(32), nullable=False, server_default="active"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "id", name="uq_netpay_clients_organization_id"))
    op.create_index("ix_netpay_clients_organization_name", "netpay_clients", ["organization_id", "normalized_name"])
    op.create_table("netpay_companies", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), *_audit_columns(), sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("legal_name", sa.String(255), nullable=False), sa.Column("normalized_legal_name", sa.String(255), nullable=False), sa.Column("tax_identifier", sa.String(64)), sa.Column("legal_address", sa.Text()), sa.Column("contact_name", sa.String(255)), sa.Column("contact_email", sa.String(320)), sa.Column("contact_phone", sa.String(40)), sa.Column("status", sa.String(32), nullable=False, server_default="active"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["organization_id", "client_id"], ["netpay_clients.organization_id", "netpay_clients.id"], name="fk_netpay_companies_client_tenant", ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "id", name="uq_netpay_companies_organization_id"), sa.UniqueConstraint("organization_id", "tax_identifier", name="uq_netpay_companies_organization_tax"))
    op.create_index("ix_netpay_companies_client_name", "netpay_companies", ["organization_id", "client_id", "normalized_legal_name"])
    op.create_table("netpay_branches", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), *_audit_columns(), sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("commercial_name", sa.String(255), nullable=False), sa.Column("normalized_commercial_name", sa.String(255), nullable=False), sa.Column("branch_match_key", sa.String(512), nullable=False), sa.Column("branch_kind", sa.String(16), nullable=False), sa.Column("address", sa.Text()), sa.Column("locality", sa.String(120)), sa.Column("state", sa.String(120)), sa.Column("postal_code", sa.String(20)), sa.Column("contact_name", sa.String(255)), sa.Column("contact_email", sa.String(320)), sa.Column("contact_phone", sa.String(40)), sa.Column("status", sa.String(32), nullable=False, server_default="active"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["organization_id", "company_id"], ["netpay_companies.organization_id", "netpay_companies.id"], name="fk_netpay_branches_company_tenant", ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "id", name="uq_netpay_branches_organization_id"), sa.UniqueConstraint("organization_id", "company_id", "branch_match_key", name="uq_netpay_branches_company_match"))
    op.create_table("netpay_store_references", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("store_id", sa.String(100), nullable=False), sa.Column("normalized_store_id", sa.String(100), nullable=False), sa.Column("source_type", sa.String(64), nullable=False), sa.Column("source_reference", sa.String(255)), sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True)), sa.Column("confirmed_by_principal_id", postgresql.UUID(as_uuid=True)), sa.Column("created_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("updated_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("removed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("source_type <> ''", name="ck_netpay_store_references_source_type"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["organization_id", "branch_id"], ["netpay_branches.organization_id", "netpay_branches.id"], name="fk_netpay_store_references_branch_tenant", ondelete="RESTRICT"), sa.ForeignKeyConstraint(["confirmed_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT"))
    op.create_index("uq_netpay_store_references_active_branch", "netpay_store_references", ["organization_id", "branch_id"], unique=True, postgresql_where=sa.text("active"))
    op.create_index("uq_netpay_store_references_active_store", "netpay_store_references", ["organization_id", "normalized_store_id"], unique=True, postgresql_where=sa.text("active"))
    op.create_table("netpay_master_command_receipts", sa.Column("command_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("command_type", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("result_resource_type", sa.String(64), nullable=False), sa.Column("result_resource_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("result_status_code", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("char_length(request_fingerprint) = 64", name="ck_netpay_master_receipts_fingerprint"), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_master_receipts_org_command_key"))


def downgrade():
    op.drop_table("netpay_master_command_receipts")
    op.drop_index("uq_netpay_store_references_active_store", table_name="netpay_store_references")
    op.drop_index("uq_netpay_store_references_active_branch", table_name="netpay_store_references")
    op.drop_table("netpay_store_references")
    op.drop_table("netpay_branches")
    op.drop_index("ix_netpay_companies_client_name", table_name="netpay_companies")
    op.drop_table("netpay_companies")
    op.drop_index("ix_netpay_clients_organization_name", table_name="netpay_clients")
    op.drop_table("netpay_clients")
