import json
import logging
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm
from pydantic import SecretStr
from sqlalchemy import func, select

from yarvis_api.application.authority import IdentityAuthorityEnvelope, permissions_for_role
from yarvis_api.application.errors import ApplicationError
from yarvis_api.bootstrap import create_app
from yarvis_api.clock import utc_now
from yarvis_api.config import Settings
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.productive_auth import (
    BootstrapWindow,
    ExternalIdentityBinding,
    OIDCAuthenticationAttempt,
    ProductiveSession,
)
from yarvis_api.services.auth_rate_limit import AuthRateLimiter, InMemoryAuthRateLimitBackend
from yarvis_api.services.identity_provisioning import IdentityProvisioningService
from yarvis_api.services.oidc import OIDCClient, oidc_denied
from yarvis_api.services.productive_auth import ProductiveAuthCleanupService, ProductiveSessionService
from yarvis_api.services.productive_bootstrap import ProductiveBootstrapService


def _settings() -> Settings:
    return Settings(
        environment="test",
        auth_mode="oidc",
        oidc_issuer="https://issuer.example",
        oidc_client_id="client",
        oidc_client_secret=SecretStr("secret"),
        oidc_attempt_encryption_key=SecretStr(Fernet.generate_key().decode()),
        oidc_redirect_uri="https://api.example/auth/callback",
        oidc_post_login_redirect_allowlist="/netpay-inbox",
        csrf_allowed_origins="https://web.example",
    )


def _seed(app, subject: str = "opaque-subject") -> None:
    with app.state.yarvis.persistence.create_session() as db:
        person = Person(display_name="Synthetic Operator", status="active")
        organization = Organization(legal_name="Synthetic Organization", display_name="Synthetic Organization")
        db.add_all((person, organization))
        db.flush()
        principal = Principal(external_subject="legacy-unused", person_id=person.id, status="active")
        db.add(principal)
        db.flush()
        db.add_all(
            (
                PrincipalMembership(
                    principal_id=principal.id,
                    organization_id=organization.id,
                    role="netpay_operations_operator",
                    status="active",
                ),
                ExternalIdentityBinding(
                    principal_id=principal.id,
                    issuer="https://issuer.example",
                    normalized_subject=subject,
                    normalization_version="1",
                    provenance_receipt_hash="0" * 64,
                    status="active",
                ),
            )
        )
        db.commit()


def test_fake_oidc_full_session_csrf_logout_and_replay(monkeypatch):
    from yarvis_api.main import app as main_app

    settings = _settings()
    app = create_app(settings)
    _seed(app)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk["kid"] = "test-key"
    callback_claims: dict[str, str] = {}

    async def fake_json(_self, url, **kwargs):
        if url.endswith("openid-configuration"):
            return {
                "issuer": settings.oidc_issuer,
                "authorization_endpoint": "https://issuer.example/authorize",
                "token_endpoint": "https://issuer.example/token",
                "jwks_uri": "https://issuer.example/jwks",
            }
        if url.endswith("/token"):
            now = utc_now()
            return {
                "id_token": jwt.encode(
                    {
                        "iss": settings.oidc_issuer,
                        "aud": settings.oidc_client_id,
                        "sub": "opaque-subject",
                        "nonce": callback_claims["nonce"],
                        "iat": now,
                        "exp": now + timedelta(minutes=5),
                    },
                    private_key,
                    algorithm="RS256",
                    headers={"kid": "test-key"},
                )
            }
        return {"keys": [public_jwk]}

    monkeypatch.setattr(OIDCClient, "_json", fake_json)
    with TestClient(app, base_url="https://api.example") as client:
        login = client.get("/auth/login?redirect=/netpay-inbox", follow_redirects=False)
        assert login.status_code == 302
        query = parse_qs(urlparse(login.headers["location"]).query)
        callback_claims["nonce"] = query["nonce"][0]
        callback = client.post(
            "/auth/callback",
            data={"code": "one-use-code", "state": query["state"][0]},
            follow_redirects=False,
        )
        assert callback.status_code == 303
        assert "HttpOnly" in callback.headers["set-cookie"]
        assert client.get("/auth/session").json()["capabilities"] == [
            "netpay.inbox.manage",
            "netpay.inbox.read",
            "netpay.master.manage",
            "netpay.master.read",
        ]
        assert client.get("/netpay/data/datasets").status_code == 200
        assert client.post(
            "/netpay/data/datasets/00000000-0000-0000-0000-000000000001/reject",
            headers={"Origin": "https://web.example", "Idempotency-Key": "synthetic-reject"},
        ).status_code == 403
        denied = client.post("/auth/logout", headers={"Origin": "https://web.example"})
        assert denied.status_code == 403
        csrf = client.cookies.get("yarvis_csrf")
        assert csrf is not None
        assert client.post(
            "/netpay/data/datasets/00000000-0000-0000-0000-000000000001/reject",
            headers={
                "Origin": "https://web.example",
                "X-CSRF-Token": csrf,
                "Idempotency-Key": "synthetic-reject",
            },
        ).status_code == 404
        assert (
            client.post("/auth/logout", headers={"Origin": "https://web.example", "X-CSRF-Token": csrf}).status_code
            == 204
        )
        assert client.get("/auth/session").status_code == 403
        assert client.get("/netpay/data/datasets").status_code == 403
        assert (
            client.post("/auth/callback", data={"code": "one-use-code", "state": query["state"][0]}).status_code == 403
        )
    with main_app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(ProductiveSession)) == 1
        stored = db.scalar(select(ProductiveSession))
        assert stored.status == "revoked"
        assert stored.session_hash not in callback.headers["set-cookie"]
        assert db.scalar(select(func.count()).select_from(DomainEvent)) == 2


def test_redirect_and_production_configuration_fail_closed():
    settings = _settings()
    app = create_app(settings)
    with TestClient(app, base_url="https://api.example") as client:
        assert client.get("/auth/login?redirect=https://evil.example").status_code == 403
    with pytest.raises(ValueError, match="OIDC authentication"):
        Settings(environment="production", database_url_secret=SecretStr("postgresql://explicit/db"))
    with pytest.raises(ValueError, match="shared rate-limit"):
        Settings(
            environment="production",
            database_url_secret=SecretStr("postgresql://explicit/db"),
            auth_mode="oidc",
            oidc_issuer="https://issuer.example",
            oidc_client_id="client",
            oidc_client_secret=SecretStr("secret"),
            oidc_attempt_encryption_key=SecretStr(Fernet.generate_key().decode()),
            oidc_redirect_uri="https://api.example/auth/callback",
            cors_origins="https://web.example",
            csrf_allowed_origins="https://web.example",
            session_cookie_name="__Host-yarvis",
            auth_deployment_replicas=2,
        )


def test_oidc_denial_logs_only_allowlisted_stage_and_preserves_public_reason(caplog):
    sensitive = ("SENSITIVE_TOKEN_SENTINEL", "SENSITIVE_CODE_SENTINEL", "SENSITIVE_SECRET_SENTINEL")
    caplog.set_level(logging.WARNING, logger="yarvis_api.services.oidc")

    with pytest.raises(ApplicationError) as raised:
        oidc_denied("not-an-allowlisted-stage")

    assert raised.value.details == {"reason": "oidc_denied"}
    messages = [record.getMessage() for record in caplog.records]
    assert messages == ["oidc_authentication_denied stage=unspecified"]
    assert not any(value in "\n".join(messages) for value in sensitive)


def test_invalid_id_token_logs_stage_without_token_or_nonce(caplog, monkeypatch):
    settings = _settings()
    sensitive_token = "SENSITIVE_TOKEN_SENTINEL"
    sensitive_nonce = "SENSITIVE_NONCE_SENTINEL"

    async def fake_json(_self, _url, **_kwargs):
        return {"keys": []}

    monkeypatch.setattr(OIDCClient, "_json", fake_json)
    caplog.set_level(logging.WARNING, logger="yarvis_api.services.oidc")
    with pytest.raises(ApplicationError) as raised:
        __import__("asyncio").run(
            OIDCClient(settings).validate_id_token(
                {"jwks_uri": "https://issuer.example/jwks"}, sensitive_token, sensitive_nonce
            )
        )

    assert raised.value.details == {"reason": "oidc_denied"}
    messages = [record.getMessage() for record in caplog.records]
    assert messages == ["oidc_authentication_denied stage=jwt_header"]
    assert sensitive_token not in "\n".join(messages)
    assert sensitive_nonce not in "\n".join(messages)


def test_state_expiry_and_pkce_attempt_fail_closed(monkeypatch):
    settings = _settings()
    app = create_app(settings)

    async def discovery_only(_self, url, **_kwargs):
        assert url.endswith("openid-configuration")
        return {
            "issuer": settings.oidc_issuer,
            "authorization_endpoint": "https://issuer.example/authorize",
            "token_endpoint": "https://issuer.example/token",
            "jwks_uri": "https://issuer.example/jwks",
        }

    monkeypatch.setattr(OIDCClient, "_json", discovery_only)
    with TestClient(app, base_url="https://api.example") as client:
        assert client.post("/auth/callback", data={"code": "x", "state": "x" * 32}).status_code == 403
        login = client.get("/auth/login?redirect=/netpay-inbox", follow_redirects=False)
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        with app.state.yarvis.persistence.create_session() as db:
            attempt = db.scalar(
                select(OIDCAuthenticationAttempt).where(
                    OIDCAuthenticationAttempt.state_hash == __import__("hashlib").sha256(state.encode()).hexdigest()
                )
            )
            attempt.pkce_verifier_encrypted = "invalid"
            db.commit()
        assert client.post("/auth/callback", data={"code": "x", "state": state}).status_code == 403
        second = client.get("/auth/login?redirect=/netpay-inbox", follow_redirects=False)
        second_state = parse_qs(urlparse(second.headers["location"]).query)["state"][0]
        with app.state.yarvis.persistence.create_session() as db:
            attempt = db.scalar(
                select(OIDCAuthenticationAttempt).where(
                    OIDCAuthenticationAttempt.state_hash
                    == __import__("hashlib").sha256(second_state.encode()).hexdigest()
                )
            )
            attempt.expires_at = utc_now() - timedelta(seconds=1)
            db.commit()
        assert client.post("/auth/callback", data={"code": "x", "state": second_state}).status_code == 403


@pytest.mark.parametrize("defect", ["issuer", "audience", "algorithm", "signature", "expired", "nonce", "kid"])
def test_oidc_claim_validation_fails_closed(monkeypatch, defect):
    settings = _settings()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if defect == "signature" else key
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk["kid"] = "trusted"
    now = utc_now()
    claims = {
        "iss": "https://wrong.example" if defect == "issuer" else settings.oidc_issuer,
        "aud": "wrong" if defect == "audience" else settings.oidc_client_id,
        "sub": "opaque-subject",
        "nonce": "wrong" if defect == "nonce" else "nonce",
        "iat": now - timedelta(minutes=10) if defect == "expired" else now,
        "exp": now - timedelta(minutes=1) if defect == "expired" else now + timedelta(minutes=5),
    }
    token = (
        jwt.encode(claims, "synthetic-test-secret", algorithm="HS256", headers={"kid": "trusted"})
        if defect == "algorithm"
        else jwt.encode(
            claims,
            signing_key,
            algorithm="RS256",
            headers={"kid": "unknown" if defect == "kid" else "trusted"},
        )
    )

    async def fake_json(_self, _url, **_kwargs):
        return {"keys": [jwk]}

    monkeypatch.setattr(OIDCClient, "_json", fake_json)
    with pytest.raises(ApplicationError):
        __import__("asyncio").run(
            OIDCClient(settings).validate_id_token(
                {"jwks_uri": "https://issuer.example/jwks"},
                token,
                __import__("hashlib").sha256(b"nonce").hexdigest(),
            )
        )


def test_local_rate_limit_bootstrap_and_cleanup_are_idempotent():
    limiter = AuthRateLimiter(InMemoryAuthRateLimitBackend())
    limiter.require("login", "client", limit=1, window_seconds=600)
    with pytest.raises(Exception):
        limiter.require("login", "client", limit=1, window_seconds=600)

    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as db:
        window = BootstrapWindow(
            authorization_hash=__import__("hashlib").sha256(b"authorization").hexdigest(),
            allowlist_reference_hash=__import__("hashlib").sha256(b"evidence").hexdigest(),
            status="open",
            expires_at=utc_now() + timedelta(hours=1),
        )
        db.add(window)
        db.commit()
        calls = []
        assert not ProductiveBootstrapService().eligibility(db, "authorization", "evidence")
        service = ProductiveBootstrapService(enabled=True)
        assert (
            service.enroll(
                db,
                authorization="authorization",
                allowlist_evidence="evidence",
                idempotency_key="key",
                execute_canonical_commands=lambda: calls.append("called"),
            )
            == "completed"
        )
        db.commit()
        assert (
            service.enroll(
                db,
                authorization="authorization",
                allowlist_evidence="evidence",
                idempotency_key="key",
                execute_canonical_commands=lambda: calls.append("replayed"),
            )
            == "completed"
        )
        assert calls == ["called"]
        expired = OIDCAuthenticationAttempt(
            state_hash="a" * 64,
            nonce_hash="b" * 64,
            pkce_verifier_encrypted="consumed",
            redirect_path="/",
            expires_at=utc_now() - timedelta(hours=1),
            status="expired",
        )
        db.add(expired)
        db.commit()
        assert ProductiveAuthCleanupService().run(db)["oidc_attempts_deleted"] == 1
        db.commit()
        assert ProductiveAuthCleanupService().run(db)["oidc_attempts_deleted"] == 0


def test_identity_binding_and_person_link_are_authorized_idempotent_and_collision_safe():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as db:
        organization = Organization(legal_name="Identity Authority", display_name="Identity Authority")
        actor_person = Person(display_name="Synthetic Identity Admin")
        target_person = Person(display_name="Synthetic Target", email="first@example.invalid")
        db.add_all((organization, actor_person, target_person))
        db.flush()
        actor = Principal(external_subject="synthetic-admin", person_id=actor_person.id)
        target = Principal(external_subject="legacy-target")
        other = Principal(external_subject="legacy-other", person_id=target_person.id)
        db.add_all((actor, target, other))
        db.flush()
        envelope = IdentityAuthorityEnvelope(
            actor.id,
            organization.id,
            permissions_for_role("identity_provisioning_operator"),
            "synthetic-test",
            "00000000-0000-0000-0000-000000000001",
        )
        service = IdentityProvisioningService()
        linked = service.link_principal_to_person(
            db,
            envelope=envelope,
            principal_id=target.id,
            person_id=target_person.id,
            approval_receipt_hash="a" * 64,
            idempotency_key="link-key",
        )
        assert linked.person_id == target_person.id
        assert (
            service.link_principal_to_person(
                db,
                envelope=envelope,
                principal_id=target.id,
                person_id=target_person.id,
                approval_receipt_hash="a" * 64,
                idempotency_key="link-key",
            ).id
            == target.id
        )
        binding = service.bind_external_identity(
            db,
            envelope=envelope,
            principal_id=target.id,
            issuer="https://issuer.example",
            normalized_subject="stable-opaque-subject",
            normalization_version="1",
            provenance_receipt_hash="b" * 64,
            idempotency_key="bind-key",
        )
        target_person.email = "changed@example.invalid"
        assert (
            service.bind_external_identity(
                db,
                envelope=envelope,
                principal_id=target.id,
                issuer="https://issuer.example",
                normalized_subject="stable-opaque-subject",
                normalization_version="1",
                provenance_receipt_hash="b" * 64,
                idempotency_key="bind-key",
            ).id
            == binding.id
        )
        with pytest.raises(ApplicationError):
            service.bind_external_identity(
                db,
                envelope=envelope,
                principal_id=other.id,
                issuer="https://issuer.example",
                normalized_subject="stable-opaque-subject",
                normalization_version="1",
                provenance_receipt_hash="c" * 64,
                idempotency_key="other-bind-key",
            )


def test_productive_session_cap_revokes_oldest_and_stores_only_hashes():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as db:
        person = Person(display_name="Synthetic Session Subject")
        organization = Organization(legal_name="Session Organization", display_name="Session Organization")
        db.add_all((person, organization))
        db.flush()
        principal = Principal(external_subject="synthetic-session", person_id=person.id)
        db.add(principal)
        db.flush()
        db.add(
            PrincipalMembership(
                principal_id=principal.id,
                organization_id=organization.id,
                role="netpay_operations_operator",
            )
        )
        db.commit()
        service = ProductiveSessionService(_settings())
        raw_values = []
        session_ids = []
        for _ in range(4):
            item, raw, csrf, _ = service.create(db, principal)
            session_ids.append(item.id)
            raw_values.extend((raw, csrf))
            db.commit()
        sessions = db.scalars(select(ProductiveSession).order_by(ProductiveSession.created_at)).all()
        assert [item.status for item in sessions].count("active") == 3
        assert db.get(ProductiveSession, session_ids[0]).status == "revoked"
        persisted = " ".join(item.session_hash + item.csrf_hash for item in sessions)
        assert all(raw not in persisted for raw in raw_values)
