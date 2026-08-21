from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.api.authentication import DeterministicAuthenticationProvider
from yarvis_api.api.routes import intake as intake_routes
from yarvis_api.application.authentication import AuthenticatedPrincipal, TransportAuthenticationRequest
from yarvis_api.application.errors import ApplicationErrorCode
from yarvis_api.config import Settings
from yarvis_api.main import app
from yarvis_api.schemas.intake import IntakeDetailRead
from yarvis_api.services.inbound_intake import InboundIntakeService


def _production_oidc_settings(**overrides) -> Settings:
    values = {
        "environment": "production",
        "database_url": "postgresql://synthetic:synthetic@db.test:5432/yarvis_test",
        "auth_mode": "oidc",
        "oidc_issuer": "https://issuer.test.invalid",
        "oidc_client_id": "yarvis-test-client",
        "oidc_client_secret": "synthetic-test-secret",
        "oidc_attempt_encryption_key": "synthetic-test-encryption-key",
        "oidc_redirect_uri": "https://yarvis.test.invalid/auth/callback",
        "oidc_post_login_redirect_allowlist": "/",
        "oidc_allowed_algorithms": "RS256",
        "cors_origins": "https://yarvis.test.invalid",
        "csrf_allowed_origins": "https://yarvis.test.invalid",
        "session_cookie_name": "__Host-yarvis_session",
    }
    values.update(overrides)
    return Settings.model_validate(values)


def _transport_request(headers: dict[str, str]) -> TransportAuthenticationRequest:
    return TransportAuthenticationRequest(headers={k.lower(): v for k, v in headers.items()}, path="/intake/deterministic", method="POST")


def _trusted_headers() -> dict[str, str]:
    return {
        "x-yarvis-actor": "connector:test",
        "x-yarvis-subject": "connector:test",
        "x-yarvis-organization": "org-123",
        "x-yarvis-authority": "inbound.intake",
        "x-yarvis-auth-token": "deterministic-inbound-intake",
        "x-yarvis-roles": "connector,system",
        "x-yarvis-permissions": "intake:receive,intake:message",
    }


def _payload() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "external_source": "email",
        "external_message_id": uuid4().hex,
        "connector_delivery_id": "delivery-1",
        "sender": "sender@example.com",
        "recipients": ["ops@example.com"],
        "subject": "Inbound",
        "text_body": "payload",
        "html_body": "<p>payload</p>",
        "content_type": "message/rfc822",
        "source_timestamp": now,
        "received_timestamp": now,
        "headers": {"message-id": uuid4().hex},
        "correlation_id": str(uuid4()),
        "causation_id": None,
        "idempotency_key": "idem-1",
    }


def test_development_provider_builds_authenticated_principal() -> None:
    provider = DeterministicAuthenticationProvider(Settings(environment="test"))

    principal = provider.authenticate(_transport_request(_trusted_headers()))

    assert principal.actor_id == "connector:test"
    assert principal.organization_id is None
    assert principal.authority == "deterministic-subject"
    assert principal.authentication_method == "trusted-header-dev"
    assert principal.roles == ()
    assert principal.permissions == ()


def test_development_provider_rejects_missing_actor() -> None:
    provider = DeterministicAuthenticationProvider(Settings(environment="test"))
    headers = _trusted_headers()
    headers.pop("x-yarvis-actor")
    headers.pop("x-yarvis-subject")

    try:
        provider.authenticate(_transport_request(headers))
        assert False, "expected authentication failure"
    except Exception as error:
        assert getattr(error, "code", None) == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_development_provider_ignores_authority_headers() -> None:
    provider = DeterministicAuthenticationProvider(Settings(environment="test"))
    headers = _trusted_headers()
    headers.pop("x-yarvis-authority")

    assert provider.authenticate(_transport_request(headers)).authority == "deterministic-subject"


def test_development_provider_ignores_invalid_legacy_authority_headers() -> None:
    provider = DeterministicAuthenticationProvider(Settings(environment="test"))
    headers = _trusted_headers()
    headers["x-yarvis-roles"] = "connector,connector"

    assert provider.authenticate(_transport_request(headers)).permissions == ()


def test_production_mode_rejects_deterministic_provider() -> None:
    provider = DeterministicAuthenticationProvider(_production_oidc_settings())

    try:
        provider.authenticate(_transport_request(_trusted_headers()))
        assert False, "expected authentication failure"
    except Exception as error:
        assert getattr(error, "code", None) == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_route_uses_resolved_intake_principal_and_passes_compatibility_projection(monkeypatch) -> None:
    client = TestClient(app)
    captured: dict[str, object] = {}

    principal = AuthenticatedPrincipal(
        actor_id="spy-principal-id",
        organization_id="spy-org",
        roles=(),
        permissions=("inbound.intake",),
        authority="inbound.intake",
        authentication_method="resolved-envelope",
        authenticated_at=datetime.now(timezone.utc),
        is_system_actor=False,
        correlation_id="spy-correlation",
    )

    def fake_resolve(request, db, *, required_scope: str) -> AuthenticatedPrincipal:
        captured["required_scope"] = required_scope
        captured["principal"] = principal
        return principal

    expected_intake_id = uuid4()

    def fake_submit(self, submission):
        captured["submission_principal"] = submission.principal
        return expected_intake_id

    def fake_load_detail(self, session, intake_id):
        captured["load_intake_id"] = intake_id
        return IntakeDetailRead(
            id=expected_intake_id,
            intake_number="INT-SPY-001",
            source_type="email",
            content_type="message/rfc822",
            title="Inbound",
            text_content="payload",
            original_filename=None,
            mime_type="message/rfc822",
            organization_id=None,
            person_id=None,
            case_id=None,
            received_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            source_metadata={},
            trace_metadata={},
            message=None,
            events=[],
        )

    monkeypatch.setattr(intake_routes, "_resolved_intake_principal", fake_resolve)
    monkeypatch.setattr(InboundIntakeService, "submit", fake_submit)
    monkeypatch.setattr(InboundIntakeService, "load_detail", fake_load_detail)

    response = client.post("/intake/deterministic", json=_payload(), headers={"x-any": "value"})

    assert response.status_code == 201, response.text
    assert captured["required_scope"] == "inbound.intake"
    assert captured["submission_principal"] == captured["principal"]
    assert captured["load_intake_id"] == expected_intake_id
