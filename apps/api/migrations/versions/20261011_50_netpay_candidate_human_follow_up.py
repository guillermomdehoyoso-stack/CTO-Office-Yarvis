"""Add append-only Netpay candidate human follow-up chronology.

Revision ID: 20261011_50
Revises: 20261008_49
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261011_50"
down_revision: str | None = "20261008_49"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

U = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "netpay_candidate_human_follow_ups",
        sa.Column("id", U, nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("candidate_id", U, nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("provenance_kind", sa.String(length=32), server_default="operator_reported", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["candidate_id"], ["netpay_intake_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "kind IN ('meeting','call','agreement','pending_item','general_follow_up')",
            name="ck_netpay_candidate_follow_ups_kind",
        ),
        sa.CheckConstraint("provenance_kind = 'operator_reported'", name="ck_netpay_candidate_follow_ups_provenance"),
    )
    op.create_index(
        "ix_netpay_candidate_follow_ups_org_candidate_recorded",
        "netpay_candidate_human_follow_ups",
        ["organization_id", "candidate_id", "recorded_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_netpay_candidate_follow_ups_org_candidate_recorded", table_name="netpay_candidate_human_follow_ups"
    )
    op.drop_table("netpay_candidate_human_follow_ups")
