"""Signed, non-HTTP founder bootstrap enrollment with durable replay protection."""

import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import FounderHandoffSelectorSettings, Settings
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.models.principal import Principal
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    BootstrapVerifiedIdentity,
    BootstrapWindow,
    ExternalIdentityBinding,
    FounderBootstrapReceipt,
)
from yarvis_api.services.governance_authority import grant_bootstrap_membership

_ROLES = frozenset({"netpay_operations_operator"})
_PAYLOAD_FIELDS = frozenset(
    {
        "purpose",
        "version",
        "key_id",
        "handoff_id",
        "organization_id",
        "role",
        "issued_at",
        "expires_at",
        "nonce",
        "idempotency_key",
    }
)


def _hash(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


class FounderBootstrapAuthorizationService:
    def select_eligible_handoff(
        self, db: Session, *, settings: Settings | FounderHandoffSelectorSettings | None = None
    ) -> BootstrapVerifiedIdentity:
        """Return exactly one provenance-backed handoff without changing it."""
        now = datetime.now(timezone.utc)
        completed_enrollment = exists(
            select(FounderBootstrapReceipt.id).where(
                FounderBootstrapReceipt.handoff_id == BootstrapVerifiedIdentity.id,
                FounderBootstrapReceipt.outcome == "enrolled",
            )
        )
        criteria = [
            BootstrapVerifiedIdentity.provenance == "founder_bootstrap",
            BootstrapVerifiedIdentity.provenance_receipt_id.is_not(None),
            BootstrapVerifiedIdentity.expires_at > now,
            BootstrapVerifiedIdentity.consumed_at.is_(None),
            ~completed_enrollment,
        ]
        if settings is not None:
            criteria.append(BootstrapVerifiedIdentity.issuer_hash == _hash(settings.oidc_issuer or ""))
        candidates = list(
            db.scalars(
                select(BootstrapVerifiedIdentity)
                .where(*criteria)
                .order_by(BootstrapVerifiedIdentity.created_at, BootstrapVerifiedIdentity.id)
            )
        )
        if not candidates:
            raise ApplicationError(
                ApplicationErrorCode.RESOURCE_NOT_FOUND, "request denied", {"reason": "handoff_unavailable"}
            )
        if len(candidates) != 1:
            raise ApplicationError(ApplicationErrorCode.CONFLICT, "request denied", {"reason": "handoff_ambiguous"})
        return candidates[0]

    def select_active_organization(self, db: Session) -> Organization:
        """Return exactly one active Organization without changing persistent state."""
        candidates = list(
            db.scalars(
                select(Organization)
                .where(Organization.status == "active")
                .order_by(Organization.created_at, Organization.id)
            )
        )
        if not candidates:
            raise ApplicationError(
                ApplicationErrorCode.RESOURCE_NOT_FOUND, "request denied", {"reason": "organization_unavailable"}
            )
        if len(candidates) != 1:
            raise ApplicationError(
                ApplicationErrorCode.CONFLICT, "request denied", {"reason": "organization_ambiguous"}
            )
        return candidates[0]

    def _verified_payload(self, authorization: bytes, settings: Settings) -> dict[str, str]:
        try:
            envelope = json.loads(authorization)
            payload = envelope["payload"]
            signature = base64.b64decode(envelope["signature"], validate=True)
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            public = Ed25519PublicKey.from_public_bytes(
                base64.b64decode(settings.founder_bootstrap_public_key or "", validate=True)
            )
            public.verify(signature, canonical)
            if not isinstance(payload, dict) or frozenset(payload) != _PAYLOAD_FIELDS:
                raise ValueError("invalid payload shape")
            issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
            if issued.tzinfo is None or expires.tzinfo is None:
                raise ValueError("timestamps must include a timezone")
            UUID(payload["handoff_id"])
            UUID(payload["organization_id"])
        except (AttributeError, KeyError, TypeError, ValueError, binascii.Error, InvalidSignature):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "invalid_authorization"}
            ) from None
        now = datetime.now(timezone.utc)
        if (
            payload.get("purpose") != "founder_bootstrap"
            or payload.get("version") != "1"
            or payload.get("key_id") != settings.founder_bootstrap_key_id
            or payload.get("role") not in _ROLES
            or not payload.get("nonce")
            or not payload.get("idempotency_key")
            or issued > now
            or expires <= now
            or (expires - issued).total_seconds() > 600
        ):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "invalid_authorization"}
            )
        return payload

    def prepare(self, db: Session, *, authorization: bytes, settings: Settings) -> FounderBootstrapReceipt:
        if not settings.founder_bootstrap_enabled or not settings.founder_bootstrap_public_key:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "gate_closed"}
            )
        payload = self._verified_payload(authorization, settings)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        handoff_id = UUID(payload["handoff_id"])
        expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        digest, nonce_hash, key_hash = _hash(canonical), _hash(payload["nonce"]), _hash(payload["idempotency_key"])
        existing = db.scalar(
            select(FounderBootstrapReceipt).where(
                (FounderBootstrapReceipt.nonce_hash == nonce_hash)
                | (FounderBootstrapReceipt.idempotency_key_hash == key_hash)
            )
        )
        if existing:
            if existing.authorization_digest != digest or existing.idempotency_key_hash != key_hash:
                raise ApplicationError(
                    ApplicationErrorCode.CONFLICT, "request denied", {"reason": "idempotency_conflict"}
                )
            return existing
        handoff = db.get(BootstrapVerifiedIdentity, handoff_id)
        issuer_hash = _hash(settings.oidc_issuer or "")
        if (
            handoff is None
            or handoff.consumed_at is not None
            or handoff.expires_at <= now
            or handoff.issuer_hash != issuer_hash
        ):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "handoff_unavailable"}
            )
        receipt = FounderBootstrapReceipt(
            authorization_digest=digest,
            nonce_hash=nonce_hash,
            idempotency_key_hash=key_hash,
            handoff_id=handoff.id,
            expires_at=expires,
        )
        db.add(receipt)
        db.flush()
        return receipt

    def enroll(self, db: Session, *, authorization: bytes, settings: Settings) -> FounderBootstrapReceipt:
        """Execute the signed, one-use founder chain; never exposed through HTTP."""
        receipt = self.prepare(db, authorization=authorization, settings=settings)
        if receipt.outcome == "enrolled":
            return receipt
        payload = self._verified_payload(authorization, settings)
        locked = db.scalar(
            select(FounderBootstrapReceipt).where(FounderBootstrapReceipt.id == receipt.id).with_for_update()
        )
        if locked is None:
            raise ApplicationError(
                ApplicationErrorCode.RESOURCE_NOT_FOUND, "request denied", {"reason": "bootstrap_unavailable"}
            )
        if locked.outcome != "prepared":
            raise ApplicationError(
                ApplicationErrorCode.PRECONDITION_FAILED, "request denied", {"reason": "bootstrap_unavailable"}
            )
        handoff = db.scalar(
            select(BootstrapVerifiedIdentity).where(BootstrapVerifiedIdentity.id == locked.handoff_id).with_for_update()
        )
        organization = db.scalar(
            select(Organization).where(
                Organization.id == UUID(payload["organization_id"]), Organization.status == "active"
            )
        )
        now = datetime.now(timezone.utc)
        if handoff is None or organization is None or handoff.consumed_at is not None or handoff.expires_at <= now:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "bootstrap_unavailable"}
            )
        key = settings.oidc_attempt_encryption_key
        if key is None:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "bootstrap_unavailable"}
            )
        try:
            normalized_subject = (
                Fernet(key.get_secret_value().encode()).decrypt(handoff.subject_encrypted.encode()).decode()
            )
        except (InvalidToken, UnicodeDecodeError):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "bootstrap_unavailable"}
            ) from None
        collision = db.scalar(
            select(ExternalIdentityBinding).where(
                ExternalIdentityBinding.issuer == (settings.oidc_issuer or ""),
                ExternalIdentityBinding.normalized_subject == normalized_subject,
            )
        )
        if collision is not None:
            raise ApplicationError(ApplicationErrorCode.CONFLICT, "request denied", {"reason": "binding_collision"})
        window = BootstrapWindow(
            authorization_hash=receipt.authorization_digest,
            allowlist_reference_hash=_hash(receipt.authorization_digest),
            status="open",
            expires_at=receipt.expires_at,
        )
        db.add(window)
        db.flush()
        person = Person(display_name="Founder bootstrap operator", status="active")
        db.add(person)
        db.flush()
        principal = Principal(external_subject=f"founder-bootstrap:{receipt.id}", person_id=person.id, status="active")
        db.add(principal)
        db.flush()
        binding = ExternalIdentityBinding(
            principal_id=principal.id,
            issuer=settings.oidc_issuer or "",
            normalized_subject=normalized_subject,
            normalization_version="1",
            provenance_receipt_hash=receipt.authorization_digest,
            status="active",
        )
        membership = grant_bootstrap_membership(
            db,
            window=window,
            principal_id=principal.id,
            organization_id=organization.id,
            role=payload["role"],
            idempotency_key=locked.idempotency_key_hash,
        )
        db.add(binding)
        db.flush()
        for event_type, aggregate_type, aggregate_id in (
            ("PersonCreated", "Person", person.id),
            ("HumanPrincipalCreated", "Principal", principal.id),
            ("ExternalIdentityBound", "ExternalIdentityBinding", binding.id),
            ("BootstrapWindowOpened", "BootstrapWindow", window.id),
            ("BootstrapEnrollmentCompleted", "FounderBootstrapReceipt", receipt.id),
        ):
            record_event(
                db,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                organization_id=organization.id,
                payload={"contract_version": "1.0.0"},
            )
        handoff.consumed_at = now
        window.enrollment_completed = True
        window.status = "closed"
        window.closed_at = now
        locked.outcome, locked.person_id, locked.principal_id, locked.membership_id = (
            "enrolled",
            person.id,
            principal.id,
            membership.id,
        )
        db.add(
            AuthenticationSecurityAudit(
                event_type="bootstrap_enrollment", outcome="success", safe_details={"version": "1"}
            )
        )
        db.flush()
        return locked

    def consume(self, db: Session, *, receipt: FounderBootstrapReceipt) -> FounderBootstrapReceipt:
        locked_receipt = db.scalar(
            select(FounderBootstrapReceipt).where(FounderBootstrapReceipt.id == receipt.id).with_for_update()
        )
        if locked_receipt is None:
            raise ApplicationError(
                ApplicationErrorCode.RESOURCE_NOT_FOUND, "request denied", {"reason": "invalid_receipt"}
            )
        if locked_receipt.outcome == "consumed":
            return locked_receipt
        if locked_receipt.outcome != "prepared":
            raise ApplicationError(
                ApplicationErrorCode.PRECONDITION_FAILED, "request denied", {"reason": "invalid_receipt"}
            )
        handoff = db.scalar(
            select(BootstrapVerifiedIdentity)
            .where(BootstrapVerifiedIdentity.id == locked_receipt.handoff_id)
            .with_for_update()
        )
        now = datetime.now(timezone.utc)
        if (
            locked_receipt.expires_at <= now
            or handoff is None
            or handoff.consumed_at is not None
            or handoff.expires_at <= now
        ):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "handoff_unavailable"}
            )
        handoff.consumed_at = now
        locked_receipt.outcome = "consumed"
        db.add(
            AuthenticationSecurityAudit(
                event_type="founder_bootstrap_authorization", outcome="consumed", safe_details={"version": "1"}
            )
        )
        db.flush()
        return locked_receipt
