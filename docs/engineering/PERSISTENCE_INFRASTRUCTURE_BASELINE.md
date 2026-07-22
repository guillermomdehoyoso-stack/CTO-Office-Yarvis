# YARVIS
# Persistence Infrastructure Baseline

## Status: Implemented Engineering Baseline — F-007 Persistence Infrastructure

## 1. Work-Package Identity and Purpose

F-007 establishes the application-owned persistence resource boundary required
by the ratified Persistence Infrastructure Design. It supplies synchronous
PostgreSQL/SQLAlchemy/psycopg Engine and Session construction without defining
repositories, canonical business state, transaction policy, or dispatch.

## 2. Canonical Authority and Files

`apps/api/src/yarvis_api/persistence/runtime.py` is the canonical runtime
authority. `PersistenceRuntime` contains one synchronous SQLAlchemy Engine and
one session factory. `build_persistence_runtime(settings)` is the explicit
construction operation. `yarvis_api.database` remains only a transitional
FastAPI route-session adapter and contains no Engine or session-factory global.

## 3. Configuration, Engine, and Session Lifecycle

`Settings.database_url_secret` remains the sole database configuration source.
The persistence adapter normalizes accepted PostgreSQL URLs to SQLAlchemy's
`postgresql+psycopg` dialect without logging or exposing the URL. Construction
uses `pool_pre_ping=True` and does not open a connection. Sessions are created
explicitly through `PersistenceRuntime.create_session()` and close through their
caller's context manager. F-007 intentionally defines no commit, rollback,
retry, idempotency, outbox, repository, or Unit of Work semantics.

## 4. Ownership and Bootstrap Integration

`create_app(settings=None, modules=None, contracts=None, persistence=None)`
builds or accepts one runtime after contract composition. Composition transfers
the runtime to an opaque application-local ownership token. A runtime already
owned by another application is rejected deterministically. Each
`ApplicationState` stores its typed `persistence` runtime and its non-service
ownership token; it remains a technical lifecycle root, not a service locator.
The FastAPI lifespan disposes only the Engine owned by that application. A
supplied runtime must be compatible with the application's typed settings;
incompatible composition fails without revealing the connection URL.

## 5. Migration Governance

Alembic remains an explicit process at `apps/api/migrations`. Its environment
reads typed `Settings` and normalizes through the canonical persistence adapter;
it never imports bootstrap or reuses a live application Engine. Bootstrap,
requests, workers, and schedulers do not run migrations or create tables.
Existing migration history is retained; F-007 introduces no business schema.

## 6. Compatibility and Domain Independence

Existing retained routes receive short-lived Sessions from the application-owned
runtime via the legacy interface adapter. New code must import
`yarvis_api.persistence`, not `yarvis_api.database`. Domain models may not
import FastAPI, persistence runtime, session factories, or application state.
No global runtime, Engine, session factory, singleton, or discovery mechanism
exists in the canonical path.

## 7. Validation Evidence

Focused tests cover URL normalization, lazy construction, explicit Session
creation, supplied-runtime ownership transfer, deterministic reuse rejection,
application isolation, lifespan disposal, and explicit PostgreSQL connection.
Architecture checks verify that the legacy adapter exposes no global Engine or
session factory and that domain models do not import persistence infrastructure.
The backend suite and Alembic upgrade verification run against the isolated
PostgreSQL test database established by the repository test fixture.

## 8. Deferred Capabilities and F-008 Readiness

F-008 may consume `PersistenceRuntime.create_session()` to establish one
context-local Unit of Work. It must own commit, rollback, outbox, and repository
binding semantics. Async persistence, multiple databases, readiness checks,
workers, scheduler persistence, repositories, and business migrations remain
deferred.

## 9. Closing Statement

F-007 makes persistence an explicit, isolated application resource while
preserving the rule that storage mechanics never create domain authority.
