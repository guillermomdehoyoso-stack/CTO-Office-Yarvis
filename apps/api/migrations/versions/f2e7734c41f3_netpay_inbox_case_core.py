"""Create the isolated tenant-owned Netpay Inbox case core."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f2e7734c41f3"
down_revision = "20260814_38"
branch_labels = None
depends_on = None

U = postgresql.UUID(as_uuid=True)


def _audit():
    return [sa.Column("organization_id", U, nullable=False), sa.Column("created_by_principal_id", U, nullable=False), sa.Column("updated_by_principal_id", U, nullable=False), sa.Column("id", U, primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_principal_id"], ["principals.id"], ondelete="RESTRICT")]


def upgrade():
    op.create_table("netpay_case_types", sa.Column("semantic_key", sa.String(64), nullable=False), sa.Column("display_name", sa.String(128), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("allowed_products", postgresql.JSONB(), nullable=False), sa.Column("default_template_version", sa.Integer()), sa.Column("completion_policy", postgresql.JSONB(), nullable=False), *_audit(), sa.UniqueConstraint("organization_id", "semantic_key", name="uq_netpay_case_types_org_key"))
    op.create_table("netpay_checklist_templates", sa.Column("case_type_key", sa.String(64), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("product", sa.String(32)), sa.Column("requirements", postgresql.JSONB(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), *_audit(), sa.UniqueConstraint("organization_id", "case_type_key", "version", name="uq_netpay_templates_org_type_version"))
    op.create_table("netpay_inbox_cases", sa.Column("folio", sa.String(64), nullable=False), sa.Column("client_id", U, nullable=False), sa.Column("company_id", U, nullable=False), sa.Column("branch_id", U), sa.Column("store_reference_id", U), sa.Column("case_type_key", sa.String(64), nullable=False), sa.Column("original_description", sa.Text(), nullable=False), sa.Column("expected_outcome", sa.Text()), sa.Column("product", sa.String(32), nullable=False), sa.Column("state", sa.String(32), nullable=False, server_default="received"), sa.Column("priority", sa.String(16), nullable=False, server_default="normal"), sa.Column("responsible_principal_id", U), sa.Column("target_date", sa.DateTime(timezone=True)), sa.Column("source_channel", sa.String(64)), sa.Column("source_reference", sa.String(255)), sa.Column("provenance", postgresql.JSONB(), nullable=False), sa.Column("checklist_template_version", sa.Integer()), *_audit(), sa.ForeignKeyConstraint(["organization_id", "client_id"], ["netpay_clients.organization_id", "netpay_clients.id"], name="fk_netpay_inbox_case_client_tenant", ondelete="RESTRICT"), sa.ForeignKeyConstraint(["organization_id", "company_id"], ["netpay_companies.organization_id", "netpay_companies.id"], name="fk_netpay_inbox_case_company_tenant", ondelete="RESTRICT"), sa.ForeignKeyConstraint(["organization_id", "branch_id"], ["netpay_branches.organization_id", "netpay_branches.id"], name="fk_netpay_inbox_case_branch_tenant", ondelete="RESTRICT"), sa.ForeignKeyConstraint(["store_reference_id"], ["netpay_store_references.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["responsible_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "folio", name="uq_netpay_inbox_cases_org_folio"), sa.CheckConstraint("state IN ('received','triage','information_pending','ready','in_progress','submitted','blocked','completed','cancelled')", name="ck_netpay_inbox_case_state"), sa.CheckConstraint("product IN ('tpv','ecommerce','mixed','not_applicable')", name="ck_netpay_inbox_case_product"), sa.CheckConstraint("priority IN ('urgent','high','normal','low')", name="ck_netpay_inbox_case_priority"))
    op.create_index("ix_netpay_inbox_cases_org_attention", "netpay_inbox_cases", ["organization_id", "state", "priority"])
    for name, extra in (("netpay_case_checklist_items", [sa.Column("template_version", sa.Integer(), nullable=False), sa.Column("requirement_key", sa.String(128), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="missing"), sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("safe_evidence_reference", sa.String(255))]), ("netpay_case_steps", [sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("description", sa.String(255), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="pending")]), ("netpay_case_next_actions", [sa.Column("description", sa.Text(), nullable=False), sa.Column("responsible_principal_id", U), sa.Column("due_date", sa.DateTime(timezone=True)), sa.Column("status", sa.String(16), nullable=False, server_default="open"), sa.Column("origin", sa.String(16), nullable=False, server_default="human"), sa.Column("provenance", postgresql.JSONB(), nullable=False)]), ("netpay_case_activities", [sa.Column("activity_type", sa.String(64), nullable=False), sa.Column("safe_summary", sa.Text(), nullable=False), sa.Column("correlation_id", U), sa.Column("causation_id", U)]), ("netpay_case_document_references", [sa.Column("document_id", U), sa.Column("document_version_id", U), sa.Column("external_evidence_reference", sa.String(255)), sa.Column("status", sa.String(32), nullable=False, server_default="pending")])):
        op.create_table(name, sa.Column("case_id", U, nullable=False), *extra, *_audit(), sa.ForeignKeyConstraint(["case_id"], ["netpay_inbox_cases.id"], ondelete="CASCADE"))
        op.create_index(f"ix_{name}_case_id", name, ["case_id"])
    op.create_index("uq_netpay_case_next_action_open", "netpay_case_next_actions", ["case_id"], unique=True, postgresql_where=sa.text("status = 'open'"))
    op.create_table("netpay_inbox_command_receipts", sa.Column("command_id", U, primary_key=True), sa.Column("organization_id", U, nullable=False), sa.Column("command_type", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("actor_principal_id", U, nullable=False), sa.Column("correlation_id", U, nullable=False), sa.Column("result_resource_id", U, nullable=False), sa.Column("result_status_code", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["actor_principal_id"], ["principals.id"], ondelete="RESTRICT"), sa.UniqueConstraint("organization_id", "command_type", "idempotency_key", name="uq_netpay_inbox_receipts_org_command_key"))


def downgrade():
    op.drop_table("netpay_inbox_command_receipts")
    op.drop_index("uq_netpay_case_next_action_open", table_name="netpay_case_next_actions")
    for name in ("netpay_case_document_references", "netpay_case_activities", "netpay_case_next_actions", "netpay_case_steps", "netpay_case_checklist_items"):
        op.drop_index(f"ix_{name}_case_id", table_name=name)
        op.drop_table(name)
    op.drop_index("ix_netpay_inbox_cases_org_attention", table_name="netpay_inbox_cases")
    op.drop_table("netpay_inbox_cases")
    op.drop_table("netpay_checklist_templates")
    op.drop_table("netpay_case_types")
