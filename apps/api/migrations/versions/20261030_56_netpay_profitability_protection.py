"""IG-016 Gates A/B equipment identity and evidence only."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261030_56"
down_revision = "20261028_55"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "netpay_equipment_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("identity_kind", sa.String(16), nullable=False),
        sa.Column("original_value", sa.String(255), nullable=False),
        sa.Column("normalized_value", sa.String(255), nullable=False),
        sa.Column("normalization_method", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("identity_kind IN ('terminal','mid','serial')", name="ck_netpay_equipment_identity_kind"),
        sa.UniqueConstraint("organization_id", "id", name="uq_netpay_equipment_identity_org_id"),
        sa.UniqueConstraint(
            "organization_id", "identity_kind", "normalized_value", name="uq_netpay_equipment_identity_value"
        ),
    )
    op.create_table(
        "netpay_equipment_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_profile", sa.String(64), nullable=False),
        sa.Column("source_batch_reference", sa.String(255), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("source_sheet", sa.String(255), nullable=False),
        sa.Column("source_row_reference", sa.String(64), nullable=False),
        sa.Column("observed_period", sa.String(16)),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
        sa.Column("original_value", sa.String(255), nullable=False),
        sa.Column("normalized_value", sa.String(255), nullable=False),
        sa.Column("normalization_method", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["organization_id", "identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        sa.UniqueConstraint(
            "organization_id",
            "source_hash",
            "source_sheet",
            "source_row_reference",
            "identity_id",
            name="uq_netpay_equipment_evidence_source",
        ),
    )
    op.create_table(
        "netpay_store_equipment_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "store_reference_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("netpay_store_references.id", ondelete="RESTRICT"),
        ),
        sa.Column("terminal_identity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("mid_identity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("serial_identity_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_equipment_evidence.id"), nullable=False
        ),
        sa.Column("candidate_store_reference_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
        sa.Column("resolution_status", sa.String(20), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "predecessor_link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_store_equipment_links.id")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "resolution_status IN ('pending','confirmed','ambiguous','contradictory','superseded')",
            name="ck_netpay_equipment_link_status",
        ),
        sa.CheckConstraint(
            "terminal_identity_id IS NOT NULL OR mid_identity_id IS NOT NULL OR serial_identity_id IS NOT NULL",
            name="ck_netpay_equipment_link_identity",
        ),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_netpay_equipment_link_dates"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "terminal_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "mid_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "serial_identity_id"],
            ["netpay_equipment_identities.organization_id", "netpay_equipment_identities.id"],
        ),
    )
    op.create_index(
        "ix_netpay_equipment_link_org_store", "netpay_store_equipment_links", ["organization_id", "store_reference_id"]
    )
    op.create_index(
        "ix_netpay_equipment_link_org_serial",
        "netpay_store_equipment_links",
        ["organization_id", "serial_identity_id", "valid_from", "valid_to"],
    )
    op.create_table(
        "netpay_equipment_identity_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_store_equipment_links.id"), nullable=False
        ),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("prior_status", sa.String(20)),
        sa.Column("resulting_status", sa.String(20), nullable=False),
        sa.Column("decision_reason", sa.String(255), nullable=False),
        sa.Column("evidence_reference", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("link_id", "aggregate_version", name="uq_netpay_equipment_decision_version"),
    )
    op.create_table(
        "netpay_equipment_identity_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "result_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("netpay_store_equipment_links.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_netpay_equipment_receipt_key"),
    )


def downgrade():
    op.drop_table("netpay_equipment_identity_receipts")
    op.drop_table("netpay_equipment_identity_decisions")
    op.drop_index("ix_netpay_equipment_link_org_serial", table_name="netpay_store_equipment_links")
    op.drop_index("ix_netpay_equipment_link_org_store", table_name="netpay_store_equipment_links")
    op.drop_table("netpay_store_equipment_links")
    op.drop_table("netpay_equipment_evidence")
    op.drop_table("netpay_equipment_identities")
