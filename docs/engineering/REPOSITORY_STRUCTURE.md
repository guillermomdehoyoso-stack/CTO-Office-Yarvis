# YARVIS
# Repository Structure

## Status: Implemented Engineering Baseline — F-001

## 1. Purpose, Scope, and Authority

This document records the minimum normalized repository structure implemented by F-001 Repository Normalization. It is governed by the Technical Blueprint and does not redefine application or bounded-context authority.

## 2. Canonical Roots and Entry Point

| Concern | Canonical location / authority |
| --- | --- |
| Python source root | `apps/api/src` |
| Python package root | `apps/api/src/yarvis_api` |
| Application entry point | `apps/api/src/yarvis_api/main.py` |
| Python package metadata | `apps/api/pyproject.toml` |
| Runtime dependencies | `apps/api/requirements.txt` |
| Development/test dependencies | `apps/api/requirements-dev.txt`, extending runtime requirements |
| Backend tests | `apps/api/tests` |
| Architecture-conformance tests | `apps/api/tests/architecture` |
| Web application | `apps/web/src` |
| Database migrations | `apps/api/migrations` |
| Scripts | `scripts` |
| Architecture documentation | `docs/architecture` |
| Engineering documentation | `docs/engineering` |

The `src` layout is the only backend import root. `yarvis_api.main:app` is the only API application entry point. Existing route, model, schema, service, storage, and module files remain in place until a subsequent approved work package moves a file for a concrete boundary reason.

## 3. Configuration, Environment, and Generated Files

`apps/api/requirements.txt` is the canonical runtime dependency manifest. `requirements-dev.txt` extends it only for development, test, lint, and type-check tools. `pyproject.toml` is the canonical package metadata, build, lint, format, and type-check configuration; it must not duplicate runtime dependency authority. The editable development installation is `python -m pip install -r requirements-dev.txt` followed by `python -m pip install -e .` from `apps/api`.

`.env.example` documents local examples only. `.env` files, credentials, keys, document uploads, databases, backups, caches, logs, virtual environments, test/build outputs, and editor-local files are not committed. `docker-compose.yml` is the canonical local service topology.

## 4. Naming, Import, Context, and Infrastructure Rules

- Interface code may translate requests; it must not own domain rules.
- Domain code must not import framework, persistence, transport, or external-provider implementations.
- Context internals cannot be imported by another context; collaboration uses public contracts.
- Database models are persistence details, not shared domain objects.
- Repositories remain context-owned and cannot cross context ownership.
- Shared technical primitives may contain no mutable domain state or mixed business authority.
- Infrastructure adapters belong under context infrastructure or shared technical infrastructure, never in Domain.
- A generic `services` directory is transitional only; new work must use the approved context/module boundary.
- Empty future packages are not evidence that a capability is implemented.

## 5. Files Retained, Files Moved, and Deferred Directories

No existing files were moved or deleted in F-001. Existing backend tests remain discoverable at `apps/api/tests`; the immediate architecture-test root is added for structural conformance. Context `domain/application/interface/infrastructure` directories, worker/scheduler packages, contract bindings, and persistence ports are deferred until their approved work packages need executable contents. This avoids an empty directory forest and false capability claims.

## 6. Validation Commands and F-002 Readiness

Canonical local commands:

```text
docker compose up -d --build
docker compose exec api sh -lc "pip install -q -r requirements-dev.txt && pytest -ra"
```

F-002 may rely on the canonical package root, package metadata, test root, and explicit structural rules. It may not bypass the current entry point, dependency manifests, or context ownership rules.

## 7. Closing Statement

F-001 establishes a stable, incremental repository baseline: one backend source root, one Yarvis package, one API entry point, one runtime dependency authority, and one test root with an explicit conformance location.
