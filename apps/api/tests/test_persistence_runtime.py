from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from yarvis_api.bootstrap import create_app
from yarvis_api.config import Settings
from yarvis_api.persistence import (
    PersistenceRuntimeDisposedError,
    PersistenceRuntimeOwnershipError,
    build_persistence_runtime,
    sqlalchemy_url,
)


def test_runtime_build_is_lazy_and_uses_psycopg_dialect() -> None:
    settings = Settings(environment="test")
    runtime = build_persistence_runtime(settings)

    assert runtime.engine.url.drivername == "postgresql+psycopg"
    assert sqlalchemy_url("postgresql://user:password@host/database").startswith("postgresql+psycopg://")
    runtime.engine.dispose()


def test_runtime_creates_explicit_sessions_without_transaction_policy() -> None:
    runtime = build_persistence_runtime(Settings(environment="test"))

    with runtime.create_session() as session:
        assert session.in_transaction() is False

    runtime.engine.dispose()


def test_applications_receive_distinct_owned_runtimes() -> None:
    first = create_app(Settings(environment="test"))
    second = create_app(Settings(environment="test"))

    assert first.state.yarvis.persistence is not second.state.yarvis.persistence
    first.state.yarvis.persistence.dispose(first.state.yarvis.persistence_owner_token)
    second.state.yarvis.persistence.dispose(second.state.yarvis.persistence_owner_token)


def test_supplied_runtime_transfers_to_one_application_only() -> None:
    runtime = build_persistence_runtime(Settings(environment="test"))
    app = create_app(Settings(environment="test"), persistence=runtime)

    with pytest.raises(PersistenceRuntimeOwnershipError, match="already owned"):
        create_app(Settings(environment="test"), persistence=runtime)

    app.state.yarvis.persistence.dispose(app.state.yarvis.persistence_owner_token)


def test_supplied_runtime_must_match_application_settings() -> None:
    runtime = build_persistence_runtime(Settings(environment="test"))
    incompatible = Settings.model_validate(
        {
            "environment": "test",
            "database_url": "postgresql://other:other@localhost/other_database",
        }
    )

    with pytest.raises(ValueError, match="incompatible"):
        create_app(incompatible, persistence=runtime)

    runtime.engine.dispose()


def test_lifespan_disposes_only_its_owned_runtime() -> None:
    runtime = build_persistence_runtime(Settings(environment="test"))
    app = create_app(Settings(environment="test"), persistence=runtime)

    with TestClient(app):
        assert app.state.yarvis.lifecycle_active is True

    with pytest.raises(PersistenceRuntimeDisposedError, match="disposed"):
        runtime.create_session()


def test_bootstrap_does_not_connect_to_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_connection(*args: object, **kwargs: object) -> object:
        raise AssertionError("persistence runtime construction must not connect")

    monkeypatch.setattr("psycopg.connect", unexpected_connection)
    app = create_app(Settings(environment="test"))

    assert app.state.yarvis.persistence.engine.url.drivername == "postgresql+psycopg"
    app.state.yarvis.persistence.dispose(app.state.yarvis.persistence_owner_token)


def test_session_connection_is_explicit_in_postgresql_integration(test_database: None) -> None:
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(text("SELECT 1")) == 1
