from pydantic import ValidationError

from yarvis_api.config import Settings, get_settings, reset_settings_cache


def test_safe_local_defaults_load() -> None:
    settings = Settings()

    assert settings.environment == "local"
    assert settings.api_port == 8000
    assert settings.debug is False


def test_constructor_values_override_environment(monkeypatch) -> None:
    monkeypatch.setenv("YARVIS_API_PORT", "9000")

    settings = Settings(api_port=9100)

    assert settings.api_port == 9100


def test_environment_values_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv("YARVIS_API_PORT", "9000")
    monkeypatch.setenv("YARVIS_LOG_LEVEL", "debug")

    settings = Settings()

    assert settings.api_port == 9000
    assert settings.log_level == "DEBUG"


def test_invalid_values_are_rejected() -> None:
    for values in (
        {"environment": "unsupported"},
        {"api_port": 0},
        {"log_level": "verbose"},
        {"document_storage_root": "   "},
        {"database_url": "mysql://secret-value"},
        {"environment": "production", "debug": True},
    ):
        try:
            Settings.model_validate(values)
        except ValidationError as exc:
            assert "secret-value" not in str(exc)
        else:
            raise AssertionError("invalid settings must be rejected")


def test_secret_is_not_in_settings_representation() -> None:
    settings = Settings.model_validate({"database_url": "postgresql://user:secret-value@localhost/yarvis"})

    assert "secret-value" not in repr(settings)


def test_psycopg_sqlalchemy_url_is_accepted_without_exposing_secrets() -> None:
    settings = Settings.model_validate({"database_url": "postgresql+psycopg://user:secret-value@localhost/yarvis"})

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert "secret-value" not in repr(settings)


def test_cached_settings_can_be_reset_deterministically(monkeypatch) -> None:
    reset_settings_cache()
    monkeypatch.setenv("YARVIS_API_PORT", "9001")
    assert get_settings().api_port == 9001

    monkeypatch.setenv("YARVIS_API_PORT", "9002")
    assert get_settings().api_port == 9001

    reset_settings_cache()
    assert get_settings().api_port == 9002
    reset_settings_cache()


def test_worker_lease_must_exceed_poll_interval() -> None:
    try:
        Settings(worker_poll_interval_seconds=10, worker_lease_seconds=10)
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid worker timing must be rejected")
def _gmail_settings(**overrides):
    values = {
        "gmail_intake_enabled": True,
        "gmail_provider": "google",
        "gmail_google_project_id": "synthetic-project",
        "gmail_oauth_client_id_file": "/safe/client-id",
        "gmail_oauth_client_secret_file": "/safe/client-secret",
        "gmail_token_key_file": "/safe/token-key",
        "gmail_token_store_root": "/safe/token-store",
        "gmail_mailbox_binding": "file-aesgcm://netpay-gmail/binding",
    }
    values.update(overrides)
    return values


def test_gmail_pilot_accepts_only_exact_local_readonly_configuration() -> None:
    settings = Settings.model_validate(_gmail_settings())
    assert settings.gmail_oauth_scopes == "https://www.googleapis.com/auth/gmail.readonly"
    assert settings.gmail_oauth_redirect_uri == "http://127.0.0.1:8000/netpay/gmail/oauth/callback"
    assert settings.gmail_backfill_days == 30
    assert settings.scheduler_enabled is False
    assert settings.worker_enabled is False


def test_gmail_pilot_fails_closed_for_scope_runtime_or_callback_expansion() -> None:
    invalid = (
        {"gmail_oauth_scopes": "https://mail.google.com/"},
        {"gmail_oauth_redirect_uri": "http://localhost:8000/other"},
        {"gmail_backfill_days": 31},
        {"scheduler_enabled": True},
        {"worker_enabled": True},
        {"environment": "test"},
    )
    for override in invalid:
        try:
            Settings.model_validate(_gmail_settings(**override))
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Gmail pilot expansion must be rejected: {override}")
