"""Add H2-Q qualification overlay and H2-I promotion trace.

Revision ID: 20261012_51
Revises: 20261011_50
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261012_51"
down_revision: str | None = "20261011_50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
U = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "netpay_candidate_qualifications",
        sa.Column("id", U, primary_key=True),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("candidate_id", U, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("provenance_kind", sa.String(32), nullable=False, server_default="operator_reported"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["candidate_id"], ["netpay_intake_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("candidate_id", "sequence", name="uq_netpay_candidate_qualification_sequence"),
    )
    op.create_index(
        "ix_netpay_candidate_qualifications_organization_id", "netpay_candidate_qualifications", ["organization_id"]
    )
    op.create_index(
        "ix_netpay_candidate_qualifications_candidate_id", "netpay_candidate_qualifications", ["candidate_id"]
    )
    op.create_table(
        "netpay_candidate_commercial_intake_traces",
        sa.Column("id", U, primary_key=True),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("candidate_id", U, nullable=False),
        sa.Column("qualification_id", U, nullable=False),
        sa.Column("commercial_intake_id", U, nullable=False),
        sa.Column("branch_drafts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["candidate_id"], ["netpay_intake_candidates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["qualification_id"], ["netpay_candidate_qualifications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["commercial_intake_id"], ["netpay_commercial_intake_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "candidate_id", name="uq_netpay_candidate_commercial_intake_trace"),
    )
    op.create_index(
        "ix_netpay_candidate_commercial_intake_traces_organization_id",
        "netpay_candidate_commercial_intake_traces",
        ["organization_id"],
    )
    op.drop_constraint("ck_netpay_commercial_intake_product", "netpay_commercial_intake_items", type_="check")
    op.create_check_constraint(
        "ck_netpay_commercial_intake_product",
        "netpay_commercial_intake_items",
        "product_interest IN ('tpv','ecommerce','mixed','other')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_netpay_commercial_intake_product", "netpay_commercial_intake_items", type_="check")
    op.create_check_constraint(
        "ck_netpay_commercial_intake_product",
        "netpay_commercial_intake_items",
        "product_interest IN ('tpv','ecommerce','other')",
    )
    op.drop_table("netpay_candidate_commercial_intake_traces")
    op.drop_table("netpay_candidate_qualifications")
