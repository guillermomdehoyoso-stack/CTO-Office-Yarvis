"""Netpay operational radar persistence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260806_31"
down_revision = "20260805_30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("radar_merchants", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", sa.String(100), nullable=False), sa.Column("trade_name", sa.String(255), nullable=False), sa.Column("legal_name", sa.String(255)), sa.Column("store_id", sa.String(100)), sa.Column("contact_name", sa.String(255)), sa.Column("email", sa.String(320)), sa.Column("phone", sa.String(40)), sa.Column("products", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("workspace_id", "store_id", name="uq_radar_merchants_workspace_store"))
    op.create_index("ix_radar_merchants_workspace_id", "radar_merchants", ["workspace_id"])
    op.create_table("radar_requests", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", sa.String(100), nullable=False), sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("radar_merchants.id"), nullable=False), sa.Column("free_text", sa.Text(), nullable=False), sa.Column("classification", sa.String(40), nullable=False), sa.Column("status", sa.String(16), nullable=False), sa.Column("priority", sa.String(16), nullable=False), sa.Column("owner", sa.String(255)), sa.Column("next_action", sa.Text()), sa.Column("due_at", sa.DateTime(timezone=True)), sa.Column("closed_at", sa.DateTime(timezone=True)), sa.Column("close_reason", sa.Text()), sa.Column("idempotency_key", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.CheckConstraint("status IN ('open', 'closed')", name="ck_radar_requests_status"), sa.CheckConstraint("priority IN ('low', 'normal', 'high')", name="ck_radar_requests_priority"), sa.UniqueConstraint("workspace_id", "idempotency_key", name="uq_radar_requests_workspace_idempotency"))
    for column in ("workspace_id", "merchant_id", "classification", "status", "priority", "due_at"):
        op.create_index("ix_radar_requests_" + column, "radar_requests", [column])
    op.create_table("radar_checklist_items", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("radar_requests.id"), nullable=False), sa.Column("item_code", sa.String(80), nullable=False), sa.Column("label", sa.String(255), nullable=False), sa.Column("required", sa.Boolean(), nullable=False), sa.Column("received", sa.Boolean(), nullable=False), sa.Column("received_by", sa.String(255)), sa.Column("received_at", sa.DateTime(timezone=True)), sa.Column("position", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("request_id", "item_code", name="uq_radar_checklist_request_code"))
    op.create_index("ix_radar_checklist_items_request_id", "radar_checklist_items", ["request_id"])
    op.create_table("radar_activities", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", sa.String(100), nullable=False), sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("radar_merchants.id"), nullable=False), sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("radar_requests.id")), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("actor", sa.String(255), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    for column in ("workspace_id", "merchant_id", "request_id", "occurred_at"):
        op.create_index("ix_radar_activities_" + column, "radar_activities", [column])
    op.execute("""
      CREATE FUNCTION protect_radar_activity_history() RETURNS trigger AS $$
      BEGIN RAISE EXCEPTION 'radar activities are append-only'; END; $$ LANGUAGE plpgsql;
      CREATE TRIGGER trg_radar_activity_history BEFORE UPDATE OR DELETE ON radar_activities
      FOR EACH ROW EXECUTE FUNCTION protect_radar_activity_history();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_radar_activity_history ON radar_activities")
    op.execute("DROP FUNCTION IF EXISTS protect_radar_activity_history()")
    op.drop_table("radar_activities")
    op.drop_table("radar_checklist_items")
    op.drop_table("radar_requests")
    op.drop_table("radar_merchants")
