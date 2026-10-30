"""IG-015 additive Core v2 and settlement evidence; no historical backfill."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261028_55"
down_revision = "20261022_54"
branch_labels = None
depends_on = None
FIELDS = (
    "activation_bonus_exact",
    "referrer_commission_exact",
    "base_commission_exact",
    "commission_v2_exact",
    "combined_benefit_exact",
    "sales_v2_exact",
)


def upgrade():
    op.drop_constraint("ck_netpay_data_batch_dataset", "netpay_operational_data_batches")
    op.create_check_constraint(
        "ck_netpay_data_batch_dataset",
        "netpay_operational_data_batches",
        "dataset_type IN ('monthly_store_profitability','no_usage_campaign','commission_settlement')",
    )
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("settlement_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column("settlement_effective", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "netpay_operational_data_batches",
        sa.Column(
            "predecessor_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_operational_data_batches.id")
        ),
    )
    op.create_index(
        "uq_netpay_settlement_effective",
        "netpay_operational_data_batches",
        ["organization_id", "reporting_period"],
        unique=True,
        postgresql_where=sa.text("dataset_type = 'commission_settlement' AND settlement_effective"),
    )
    op.add_column(
        "netpay_store_profitability_facts",
        sa.Column("metric_definition_version", sa.String(48), nullable=False, server_default="legacy_as_v1"),
    )
    for field in FIELDS:
        op.add_column("netpay_store_profitability_facts", sa.Column(field, sa.Numeric(), nullable=True))


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM netpay_operational_data_batches "
            "WHERE dataset_type='commission_settlement') OR EXISTS "
            "(SELECT 1 FROM netpay_store_profitability_facts "
            "WHERE metric_definition_version <> 'legacy_as_v1')"
        )
    ):
        raise RuntimeError("IG-015 downgrade would discard evidence; migrate forward")
    for field in (*FIELDS, "metric_definition_version"):
        op.drop_column("netpay_store_profitability_facts", field)
    op.drop_index("uq_netpay_settlement_effective", table_name="netpay_operational_data_batches")
    for field in ("predecessor_batch_id", "settlement_effective", "settlement_metadata"):
        op.drop_column("netpay_operational_data_batches", field)
    op.drop_constraint("ck_netpay_data_batch_dataset", "netpay_operational_data_batches")
    op.create_check_constraint(
        "ck_netpay_data_batch_dataset",
        "netpay_operational_data_batches",
        "dataset_type IN ('monthly_store_profitability','no_usage_campaign')",
    )
