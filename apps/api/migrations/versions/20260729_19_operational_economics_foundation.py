"""Operational Economics append-only foundation.

Revision ID: 20260729_19
Revises: 20260728_18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260729_19"
down_revision = "20260728_18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "economic_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fact_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("actor_subject_id", sa.String(length=255), nullable=False),
        sa.Column("authority_scope", sa.String(length=100), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("supersedes_fact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correction_reason", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.UniqueConstraint("id", "organization_id", name="uq_economic_facts_id_organization"),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_economic_facts_org_idempotency"),
        sa.ForeignKeyConstraint(["supersedes_fact_id", "organization_id"], ["economic_facts.id", "economic_facts.organization_id"], name="fk_economic_facts_supersedes_organization"),
        sa.CheckConstraint("fact_type IN ('revenue_expected', 'revenue_contracted', 'cost_estimated', 'cost_committed', 'cost_incurred', 'labor_cost', 'cash_in', 'cash_out', 'cost_to_complete')", name="ck_economic_facts_fact_type"),
        sa.CheckConstraint("subject_type IN ('project', 'mission_work_item', 'process_instance', 'task')", name="ck_economic_facts_subject_type"),
        sa.CheckConstraint("amount > 0", name="ck_economic_facts_amount_positive"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_economic_facts_currency_iso"),
    )
    op.create_index("ix_economic_facts_org_subject_effective", "economic_facts", ["organization_id", "subject_type", "subject_id", "effective_at"])
    op.create_index("ix_economic_facts_org_subject_type", "economic_facts", ["organization_id", "subject_type", "subject_id", "fact_type"])
    op.create_index("ix_economic_facts_org_supersedes", "economic_facts", ["organization_id", "supersedes_fact_id"])
    op.execute("""
        CREATE FUNCTION economic_facts_append_only_guard() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'economic_facts are append-only'; END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER economic_facts_append_only
        BEFORE UPDATE OR DELETE ON economic_facts
        FOR EACH ROW EXECUTE FUNCTION economic_facts_append_only_guard();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER economic_facts_append_only ON economic_facts")
    op.execute("DROP FUNCTION economic_facts_append_only_guard()")
    op.drop_table("economic_facts")
