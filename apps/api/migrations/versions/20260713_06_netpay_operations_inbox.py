"""netpay operations inbox

Revision ID: 20260713_06
Revises: 20260712_05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260713_06"
down_revision = "20260712_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    stamp = sa.DateTime(timezone=True)

    op.create_table(
        "netpay_service_cases",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("folio", sa.String(length=100), nullable=False),
        sa.Column("received_at", stamp, nullable=False),
        sa.Column("case_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source_email_id", sa.String(length=255), nullable=True),
        sa.Column("source_thread_id", sa.String(length=255), nullable=True),
        sa.Column("source_subject", sa.String(length=500), nullable=False),
        sa.Column("source_sender", sa.String(length=320), nullable=True),
        sa.Column("source_intake_item_id", uuid, sa.ForeignKey("intake_items.id"), nullable=True),
        sa.Column("sent_at", stamp, nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("store_id", sa.String(length=100), nullable=True),
        sa.Column("device_serial", sa.String(length=100), nullable=True),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("investigation_status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("to_addresses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cc_addresses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reply_to_addresses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("delivered_to", sa.String(length=320), nullable=True),
        sa.Column("x_original_to", sa.String(length=320), nullable=True),
        sa.Column("original_recipient", sa.String(length=320), nullable=True),
        sa.Column("recipient_addresses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("operational_recipient", sa.String(length=320), nullable=True),
        sa.Column("recipient_resolution_source", sa.String(length=50), nullable=True),
        sa.Column("recipient_resolution_confidence", sa.Float(), nullable=False),
        sa.Column("body_normalized", sa.Text(), nullable=True),
        sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("folio", name="uq_netpay_service_case_folio"),
        sa.UniqueConstraint("source_email_id", name="uq_netpay_service_case_source_email"),
    )
    op.create_index("ix_netpay_service_cases_folio", "netpay_service_cases", ["folio"])
    op.create_index("ix_netpay_service_cases_source_email_id", "netpay_service_cases", ["source_email_id"])
    op.create_index("ix_netpay_service_cases_source_intake_item_id", "netpay_service_cases", ["source_intake_item_id"])

    op.create_table(
        "netpay_shipments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("service_case_id", uuid, sa.ForeignKey("netpay_service_cases.id"), nullable=False),
        sa.Column("tracking_number", sa.String(length=120), nullable=False),
        sa.Column("carrier", sa.String(length=120), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("shipped_at", stamp, nullable=True),
        sa.Column("delivered_at", stamp, nullable=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        sa.Column("receiver_company", sa.String(length=255), nullable=True),
        sa.Column("branch", sa.String(length=255), nullable=True),
        sa.Column("address_full", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("folio", sa.String(length=100), nullable=True),
        sa.Column("store_id", sa.String(length=100), nullable=True),
        sa.Column("device_serial", sa.String(length=100), nullable=True),
        sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_netpay_shipments_service_case_id", "netpay_shipments", ["service_case_id"])
    op.create_index("ix_netpay_shipments_tracking_number", "netpay_shipments", ["tracking_number"])

    op.create_table(
        "netpay_device_assignments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("device_serial", sa.String(length=100), nullable=False),
        sa.Column("store_id", sa.String(length=100), nullable=True),
        sa.Column("organization_id", uuid, sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("assigned_at", stamp, nullable=True),
        sa.Column("returned_at", stamp, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("service_case_id", uuid, sa.ForeignKey("netpay_service_cases.id"), nullable=True),
        sa.Column("created_at", stamp, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", stamp, server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_netpay_device_assignments_device_serial", "netpay_device_assignments", ["device_serial"])
    op.create_index("ix_netpay_device_assignments_store_id", "netpay_device_assignments", ["store_id"])
    op.create_index("ix_netpay_device_assignments_organization_id", "netpay_device_assignments", ["organization_id"])
    op.create_index("ix_netpay_device_assignments_service_case_id", "netpay_device_assignments", ["service_case_id"])


def downgrade() -> None:
    op.drop_table("netpay_device_assignments")
    op.drop_table("netpay_shipments")
    op.drop_table("netpay_service_cases")
