"""Closed administrative bootstrap workflow; never exposed as a web endpoint."""

from __future__ import annotations

import hashlib
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.clock import utc_now
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    BootstrapEnrollmentReceipt,
    BootstrapWindow,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class ProductiveBootstrapService:
    """Verify a pre-authorized window and orchestrate canonical commands atomically."""

    def __init__(self, *, enabled: bool = False):
        self._enabled = enabled

    def eligibility(self, db: Session, authorization: str, allowlist_evidence: str) -> bool:
        if not self._enabled:
            return False
        window = db.scalar(select(BootstrapWindow).where(BootstrapWindow.authorization_hash == _hash(authorization)))
        return bool(
            window
            and window.status == "open"
            and not window.enrollment_completed
            and window.expires_at > utc_now()
            and window.allowlist_reference_hash == _hash(allowlist_evidence)
        )

    def enroll(
        self,
        db: Session,
        *,
        authorization: str,
        allowlist_evidence: str,
        idempotency_key: str,
        execute_canonical_commands: Callable[[], None],
    ) -> str:
        if not self._enabled:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "request denied",
                {"reason": "bootstrap_disabled"},
            )
        window = db.scalar(
            select(BootstrapWindow).where(BootstrapWindow.authorization_hash == _hash(authorization)).with_for_update()
        )
        key_hash = _hash(idempotency_key)
        fingerprint = _hash(f"{_hash(authorization)}:{_hash(allowlist_evidence)}")
        if window is not None:
            replay = db.scalar(
                select(BootstrapEnrollmentReceipt).where(
                    BootstrapEnrollmentReceipt.window_id == window.id,
                    BootstrapEnrollmentReceipt.idempotency_key_hash == key_hash,
                )
            )
            if replay is not None:
                if replay.request_fingerprint != fingerprint:
                    raise ApplicationError(
                        ApplicationErrorCode.CONFLICT,
                        "request denied",
                        {"reason": "idempotency_conflict"},
                    )
                return replay.outcome
        if not window or not self.eligibility(db, authorization, allowlist_evidence):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "request denied",
                {"reason": "bootstrap_closed"},
            )
        window.attempt_count += 1
        if window.attempt_count > 5:
            window.status = "locked"
            window.closed_at = utc_now()
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "request denied",
                {"reason": "bootstrap_rate_limited"},
            )
        execute_canonical_commands()
        window.enrollment_completed = True
        window.status = "closed"
        window.closed_at = utc_now()
        receipt = BootstrapEnrollmentReceipt(
            window_id=window.id,
            idempotency_key_hash=key_hash,
            request_fingerprint=fingerprint,
            outcome="completed",
        )
        db.add(receipt)
        db.add(
            AuthenticationSecurityAudit(
                event_type="bootstrap_enrollment",
                outcome="success",
                reason_code="first_success_closed",
                safe_details={"policy_version": "AUTH-POLICY-001"},
            )
        )
        return "completed"

    def close(self, db: Session, window: BootstrapWindow, reason: str) -> None:
        if reason not in {"manual", "expired", "incident", "completed"}:
            raise ValueError("unsupported bootstrap close reason")
        if window.status == "open":
            window.status = "closed" if reason != "expired" else "expired"
            window.closed_at = utc_now()
            db.add(
                AuthenticationSecurityAudit(
                    event_type="bootstrap_closed",
                    outcome="success",
                    reason_code=reason,
                    safe_details={"contract_id": "IC-GOVERNANCE-EVT-002"},
                )
            )
