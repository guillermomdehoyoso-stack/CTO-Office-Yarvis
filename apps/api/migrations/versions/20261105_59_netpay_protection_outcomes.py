"""IG-016A C4 synthetic outcome evidence and financial assessments."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261105_59"
down_revision = "20261102_58"
branch_labels = None
depends_on = None


def _identity() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.add_column("netpay_protection_cases", sa.Column("closure_kind", sa.String(48)))
    op.add_column("netpay_protection_cases", sa.Column("closure_evidence_id", postgresql.UUID(as_uuid=True)))
    op.add_column("netpay_protection_cases", sa.Column("closure_snapshot_id", postgresql.UUID(as_uuid=True)))
    op.drop_constraint("ck_netpay_protection_status", "netpay_protection_cases", type_="check")
    op.create_check_constraint(
        "ck_netpay_protection_status",
        "netpay_protection_cases",
        "status IN ('identity_pending','contact_pending','ready_to_contact','contact_attempted',"
        "'reactivation_agreed','return_requested','monitoring','escalated','unrecoverable',"
        "'reactivation_verified','equipment_return_verified','closed')",
    )
    op.create_table(
        "netpay_protection_outcome_evidence",
        *_identity(),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id"), nullable=False),
        sa.Column("evidence_kind", sa.String(48), nullable=False),
        sa.Column("profile_version", sa.String(64), nullable=False),
        sa.Column("source_authority", sa.String(32), nullable=False),
        sa.Column("source_reference", sa.String(128), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(64), nullable=False),
        sa.Column("identity_scope", sa.String(24), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_key", sa.String(16)),
        sa.Column("amount", sa.Numeric(18, 6)),
        sa.Column("currency", sa.String(3)),
        sa.Column("supersedes_evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_outcome_evidence.id")),
        sa.Column("actor_principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("supersedes_evidence_id", name="uq_netpay_outcome_evidence_successor"),
    )
    op.create_table(
        "netpay_protection_outcome_assessments",
        *_identity(),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id"), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_outcome_evidence.id"), nullable=False),
        sa.Column("assessment_kind", sa.String(48), nullable=False),
        sa.Column("certainty", sa.String(16), nullable=False),
        sa.Column("rule_version", sa.String(48), nullable=False),
        sa.Column("supersedes_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_outcome_assessments.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("supersedes_assessment_id", name="uq_netpay_outcome_assessment_successor"),
    )
    op.create_table(
        "netpay_protection_financial_snapshots",
        *_identity(),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id"), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_outcome_evidence.id"), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_outcome_assessments.id"), nullable=False),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("certainty", sa.String(16), nullable=False),
        sa.Column("currency", sa.String(3)),
        sa.Column("amount", sa.Numeric(18, 6)),
        sa.Column("period_key", sa.String(16)),
        sa.Column("components", postgresql.JSONB, nullable=False),
        sa.Column("supersedes_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_financial_snapshots.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("supersedes_snapshot_id", name="uq_netpay_financial_snapshot_successor"),
    )
    op.create_table(
        "netpay_protection_outcome_receipts",
        *_identity(),
        sa.Column("command_id", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("netpay_protection_cases.id")),
        sa.Column("response_body", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "idempotency_key", "request_fingerprint", name="uq_netpay_outcome_receipt_attempt"
        ),
    )
    for table in (
        "netpay_protection_outcome_evidence",
        "netpay_protection_outcome_assessments",
        "netpay_protection_financial_snapshots",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION netpay_protection_history_append_only_guard();"
        )


def downgrade() -> None:
    for table in (
        "netpay_protection_financial_snapshots",
        "netpay_protection_outcome_assessments",
        "netpay_protection_outcome_evidence",
    ):
        op.execute(f"DROP TRIGGER trg_{table}_append_only ON {table}")
    op.drop_table("netpay_protection_outcome_receipts")
    op.drop_table("netpay_protection_financial_snapshots")
    op.drop_table("netpay_protection_outcome_assessments")
    op.drop_table("netpay_protection_outcome_evidence")
    op.drop_constraint("ck_netpay_protection_status", "netpay_protection_cases", type_="check")
    op.create_check_constraint(
        "ck_netpay_protection_status",
        "netpay_protection_cases",
        "status IN ('identity_pending','contact_pending','ready_to_contact','contact_attempted',"
        "'reactivation_agreed','return_requested','monitoring','escalated','unrecoverable')",
    )
    op.drop_column("netpay_protection_cases", "closure_snapshot_id")
    op.drop_column("netpay_protection_cases", "closure_evidence_id")
    op.drop_column("netpay_protection_cases", "closure_kind")
