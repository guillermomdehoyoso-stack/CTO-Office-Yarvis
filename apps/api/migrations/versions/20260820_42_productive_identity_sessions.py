"""Add productive identity binding and server-side sessions.

Revision ID: 20260820_42
Revises: 20260819_41
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260820_42"
down_revision = "20260819_41"
branch_labels = None
depends_on = None
U = postgresql.UUID(as_uuid=True)
T = sa.DateTime(timezone=True)


def upgrade():
    op.create_table(
        "external_identity_bindings",
        sa.Column("id", U, primary_key=True),
        sa.Column("principal_id", U, nullable=False),
        sa.Column("issuer", sa.String(512), nullable=False),
        sa.Column("normalized_subject", sa.String(512), nullable=False),
        sa.Column("normalization_version", sa.String(16), nullable=False),
        sa.Column("provenance_receipt_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("issuer", "normalized_subject", name="uq_identity_binding_issuer_subject"),
    )
    op.create_index("ix_external_identity_bindings_principal_id", "external_identity_bindings", ["principal_id"])
    op.create_table(
        "identity_provisioning_receipts",
        sa.Column("id", U, primary_key=True),
        sa.Column("contract_id", sa.String(32), nullable=False),
        sa.Column("authority_scope", sa.String(128), nullable=False),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("aggregate_id", U, nullable=False),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "contract_id",
            "authority_scope",
            "idempotency_key_hash",
            name="uq_identity_receipt_scope_key",
        ),
    )
    op.create_table(
        "oidc_authentication_attempts",
        sa.Column("id", U, primary_key=True),
        sa.Column("state_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("nonce_hash", sa.String(64), nullable=False),
        sa.Column("pkce_verifier_encrypted", sa.String(1024), nullable=False),
        sa.Column("redirect_path", sa.String(512), nullable=False),
        sa.Column("expires_at", T, nullable=False),
        sa.Column("consumed_at", T),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('pending','consumed','expired','failed')", name="ck_oidc_attempt_status"),
    )
    op.create_index("ix_oidc_attempt_expires", "oidc_authentication_attempts", ["expires_at"])
    op.create_table(
        "productive_sessions",
        sa.Column("id", U, primary_key=True),
        sa.Column("principal_id", U, nullable=False),
        sa.Column("organization_id", U, nullable=False),
        sa.Column("membership_id", U, nullable=False),
        sa.Column("session_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("last_seen_at", T, nullable=False),
        sa.Column("idle_expires_at", T, nullable=False),
        sa.Column("absolute_expires_at", T, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("revoked_at", T),
        sa.Column("revoke_reason", sa.String(64)),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["membership_id"], ["principal_memberships.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("status IN ('active','expired','revoked')", name="ck_productive_session_status"),
    )
    op.create_index("ix_productive_sessions_principal_status", "productive_sessions", ["principal_id", "status"])
    op.create_index("ix_productive_sessions_session_hash", "productive_sessions", ["session_hash"], unique=True)
    op.create_table(
        "identity_bootstrap_windows",
        sa.Column("id", U, primary_key=True),
        sa.Column("authorization_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("allowlist_reference_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("expires_at", T, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("enrollment_completed", sa.Boolean(), nullable=False),
        sa.Column("closed_at", T),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('open','closed','expired','locked')", name="ck_bootstrap_window_status"),
    )
    op.create_table(
        "authentication_security_audit",
        sa.Column("id", U, primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(64)),
        sa.Column("principal_id", U),
        sa.Column("organization_id", U),
        sa.Column("correlation_id", sa.String(64)),
        sa.Column("safe_details", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_auth_security_audit_event_type", "authentication_security_audit", ["event_type"])
    op.create_table(
        "identity_bootstrap_enrollment_receipts",
        sa.Column("id", U, primary_key=True),
        sa.Column("window_id", U, nullable=False),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("created_at", T, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", T, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["window_id"], ["identity_bootstrap_windows.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("window_id", "idempotency_key_hash", name="uq_bootstrap_receipt_window_key"),
    )


def downgrade():
    op.drop_table("identity_bootstrap_enrollment_receipts")
    op.drop_table("authentication_security_audit")
    op.drop_table("identity_bootstrap_windows")
    op.drop_table("productive_sessions")
    op.drop_table("oidc_authentication_attempts")
    op.drop_table("identity_provisioning_receipts")
    op.drop_table("external_identity_bindings")
