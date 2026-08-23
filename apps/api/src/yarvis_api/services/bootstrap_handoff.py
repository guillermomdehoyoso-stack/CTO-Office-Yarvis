"""Opaque, one-use OIDC handoff for a future administrative bootstrap operation."""

import hashlib
from datetime import timedelta
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    BootstrapVerifiedIdentity,
    OIDCAuthenticationAttempt,
)


class BootstrapIdentityHandoffService:
    """Persist only ciphertext after complete OIDC validation and only while bootstrap is enabled."""

    def record(
        self,
        db: Session,
        *,
        attempt: OIDCAuthenticationAttempt,
        issuer: str,
        subject: str,
        encryption_key: str,
    ) -> BootstrapVerifiedIdentity:
        existing = db.scalar(
            select(BootstrapVerifiedIdentity).where(BootstrapVerifiedIdentity.oidc_attempt_id == attempt.id)
        )
        if existing is not None:
            return existing
        now = utc_now()
        item = BootstrapVerifiedIdentity(
            oidc_attempt_id=attempt.id,
            issuer_hash=hashlib.sha256(issuer.encode()).hexdigest(),
            subject_encrypted=Fernet(encryption_key.encode()).encrypt(subject.encode()).decode(),
            expires_at=now + timedelta(minutes=10),
            provenance="founder_bootstrap",
            provenance_receipt_id=uuid4(),
        )
        db.add(item)
        db.add(
            AuthenticationSecurityAudit(
                event_type="bootstrap_identity_handoff",
                outcome="verified",
                reason_code="oidc_validated",
                safe_details={"version": "1", "provenance_receipt_id": str(item.provenance_receipt_id)},
            )
        )
        db.flush()
        return item
