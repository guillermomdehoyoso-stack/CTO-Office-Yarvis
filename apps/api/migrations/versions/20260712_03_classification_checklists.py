"""classification and configurable checklists

Revision ID: 20260712_03
Revises: 20260712_02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260712_03"
down_revision = "20260712_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    stamp = sa.DateTime(timezone=True)
    op.create_table("case_types", sa.Column("id", uuid, primary_key=True), sa.Column("code", sa.String(100), nullable=False, unique=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text), sa.Column("active", sa.Boolean, nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False))
    op.create_table("document_types", sa.Column("id", uuid, primary_key=True), sa.Column("code", sa.String(100), nullable=False, unique=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text), sa.Column("validity_days", sa.Integer), sa.Column("active", sa.Boolean, nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False))
    op.add_column("cases", sa.Column("case_type_id", uuid, nullable=True))
    op.create_foreign_key("fk_cases_case_type_id", "cases", "case_types", ["case_type_id"], ["id"])
    op.create_index("ix_cases_case_type_id", "cases", ["case_type_id"])
    op.create_table("checklist_templates", sa.Column("id", uuid, primary_key=True), sa.Column("case_type_id", uuid, sa.ForeignKey("case_types.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("version", sa.Integer, nullable=False), sa.Column("active", sa.Boolean, nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("case_type_id", "version", name="uq_checklist_template_version"))
    op.create_table("checklist_requirements", sa.Column("id", uuid, primary_key=True), sa.Column("checklist_template_id", uuid, sa.ForeignKey("checklist_templates.id"), nullable=False), sa.Column("code", sa.String(100), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text), sa.Column("document_type_id", uuid, sa.ForeignKey("document_types.id")), sa.Column("required", sa.Boolean, nullable=False), sa.Column("multiple_allowed", sa.Boolean, nullable=False), sa.Column("display_order", sa.Integer, nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("checklist_template_id", "code", name="uq_checklist_requirement_code"))
    op.create_table("case_checklists", sa.Column("id", uuid, primary_key=True), sa.Column("case_id", uuid, sa.ForeignKey("cases.id"), nullable=False), sa.Column("checklist_template_id", uuid, sa.ForeignKey("checklist_templates.id"), nullable=False), sa.Column("template_version", sa.Integer, nullable=False), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("case_id", "checklist_template_id", "template_version", name="uq_case_checklist_template_version"))
    op.create_table("requirement_fulfillments", sa.Column("id", uuid, primary_key=True), sa.Column("case_checklist_id", uuid, sa.ForeignKey("case_checklists.id"), nullable=False), sa.Column("checklist_requirement_id", uuid, sa.ForeignKey("checklist_requirements.id"), nullable=False), sa.Column("intake_item_id", uuid, sa.ForeignKey("intake_items.id")), sa.Column("evidence_id", uuid, sa.ForeignKey("evidence.id")), sa.Column("status", sa.String(50), nullable=False), sa.Column("notes", sa.Text), sa.Column("validated_at", stamp), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("status IN ('missing','received','under_review','valid','rejected','expired','not_applicable')", name="ck_fulfillment_status"), sa.CheckConstraint("status NOT IN ('received','under_review','valid','rejected','expired') OR intake_item_id IS NOT NULL OR evidence_id IS NOT NULL", name="ck_fulfillment_reference"), sa.CheckConstraint("status <> 'not_applicable' OR notes IS NOT NULL", name="ck_fulfillment_notes"))
    op.create_table("intake_classifications", sa.Column("id", uuid, primary_key=True), sa.Column("intake_item_id", uuid, sa.ForeignKey("intake_items.id"), nullable=False), sa.Column("document_type_id", uuid, sa.ForeignKey("document_types.id")), sa.Column("evidence_type", sa.String(50)), sa.Column("proposed_case_type_id", uuid, sa.ForeignKey("case_types.id")), sa.Column("confidence", sa.Integer), sa.Column("status", sa.String(50), nullable=False), sa.Column("confirmed_by", sa.String(255)), sa.Column("confirmed_at", stamp), sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("status IN ('proposed','confirmed','rejected')", name="ck_classification_status"), sa.CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 100", name="ck_classification_confidence"))
    for table, column in (("checklist_templates", "case_type_id"), ("checklist_requirements", "checklist_template_id"), ("case_checklists", "case_id"), ("requirement_fulfillments", "case_checklist_id"), ("requirement_fulfillments", "checklist_requirement_id"), ("intake_classifications", "intake_item_id")):
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    op.drop_table("intake_classifications"); op.drop_table("requirement_fulfillments"); op.drop_table("case_checklists"); op.drop_table("checklist_requirements"); op.drop_table("checklist_templates")
    op.drop_index("ix_cases_case_type_id", table_name="cases"); op.drop_constraint("fk_cases_case_type_id", "cases", type_="foreignkey"); op.drop_column("cases", "case_type_id")
    op.drop_table("document_types"); op.drop_table("case_types")
