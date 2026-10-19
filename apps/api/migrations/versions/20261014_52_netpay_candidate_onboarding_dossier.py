"""Add approved H2-D candidate onboarding dossier.

Revision ID: 20261014_52
Revises: 20261012_51
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261014_52"
down_revision: str | None = "20261012_51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
U = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "netpay_candidate_onboarding_dossiers",
        sa.Column("id", U, primary_key=True),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("candidate_id", U, nullable=False),
        sa.Column("commercial_intake_id", U, nullable=False),
        sa.Column("qualification_id", U, nullable=False),
        sa.Column("catalog_version", sa.String(32), nullable=False),
        sa.Column("catalog_effective_date", sa.String(10), nullable=False),
        sa.Column("catalog_sha256", sa.String(64), nullable=False),
        sa.Column("catalog_owner", sa.String(255), nullable=False),
        sa.Column("applicant_kind", sa.String(32), nullable=False),
        sa.Column("products", postgresql.JSONB(), nullable=False),
        sa.Column("branch_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("requirement_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["candidate_id"], ["netpay_intake_candidates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["commercial_intake_id"], ["netpay_commercial_intake_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["qualification_id"], ["netpay_candidate_qualifications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "candidate_id", name="uq_netpay_candidate_onboarding_dossier"),
    )
    op.create_index(
        "ix_netpay_candidate_onboarding_dossiers_organization_id",
        "netpay_candidate_onboarding_dossiers",
        ["organization_id"],
    )
    op.create_table(
        "netpay_dossier_evidence_references",
        sa.Column("id", U, primary_key=True),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("dossier_id", U, nullable=False),
        sa.Column("source_item_id", U, nullable=False),
        sa.Column("attachment_index", sa.Integer(), nullable=False),
        sa.Column("metadata_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("suggestion", sa.String(128)),
        sa.Column("verification", sa.String(32), server_default="unverified", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dossier_id"], ["netpay_candidate_onboarding_dossiers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_item_id"], ["netpay_gmail_source_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("attachment_index >= 0", name="ck_netpay_dossier_evidence_attachment_index"),
        sa.CheckConstraint("verification = 'unverified'", name="ck_netpay_dossier_evidence_verification"),
        sa.UniqueConstraint(
            "dossier_id", "source_item_id", "attachment_index", name="uq_netpay_dossier_evidence_metadata"
        ),
    )
    op.create_index(
        "ix_netpay_dossier_evidence_references_organization_id",
        "netpay_dossier_evidence_references",
        ["organization_id"],
    )
    op.create_table(
        "netpay_dossier_requirement_reviews",
        sa.Column("id", U, primary_key=True),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("dossier_id", U, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("requirement_snapshot_key", sa.String(255), nullable=False),
        sa.Column("prior_state", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("evidence_reference_id", U),
        sa.Column("review_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("comment", sa.String(1000)),
        sa.Column("provenance_kind", sa.String(32), server_default="operator_reported", nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_principal_id", U, nullable=False),
        sa.Column("correlation_id", U, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dossier_id"], ["netpay_candidate_onboarding_dossiers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["evidence_reference_id"], ["netpay_dossier_evidence_references.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by_principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "prior_state IN ('pending','attachment_detected','under_review','validated','observed','not_applicable')",
            name="ck_netpay_dossier_requirement_prior_state",
        ),
        sa.CheckConstraint(
            "state IN ('pending','attachment_detected','under_review','validated','observed','not_applicable')",
            name="ck_netpay_dossier_requirement_review_state",
        ),
        sa.CheckConstraint("provenance_kind = 'operator_reported'", name="ck_netpay_dossier_review_provenance"),
        sa.UniqueConstraint("dossier_id", "sequence", name="uq_netpay_dossier_review_sequence"),
    )
    op.create_index(
        "ix_netpay_dossier_requirement_reviews_organization_id",
        "netpay_dossier_requirement_reviews",
        ["organization_id"],
    )
    op.create_index(
        "ix_netpay_dossier_reviews_dossier_recorded",
        "netpay_dossier_requirement_reviews",
        ["dossier_id", "recorded_at", "id"],
    )
    op.execute("""
        CREATE FUNCTION netpay_h2d_reject_mutation() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'H2-D records are append-only'; END;
        $$ LANGUAGE plpgsql;
    """)
    for table in (
        "netpay_candidate_onboarding_dossiers",
        "netpay_dossier_evidence_references",
        "netpay_dossier_requirement_reviews",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION netpay_h2d_reject_mutation()"
        )


def downgrade() -> None:
    for table in (
        "netpay_dossier_requirement_reviews",
        "netpay_dossier_evidence_references",
        "netpay_candidate_onboarding_dossiers",
    ):
        op.execute(f"DROP TRIGGER trg_{table}_append_only ON {table}")
    op.execute("DROP FUNCTION netpay_h2d_reject_mutation")
    op.drop_table("netpay_dossier_requirement_reviews")
    op.drop_table("netpay_dossier_evidence_references")
    op.drop_table("netpay_candidate_onboarding_dossiers")
