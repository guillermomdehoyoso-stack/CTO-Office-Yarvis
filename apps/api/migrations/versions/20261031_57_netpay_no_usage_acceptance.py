"""IG-016A C2 checkpoint, acceptance and readback only."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261031_57"
down_revision = "20261030_56"
branch_labels = None
depends_on = None


def _identity_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
    ]


def upgrade():
    op.create_table("netpay_no_usage_checkpoints", *_identity_columns(), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("contract_version", sa.String(16), nullable=False), sa.Column("preview_digest", sa.String(64), nullable=False), sa.Column("payload_fingerprint", sa.String(64), nullable=False), sa.Column("decision", sa.String(16), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("consumed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("netpay_no_usage_batches", *_identity_columns(), sa.Column("checkpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_no_usage_checkpoints.id"), nullable=False), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("source_set_fingerprint", sa.String(64), nullable=False), sa.Column("preview_digest", sa.String(64), nullable=False), sa.Column("status", sa.String(16), nullable=False), sa.Column("aggregate_version", sa.Integer, nullable=False, server_default="1"), sa.Column("counts", postgresql.JSONB, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("organization_id", "source_set_fingerprint", name="uq_no_usage_batch_source_set"))
    op.create_table("netpay_no_usage_sources", *_identity_columns(), sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_no_usage_batches.id"), nullable=False), sa.Column("profile", sa.String(80), nullable=False), sa.Column("profile_version", sa.String(16), nullable=False), sa.Column("source_hash", sa.String(64), nullable=False), sa.Column("sheet", sa.String(64), nullable=False), sa.Column("structural_signature", sa.String(64), nullable=False), sa.UniqueConstraint("batch_id", "profile", name="uq_no_usage_source_profile"))
    op.create_table("netpay_no_usage_exceptions", *_identity_columns(), sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_no_usage_batches.id"), nullable=False), sa.Column("classification", sa.String(48), nullable=False), sa.Column("item_count", sa.Integer, nullable=False), sa.UniqueConstraint("batch_id", "classification", name="uq_no_usage_exception_class"))
    op.create_table("netpay_no_usage_history", *_identity_columns(), sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_no_usage_batches.id"), nullable=False), sa.Column("aggregate_version", sa.Integer, nullable=False), sa.Column("action", sa.String(32), nullable=False), sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("safe_snapshot", postgresql.JSONB, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("batch_id", "aggregate_version", name="uq_no_usage_history_version"))
    op.create_table("netpay_no_usage_receipts", *_identity_columns(), sa.Column("idempotency_key", sa.String(255), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_no_usage_batches.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_no_usage_receipt_key"))
    op.execute("CREATE FUNCTION netpay_no_usage_history_append_only_guard() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'netpay_no_usage_history is append-only'; END; $$ LANGUAGE plpgsql;")
    op.execute("CREATE TRIGGER trg_netpay_no_usage_history_append_only BEFORE UPDATE OR DELETE ON netpay_no_usage_history FOR EACH ROW EXECUTE FUNCTION netpay_no_usage_history_append_only_guard();")


def downgrade():
    op.execute("DROP TRIGGER trg_netpay_no_usage_history_append_only ON netpay_no_usage_history")
    op.execute("DROP FUNCTION netpay_no_usage_history_append_only_guard()")
    for table in ("netpay_no_usage_receipts", "netpay_no_usage_history", "netpay_no_usage_exceptions", "netpay_no_usage_sources", "netpay_no_usage_batches", "netpay_no_usage_checkpoints"):
        op.drop_table(table)
