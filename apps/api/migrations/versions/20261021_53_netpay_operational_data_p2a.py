"""Add governed P2A metadata, exact money and explicit supersession.

Revision ID: 20261021_53
Revises: 20261014_52
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261021_53"
down_revision: str | None = "20261014_52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
U = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.drop_constraint("ck_netpay_data_batch_status", "netpay_operational_data_batches", type_="check")
    op.create_check_constraint(
        "ck_netpay_data_batch_status",
        "netpay_operational_data_batches",
        "status IN ('uploaded','validating','needs_review','metadata_pending','accepted','rejected')",
    )
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("source_profile", sa.String(64), nullable=False, server_default="legacy_d1"),
    )
    op.add_column("netpay_operational_data_batches", sa.Column("currency_code", sa.String(3)))
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("completeness_status", sa.String(16), nullable=False, server_default="partial"),
    )
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column("netpay_operational_data_batches", sa.Column("source_generated_at", sa.DateTime(timezone=True)))
    op.add_column("netpay_operational_data_batches", sa.Column("data_cutoff_at", sa.DateTime(timezone=True)))
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("source_producer", sa.String(128), nullable=False, server_default="Netpay"),
    )
    op.add_column("netpay_operational_data_batches", sa.Column("delivery_channel", sa.String(128)))

    op.add_column("netpay_store_profitability_facts", sa.Column("volume_exact", sa.Numeric(24, 8)))
    op.add_column("netpay_store_profitability_facts", sa.Column("distributor_commission_exact", sa.Numeric(24, 8)))
    op.add_column("netpay_store_profitability_facts", sa.Column("source_scale", sa.Integer()))
    op.add_column(
        "netpay_store_profitability_facts",
        sa.Column(
            "precision_classification",
            sa.String(40),
            nullable=False,
            server_default="legacy_float_precision_unverified",
        ),
    )
    op.add_column(
        "netpay_store_profitability_facts",
        sa.Column("effective_status", sa.String(16), nullable=False, server_default="effective"),
    )
    op.add_column("netpay_store_profitability_facts", sa.Column("predecessor_fact_id", U))
    op.add_column("netpay_store_profitability_facts", sa.Column("superseded_by_fact_id", U))
    op.add_column("netpay_store_profitability_facts", sa.Column("correction_reason", sa.String(255)))
    op.add_column("netpay_store_profitability_facts", sa.Column("correction_actor_principal_id", U))
    op.create_foreign_key(
        "fk_netpay_profitability_correction_actor",
        "netpay_store_profitability_facts",
        "principals",
        ["correction_actor_principal_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column(
        "netpay_store_profitability_facts",
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_foreign_key(
        "fk_netpay_profitability_predecessor",
        "netpay_store_profitability_facts",
        "netpay_store_profitability_facts",
        ["predecessor_fact_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_netpay_profitability_superseded_by",
        "netpay_store_profitability_facts",
        "netpay_store_profitability_facts",
        ["superseded_by_fact_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    for column in ("effective_status", "correction_reason"):
        definition = (
            sa.Column(
                column,
                sa.String(16 if column == "effective_status" else 255),
                nullable=False,
                server_default="effective",
            )
            if column == "effective_status"
            else sa.Column(column, sa.String(255))
        )
        op.add_column("netpay_no_usage_campaign_entries", definition)
    op.add_column("netpay_no_usage_campaign_entries", sa.Column("correction_actor_principal_id", U))
    op.create_foreign_key(
        "fk_netpay_no_usage_correction_actor",
        "netpay_no_usage_campaign_entries",
        "principals",
        ["correction_actor_principal_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("netpay_no_usage_campaign_entries", sa.Column("predecessor_entry_id", U))
    op.add_column("netpay_no_usage_campaign_entries", sa.Column("superseded_by_entry_id", U))
    op.add_column(
        "netpay_no_usage_campaign_entries",
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_foreign_key(
        "fk_netpay_no_usage_predecessor",
        "netpay_no_usage_campaign_entries",
        "netpay_no_usage_campaign_entries",
        ["predecessor_entry_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_netpay_no_usage_superseded_by",
        "netpay_no_usage_campaign_entries",
        "netpay_no_usage_campaign_entries",
        ["superseded_by_entry_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_netpay_no_usage_correction_actor", "netpay_no_usage_campaign_entries", type_="foreignkey")
    for name in ("fk_netpay_no_usage_superseded_by", "fk_netpay_no_usage_predecessor"):
        op.drop_constraint(name, "netpay_no_usage_campaign_entries", type_="foreignkey")
    for column in (
        "effective_at",
        "superseded_by_entry_id",
        "predecessor_entry_id",
        "correction_reason",
        "effective_status",
        "correction_actor_principal_id",
    ):
        op.drop_column("netpay_no_usage_campaign_entries", column)
    for name in ("fk_netpay_profitability_superseded_by", "fk_netpay_profitability_predecessor"):
        op.drop_constraint(name, "netpay_store_profitability_facts", type_="foreignkey")
    op.drop_constraint(
        "fk_netpay_profitability_correction_actor", "netpay_store_profitability_facts", type_="foreignkey"
    )
    for column in (
        "effective_at",
        "correction_reason",
        "superseded_by_fact_id",
        "predecessor_fact_id",
        "effective_status",
        "precision_classification",
        "source_scale",
        "distributor_commission_exact",
        "volume_exact",
        "correction_actor_principal_id",
    ):
        op.drop_column("netpay_store_profitability_facts", column)
    for column in (
        "delivery_channel",
        "source_producer",
        "data_cutoff_at",
        "source_generated_at",
        "received_at",
        "completeness_status",
        "currency_code",
        "source_profile",
    ):
        op.drop_column("netpay_operational_data_batches", column)
    op.drop_constraint("ck_netpay_data_batch_status", "netpay_operational_data_batches", type_="check")
    op.create_check_constraint(
        "ck_netpay_data_batch_status",
        "netpay_operational_data_batches",
        "status IN ('uploaded','validating','needs_review','accepted','rejected')",
    )
