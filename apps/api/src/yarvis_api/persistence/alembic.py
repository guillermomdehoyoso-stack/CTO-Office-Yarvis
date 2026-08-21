"""Explicit database URL resolution for the Alembic migration adapter."""

import os
from collections.abc import Mapping

from yarvis_api.config import Settings
from yarvis_api.persistence.runtime import sqlalchemy_url


def resolve_migration_database_url(
    configured_url: str | None,
    settings: Settings | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve Alembic's URL without exposing migration credentials to runtime settings."""

    migration_url = (environ or os.environ).get("YARVIS_MIGRATOR_DATABASE_URL")
    target_url = configured_url or migration_url or (settings or Settings()).database_url
    return sqlalchemy_url(target_url)
