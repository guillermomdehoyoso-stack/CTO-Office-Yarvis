"""Ed25519 founder-bootstrap authorization preparation; never executes enrollment."""

import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import Settings
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    BootstrapVerifiedIdentity,
    FounderBootstrapReceipt,
)

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
    def prepare(self, db: Session, *, authorization: bytes, settings: Settings) -> FounderBootstrapReceipt:
        if not settings.founder_bootstrap_enabled or not settings.founder_bootstrap_public_key:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied", {"reason": "gate_closed"}
            )
        try:
            envelope = json.loads(authorization)
            payload = envelope["payload"]
            signature = base64.b64decode(envelope["signature"], validate=True)
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            public = Ed25519PublicKey.from_public_bytes(
                base64.b64decode(settings.founder_bootstrap_public_key, validate=True)
            )
            public.verify(signature, canonical)
            if not isinstance(payload, dict) or frozenset(payload) != _PAYLOAD_FIELDS:
                raise ValueError("invalid payload shape")
            issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
            if issued.tzinfo is None or expires.tzinfo is None:
                raise ValueError("timestamps must include a timezone")
            handoff_id = UUID(payload["handoff_id"])
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
