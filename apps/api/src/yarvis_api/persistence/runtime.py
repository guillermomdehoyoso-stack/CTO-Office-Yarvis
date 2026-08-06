"""Per-application SQLAlchemy persistence runtime.

This module establishes resource ownership only.  Transaction policy belongs to
the future Unit of Work work package.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from yarvis_api.config import Settings


class PersistenceRuntimeOwnershipError(ValueError):
    """Raised when a runtime is composed into more than one application."""


class PersistenceRuntimeDisposedError(RuntimeError):
    """Raised when a disposed persistence runtime is asked to open a session."""


def sqlalchemy_url(database_url: str) -> str:
    """Normalize a PostgreSQL URL for SQLAlchemy's synchronous psycopg dialect."""

    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    raise ValueError("database URL must use a PostgreSQL scheme")


@dataclass(slots=True)
class PersistenceRuntime:
    """One lazily connecting Engine and session factory owned by one application."""

    engine: Engine
    session_factory: sessionmaker[Session]
    _database_url: str = field(repr=False)
    _owner_token: object | None = field(default=None, init=False, repr=False)
    _disposed: bool = field(default=False, init=False, repr=False)

    @property
    def is_disposed(self) -> bool:
        """Expose only the safe readiness state; never the underlying Engine."""

        return self._disposed

    def transfer_ownership(self, owner_token: object) -> None:
        """Transfer this runtime to exactly one application composition root."""

        if self._owner_token is not None:
            raise PersistenceRuntimeOwnershipError("persistence runtime is already owned by an application")
        if self._disposed:
            raise PersistenceRuntimeDisposedError("disposed persistence runtime cannot be owned")
        self._owner_token = owner_token

    def is_compatible_with(self, settings: Settings) -> bool:
        """Check composition compatibility without exposing secret configuration."""

        return self._database_url == sqlalchemy_url(settings.database_url)

    def create_session(self) -> Session:
        """Create one explicit session without defining transaction behavior."""

        if self._disposed:
            raise PersistenceRuntimeDisposedError("disposed persistence runtime cannot create sessions")
        return self.session_factory()

    def dispose(self, owner_token: object) -> None:
        """Dispose the Engine only when requested by its owning application."""

        if self._owner_token is not owner_token:
            raise PersistenceRuntimeOwnershipError("persistence runtime disposal requires its owning application")
        if not self._disposed:
            self.engine.dispose()
            self._disposed = True


def build_persistence_runtime(settings: Settings) -> PersistenceRuntime:
    """Build a synchronous runtime without opening a database connection."""

    normalized_url = sqlalchemy_url(settings.database_url)
    engine = create_engine(normalized_url, pool_pre_ping=True)
    return PersistenceRuntime(
        engine=engine,
        session_factory=sessionmaker(bind=engine, autoflush=False, autocommit=False),
        _database_url=normalized_url,
    )
