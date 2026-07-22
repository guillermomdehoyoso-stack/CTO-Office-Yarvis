from __future__ import annotations

from functools import lru_cache
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
    worker_enabled: bool = False
    worker_poll_interval_seconds: int = 5
    worker_lease_seconds: int = 30
    scheduler_enabled: bool = False
    scheduler_poll_interval_seconds: int = 30

    @property
    def database_url(self) -> str:
        return self.database_url_secret.get_secret_value()

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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
