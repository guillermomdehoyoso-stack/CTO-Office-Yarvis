from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "production"]
DEFAULT_LOCAL_DATABASE_URL = "postgresql://yarvis:yarvis@localhost:5432/yarvis"


class Settings(BaseSettings):
    """Typed process configuration; domain modules must not read process environment."""

    model_config = SettingsConfigDict(
        env_prefix="YARVIS_",
        env_file=None,
        extra="ignore",
        hide_input_in_errors=True,
        populate_by_name=True,
    )

    app_name: str = "Yarvis API"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_docs_enabled: bool = True
    database_url_secret: SecretStr = Field(
        default=SecretStr(DEFAULT_LOCAL_DATABASE_URL),
        validation_alias=AliasChoices("database_url", "YARVIS_DATABASE_URL", "DATABASE_URL"),
        repr=False,
    )
    document_storage_root: str = Field(
        default="/data/yarvis",
        validation_alias=AliasChoices("document_storage_root", "YARVIS_DOCUMENT_STORAGE_ROOT", "DOCUMENT_STORAGE_ROOT"),
    )
    max_upload_size_bytes: int = 5_242_880
    preview_row_limit: int = 200
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auth_mode: Literal["deterministic", "oidc"] = "deterministic"
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: SecretStr | None = Field(default=None, repr=False)
    oidc_attempt_encryption_key: SecretStr | None = Field(default=None, repr=False)
    oidc_redirect_uri: str | None = None
    oidc_post_login_redirect_allowlist: str = "/"
    oidc_allowed_algorithms: str = "RS256"
    session_cookie_name: str = "yarvis_session"
    session_idle_seconds: int = 1800
    session_absolute_seconds: int = 28800
    session_max_active: int = 3
    csrf_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    bootstrap_enabled: bool = False
    bootstrap_window_seconds: int = 86400
    auth_rate_limit_backend: Literal["memory", "shared"] = "memory"
    auth_deployment_replicas: int = 1
    auth_cleanup_session_retention_days: int = 7
    worker_enabled: bool = False
    worker_poll_interval_seconds: int = 5
    worker_lease_seconds: int = 30
    scheduler_enabled: bool = False
    scheduler_poll_interval_seconds: int = 30
    workspace_access_token_secret: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("workspace_access_token", "YARVIS_WORKSPACE_ACCESS_TOKEN"),
        repr=False,
    )
    workspace_repository_root: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("workspace_repository_root", "YARVIS_WORKSPACE_REPOSITORY_ROOT"),
    )

    @property
    def database_url(self) -> str:
        return self.database_url_secret.get_secret_value()

    @property
    def workspace_access_token(self) -> str | None:
        if self.workspace_access_token_secret is None:
            return None
        return self.workspace_access_token_secret.get_secret_value()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, value: int) -> int:
        if not 1 <= value <= 65_535:
            raise ValueError("API port must be between 1 and 65535")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("log level must be a supported standard level")
        return normalized

    @field_validator("document_storage_root", "api_host")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("database_url_secret")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
            raise ValueError("database URL must use a PostgreSQL scheme")
        return value

    @field_validator("worker_poll_interval_seconds", "worker_lease_seconds", "scheduler_poll_interval_seconds")
    @classmethod
    def validate_positive_interval(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("interval must be positive")
        return value

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> Settings:
        if self.environment == "production" and self.debug:
            raise ValueError("production debug must be disabled")
        if self.worker_lease_seconds <= self.worker_poll_interval_seconds:
            raise ValueError("worker lease duration must exceed worker polling interval")
        if self.environment == "production" and self.database_url == DEFAULT_LOCAL_DATABASE_URL:
            raise ValueError("production requires an explicit database URL")
        if self.environment == "production":
            if self.auth_mode != "oidc":
                raise ValueError("production requires OIDC authentication")
            required = (
                self.oidc_issuer,
                self.oidc_client_id,
                self.oidc_client_secret,
                self.oidc_attempt_encryption_key,
                self.oidc_redirect_uri,
            )
            if any(value is None for value in required):
                raise ValueError("production OIDC configuration is incomplete")
            issuer = self.oidc_issuer
            redirect_uri = self.oidc_redirect_uri
            assert issuer is not None and redirect_uri is not None
            if not issuer.startswith("https://") or not redirect_uri.startswith("https://"):
                raise ValueError("production OIDC endpoints require HTTPS")
            if any("*" in origin or "localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origin_list):
                raise ValueError("production CORS origins must be exact non-local origins")
            if not self.session_cookie_name.startswith("__Host-"):
                raise ValueError("production session cookie must use __Host- prefix")
            if self.auth_deployment_replicas > 1 and self.auth_rate_limit_backend != "shared":
                raise ValueError("multi-replica production authentication requires a shared rate-limit backend")
        if self.bootstrap_window_seconds > 86400:
            raise ValueError("bootstrap window cannot exceed 24 hours")
        if self.session_idle_seconds != 1800 or self.session_absolute_seconds != 28800:
            raise ValueError("session durations must match AUTH-POLICY-001")
        if self.session_max_active != 3:
            raise ValueError("maximum active sessions must match AUTH-POLICY-001")
        return self

    @property
    def csrf_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.csrf_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
