"""Persist the actor that ended a Document Association.

Revision ID: 20260801_23
Revises: 20260731_22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260801_23"
down_revision = "20260731_22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_associations",
        sa.Column("unlinked_by_subject_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_associations", "unlinked_by_subject_id")
