"""Add immutable response snapshots to Netpay Inbox receipts.

Revision ID: 20260814_39
Revises: f2e7734c41f3
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260814_39"
down_revision = "f2e7734c41f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "netpay_inbox_command_receipts",
        sa.Column("result_response_body", postgresql.JSONB(), nullable=True),
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM netpay_inbox_command_receipts
                WHERE result_response_body IS NULL
            ) THEN
                RAISE EXCEPTION
                    'cannot add Inbox response snapshots: existing receipt body is not reconstructible';
            END IF;
        END
        $$
        """
    )
    op.alter_column(
        "netpay_inbox_command_receipts",
        "result_response_body",
        existing_type=postgresql.JSONB(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("netpay_inbox_command_receipts", "result_response_body")
