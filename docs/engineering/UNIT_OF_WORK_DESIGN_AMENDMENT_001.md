# YARVIS
# Unit of Work Design Amendment 001

## Status: Consolidated Engineering-Design Amendment

## 1. Amendment Identity

**Amendment ID:** `UNIT-OF-WORK-DESIGN-AMENDMENT-001`  
**Affected work package:** F-008 — Unit of Work  
**Phase:** Design Amendment

## 2. Reason and Findings Resolved

The F-008 Engineering Design Review identified material ambiguity in canonical
activation, Session versus transaction terminology, failure transitions,
nested-use detection, and legacy-path containment. This amendment resolves
those findings without redesigning Persistence Infrastructure, repositories,
Dispatch, or domain behavior.

## 3. Activation and Lifecycle Clarification

Synchronous `__enter__` is the only canonical activation path. Construction
creates neither Session nor transaction. Entry validates the explicit operation
scope, rejects nesting, acquires one Session, explicitly begins one transaction,
transitions to `ACTIVE`, and returns the Unit of Work. There is no public
`begin()` method and SQLAlchemy autobegin is not the architectural boundary.

The consolidated lifecycle is:

```text
NEW → ACTIVE → COMMITTED | ROLLED_BACK | FAILED → DISPOSED
NEW → FAILED → DISPOSED
```

`FAILED` represents failed acquisition, explicit activation, commit, rollback,
or close/disposal processing. It prohibits further business activity, commit,
and public rollback while allowing only safe final close cleanup.

## 4. Failure, Context-Manager, and Disposal Semantics

Session-acquisition failure moves to `FAILED`, preserves the original exception,
and rolls back only if a transaction actually activated. Explicit activation
failure closes the acquired Session and retains cleanup failure only as secondary
diagnostic context.

Commit failure moves to `FAILED`, attempts one permitted cleanup rollback,
preserves and re-raises the original commit exception, and prohibits later
commit or public rollback. Rollback failure moves to `FAILED`, re-raises its
exception, and is never retried.

`__exit__` never commits implicitly. It rolls back active work, disposes, and
never suppresses a body exception. Body exceptions retain priority over cleanup
failures. Disposal is idempotent: it performs the state-specific cleanup in the
consolidated design, never commits, and performs no work after `DISPOSED`.

## 5. Nested Use and Valid Concurrency

The application or future Dispatch boundary supplies an explicit operation scope
per accepted command. That scope permits one active Unit of Work. A second entry
in the same scope raises `NestedUnitOfWorkError`; registration releases during
deterministic disposal. Separate operation scopes permit valid concurrent Units
of Work and Sessions. No global registry, thread-local, ambient Session, or
global counter is permitted.

## 6. Repository, Dependency, and Legacy Clarification

Context-owned infrastructure adapters receive only the active Unit of Work
Session through explicit wiring. They never acquire, commit, roll back, close,
or reuse Sessions. Repository properties, generic factories, and port shapes
remain deferred.

Application depends on a narrow synchronous Unit of Work port; infrastructure
implements it with `PersistenceRuntime` and SQLAlchemy; Domain remains
independent of all persistence and concrete adapter types.

The retained legacy route/session adapter is excluded from all new canonical
command writes. It may support existing routes only, must not become a competing
Unit of Work or F-009 basis, and must be guarded by conformance tests until
approved bounded-context migration retires it.

## 7. Error Model Reduction

The minimum hierarchy is `UnitOfWorkError`, `UnitOfWorkLifecycleError`,
`UnitOfWorkDisposedError`, `NestedUnitOfWorkError`, and
`RepositoryOwnershipError`. Database and SQLAlchemy exceptions remain visible;
no redundant completed-transaction error is required.

## 8. Acceptance-Test Additions

Future F-008 implementation must test construction/entry separation,
activation failure, terminal lifecycle failures, commit and rollback cleanup,
body-exception priority, all disposal states, per-scope nesting and concurrency,
Session exclusivity, repository binding and reuse, legacy-path exclusion,
PostgreSQL integration, and dependency conformance.

## 9. Unchanged Decisions and Exclusions

This amendment preserves PostgreSQL 16, synchronous SQLAlchemy 2.x, psycopg 3,
one application-owned `PersistenceRuntime`, one Unit of Work/one Session,
explicit commit, infrastructure-only repositories, F-009's one-Unit-of-Work
per accepted owner command, Domain independence, and deferred asynchronous
behavior.

It does not design or implement concrete repositories, ORM models, business
tables, Dispatch, buses, outbox, workers, scheduler, request-wide transactions,
automatic commit, automatic migrations, or legacy route migration.

## 10. Implementation-Readiness Conclusion

The consolidated F-008 design is implementation-authoritative. No architecture
amendment is required. F-008 implementation may begin subject to its acceptance
criteria and ratified Foundation constraints.
