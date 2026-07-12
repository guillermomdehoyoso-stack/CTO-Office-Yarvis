"""document review validity and operational alerts

Revision ID: 20260712_04
Revises: 20260712_03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260712_04"
down_revision = "20260712_03"
branch_labels = None
depends_on = None

def upgrade() -> None:
    stamp = sa.DateTime(timezone=True); uuid = postgresql.UUID(as_uuid=True)
    for name, type_ in (("document_date", stamp), ("valid_from", stamp), ("valid_until", stamp), ("reviewed_by", sa.String(255)), ("reviewed_at", stamp), ("rejection_reason", sa.Text()), ("expiration_evaluated_at", stamp)):
        op.add_column("requirement_fulfillments", sa.Column(name, type_, nullable=True))
    op.create_index("ix_requirement_fulfillments_valid_until", "requirement_fulfillments", ["valid_until"])
    op.create_table("operational_alerts", sa.Column("id", uuid, primary_key=True), sa.Column("case_id", uuid, sa.ForeignKey("cases.id"), nullable=False), sa.Column("alert_type", sa.String(50), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text, nullable=False), sa.Column("source_entity_type", sa.String(100), nullable=False), sa.Column("source_entity_id", uuid, nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("due_at", stamp), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("resolved_at", stamp), sa.Column("resolution_note", sa.Text), sa.UniqueConstraint("case_id", "alert_type", "source_entity_type", "source_entity_id", name="uq_operational_alert_source"))
    op.create_index("ix_operational_alerts_case_id", "operational_alerts", ["case_id"])
    op.create_table("next_action_suggestions", sa.Column("id", uuid, primary_key=True), sa.Column("case_id", uuid, sa.ForeignKey("cases.id"), nullable=False), sa.Column("action_type", sa.String(100), nullable=False), sa.Column("summary", sa.String(500), nullable=False), sa.Column("rationale", sa.Text, nullable=False), sa.Column("source_alert_id", uuid, sa.ForeignKey("operational_alerts.id")), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("dismissed_at", stamp), sa.Column("completed_at", stamp), sa.UniqueConstraint("case_id", "action_type", "source_alert_id", name="uq_next_action_source"))
    op.create_index("ix_next_action_suggestions_case_id", "next_action_suggestions", ["case_id"])

def downgrade() -> None:
    op.drop_table("next_action_suggestions"); op.drop_table("operational_alerts")
    op.drop_index("ix_requirement_fulfillments_valid_until", table_name="requirement_fulfillments")
    for name in ("expiration_evaluated_at", "rejection_reason", "reviewed_at", "reviewed_by", "valid_until", "valid_from", "document_date"): op.drop_column("requirement_fulfillments", name)
