import base64
import sys
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import SecretStr

from yarvis_api import founder_bootstrap_cli as cli
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import Settings


class _Session:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _production_settings() -> Settings:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return Settings(
        environment="production",
        debug=False,
        database_url_secret=SecretStr("postgresql://synthetic:synthetic@db.synthetic/yarvis"),
        auth_mode="oidc",
        oidc_issuer="https://issuer.synthetic.example",
        oidc_client_id="synthetic-client",
        oidc_client_secret=SecretStr("synthetic-secret"),
        oidc_attempt_encryption_key=SecretStr(Fernet.generate_key().decode()),
        oidc_redirect_uri="https://pilot.synthetic.example/auth/callback",
        cors_origins="https://pilot.synthetic.example",
        csrf_allowed_origins="https://pilot.synthetic.example",
        session_cookie_name="__Host-synthetic",
        founder_bootstrap_enabled=True,
        founder_bootstrap_public_key=base64.b64encode(public_key).decode(),
        founder_bootstrap_key_id="synthetic-founder-v1",
    )


def _app(settings, session: _Session):
    return SimpleNamespace(
        state=SimpleNamespace(
            yarvis=SimpleNamespace(
                settings=settings,
                persistence=SimpleNamespace(create_session=lambda: session),
            )
        )
    )


def test_enroll_uses_only_signed_file_input_and_emits_no_sensitive_output(monkeypatch, tmp_path, capsys) -> None:
    authorization = tmp_path / "authorization.bin"
    authorization.write_bytes(b"SENSITIVE_SIGNED_AUTHORIZATION")
    session = _Session()

    class Service:
        def enroll(self, _db, *, authorization: bytes, settings):
            assert authorization == b"SENSITIVE_SIGNED_AUTHORIZATION"
            assert settings.environment == "production"
            return SimpleNamespace(outcome="enrolled")

    monkeypatch.setattr(cli, "create_app", lambda: _app(_production_settings(), session))
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "enroll", "--authorization-file", str(authorization)])

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == "founder_bootstrap_enrollment_completed status=enrolled\n"
    assert captured.err == ""
    assert "SENSITIVE_SIGNED_AUTHORIZATION" not in captured.out + captured.err
    assert session.commits == 1 and session.rollbacks == 0


def test_enroll_fails_closed_outside_production(monkeypatch, tmp_path) -> None:
    authorization = tmp_path / "authorization.bin"
    authorization.write_bytes(b"opaque")
    session = _Session()
    monkeypatch.setattr(cli, "create_app", lambda: _app(SimpleNamespace(environment="test"), session))
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "enroll", "--authorization-file", str(authorization)])

    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert session.commits == 0 and session.rollbacks == 0


def test_enroll_redacts_application_error(monkeypatch, tmp_path, capsys) -> None:
    authorization = tmp_path / "authorization.bin"
    authorization.write_bytes(b"SENSITIVE_SIGNED_AUTHORIZATION")
    session = _Session()

    class Service:
        def enroll(self, *_args, **_kwargs):
            raise ApplicationError(
                ApplicationErrorCode.CONFLICT,
                "SENSITIVE_SUBJECT_TOKEN_SECRET",
                {"reason": "idempotency_conflict"},
            )

    monkeypatch.setattr(cli, "create_app", lambda: _app(_production_settings(), session))
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "enroll", "--authorization-file", str(authorization)])

    assert cli.main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "founder_bootstrap_failed code=CONFLICT\n"
    assert "SENSITIVE" not in captured.out + captured.err
    assert session.commits == 0 and session.rollbacks == 1
