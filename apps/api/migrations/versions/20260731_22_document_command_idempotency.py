"""DI-002B document command idempotency.

Revision ID: 20260731_22
Revises: 20260731_21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260731_22"
down_revision = "20260731_21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_command_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contract_id", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_kind", sa.String(32), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_document_command_idempotency_organization"),
        sa.UniqueConstraint("organization_id", "contract_id", "idempotency_key", name="uq_document_command_idempotency"),
        sa.CheckConstraint("char_length(request_fingerprint) = 64", name="ck_document_command_idempotency_fingerprint"),
    )


def downgrade() -> None:
    op.drop_table("document_command_idempotency")
