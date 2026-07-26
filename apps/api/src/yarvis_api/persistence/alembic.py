"""Explicit database URL resolution for the Alembic migration adapter."""

from yarvis_api.config import Settings
from yarvis_api.persistence.runtime import sqlalchemy_url


def resolve_migration_database_url(
    configured_url: str | None,
    settings: Settings | None = None,
) -> str:
    """Prefer an explicitly configured Alembic URL; otherwise use application settings."""

    target_url = configured_url if configured_url else (settings or Settings()).database_url
    return sqlalchemy_url(target_url)
