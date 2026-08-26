import base64
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import SecretStr
from sqlalchemy import func, select

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.clock import utc_now
from yarvis_api.config import FounderFirstOrganizationSettings
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.productive_auth import AuthenticationSecurityAudit, FirstOrganizationReceipt
from yarvis_api.services.first_organization import FirstOrganizationAuthorizationService


def _settings(private_key: Ed25519PrivateKey) -> FounderFirstOrganizationSettings:
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return FounderFirstOrganizationSettings(
        environment="production",
        database_url_secret=SecretStr("postgresql://synthetic:synthetic@db.synthetic/yarvis"),
        founder_bootstrap_enabled=True,
        founder_bootstrap_public_key=base64.b64encode(public_key).decode(),
        founder_bootstrap_key_id="synthetic-founder-v1",
    )


def _authorization(
    private_key: Ed25519PrivateKey,
    *,
    nonce: str = "synthetic-nonce",
    idempotency_key: str = "synthetic-key",
    purpose: str = "create_first_organization",
) -> bytes:
    now = utc_now()
    payload = {
        "purpose": purpose,
        "version": "1",
        "key_id": "synthetic-founder-v1",
        "legal_name": "GMDHO",
        "display_name": "Yarvis en NetPay",
        "organization_type": "organization",
        "status": "active",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": nonce,
        "idempotency_key": idempotency_key,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return json.dumps(
        {"payload": payload, "signature": base64.b64encode(private_key.sign(canonical)).decode()},
        separators=(",", ":"),
    ).encode()


def test_create_first_organization_is_atomic_idempotent_and_sanitized() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    authorization = _authorization(private_key)
    service = FirstOrganizationAuthorizationService()
    with app.state.yarvis.persistence.create_session() as db:
        result = service.create(db, authorization=authorization, settings=settings)
        assert result.replayed is False
        assert db.scalar(select(func.count()).select_from(Organization)) == 1
        organization = db.scalar(select(Organization))
        assert organization is not None
        assert (
            organization.legal_name,
            organization.display_name,
            organization.organization_type,
            organization.status,
        ) == (
            "GMDHO",
            "Yarvis en NetPay",
            "organization",
            "active",
        )
        replay = service.create(db, authorization=authorization, settings=settings)
        assert replay.replayed is True and replay.receipt.id == result.receipt.id
        assert db.scalar(select(func.count()).select_from(FirstOrganizationReceipt)) == 1
        event = db.scalar(select(DomainEvent))
        audit = db.scalar(select(AuthenticationSecurityAudit))
        assert event is not None and event.event_type == "FirstOrganizationCreated"
        assert event.payload == {"contract_id": "IC-GOVERNANCE-EVT-005", "version": "1", "outcome": "created"}
        assert audit is not None and audit.safe_details == {
            "contract_id": "IC-GOVERNANCE-CMD-006",
            "version": "1",
            "outcome": "created",
        }
        rendered = f"{event.payload}{audit.safe_details}"
        assert "GMDHO" not in rendered and "NetPay" not in rendered and "synthetic-nonce" not in rendered
        db.rollback()


def test_create_first_organization_fails_closed_for_existing_or_conflicting_replay() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    service = FirstOrganizationAuthorizationService()
    with app.state.yarvis.persistence.create_session() as db:
        first = _authorization(private_key, nonce="nonce-a", idempotency_key="key-a")
        service.create(db, authorization=first, settings=settings)
        with pytest.raises(ApplicationError) as conflict:
            service.create(
                db,
                authorization=_authorization(private_key, nonce="nonce-a", idempotency_key="key-b"),
                settings=settings,
            )
        assert conflict.value.code == ApplicationErrorCode.CONFLICT
        with pytest.raises(ApplicationError) as existing:
            service.create(
                db,
                authorization=_authorization(private_key, nonce="nonce-b", idempotency_key="key-b"),
                settings=settings,
            )
        assert existing.value.code == ApplicationErrorCode.CONFLICT
        db.rollback()


def test_concurrent_equivalent_requests_create_only_one_organization() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    authorization = _authorization(private_key)

    def create_once() -> bool:
        with app.state.yarvis.persistence.create_session() as db:
            result = FirstOrganizationAuthorizationService().create(db, authorization=authorization, settings=settings)
            db.commit()
            return result.replayed

    with ThreadPoolExecutor(max_workers=2) as executor:
        replays = list(executor.map(lambda _unused: create_once(), range(2)))
    assert sorted(replays) == [False, True]
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(Organization)) == 1
        assert db.scalar(select(func.count()).select_from(FirstOrganizationReceipt)) == 1
        db.rollback()


@pytest.mark.parametrize("mutation", ("invalid_signature", "wrong_purpose", "expired"))
def test_create_first_organization_rejects_invalid_authorization_before_writes(mutation: str) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    authorization = _authorization(
        private_key, purpose="different" if mutation == "wrong_purpose" else "create_first_organization"
    )
    envelope = json.loads(authorization)
    if mutation == "invalid_signature":
        envelope["signature"] = base64.b64encode(b"x" * 64).decode()
    if mutation == "expired":
        envelope["payload"]["expires_at"] = (utc_now() - timedelta(seconds=1)).isoformat()
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(ApplicationError) as error:
            FirstOrganizationAuthorizationService().create(
                db, authorization=json.dumps(envelope).encode(), settings=settings
            )
        assert error.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED
        assert db.scalar(select(func.count()).select_from(Organization)) == 0
        db.rollback()
