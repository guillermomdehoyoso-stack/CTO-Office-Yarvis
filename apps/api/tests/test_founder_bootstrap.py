import base64
import hashlib
import json
import logging
from datetime import timedelta
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.clock import utc_now
from yarvis_api.config import Settings
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.productive_auth import (
    AuthenticationSecurityAudit,
    BootstrapVerifiedIdentity,
    BootstrapWindow,
    ExternalIdentityBinding,
    FounderBootstrapReceipt,
    OIDCAuthenticationAttempt,
)
from yarvis_api.services.founder_bootstrap import FounderBootstrapAuthorizationService


def _settings(private_key: Ed25519PrivateKey) -> Settings:
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return Settings(
        environment="test",
        auth_mode="oidc",
        oidc_issuer="https://issuer.synthetic.example",
        oidc_attempt_encryption_key=SecretStr(Fernet.generate_key().decode()),
        founder_bootstrap_enabled=True,
        founder_bootstrap_public_key=base64.b64encode(public_key).decode(),
        founder_bootstrap_key_id="synthetic-founder-v1",
    )


def _seed_handoff(
    db,
    settings: Settings,
    *,
    expired: bool = False,
    consumed: bool = False,
    issuer: str | None = None,
    provenance: str | None = None,
) -> BootstrapVerifiedIdentity:
    now = utc_now()
    issuer = issuer or settings.oidc_issuer
    encryption_key = settings.oidc_attempt_encryption_key
    assert issuer is not None
    assert encryption_key is not None
    attempt = OIDCAuthenticationAttempt(
        state_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
        nonce_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
        pkce_verifier_encrypted="opaque-test-ciphertext",
        redirect_path="/",
        expires_at=now + timedelta(minutes=5),
        status="consumed",
        consumed_at=now,
    )
    db.add(attempt)
    db.flush()
    handoff = BootstrapVerifiedIdentity(
        oidc_attempt_id=attempt.id,
        issuer_hash=hashlib.sha256(issuer.encode()).hexdigest(),
        subject_encrypted=Fernet(encryption_key.get_secret_value().encode()).encrypt(b"synthetic-subject").decode(),
        expires_at=now - timedelta(seconds=1) if expired else now + timedelta(minutes=5),
        consumed_at=now if consumed else None,
        provenance=provenance,
        provenance_receipt_id=uuid4() if provenance is not None else None,
    )
    db.add(handoff)
    db.flush()
    return handoff


def test_founder_handoff_selector_returns_only_one_current_provenanced_candidate(caplog) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    sentinel = "synthetic-subject-must-not-log"
    with app.state.yarvis.persistence.create_session() as db, caplog.at_level(logging.WARNING):
        handoff = _seed_handoff(db, settings, provenance="founder_bootstrap")
        selected = FounderBootstrapAuthorizationService().select_eligible_handoff(db, settings=settings)

        assert selected.id == handoff.id
        assert selected.consumed_at is None
    assert sentinel not in caplog.text
    assert "opaque-test-ciphertext" not in caplog.text


@pytest.mark.parametrize(
    ("expired", "consumed", "provenance", "issuer"),
    (
        (False, False, None, None),
        (True, False, "founder_bootstrap", None),
        (False, True, "founder_bootstrap", None),
        (False, False, "founder_bootstrap", "https://other-issuer.synthetic.example"),
    ),
)
def test_founder_handoff_selector_excludes_noneligible_candidates(expired, consumed, provenance, issuer) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        _seed_handoff(
            db,
            settings,
            expired=expired,
            consumed=consumed,
            provenance=provenance,
            issuer=issuer,
        )
        with pytest.raises(ApplicationError) as error:
            FounderBootstrapAuthorizationService().select_eligible_handoff(db, settings=settings)
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND


def test_founder_handoff_provenance_is_closed_and_historical_rows_stay_ineligible() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        historical = _seed_handoff(db, settings)
        assert historical.provenance is None and historical.provenance_receipt_id is None
        attempt = OIDCAuthenticationAttempt(
            state_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
            nonce_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
            pkce_verifier_encrypted="opaque-test-ciphertext",
            redirect_path="/",
            expires_at=utc_now() + timedelta(minutes=5),
            status="consumed",
            consumed_at=utc_now(),
        )
        db.add(attempt)
        db.flush()
        invalid = BootstrapVerifiedIdentity(
            oidc_attempt_id=attempt.id,
            issuer_hash=hashlib.sha256((settings.oidc_issuer or "").encode()).hexdigest(),
            subject_encrypted="opaque-test-ciphertext",
            expires_at=utc_now() + timedelta(minutes=5),
            provenance="not_founder_bootstrap",
            provenance_receipt_id=uuid4(),
        )
        db.add(invalid)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


def test_founder_handoff_selector_excludes_completed_enrollment() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        handoff = _seed_handoff(db, settings, provenance="founder_bootstrap")
        db.add(
            FounderBootstrapReceipt(
                authorization_digest=hashlib.sha256(uuid4().bytes).hexdigest(),
                nonce_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
                idempotency_key_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
                handoff_id=handoff.id,
                expires_at=utc_now() + timedelta(minutes=5),
                outcome="enrolled",
            )
        )
        db.flush()
        with pytest.raises(ApplicationError) as error:
            FounderBootstrapAuthorizationService().select_eligible_handoff(db, settings=settings)
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND


def test_founder_handoff_selector_fails_closed_for_multiple_candidates() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        _seed_handoff(db, settings, provenance="founder_bootstrap")
        _seed_handoff(db, settings, provenance="founder_bootstrap")
        with pytest.raises(ApplicationError) as error:
            FounderBootstrapAuthorizationService().select_eligible_handoff(db, settings=settings)
        assert error.value.code == ApplicationErrorCode.CONFLICT


@pytest.mark.parametrize(
    ("organizations", "expected"),
    (
        ((), ApplicationErrorCode.RESOURCE_NOT_FOUND),
        ((SimpleNamespace(), SimpleNamespace()), ApplicationErrorCode.CONFLICT),
    ),
)
def test_founder_organization_selector_fails_closed_without_exactly_one_active_candidate(
    organizations, expected
) -> None:
    class ReadOnlySession:
        def scalars(self, _statement):
            return iter(organizations)

    with pytest.raises(ApplicationError) as error:
        FounderBootstrapAuthorizationService().select_active_organization(cast(Session, ReadOnlySession()))
    assert error.value.code == expected


def _authorization(
    private_key: Ed25519PrivateKey,
    handoff: BootstrapVerifiedIdentity,
    *,
    purpose: str = "founder_bootstrap",
    key_id: str = "synthetic-founder-v1",
    expires_at=None,
    nonce: str = "synthetic-nonce",
    idempotency_key: str = "synthetic-idempotency",
    organization_id=None,
) -> bytes:
    now = utc_now()
    payload = {
        "purpose": purpose,
        "version": "1",
        "key_id": key_id,
        "handoff_id": str(handoff.id),
        "organization_id": str(organization_id or uuid4()),
        "role": "netpay_operations_operator",
        "issued_at": now.isoformat(),
        "expires_at": (expires_at or now + timedelta(minutes=5)).isoformat(),
        "nonce": nonce,
        "idempotency_key": idempotency_key,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return json.dumps(
        {"payload": payload, "signature": base64.b64encode(private_key.sign(canonical)).decode()},
        separators=(",", ":"),
    ).encode()


def test_founder_authorization_is_verified_consumed_once_and_never_creates_identity(caplog) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    service = FounderBootstrapAuthorizationService()
    sentinel = "synthetic-subject-must-not-log"
    with app.state.yarvis.persistence.create_session() as db, caplog.at_level(logging.WARNING):
        handoff = _seed_handoff(db, settings)
        authorization = _authorization(private_key, handoff)
        receipt = service.prepare(db, authorization=authorization, settings=settings)
        assert receipt.outcome == "prepared"
        assert service.prepare(db, authorization=authorization, settings=settings).id == receipt.id
        assert service.consume(db, receipt=receipt).outcome == "consumed"
        assert service.consume(db, receipt=receipt).id == receipt.id
        db.commit()
        assert db.scalar(select(func.count()).select_from(FounderBootstrapReceipt)) == 1
        assert db.scalar(select(func.count()).select_from(Person)) == 0
        assert db.scalar(select(func.count()).select_from(Principal)) == 0
        assert db.scalar(select(func.count()).select_from(PrincipalMembership)) == 0
        audit = db.scalar(select(AuthenticationSecurityAudit))
        assert audit is not None and audit.safe_details == {"version": "1"}
    assert sentinel not in caplog.text
    assert "opaque-test-ciphertext" not in caplog.text


@pytest.mark.parametrize("mutation", ("signature", "payload", "expired", "purpose", "key_id"))
def test_founder_authorization_rejects_invalid_signed_material(mutation: str) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        handoff = _seed_handoff(db, settings)
        authorization = _authorization(
            private_key,
            handoff,
            expires_at=utc_now() - timedelta(seconds=1) if mutation == "expired" else None,
            purpose="not_founder" if mutation == "purpose" else "founder_bootstrap",
            key_id="unknown-key" if mutation == "key_id" else "synthetic-founder-v1",
        )
        envelope = json.loads(authorization)
        if mutation == "signature":
            envelope["signature"] = base64.b64encode(b"x" * 64).decode()
        if mutation == "payload":
            envelope["payload"]["role"] = "different-role"
        with pytest.raises(ApplicationError) as error:
            FounderBootstrapAuthorizationService().prepare(
                db, authorization=json.dumps(envelope).encode(), settings=settings
            )
        assert error.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED
        assert db.scalar(select(func.count()).select_from(FounderBootstrapReceipt)) == 0


def test_founder_authorization_rejects_replay_conflict_and_unavailable_handoff() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    service = FounderBootstrapAuthorizationService()
    with app.state.yarvis.persistence.create_session() as db:
        handoff = _seed_handoff(db, settings)
        first = _authorization(private_key, handoff, nonce="same-nonce", idempotency_key="same-key")
        service.prepare(db, authorization=first, settings=settings)
        conflict = _authorization(private_key, handoff, nonce="same-nonce", idempotency_key="other-key")
        with pytest.raises(ApplicationError) as error:
            service.prepare(db, authorization=conflict, settings=settings)
        assert error.value.code == ApplicationErrorCode.CONFLICT
        idempotency_conflict = _authorization(private_key, handoff, nonce="other-nonce", idempotency_key="same-key")
        with pytest.raises(ApplicationError) as error:
            service.prepare(db, authorization=idempotency_conflict, settings=settings)
        assert error.value.code == ApplicationErrorCode.CONFLICT


def test_founder_enrollment_creates_one_complete_chain_and_terminally_closes() -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    service = FounderBootstrapAuthorizationService()
    with app.state.yarvis.persistence.create_session() as db:
        organization = Organization(legal_name="Synthetic founder organization", display_name="Synthetic founder")
        db.add(organization)
        db.flush()
        handoff = _seed_handoff(db, settings)
        authorization = _authorization(private_key, handoff, organization_id=organization.id)
        receipt = service.enroll(db, authorization=authorization, settings=settings)
        assert receipt.outcome == "enrolled"
        assert receipt.person_id and receipt.principal_id and receipt.membership_id
        assert service.enroll(db, authorization=authorization, settings=settings).id == receipt.id
        assert db.scalar(select(func.count()).select_from(Person)) == 1
        assert db.scalar(select(func.count()).select_from(Principal)) == 1
        assert db.scalar(select(func.count()).select_from(PrincipalMembership)) == 1
        assert db.scalar(select(func.count()).select_from(ExternalIdentityBinding)) == 1
        assert db.scalar(select(func.count()).select_from(BootstrapWindow)) == 1
        window = db.scalar(select(BootstrapWindow))
        assert window is not None and window.status == "closed" and window.enrollment_completed is True
        assert db.scalar(select(BootstrapVerifiedIdentity)).consumed_at is not None
        events = db.scalars(select(DomainEvent)).all()
        assert {event.event_type for event in events} >= {
            "PersonCreated",
            "HumanPrincipalCreated",
            "AuthorityChanged",
            "BootstrapWindowOpened",
            "BootstrapEnrollmentCompleted",
        }
        assert all(set(event.payload) <= {"contract_version", "transition"} for event in events)
        audit = db.scalar(select(AuthenticationSecurityAudit))
        assert audit is not None and audit.safe_details == {"version": "1"}
        db.commit()


@pytest.mark.parametrize("expired,consumed", ((True, False), (False, True)))
def test_founder_authorization_rejects_unavailable_handoff(expired: bool, consumed: bool) -> None:
    from yarvis_api.main import app

    private_key = Ed25519PrivateKey.generate()
    settings = _settings(private_key)
    with app.state.yarvis.persistence.create_session() as db:
        unavailable = _seed_handoff(db, settings, expired=expired, consumed=consumed)
        with pytest.raises(ApplicationError) as error:
            FounderBootstrapAuthorizationService().prepare(
                db, authorization=_authorization(private_key, unavailable), settings=settings
            )
        assert error.value.details == {"reason": "handoff_unavailable"}
