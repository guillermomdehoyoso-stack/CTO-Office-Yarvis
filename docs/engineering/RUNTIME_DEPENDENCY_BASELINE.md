# YARVIS
# Runtime Dependency Baseline

## Status: Implemented Engineering Baseline — F-002 Runtime/dependency baseline

## Purpose

Establish reproducible package installation, dependency authority, FastAPI execution, test discovery, and initial static-quality commands without introducing business behavior.

## Dependency Authority

- `apps/api/requirements.txt` is the canonical runtime dependency authority: FastAPI, PostgreSQL driver, SQLAlchemy, Alembic, validation support, Uvicorn, XLSX support, and multipart intake support.
- `apps/api/requirements-dev.txt` extends runtime dependencies with pytest, Ruff, and Pyright.
- `apps/api/pyproject.toml` is package/build metadata and quality-tool configuration only; it deliberately does not duplicate runtime dependencies.

Supported Python is `>=3.12,<3.13`. The package is installed editable from `apps/api`.

## Canonical Commands

```text
# setup, from apps/api
python -m pip install -r requirements-dev.txt
python -m pip install -e .

# run, from apps/api
uvicorn yarvis_api.main:app --reload

# test, from apps/api
pytest -ra

# lint, from apps/api
ruff check

# format check, from apps/api
ruff format --check

# type check, from apps/api
pyright
```

Docker remains compatible through `docker compose up -d --build`; the API image adds `libatomic1`, required by the selected Pyright runtime, installs the canonical runtime requirements, and resolves `src` through the existing `--app-dir src` setting.

## Validation and Deferred Capabilities

F-002 adds architecture tests for package root, Python support, dependency/quality authority, and FastAPI application import. Ruff and Pyright initially cover new architecture-test code; existing legacy source is intentionally excluded until a later approved conformance work package establishes incremental remediation. Expansion to new application modules is required as those modules are introduced. No repositories, migrations, dispatch, worker, scheduler, authentication, authorization, or business behavior is implemented here.

## Findings and Next Readiness

The local host Python launcher is unavailable in the current environment; Docker is the executable validation environment. The next approved work package is F-003 Configuration, which may consume this package/install baseline.
