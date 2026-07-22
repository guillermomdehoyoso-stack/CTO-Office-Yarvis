# YARVIS
# Persistence Infrastructure Design

## Status: Ratified Engineering Design

## Amendment History

| Amendment | Status | Summary |
| --- | --- | --- |
| `PERSISTENCE-INFRASTRUCTURE-AMENDMENT-001` | Ratified engineering-design alignment | Defines exclusive PersistenceRuntime ownership and rejects reuse across application instances. |

## 1. Work-Package Identity and Purpose

**Work package:** F-007 — Database and Migrations  
**Phase:** Design only

F-007 defines the technical persistence infrastructure that will support
context-owned canonical state, append-only records, projections, and later
Unit of Work behavior without making a database, ORM model, or repository a
source of domain authority.

Its governing question is: **how is persistence composed, configured,
acquired, and retired while preserving Yarvis ownership boundaries?**

## 2. Authority and Architectural Position

Authority remains the Constitution, Application Architecture, Identity and
Governance Model, Interaction Contract Catalog, Architectural Decision Trace,
Technical Blueprint, and established Engineering Foundation baselines.

Persistence is infrastructure. Context modules own canonical semantics and
future repositories; PostgreSQL tables, SQLAlchemy mappings, sessions, and
migrations do not create ownership. One context's transaction must not become
another context's mutation path.

## 3. Selected Persistence Architecture

F-007 selects one canonical relational persistence foundation:

| Concern | Selection | Reason |
| --- | --- | --- |
| Database | PostgreSQL 16 | Ratified Technical Blueprint selection; existing Compose topology; transactional, relational, JSON-metadata, and durable-work capability. |
| SQL toolkit | SQLAlchemy 2.x | Ratified mapping technology; confines mapping mechanics to infrastructure and supports explicit Engine/Session lifecycle. |
| Driver | psycopg 3 through SQLAlchemy's `postgresql+psycopg` dialect | Existing runtime dependency and synchronous migration compatibility. |
| Engine model | Synchronous SQLAlchemy `Engine` | Matches the existing synchronous psycopg and SQLAlchemy baseline, Alembic's synchronous execution model, and a modular-monolith first slice. |
| Session model | Synchronous SQLAlchemy `Session` created by a per-application factory | Keeps a session local to a future context-local Unit of Work and avoids mixed sync/async transaction semantics. |
| Migration tool | Alembic | Ratified versioned-migration mechanism. |

`AsyncEngine` and `AsyncSession` are not the F-007 foundation. They would add a
second transaction model without a ratified need. A later architecture-approved
adapter change may introduce async persistence only behind the same ownership
and Unit of Work boundaries; it must not mix session models inside one unit of
work.

## 4. Repository Layout

F-007 implementation will add one technical package rather than expand the
legacy global module:

```text
apps/api/src/yarvis_api/
  persistence/
    __init__.py
    runtime.py          # PersistenceRuntime and Engine construction
    sessions.py         # Session-factory and session-lifecycle boundary
    migrations.py       # Alembic invocation/configuration boundary, if needed
```

`apps/api/src/yarvis_api/database.py` is a legacy transitional implementation
with a process-global engine and `SessionLocal`. It is not the F-007 authority.
F-007 implementation must move new technical composition to `persistence/`
and incrementally redirect legacy callers; it must not perform a mass model or
repository relocation.

Alembic remains at `apps/api/migrations/` with `alembic.ini`. Existing migration
history is retained. The Alembic environment is a migration adapter, not an
application composition root.

## 5. Configuration Model

`yarvis_api.config.Settings` remains the sole application configuration
authority. `database_url_secret` supplies the PostgreSQL URL and remains
secret-classified. A persistence configuration adapter derives the SQLAlchemy
URL by selecting the psycopg dialect; it must not log or expose the raw URL.

F-007 may add typed, non-secret pool and connection settings only when an
implementation requirement needs them. Their defaults must be deterministic,
profile-aware, and validated by `Settings`. Neither environment variables nor
Alembic configuration files become an alternate source of database authority.

The configured URL is accepted only for PostgreSQL. SQLite and in-memory
substitutions are not canonical F-007 runtime or integration-test databases
because they would weaken PostgreSQL migration and transaction conformance.

## 6. Engine Lifecycle and Connection Factory

Future `PersistenceRuntime` is an application-owned immutable technical object
containing:

- one synchronous SQLAlchemy `Engine`;
- one session factory bound to that Engine; and
- safe, non-secret diagnostic metadata only where needed.

`build_persistence_runtime(settings)` is the explicit composition operation.
It creates the Engine from the resolved typed settings and configures
connection-pool health checking. Engine construction must be lazy with respect
to opening a database connection: application bootstrap may compose the
runtime, but it must not connect, run migrations, create tables, or validate
business state.

Each `create_app` call receives or builds one distinct runtime. There is no
global engine, singleton, module-import side effect, mutable service locator,
or shared process registry. Each `PersistenceRuntime` has exactly one owning
application instance. A runtime built during composition transfers directly to
that application; a supplied runtime transfers exclusive ownership when it is
accepted by composition. An owned runtime must not be composed into another
application. Reuse must fail explicitly and deterministically; reference
counting and shared runtimes are prohibited.

The API lifespan owns disposal: on shutdown it stops accepting new work through
later runtime controls and calls the Engine's safe disposal operation only for
the runtime owned by that application. It never disposes another application's
Engine.

Connection acquisition occurs only when a future session is opened or an
explicit infrastructure health/migration action runs. Neutral `/health`
continues to report API-process availability only; database readiness belongs
to a later readiness control.

## 7. Session Lifecycle

The session factory creates a new synchronous `Session` per future application
operation or context-local Unit of Work. Sessions are never global, never held
in `ApplicationState`, and never imported by domain code.

The session boundary has these rules:

1. A session is opened explicitly by infrastructure/application composition.
2. It is supplied only to the context-owned repository adapters participating
   in the same future Unit of Work.
3. The caller closes it in `finally`, including after errors.
4. F-007 does not define commit, rollback, retry, idempotency, or outbox
   behavior; F-008 Unit of Work will own those transaction decisions.
5. A session may not be shared across contexts as a shortcut to a distributed
   transaction.

The future public technical interface is therefore a runtime/session-factory
boundary, not a `get_db` framework dependency exported to domain or interface
code. FastAPI dependency adaptation, if later needed, must remain an Interface
adapter over the application-owned session/UoW boundary.

## 8. Migration Architecture and Alembic Integration

Alembic is the canonical migration mechanism. Migrations are explicit,
versioned persistence changes and are run by an operator or controlled delivery
command, never by API bootstrap, worker startup, import side effects, or a
request path.

The future Alembic environment must obtain its URL through the same typed
configuration authority used by the application, while remaining independently
invocable as a migration process. It may normalize that URL for the psycopg
SQLAlchemy dialect. It must not import `bootstrap`, construct an application,
or reuse a live application Engine.

Migration governance rules are:

- retain existing migration history and heads;
- do not edit an applied migration;
- create explicit revisions for every schema change;
- prefer additive and forward-compatible changes;
- provide downgrade only when it is materially safe; otherwise record why it
  is intentionally unavailable;
- never use `create_all` as a production schema-management path;
- validate empty-database upgrade and existing-database upgrade paths; and
- require rollback and restore procedures to target a non-primary database by
  default.

Migration metadata reflects persistence structure only. It must not redefine
bounded-context ownership, contract semantics, governance, or canonical truth.

## 9. Application Composition and State

F-007 will extend the existing factory conceptually as follows:

```python
create_app(settings=None, modules=None, contracts=None, persistence=None)
```

The intended composition order is:

```text
Settings
  → ModuleRegistry
  → ContractRegistry
  → PersistenceRuntime
  → typed ApplicationState
  → route registration
```

`persistence=None` selects a newly built runtime from that application's
settings. An explicit runtime is permitted only for isolated tests or controlled
composition and replaces the default for that application. Acceptance transfers
exclusive ownership to that application; bootstrap must reject a supplied
runtime that is already owned. The runtime must remain compatible with the
supplied Settings and be independently disposable by its owner.

`ApplicationState` will gain one typed `persistence` field. This field is an
application-lifecycle resource root, not a generic service-locator dictionary.
It must not contain repositories, domain services, module internals, active
sessions, transactions, or canonical state.

Module Registry and Contract Registry remain metadata/composition authorities.
They neither create database connections nor grant session access. Future
repository adapters are context-owned and receive persistence through explicit
application composition or future Unit of Work construction.

## 10. Future Unit of Work Integration

F-008 will depend on the F-007 session-factory boundary. A Unit of Work will:

- create one session from the per-application runtime;
- bind that session to one owning context's repository adapters;
- define commit, rollback, outbox, idempotency, and failure semantics; and
- close the session deterministically.

F-007 must not introduce a generic cross-context transaction wrapper,
repository registry, ambient thread-local session, or transaction policy.
Cross-context coordination will continue through public contracts, durable
owner assertions, projections, and later compensation—not shared sessions.

## 11. Dependency Model

```text
Settings
  → PersistenceRuntime
  → Engine / Session factory
  → future infrastructure repository adapter
  → future context application boundary
  → future context Domain

Alembic migration adapter → Settings + persistence metadata only
```

Dependencies point inward. Domain code must not import SQLAlchemy, psycopg,
Alembic, `PersistenceRuntime`, session factories, `app.state`, environment
variables, or the legacy `database.py`. Application code depends on an
inward-owned persistence port only when a later context work package defines
one. Infrastructure implements the port and is wired exclusively at
composition.

## 12. Testing Strategy

F-007 implementation will use PostgreSQL-backed tests, not SQLite stand-ins,
for connection, transaction, and migration conformance. Test database URLs are
explicit injected configuration and must not target the local development or
production database.

Required evidence includes:

1. per-application Engine/runtime isolation;
2. no connection during bootstrap or module/contract registry composition;
3. explicit connection verification when requested by an infrastructure test;
4. session creation and deterministic close without transaction policy;
5. Engine disposal on application shutdown;
6. runtime reuse rejection: one runtime cannot attach to two applications, and
   each application disposes only its own runtime;
7. empty PostgreSQL database upgrade to Alembic head;
8. upgrade from the retained existing migration history to head;
9. safe failure on invalid PostgreSQL configuration without secret leakage;
10. no domain import of persistence infrastructure; and
11. no migration execution in bootstrap, worker, or request paths.

Fixtures must be synthetic and isolated. Integration tests create an ephemeral
or uniquely named PostgreSQL test database and remove it only through an
explicit test-lifecycle cleanup operation after validation.

## 13. Explicit Exclusions

F-007 does not implement repositories, ORM models, tables, entities, business
objects, Unit of Work, dispatch, outbox, workers, scheduler, authorization,
identity, domain events, business modules, payload bindings, or HTTP bindings.
It also does not select multiple databases, microservices, a broker, an async
session model, or a generic cross-context data-access layer.

## 14. Risks and Mitigations

| Risk | Classification | Mitigation |
| --- | --- | --- |
| Legacy global `database.py` bypasses application isolation | Architectural | Make `persistence/` the F-007 authority; incrementally redirect callers and add conformance checks. |
| Bootstrap connection or migration causes startup coupling | Architectural / operational | Construct lazily; prohibit connection, migration, and schema work in bootstrap. |
| Session becomes a cross-context mutation shortcut | Architectural | Restrict sessions to future context-local UoW and repository adapters; test prohibited imports/access. |
| Migration drift or destructive revision | Migration | Retain history, test empty/upgrade paths, review revisions, prefer additive compatibility. |
| Test touches development data | Testing / operational | Require explicit isolated PostgreSQL test URL and fail safe when unsafe targets are detected. |
| Pool exhaustion or stale connections | Operational | Configure pool health checks, dispose on shutdown, and add later readiness/metrics controls. |
| Future scale requires different pool or async model | Future scaling | Keep Engine/session factory behind `PersistenceRuntime`; evolve through an approved adapter boundary. |

## 15. Acceptance Criteria

F-007 implementation may be accepted only when:

1. PostgreSQL 16, SQLAlchemy 2.x synchronous Engine/Session, psycopg, and
   Alembic are composed explicitly per application.
2. No global Engine, session factory, or hidden state remains in the canonical
   F-007 path.
3. Typed settings are the sole configuration authority and secrets remain
   redacted.
4. Bootstrap builds but does not connect, migrate, or initialize database
   state; lifecycle disposes only its own Engine.
5. One runtime cannot attach to two applications; attempted reuse fails
   deterministically, and each application disposes only its owned runtime.
6. Sessions are explicit, short-lived, deterministic, and unavailable to
   domain code.
7. Alembic uses controlled typed configuration, retains prior migration
   history, and passes empty/upgrade-path verification.
8. Tests prove application/runtime isolation, disposal, migration behavior,
   and no persistence leakage into domains.
9. No repository, model, Unit of Work, dispatch, or business behavior is
   introduced.

## 16. Future Work and Closing Statement

F-008 will add the context-local Unit of Work and transactional outbox rules on
this session lifecycle. F-010 will add durable worker/scheduler persistence
only after dispatch and its owning contracts exist. Context-owned repositories,
ORM mappings, and canonical tables belong to later operational-domain work.

F-007 gives Yarvis a deterministic persistence foundation: technology is
explicitly composed and replaceable, while context ownership, contract
governance, and domain truth remain outside the database.
