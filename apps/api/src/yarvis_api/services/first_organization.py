"""IC-GOVERNANCE-CMD-006: first Organization creation under signed Founder authority."""

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import FounderFirstOrganizationSettings
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.organization import Organization
from yarvis_api.models.productive_auth import AuthenticationSecurityAudit, FirstOrganizationReceipt

_CONTRACT_ID = "IC-GOVERNANCE-CMD-006"
_EVENT_ID = "IC-GOVERNANCE-EVT-005"
_ADVISORY_LOCK_KEY = 8_106_202_608_23
_FIELDS = frozenset(
    {
        "purpose",
        "version",
        "key_id",
        "legal_name",
        "display_name",
        "organization_type",
        "status",
        "issued_at",
        "expires_at",
        "nonce",
        "idempotency_key",
    }
)
_RATIFIED_VALUES = {
    "legal_name": "GMDHO",
    "display_name": "Yarvis en NetPay",
    "organization_type": "organization",
    "status": "active",
}


def _hash(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


@dataclass(frozen=True)
class FirstOrganizationResult:
    receipt: FirstOrganizationReceipt
    replayed: bool


class FirstOrganizationAuthorizationService:
    """Create one Organization only; callers own the transaction commit/rollback."""

    def _verified_payload(self, authorization: bytes, settings: FounderFirstOrganizationSettings) -> dict[str, str]:
        try:
            envelope = json.loads(authorization)
            payload = envelope["payload"]
            signature = base64.b64decode(envelope["signature"], validate=True)
            if not isinstance(payload, dict) or frozenset(payload) != _FIELDS:
                raise ValueError("invalid payload shape")
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            public = Ed25519PublicKey.from_public_bytes(
                base64.b64decode(settings.founder_bootstrap_public_key or "", validate=True)
            )
            public.verify(signature, canonical)
            issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        except (AttributeError, KeyError, TypeError, ValueError, binascii.Error, InvalidSignature):
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied") from None
        now = datetime.now(timezone.utc)
        if (
            payload.get("purpose") != "create_first_organization"
            or payload.get("version") != "1"
            or payload.get("key_id") != settings.founder_bootstrap_key_id
            or any(payload.get(field) != value for field, value in _RATIFIED_VALUES.items())
            or not payload.get("nonce")
            or not payload.get("idempotency_key")
            or issued.tzinfo is None
            or expires.tzinfo is None
            or issued > now
            or expires <= now
            or (expires - issued).total_seconds() > 600
        ):
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "request denied")
        return payload

    def create(
        self, db: Session, *, authorization: bytes, settings: FounderFirstOrganizationSettings
    ) -> FirstOrganizationResult:
        payload = self._verified_payload(authorization, settings)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        digest = _hash(canonical)
        nonce_hash = _hash(payload["nonce"])
        key_hash = _hash(payload["idempotency_key"])

        # A transaction-scoped PostgreSQL advisory lock protects the zero-row predicate.
        db.execute(select(func.pg_advisory_xact_lock(_ADVISORY_LOCK_KEY)))
        existing = db.scalar(
            select(FirstOrganizationReceipt).where(
                (FirstOrganizationReceipt.authorization_digest == digest)
                | (FirstOrganizationReceipt.nonce_hash == nonce_hash)
                | (FirstOrganizationReceipt.idempotency_key_hash == key_hash)
            )
        )
        if existing is not None:
            if (
                existing.authorization_digest != digest
                or existing.nonce_hash != nonce_hash
                or existing.idempotency_key_hash != key_hash
            ):
                raise ApplicationError(ApplicationErrorCode.CONFLICT, "request denied")
            return FirstOrganizationResult(receipt=existing, replayed=True)
        if db.scalar(select(func.count()).select_from(Organization)) != 0:
            raise ApplicationError(ApplicationErrorCode.CONFLICT, "request denied")

        organization = Organization(**_RATIFIED_VALUES)
        db.add(organization)
        db.flush()
        receipt = FirstOrganizationReceipt(
            authorization_digest=digest,
            nonce_hash=nonce_hash,
            idempotency_key_hash=key_hash,
            request_fingerprint=digest,
            organization_id=organization.id,
            outcome="created",
        )
        db.add(receipt)
        db.flush()
        record_event(
            db,
            event_type="FirstOrganizationCreated",
            aggregate_type="Organization",
            aggregate_id=organization.id,
            organization_id=organization.id,
            payload={"contract_id": _EVENT_ID, "version": "1", "outcome": "created"},
        )
        db.add(
            AuthenticationSecurityAudit(
                event_type="first_organization_created",
                outcome="success",
                organization_id=organization.id,
                correlation_id=digest,
                safe_details={"contract_id": _CONTRACT_ID, "version": "1", "outcome": "created"},
            )
        )
        db.flush()
        return FirstOrganizationResult(receipt=receipt, replayed=False)
