from fastapi import FastAPI
from fastapi.testclient import TestClient

from yarvis_api.bootstrap import ApplicationState, create_app
from yarvis_api.canonical_contracts import CANONICAL_CONTRACTS
from yarvis_api.config import Settings


def test_factory_returns_distinct_applications_with_isolated_state() -> None:
    first = create_app(Settings(environment="test", app_name="First API"))
    second = create_app(Settings(environment="test", app_name="Second API"))

    assert isinstance(first, FastAPI)
    assert first is not second
    assert isinstance(first.state.yarvis, ApplicationState)
    assert first.state.yarvis is not second.state.yarvis
    assert first.state.yarvis.contract_registry is not second.state.yarvis.contract_registry
    assert first.state.yarvis.handler_registry is not second.state.yarvis.handler_registry
    assert first.state.yarvis.dispatcher is not second.state.yarvis.dispatcher
    assert first.state.yarvis.settings.app_name == "First API"
    assert second.state.yarvis.settings.app_name == "Second API"


def test_factory_uses_explicit_settings_for_metadata_and_documentation() -> None:
    settings = Settings(environment="test", app_name="Configured API", debug=True, api_docs_enabled=True)
    app = create_app(settings)

    assert app.title == "Configured API"
    assert app.debug is True
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_local_documentation_is_enabled_by_default() -> None:
    app = create_app(Settings(environment="local"))

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200


def test_factory_uses_canonical_provider_when_settings_are_omitted(monkeypatch) -> None:
    expected = Settings(environment="test", app_name="Provided API")
    monkeypatch.setattr("yarvis_api.bootstrap.get_settings", lambda: expected)

    app = create_app()

    assert app.state.yarvis.settings is expected
    assert app.title == "Provided API"


def test_production_can_disable_documentation_explicitly() -> None:
    settings = Settings.model_validate(
        {
            "environment": "production",
            "api_docs_enabled": False,
            "database_url": "postgresql://test:test@localhost/yarvis",
        }
    )
    app = create_app(settings)

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_lifespan_has_deterministic_technical_boundaries() -> None:
    app = create_app(Settings(environment="test"))

    assert app.state.yarvis.lifecycle_active is False
    with TestClient(app):
        assert app.state.yarvis.lifecycle_active is True
    assert app.state.yarvis.lifecycle_active is False


def test_bootstrap_does_not_open_database_or_start_future_runtime(monkeypatch) -> None:
    import psycopg

    def database_connection_attempt(*args, **kwargs):
        raise AssertionError("bootstrap must not connect to PostgreSQL")

    monkeypatch.setattr(psycopg, "connect", database_connection_attempt)
    app = create_app(Settings(environment="test", worker_enabled=True, scheduler_enabled=True))

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "service": "yarvis-api"}


def test_existing_interface_routes_are_preserved_without_new_business_routes() -> None:
    app = create_app(Settings(environment="test"))
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/organizations" in paths
    assert "/health" in paths
    assert "/inbox" not in paths
    assert "/automation" not in paths


def test_default_and_explicit_empty_contract_composition_are_isolated() -> None:
    default_app = create_app(Settings(environment="test"))
    empty_app = create_app(Settings(environment="test"), contracts=())
    default_contracts = default_app.state.yarvis.contract_registry.list()
    default_contract_ids = {contract.interaction_contract_id for contract in default_contracts}

    assert default_app.state.yarvis.contract_registry.is_sealed is True
    assert len(default_contracts) == len(CANONICAL_CONTRACTS) == 45
    assert {
        "IC-TASK-CMD-001",
        "IC-TASK-CMD-002",
        "IC-TASK-CMD-003",
        "IC-TASK-CMD-004",
        "IC-TASK-CMD-005",
        "IC-TASK-CMD-006",
        "IC-TASK-CMD-007",
    }.issubset(default_contract_ids)
    assert "IC-WORKSPACE-QRY-001" in default_contract_ids
    assert empty_app.state.yarvis.contract_registry.is_sealed is True
    assert empty_app.state.yarvis.contract_registry.list() == ()
    assert default_contracts != empty_app.state.yarvis.contract_registry.list()
    assert default_app.state.yarvis.handler_registry.is_sealed is True
    assert default_app.state.yarvis.handler_registry.list() == ()
