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
