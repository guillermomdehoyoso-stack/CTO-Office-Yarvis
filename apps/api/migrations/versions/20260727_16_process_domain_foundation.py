"""process domain foundation

Revision ID: 20260727_16
Revises: 20260727_15
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260727_16"
down_revision = "20260727_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "process_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_process_definitions_id_organization_id"),
        sa.UniqueConstraint("organization_id", "name", "version", name="uq_process_definitions_organization_name_version"),
        sa.CheckConstraint("lifecycle IN ('draft', 'published', 'retired')", name="ck_process_definitions_lifecycle"),
    )
    op.create_index("ix_process_definitions_organization_id", "process_definitions", ["organization_id"])
    op.create_index("ix_process_definitions_organization_lifecycle", "process_definitions", ["organization_id", "lifecycle"])
    op.create_table(
        "process_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stage_type", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["process_definition_id", "organization_id"],
            ["process_definitions.id", "process_definitions.organization_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "process_definition_id", "organization_id", name="uq_process_stages_id_definition_organization"),
        sa.UniqueConstraint("process_definition_id", "stage_key", name="uq_process_stages_definition_key"),
        sa.UniqueConstraint("process_definition_id", "display_order", name="uq_process_stages_definition_display_order"),
        sa.CheckConstraint("stage_type IN ('start', 'work', 'wait', 'decision', 'terminal')", name="ck_process_stages_type"),
    )
    op.create_index("ix_process_stages_organization_id", "process_stages", ["organization_id"])
    op.create_index("ix_process_stages_definition_id", "process_stages", ["process_definition_id"])
    op.create_table(
        "process_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["process_definition_id", "organization_id"],
            ["process_definitions.id", "process_definitions.organization_id"],
        ),
        sa.ForeignKeyConstraint(
            ["from_stage_id", "process_definition_id", "organization_id"],
            ["process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"],
        ),
        sa.ForeignKeyConstraint(
            ["to_stage_id", "process_definition_id", "organization_id"],
            ["process_stages.id", "process_stages.process_definition_id", "process_stages.organization_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "process_definition_id", "organization_id", name="uq_process_transitions_id_definition_organization"),
        sa.UniqueConstraint("process_definition_id", "from_stage_id", "to_stage_id", name="uq_process_transitions_definition_edge"),
    )
    op.create_index("ix_process_transitions_organization_id", "process_transitions", ["organization_id"])
    op.create_index("ix_process_transitions_definition_id", "process_transitions", ["process_definition_id"])


def downgrade() -> None:
    op.drop_table("process_transitions")
    op.drop_table("process_stages")
    op.drop_table("process_definitions")
