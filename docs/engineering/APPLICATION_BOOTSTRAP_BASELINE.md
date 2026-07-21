# YARVIS
# Application Bootstrap Baseline

## Status: Implemented Engineering Baseline - F-004 Application Bootstrap

## 1. Purpose and Work-Package Identity

F-004 establishes the deterministic API composition root required by the Technical Blueprint. It constructs a FastAPI process from validated configuration without adding domain behavior, persistence activity, worker execution, scheduler execution, or module-registry behavior.

## 2. Composition Root, Factory, and ASGI Adapter

`apps/api/src/yarvis_api/bootstrap.py` is the sole API composition root. Its public factory is `create_app(settings: Settings | None = None) -> FastAPI`; every call creates a distinct application. `apps/api/src/yarvis_api/main.py` is only the Uvicorn-compatible adapter: `app = create_app()`.

The factory uses explicitly supplied settings when present and otherwise calls the canonical F-003 cached `get_settings()` provider. Application title, version, debug state, CORS configuration, and documentation routes derive from that typed settings object. With `modules=None`, it composes the F-005A canonical context-module baseline; an explicit iterable, including `()`, overrides that baseline for isolated composition. `Settings.app_version` remains the current version authority; package-metadata integration is deferred rather than duplicated.

## 3. Lifecycle, State, and Composition Boundaries

The factory uses FastAPI lifespan. It owns deterministic startup and shutdown boundaries only; it opens no database connection, runs no migration, starts no worker or scheduler, dispatches no contract, and contacts no external system.

Each application has one `ApplicationState` under `app.state.yarvis`. It contains application settings, lifecycle marker, and the per-instance sealed F-005 `ModuleRegistry`. It is typed technical state, not a mutable service locator, and must not contain domain state or concrete infrastructure services.

`register_routes`, `register_middleware`, and `register_exception_handlers` are explicit composition boundaries. Existing incremental interface routes are retained through the single route-registration function; supplied F-005 module route hooks run once in resolved registry order. CORS remains the only required middleware. Exception-handler registration is intentionally empty until F-012 establishes typed error handling.

## 4. Documentation, Health, Imports, and Tests

Documentation and OpenAPI routes are enabled only when `api_docs_enabled` is true. The setting is explicit for local, test, and production profiles; production can disable the routes. The neutral `/health` endpoint proves only API-process availability and does not claim database, worker, scheduler, or external dependency readiness.

Importing `bootstrap` starts no external resource. Constructing applications is isolated and testable without Docker or PostgreSQL connections. Importing `main.app` may validate default configuration through F-003, but composition itself does not establish external connections.

Focused tests cover factory isolation, explicit/default settings, metadata, documentation behavior, lifespan, `main.app`, neutral health, retained interface routes, and absence of bootstrap database/worker/scheduler activity. Architecture tests enforce the single factory, thin ASGI adapter, and current model-layer framework/bootstrap independence.

## 5. Prohibited Shortcuts and Deferred Capabilities

F-004 does not create a dependency-injection framework, a mutable global container, domain routes, placeholder context routes, workers, scheduler, database lifecycle, migrations, authentication, authorization, module registry, contract registry, typed exception behavior, tracing, or readiness semantics. Existing legacy interface routes are retained only for incremental compatibility; their relocation awaits approved context work.

## 6. Files, Validation, Findings, and Next Readiness

Changed implementation: `bootstrap.py`, `main.py`, and the neutral health test. Added focused bootstrap and architecture-conformance tests; quality configuration includes this new implementation scope. `REPOSITORY_STRUCTURE.md` records the new canonical composition root.

Validation evidence comprises package installation, Python 3.12, bootstrap/main imports, isolated application construction, lifespan tests, local/test/production documentation tests, no-bootstrap-connection test, Ruff, formatting, Pyright, complete backend tests, Compose rebuild/start, and `/health` smoke testing.

Findings: none. F-005 Module Registry may begin after this baseline is committed; registry, context shells, and application behavior remain deferred.

## 7. Closing Statement

F-004 makes application composition explicit and testable while preserving the ratified modular-monolith direction: configuration enters at one technical root, interface registration is centralized, and no technical bootstrap acquires domain authority.
