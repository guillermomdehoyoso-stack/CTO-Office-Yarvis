"""netpay provenance and document intelligence

Revision ID: 20260714_07
Revises: 20260713_06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260714_07"
down_revision = "20260713_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("netpay_service_cases", sa.Column("physical_destination_resolution_source", sa.String(length=50), nullable=True))
    op.add_column("netpay_service_cases", sa.Column("physical_destination_resolution_confidence", sa.Float(), nullable=False, server_default=sa.text("0")))
    op.add_column("netpay_service_cases", sa.Column("attachments_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("netpay_service_cases", sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("netpay_service_cases", sa.Column("operational_resolution", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))

    op.add_column("netpay_shipments", sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))


def downgrade() -> None:
    op.drop_column("netpay_shipments", "extracted_fields")
    op.drop_column("netpay_service_cases", "operational_resolution")
    op.drop_column("netpay_service_cases", "extracted_fields")
    op.drop_column("netpay_service_cases", "attachments_metadata")
    op.drop_column("netpay_service_cases", "physical_destination_resolution_confidence")
    op.drop_column("netpay_service_cases", "physical_destination_resolution_source")
