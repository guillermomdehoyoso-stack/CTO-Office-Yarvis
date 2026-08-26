import base64
import sys
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import SecretStr
from sqlalchemy.orm.exc import DetachedInstanceError

from yarvis_api import founder_bootstrap_cli as cli
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import FounderFirstOrganizationSettings, FounderHandoffSelectorSettings, Settings


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


def test_select_handoff_prints_only_the_opaque_reference_and_never_consumes(monkeypatch, capsys) -> None:
    session = _Session()
    opaque_id = "00000000-0000-0000-0000-000000000001"

    class Service:
        def select_eligible_handoff(self, _db, *, settings):
            assert settings.oidc_issuer == "https://issuer.synthetic.example"
            return SimpleNamespace(id=opaque_id, subject_encrypted="SENSITIVE_SUBJECT_TOKEN")

    monkeypatch.setattr(
        cli,
        "FounderHandoffSelectorSettings",
        lambda: SimpleNamespace(
            environment="production",
            database_url="postgresql://synthetic/select",
            oidc_issuer="https://issuer.synthetic.example",
        ),
    )
    monkeypatch.setattr(cli, "_selector_session", lambda _settings: session)
    monkeypatch.setattr(cli, "create_app", lambda: (_ for _ in ()).throw(AssertionError("must not initialize app")))
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "select-handoff"])

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == f"founder_bootstrap_handoff_id={opaque_id}\n"
    assert captured.err == ""
    assert "SENSITIVE" not in captured.out + captured.err
    assert session.commits == 0 and session.rollbacks == 1


def test_select_handoff_materializes_the_opaque_id_before_rollback(monkeypatch, capsys) -> None:
    session = _Session()
    opaque_id = "00000000-0000-0000-0000-000000000002"

    class DetachedAfterRollback:
        @property
        def id(self):
            if session.rollbacks:
                raise DetachedInstanceError("synthetic detached handoff")
            return opaque_id

    class Service:
        def select_eligible_handoff(self, _db, *, settings):
            assert settings.oidc_issuer == "https://issuer.synthetic.example"
            return DetachedAfterRollback()

    monkeypatch.setattr(
        cli,
        "FounderHandoffSelectorSettings",
        lambda: SimpleNamespace(
            environment="production",
            database_url="postgresql://synthetic/select",
            oidc_issuer="https://issuer.synthetic.example",
        ),
    )
    monkeypatch.setattr(cli, "_selector_session", lambda _settings: session)
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "select-handoff"])

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == f"founder_bootstrap_handoff_id={opaque_id}\n"
    assert captured.err == ""
    assert session.commits == 0 and session.rollbacks == 1


def test_select_handoff_settings_require_only_production_administrative_database_url_and_issuer(monkeypatch) -> None:
    monkeypatch.setenv("YARVIS_ENVIRONMENT", "production")
    monkeypatch.setenv("YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL", "postgresql://synthetic:synthetic@db.synthetic/yarvis")
    monkeypatch.setenv("YARVIS_OIDC_ISSUER", "https://issuer.synthetic.example")
    for name in (
        "YARVIS_AUTH_MODE",
        "YARVIS_OIDC_CLIENT_ID",
        "YARVIS_OIDC_CLIENT_SECRET",
        "YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY",
        "YARVIS_OIDC_REDIRECT_URI",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = FounderHandoffSelectorSettings()

    assert settings.environment == "production"
    assert settings.database_url == "postgresql://synthetic:synthetic@db.synthetic/yarvis"
    assert settings.oidc_issuer == "https://issuer.synthetic.example"


def test_select_organization_prints_only_the_opaque_reference_and_never_writes(monkeypatch, capsys) -> None:
    session = _Session()
    opaque_id = "00000000-0000-0000-0000-000000000003"

    class DetachedAfterRollback:
        @property
        def id(self):
            if session.rollbacks:
                raise DetachedInstanceError("synthetic detached organization")
            return opaque_id

    class Service:
        def select_active_organization(self, _db):
            return DetachedAfterRollback()

    monkeypatch.setattr(
        cli,
        "FounderHandoffSelectorSettings",
        lambda: SimpleNamespace(
            environment="production",
            database_url="postgresql://synthetic/select",
            oidc_issuer="https://issuer.synthetic.example",
        ),
    )
    monkeypatch.setattr(cli, "_selector_session", lambda _settings: session)
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "select-organization"])

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == f"founder_bootstrap_organization_id={opaque_id}\n"
    assert captured.err == ""
    assert "SENSITIVE" not in captured.out + captured.err
    assert session.commits == 0 and session.rollbacks == 1


@pytest.mark.parametrize("code", (ApplicationErrorCode.RESOURCE_NOT_FOUND, ApplicationErrorCode.CONFLICT))
def test_select_organization_fails_closed_for_zero_or_multiple_candidates(monkeypatch, capsys, code) -> None:
    session = _Session()

    class Service:
        def select_active_organization(self, _db):
            raise ApplicationError(code, "SENSITIVE_ORGANIZATION_NAME", {"reason": "organization_unavailable"})

    monkeypatch.setattr(
        cli,
        "FounderHandoffSelectorSettings",
        lambda: SimpleNamespace(
            environment="production",
            database_url="postgresql://synthetic/select",
            oidc_issuer="https://issuer.synthetic.example",
        ),
    )
    monkeypatch.setattr(cli, "_selector_session", lambda _settings: session)
    monkeypatch.setattr(cli, "FounderBootstrapAuthorizationService", Service)
    monkeypatch.setattr(sys, "argv", ["founder_bootstrap_cli", "select-organization"])

    assert cli.main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"founder_bootstrap_failed code={code}\n"
    assert "SENSITIVE" not in captured.out + captured.err
    assert session.commits == 0 and session.rollbacks == 1


def test_create_first_organization_uses_signed_file_and_redacts_all_material(monkeypatch, tmp_path, capsys) -> None:
    authorization = tmp_path / "authorization.bin"
    authorization.write_bytes(b"SENSITIVE_SIGNED_AUTHORIZATION")
    session = _Session()

    class Service:
        def create(self, _db, *, authorization: bytes, settings):
            assert authorization == b"SENSITIVE_SIGNED_AUTHORIZATION"
            assert settings.environment == "production"
            return SimpleNamespace(replayed=False)

    monkeypatch.setattr(
        cli,
        "FounderFirstOrganizationSettings",
        lambda: SimpleNamespace(environment="production", database_url="postgresql://synthetic/create"),
    )
    monkeypatch.setattr(cli, "_selector_session", lambda _settings: session)
    monkeypatch.setattr(cli, "FirstOrganizationAuthorizationService", Service)
    monkeypatch.setattr(
        sys, "argv", ["founder_bootstrap_cli", "create-first-organization", "--authorization-file", str(authorization)]
    )

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == "founder_bootstrap_first_organization_created status=created\n"
    assert captured.err == ""
    assert "SENSITIVE" not in captured.out + captured.err
    assert session.commits == 1 and session.rollbacks == 0


def test_create_first_organization_settings_require_only_administrative_founder_inputs(monkeypatch) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setenv("YARVIS_ENVIRONMENT", "production")
    monkeypatch.setenv("YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL", "postgresql://synthetic:synthetic@db.synthetic/yarvis")
    monkeypatch.setenv("YARVIS_FOUNDER_BOOTSTRAP_ENABLED", "true")
    monkeypatch.setenv("YARVIS_FOUNDER_BOOTSTRAP_PUBLIC_KEY", base64.b64encode(public_key).decode())
    monkeypatch.setenv("YARVIS_FOUNDER_BOOTSTRAP_KEY_ID", "synthetic-founder-v1")
    for name in (
        "YARVIS_AUTH_MODE",
        "YARVIS_OIDC_CLIENT_ID",
        "YARVIS_OIDC_CLIENT_SECRET",
        "YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    assert FounderFirstOrganizationSettings().environment == "production"
