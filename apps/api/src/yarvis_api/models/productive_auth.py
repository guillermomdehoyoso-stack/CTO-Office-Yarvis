"""Productive OIDC binding, attempt, session, bootstrap and safe audit state."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class ExternalIdentityBinding(TimestampedUUIDMixin, Base):
    __tablename__ = "external_identity_bindings"
    __table_args__ = (UniqueConstraint("issuer", "normalized_subject", name="uq_identity_binding_issuer_subject"),)
    principal_id: Mapped[object] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issuer: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_subject: Mapped[str] = mapped_column(String(512), nullable=False)
    normalization_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1")
    provenance_receipt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class IdentityProvisioningReceipt(TimestampedUUIDMixin, Base):
    __tablename__ = "identity_provisioning_receipts"
    __table_args__ = (
        UniqueConstraint(
            "contract_id", "authority_scope", "idempotency_key_hash", name="uq_identity_receipt_scope_key"
        ),
    )
    contract_id: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_scope: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[object] = mapped_column(PG_UUID(as_uuid=True), nullable=False)


class OIDCAuthenticationAttempt(TimestampedUUIDMixin, Base):
    __tablename__ = "oidc_authentication_attempts"
    __table_args__ = (
        CheckConstraint("status IN ('pending','consumed','expired','failed')", name="ck_oidc_attempt_status"),
    )
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    nonce_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    pkce_verifier_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    redirect_path: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")


class ProductiveSession(TimestampedUUIDMixin, Base):
    __tablename__ = "productive_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active','expired','revoked')", name="ck_productive_session_status"),
        Index("ix_productive_sessions_principal_status", "principal_id", "status"),
    )
    principal_id: Mapped[object] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    organization_id: Mapped[object] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[object] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("principal_memberships.id", ondelete="RESTRICT"), nullable=False
    )
    session_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    csrf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(nullable=False)
    idle_expires_at: Mapped[datetime] = mapped_column(nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class BootstrapWindow(TimestampedUUIDMixin, Base):
    __tablename__ = "identity_bootstrap_windows"
    __table_args__ = (
        CheckConstraint("status IN ('open','closed','expired','locked')", name="ck_bootstrap_window_status"),
    )
    authorization_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    allowlist_reference_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enrollment_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class BootstrapEnrollmentReceipt(TimestampedUUIDMixin, Base):
    __tablename__ = "identity_bootstrap_enrollment_receipts"
    __table_args__ = (UniqueConstraint("window_id", "idempotency_key_hash", name="uq_bootstrap_receipt_window_key"),)
    window_id: Mapped[object] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("identity_bootstrap_windows.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)


class AuthenticationSecurityAudit(TimestampedUUIDMixin, Base):
    __tablename__ = "authentication_security_audit"
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    principal_id: Mapped[object | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    organization_id: Mapped[object | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    safe_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
