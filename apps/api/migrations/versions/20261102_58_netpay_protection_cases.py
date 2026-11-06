"""IG-016A C3 protection cases, history, safe receipts and access audit."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261102_58"
down_revision = "20261031_57"
branch_labels = None
depends_on = None


def _identity():
    return [sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False)]


def upgrade():
    op.create_table("netpay_protection_cases", *_identity(), sa.Column("source_kind", sa.String(24), nullable=False), sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("store_reference_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_store_references.id")), sa.Column("cause_code", sa.String(48), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("aggregate_version", sa.Integer, nullable=False, server_default="1"), sa.Column("assigned_principal_id", postgresql.UUID(as_uuid=True)), sa.Column("next_action_code", sa.String(48)), sa.Column("commitment_at", sa.DateTime(timezone=True)), sa.Column("contact_available", sa.Boolean, nullable=False, server_default=sa.false()), sa.Column("terminal_at", sa.DateTime(timezone=True)), sa.Column("supersedes_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("source_kind IN ('link','batch_exception')", name="ck_netpay_protection_source_kind"), sa.CheckConstraint("status IN ('identity_pending','contact_pending','ready_to_contact','contact_attempted','reactivation_agreed','return_requested','monitoring','escalated','unrecoverable')", name="ck_netpay_protection_status"))
    op.create_index("uq_netpay_protection_active_source_cause", "netpay_protection_cases", ["organization_id", "source_kind", "source_id", "cause_code"], unique=True, postgresql_where=sa.text("terminal_at IS NULL"))
    op.create_table("netpay_protection_case_history", *_identity(), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id"), nullable=False), sa.Column("aggregate_version", sa.Integer, nullable=False), sa.Column("prior_status", sa.String(32)), sa.Column("resulting_status", sa.String(32), nullable=False), sa.Column("action_code", sa.String(64), nullable=False), sa.Column("reason_code", sa.String(48), nullable=False), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("correlation_id", sa.String(64), nullable=False), sa.Column("causation_id", sa.String(64)), sa.Column("evidence_reference", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("case_id", "aggregate_version", name="uq_netpay_protection_history_version"))
    op.create_table("netpay_protection_command_receipts", *_identity(), sa.Column("command_id", sa.String(32), nullable=False), sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id")), sa.Column("response_body", postgresql.JSONB, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_netpay_protection_receipt_key"))
    op.create_table("netpay_protection_sensitive_access", *_identity(), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id"), nullable=False), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("purpose_code", sa.String(48), nullable=False), sa.Column("master_version", sa.String(64), nullable=False), sa.Column("opaque_reference", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.execute("CREATE FUNCTION netpay_protection_history_append_only_guard() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'netpay_protection_case_history is append-only'; END; $$ LANGUAGE plpgsql;")
    op.execute("CREATE TRIGGER trg_netpay_protection_history_append_only BEFORE UPDATE OR DELETE ON netpay_protection_case_history FOR EACH ROW EXECUTE FUNCTION netpay_protection_history_append_only_guard();")


def downgrade():
    op.execute("DROP TRIGGER trg_netpay_protection_history_append_only ON netpay_protection_case_history")
    op.execute("DROP FUNCTION netpay_protection_history_append_only_guard()")
    for table in ("netpay_protection_sensitive_access", "netpay_protection_command_receipts", "netpay_protection_case_history", "netpay_protection_cases"):
        op.drop_table(table)
