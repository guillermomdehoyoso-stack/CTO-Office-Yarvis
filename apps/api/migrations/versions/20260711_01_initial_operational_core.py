"""initial operational core

Revision ID: 20260711_01
Revises:
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260711_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("organization_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legal_name"),
    )
    op.create_index("ix_organizations_legal_name", "organizations", ["legal_name"])
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("first_name IS NOT NULL OR last_name IS NOT NULL OR display_name <> ''", name="ck_people_name_present"),
    )
    op.create_index("ix_people_email", "people", ["email"])
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_number", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("case_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("owner_organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_action_summary", sa.String(length=500), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("blocked_reason", sa.String(length=500), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("blocked OR blocked_reason IS NULL", name="ck_cases_blocked_reason"),
        sa.CheckConstraint("case_type IN ('cfe', 'netpay', 'general')", name="ck_cases_case_type"),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_cases_status"),
        sa.CheckConstraint("stage IN ('intake', 'in_progress', 'complete')", name="ck_cases_stage"),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="ck_cases_priority"),
        sa.ForeignKeyConstraint(["owner_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["primary_person_id"], ["people.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number"),
    )
    op.create_index("ix_cases_case_number", "cases", ["case_number"])
    op.create_index("ix_cases_owner_organization_id", "cases", ["owner_organization_id"])
    op.create_index("ix_cases_primary_person_id", "cases", ["primary_person_id"])


def downgrade() -> None:
    op.drop_index("ix_cases_primary_person_id", table_name="cases")
    op.drop_index("ix_cases_owner_organization_id", table_name="cases")
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_table("cases")
    op.drop_index("ix_people_email", table_name="people")
    op.drop_table("people")
    op.drop_index("ix_organizations_legal_name", table_name="organizations")
    op.drop_table("organizations")
