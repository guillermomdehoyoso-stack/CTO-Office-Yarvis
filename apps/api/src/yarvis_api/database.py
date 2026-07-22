"""Legacy FastAPI dependency adapter over the application-owned runtime.

New infrastructure must import :mod:`yarvis_api.persistence`, not this module.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from fastapi import Request
from sqlalchemy.orm import Session

from yarvis_api.persistence import sqlalchemy_url

__all__ = ["check_database_connection", "get_db", "legacy_session", "sqlalchemy_url"]


def check_database_connection(database_url: str) -> None:
    with psycopg.connect(database_url, connect_timeout=3) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


@contextmanager
def legacy_session() -> Iterator[Session]:
    """Support retained command-line utilities without a process-global session factory."""

    from yarvis_api.config import get_settings
    from yarvis_api.persistence import build_persistence_runtime

    runtime = build_persistence_runtime(get_settings())
    owner_token = object()
    runtime.transfer_ownership(owner_token)
    try:
        with runtime.create_session() as session:
            yield session
    finally:
        runtime.dispose(owner_token)


def get_db(request: Request) -> Iterator[Session]:
    """Provide a short-lived legacy route session without transaction policy."""

    with request.app.state.yarvis.persistence.create_session() as session:
        yield session
