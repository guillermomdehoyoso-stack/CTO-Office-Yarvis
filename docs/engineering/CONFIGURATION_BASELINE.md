# YARVIS
# Configuration Baseline

## Status: Implemented Engineering Baseline — F-003 Configuration

## 1. Purpose and Authority

F-003 establishes the single typed process-configuration authority for API, future worker, and future scheduler processes. It is infrastructure configuration, not domain state, and is governed by the Technical Blueprint and ratified authority boundaries.

## 2. Implementation, Sources, and Environments

The canonical implementation is `apps/api/src/yarvis_api/config.py`. `Settings` is the single `pydantic-settings` model; `get_settings()` is a cached provider for bootstrap/interface/infrastructure composition, while tests construct `Settings` directly and use `reset_settings_cache()`.

Supported environments are `local`, `test`, and `production`. Environment selection grants no authority. Precedence is explicit constructor values, process environment, then safe defaults. The application does not auto-load `.env` files or depend on the current working directory. Docker Compose reads the root `.env` for Compose substitution and injects `YARVIS_` values into the API.

## 3. Convention, Categories, and Secrets

The stable prefix is `YARVIS_`. Legacy `DATABASE_URL` and `DOCUMENT_STORAGE_ROOT` are supported as documented transitional aliases for existing Docker/tests. Settings include application identity/environment/debug/log/API/CORS; database and document storage; intake limits; and non-operational worker/scheduler preparation flags and timing.

`database_url_secret` is secret-classified, excluded from normal representation, and has no production-safe default. Application/database/document locations, ports, intervals, and log level are public/internal operational configuration. Derived values are the resolved database URL and parsed CORS origins; none are domain state.

## 4. Validation and Safe Startup

Ports, log level, host/storage path, PostgreSQL URL scheme, positive timing, worker lease ordering, supported environment, production debug, and production local-default database use are validated. Invalid configuration raises before the FastAPI application can finish import/startup; errors do not display secret values.

## 5. Docker, Tests, and Deferred Capabilities

Compose injects `YARVIS_ENVIRONMENT`, `YARVIS_DATABASE_URL`, and `YARVIS_DOCUMENT_STORAGE_ROOT`. `.env.example` contains local Compose values and non-secret `YARVIS_` examples; real `.env` variants remain ignored. Tests use direct construction, `monkeypatch`, and cache reset without environment leakage.

Authentication, authorization, workers, scheduler behavior, observability pipeline, repositories, and business configuration remain deferred. The next work package is F-004 Application Bootstrap.
