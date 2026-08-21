"""Provider-neutral productive session and canonical authority boundary."""

import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import cast
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope, permissions_for_role
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.clock import utc_now
from yarvis_api.config import Settings
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    ExternalIdentityBinding,
    OIDCAuthenticationAttempt,
    ProductiveSession,
)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


_hash = hash_secret


class ProductiveSessionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def resolve_binding(self, db: Session, issuer: str, subject: str) -> Principal:
        if not issuer or not subject or len(issuer) > 512 or len(subject) > 512:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication denied", {"reason": "invalid_identity_key"}
            )
        binding = db.scalar(
            select(ExternalIdentityBinding).where(
                ExternalIdentityBinding.issuer == issuer,
                ExternalIdentityBinding.normalized_subject == subject,
                ExternalIdentityBinding.status == "active",
            )
        )
        if binding is None:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication denied", {"reason": "binding_not_found"}
            )
        principal = db.get(Principal, binding.principal_id)
        if principal is None or principal.status != "active" or principal.person_id is None:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication denied", {"reason": "principal_unavailable"}
            )
        return principal

    def create(
        self, db: Session, principal: Principal
    ) -> tuple[ProductiveSession, str, str, IdentityAuthorityEnvelope]:
        # Serialize session creation even when the Principal has no sessions yet.
        db.scalar(select(Principal.id).where(Principal.id == principal.id).with_for_update())
        memberships = db.scalars(
            select(PrincipalMembership).where(
                PrincipalMembership.principal_id == principal.id, PrincipalMembership.status == "active"
            )
        ).all()
        if len(memberships) != 1:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication denied", {"reason": "membership_unavailable"}
            )
        membership = memberships[0]
        organization = db.get(Organization, membership.organization_id)
        if organization is None or organization.status != "active":
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "authentication denied",
                {"reason": "organization_unavailable"},
            )
        now = utc_now()
        raw = secrets.token_urlsafe(48)
        csrf = secrets.token_urlsafe(32)
        active = db.scalars(
            select(ProductiveSession)
            .where(ProductiveSession.principal_id == principal.id, ProductiveSession.status == "active")
            .order_by(ProductiveSession.created_at)
        ).all()
        sessions_to_revoke = max(0, len(active) - self.settings.session_max_active + 1)
        for old in active[:sessions_to_revoke]:
            self.revoke(db, old, "session_limit")
        item = ProductiveSession(
            principal_id=principal.id,
            organization_id=organization.id,
            membership_id=membership.id,
            session_hash=_hash(raw),
            csrf_hash=_hash(csrf),
            last_seen_at=now,
            idle_expires_at=now + timedelta(seconds=self.settings.session_idle_seconds),
            absolute_expires_at=now + timedelta(seconds=self.settings.session_absolute_seconds),
            status="active",
        )
        db.add(item)
        db.flush()
        record_event(
            db,
            event_type="ProductiveSessionStarted",
            aggregate_type="ProductiveSession",
            aggregate_id=item.id,
            organization_id=organization.id,
            payload={
                "contract_id": "IC-IDENTITY-EVT-004",
                "contract_version": "1.0.0",
                "principal_id": str(principal.id),
                "policy_version": "AUTH-POLICY-001",
                "idle_expires_at": item.idle_expires_at.isoformat(),
                "absolute_expires_at": item.absolute_expires_at.isoformat(),
            },
        )
        db.add(
            AuthenticationSecurityAudit(
                event_type="session_started",
                outcome="success",
                principal_id=principal.id,
                organization_id=organization.id,
                safe_details={"policy_version": "AUTH-POLICY-001"},
            )
        )
        return (
            item,
            raw,
            csrf,
            IdentityAuthorityEnvelope(
                principal.id, organization.id, permissions_for_role(membership.role), "oidc", secrets.token_hex(16)
            ),
        )

    def authenticate(
        self, db: Session, request: Request, *, mutation: bool = False
    ) -> tuple[ProductiveSession, IdentityAuthorityEnvelope]:
        raw = request.cookies.get(self.settings.session_cookie_name)
        if not raw:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication required", {"reason": "no_session"}
            )
        item = db.scalar(select(ProductiveSession).where(ProductiveSession.session_hash == _hash(raw)))
        now = utc_now()
        if item is None or item.status != "active" or now >= item.idle_expires_at or now >= item.absolute_expires_at:
            if item is not None and item.status == "active":
                item.status = "expired"
                db.add(
                    AuthenticationSecurityAudit(
                        event_type="session_expired",
                        outcome="success",
                        principal_id=item.principal_id,
                        organization_id=item.organization_id,
                        safe_details={},
                    )
                )
                db.commit()
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication required", {"reason": "session_inactive"}
            )
        membership = db.get(PrincipalMembership, item.membership_id)
        principal = db.get(Principal, item.principal_id)
        organization = db.get(Organization, item.organization_id)
        if (
            membership is None
            or membership.status != "active"
            or principal is None
            or principal.status != "active"
            or organization is None
            or organization.status != "active"
        ):
            self.revoke(db, item, "authority_changed")
            db.commit()
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "authentication required", {"reason": "authority_changed"}
            )
        if mutation:
            csrf = request.headers.get("x-csrf-token", "")
            origin = request.headers.get("origin")
            if not hmac.compare_digest(_hash(csrf), item.csrf_hash) or origin not in self.settings.csrf_origin_list:
                raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "csrf"})
        if (now - item.last_seen_at).total_seconds() >= 60:
            item.last_seen_at = now
            item.idle_expires_at = min(
                now + timedelta(seconds=self.settings.session_idle_seconds), item.absolute_expires_at
            )
        return item, IdentityAuthorityEnvelope(
            principal.id,
            organization.id,
            permissions_for_role(membership.role),
            "oidc",
            request.headers.get("x-correlation-id") or secrets.token_hex(16),
        )

    def revoke(self, db: Session, item: ProductiveSession, reason: str = "logout"):
        if item.status == "active":
            item.status = "revoked"
            item.revoked_at = utc_now()
            item.revoke_reason = reason
            record_event(
                db,
                event_type="ProductiveSessionRevoked",
                aggregate_type="ProductiveSession",
                aggregate_id=item.id,
                organization_id=cast(UUID, item.organization_id),
                payload={
                    "contract_id": "IC-IDENTITY-EVT-005",
                    "contract_version": "1.0.0",
                    "reason": reason,
                },
            )
            db.add(
                AuthenticationSecurityAudit(
                    event_type="session_revoked",
                    outcome="success",
                    reason_code=reason,
                    principal_id=item.principal_id,
                    organization_id=item.organization_id,
                    safe_details={},
                )
            )

    def logout(self, db: Session, request: Request) -> None:
        """Revoke once and make an equivalent authenticated replay harmless."""
        raw = request.cookies.get(self.settings.session_cookie_name)
        if not raw:
            return
        item = db.scalar(select(ProductiveSession).where(ProductiveSession.session_hash == _hash(raw)))
        if item is None:
            return
        csrf = request.headers.get("x-csrf-token", "")
        origin = request.headers.get("origin")
        if not hmac.compare_digest(_hash(csrf), item.csrf_hash) or origin not in self.settings.csrf_origin_list:
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "csrf"})
        self.revoke(db, item)


class ProductiveAuthCleanupService:
    """Idempotent retention cleanup; scheduling remains a deployment concern."""

    def run(self, db: Session) -> dict[str, int]:
        now = utc_now()
        attempts = db.scalars(
            select(OIDCAuthenticationAttempt).where(OIDCAuthenticationAttempt.expires_at < now - timedelta(minutes=5))
        ).all()
        for attempt in attempts:
            db.delete(attempt)
        sessions = db.scalars(
            select(ProductiveSession).where(
                ProductiveSession.status != "active",
                ProductiveSession.updated_at < now - timedelta(days=self._session_retention_days),
            )
        ).all()
        for session in sessions:
            db.delete(session)
        return {"oidc_attempts_deleted": len(attempts), "sessions_deleted": len(sessions)}

    def __init__(self, session_retention_days: int = 7):
        if session_retention_days < 1:
            raise ValueError("session retention must be positive")
        self._session_retention_days = session_retention_days
