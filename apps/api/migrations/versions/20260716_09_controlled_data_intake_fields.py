"""controlled data intake document fields

Revision ID: 20260716_09
Revises: 20260716_08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260716_09"
down_revision = "20260716_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_records", sa.Column("original_filename", sa.String(length=500), nullable=True))
    op.add_column("document_records", sa.Column("detected_file_type", sa.String(length=100), nullable=True))
    op.add_column("document_records", sa.Column("detected_report_type", sa.String(length=100), nullable=True))
    op.add_column("document_records", sa.Column("classification_confidence", sa.Float(), nullable=True))
    op.add_column("document_records", sa.Column("parser_key", sa.String(length=100), nullable=True))
    op.add_column("document_records", sa.Column("parser_version", sa.String(length=50), nullable=True))
    op.add_column("document_records", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("document_records", sa.Column("row_count", sa.Integer(), nullable=True))
    op.add_column("document_records", sa.Column("observation_count", sa.Integer(), nullable=True))
    op.add_column("document_records", sa.Column("duplicate_of_document_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("document_records", sa.Column("review_status", sa.String(length=20), nullable=False, server_default="pending"))
    op.add_column("document_records", sa.Column("confirmed_by", sa.String(length=255), nullable=True))
    op.add_column("document_records", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key("fk_document_records_duplicate_of_document_id", "document_records", "document_records", ["duplicate_of_document_id"], ["id"])
    op.create_index("ix_document_records_detected_report_type", "document_records", ["detected_report_type"])
    op.create_index("ix_document_records_duplicate_of_document_id", "document_records", ["duplicate_of_document_id"])
    op.create_index("ix_document_records_review_status", "document_records", ["review_status"])
    op.create_check_constraint(
        "ck_document_records_review_status",
        "document_records",
        "review_status IN ('pending', 'preview_ready', 'confirmed', 'rejected', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_document_records_review_status", "document_records", type_="check")
    op.drop_index("ix_document_records_review_status", table_name="document_records")
    op.drop_index("ix_document_records_duplicate_of_document_id", table_name="document_records")
    op.drop_index("ix_document_records_detected_report_type", table_name="document_records")
    op.drop_constraint("fk_document_records_duplicate_of_document_id", "document_records", type_="foreignkey")

    op.drop_column("document_records", "confirmed_at")
    op.drop_column("document_records", "confirmed_by")
    op.drop_column("document_records", "review_status")
    op.drop_column("document_records", "duplicate_of_document_id")
    op.drop_column("document_records", "observation_count")
    op.drop_column("document_records", "row_count")
    op.drop_column("document_records", "processing_error")
    op.drop_column("document_records", "parser_version")
    op.drop_column("document_records", "parser_key")
    op.drop_column("document_records", "classification_confidence")
    op.drop_column("document_records", "detected_report_type")
    op.drop_column("document_records", "detected_file_type")
    op.drop_column("document_records", "original_filename")
