"""intake operational context association

Revision ID: 20260726_12
Revises: 20260716_11
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260726_12"
down_revision = "20260716_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "intake_items",
        sa.Column("intake_mode", sa.String(length=50), server_default="legacy", nullable=False),
    )
    op.execute(
        """
        UPDATE intake_items
        SET intake_mode = 'deterministic'
        WHERE organization_id IS NOT NULL
          AND idempotency_key IS NOT NULL
          AND idempotency_fingerprint IS NOT NULL
        """
    )
    op.create_unique_constraint(
        "uq_intake_items_id_organization_id",
        "intake_items",
        ["id", "organization_id"],
    )

    op.create_table(
        "sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_sites_id_organization_id"),
        sa.UniqueConstraint("organization_id", "reference", name="uq_sites_organization_id_reference"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_projects_id_organization_id"),
        sa.UniqueConstraint(
            "id",
            "site_id",
            "organization_id",
            name="uq_projects_id_site_id_organization_id",
        ),
        sa.UniqueConstraint("site_id", "reference", name="uq_projects_site_id_reference"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["site_id", "organization_id"],
            ["sites.id", "sites.organization_id"],
            name="fk_projects_site_org",
        ),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])
    op.create_index("ix_projects_site_id", "projects", ["site_id"])

    op.create_table(
        "connector_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connector_reference", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_connector_mappings_id_organization_id"),
        sa.UniqueConstraint(
            "id",
            "project_id",
            "organization_id",
            name="uq_connector_mappings_id_project_id_organization_id",
        ),
        sa.UniqueConstraint(
            "project_id",
            "connector_reference",
            name="uq_connector_mappings_project_id_connector_reference",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["project_id", "organization_id"],
            ["projects.id", "projects.organization_id"],
            name="fk_connector_mappings_project_org",
        ),
    )
    op.create_index("ix_connector_mappings_organization_id", "connector_mappings", ["organization_id"])
    op.create_index("ix_connector_mappings_project_id", "connector_mappings", ["project_id"])

    op.create_table(
        "intake_operational_context_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intake_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connector_mapping_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("associated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["intake_item_id", "organization_id"],
            ["intake_items.id", "intake_items.organization_id"],
            name="fk_ioca_intake_org",
        ),
        sa.ForeignKeyConstraint(
            ["site_id", "organization_id"],
            ["sites.id", "sites.organization_id"],
            name="fk_ioca_site_org",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "site_id", "organization_id"],
            ["projects.id", "projects.site_id", "projects.organization_id"],
            name="fk_ioca_project_site_org",
        ),
        sa.ForeignKeyConstraint(
            ["connector_mapping_id", "project_id", "organization_id"],
            ["connector_mappings.id", "connector_mappings.project_id", "connector_mappings.organization_id"],
            name="fk_ioca_mapping_project_org",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("intake_item_id", name="uq_intake_operational_context_associations_intake_item_id"),
        sa.UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_ioca_org_idempotency_key",
        ),
    )
    op.create_index("ix_intake_operational_context_associations_site_id", "intake_operational_context_associations", ["site_id"])
    op.create_index("ix_intake_operational_context_associations_project_id", "intake_operational_context_associations", ["project_id"])
    op.create_index(
        "ix_intake_operational_context_associations_connector_mapping_id",
        "intake_operational_context_associations",
        ["connector_mapping_id"],
    )
    op.create_index(
        "ix_intake_operational_context_associations_correlation_id",
        "intake_operational_context_associations",
        ["correlation_id"],
    )
    op.create_index(
        "ix_intake_operational_context_associations_causation_id",
        "intake_operational_context_associations",
        ["causation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_intake_operational_context_associations_causation_id", table_name="intake_operational_context_associations")
    op.drop_index("ix_intake_operational_context_associations_correlation_id", table_name="intake_operational_context_associations")
    op.drop_index("ix_intake_operational_context_associations_connector_mapping_id", table_name="intake_operational_context_associations")
    op.drop_index("ix_intake_operational_context_associations_project_id", table_name="intake_operational_context_associations")
    op.drop_index("ix_intake_operational_context_associations_site_id", table_name="intake_operational_context_associations")
    op.drop_table("intake_operational_context_associations")
    op.drop_index("ix_connector_mappings_project_id", table_name="connector_mappings")
    op.drop_index("ix_connector_mappings_organization_id", table_name="connector_mappings")
    op.drop_table("connector_mappings")
    op.drop_index("ix_projects_site_id", table_name="projects")
    op.drop_index("ix_projects_organization_id", table_name="projects")
    op.drop_table("projects")
    op.drop_table("sites")
    op.drop_constraint("uq_intake_items_id_organization_id", "intake_items", type_="unique")
    op.drop_column("intake_items", "intake_mode")
