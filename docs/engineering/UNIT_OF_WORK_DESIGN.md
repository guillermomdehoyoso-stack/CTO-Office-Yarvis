# YARVIS
# Unit of Work Design

## Status: Amended Engineering Design — F-008 Unit of Work

## Amendment History

| Amendment | Status | Summary |
| --- | --- | --- |
| `UNIT-OF-WORK-DESIGN-AMENDMENT-001` | Consolidated | Defines canonical activation, failure states, operation-scope nesting, and legacy-path containment. |

## 1. Purpose and Authority

F-008 defines the canonical synchronous transactional boundary for future
Yarvis writes. It specializes the ratified Persistence Infrastructure Design;
it does not redefine bounded-context ownership, contract semantics, identity,
governance, or domain lifecycle.

One Unit of Work owns one local transactional operation: it acquires one
Session from an application-owned `PersistenceRuntime`, coordinates the owning
context's repository adapters, owns commit, rollback, close, and disposal, and
preserves failure evidence. It is the sole authority for these Session
lifecycle actions within a canonical write operation.

## 2. Architectural Position and Dependency Placement

```text
Interface / worker adapter
        ↓
Application command handler → synchronous Unit of Work port
        ↓
Infrastructure Unit of Work implementation → PersistenceRuntime → SQLAlchemy → PostgreSQL
        ↓
Context-owned infrastructure repository adapters
```

Application handlers may depend only on a narrow synchronous Unit of Work port
or protocol. The infrastructure implementation depends on `PersistenceRuntime`
and SQLAlchemy and binds repository adapters to its owned Session. Domain code
does not import Unit of Work infrastructure, SQLAlchemy, `PersistenceRuntime`,
or concrete repositories. Exact port and file placement remain implementation
decisions subject to this direction.

`ApplicationState` continues to own only `PersistenceRuntime`; it must not hold
active Units of Work, Sessions, repositories, transactions, or domain state.

## 3. Ownership and Scope

One accepted owner-command execution receives one context-local Unit of Work.
One background-job execution that handles one accepted command follows the
same rule. HTTP transport does not itself define a transaction: read-only
requests require none, and a request containing separate accepted commands
receives one Unit of Work per command, never a request-wide transaction.

Construction acquires no Session and begins no transaction. A Unit of Work owns
exactly one Session only after successful activation. A Session belongs to one
Unit of Work and must never be passed into, reused by, or shared with another.
The Engine remains owned by `PersistenceRuntime` and only application lifespan
may dispose it.

## 4. Canonical Activation and Session Semantics

Synchronous context-manager entry is the only canonical activation path.
There is no public `begin()` method. Any private helper is an implementation
detail called only by `__enter__`.

```text
with unit_of_work:
    # active; one Session and one explicit transaction are owned here
    handler performs its context-local operation
    unit_of_work.commit()  # explicit; never implicit
```

`__enter__`, permitted only from `NEW`, must:

1. validate its explicit operation scope;
2. reject prohibited nesting;
3. acquire exactly one Session from `PersistenceRuntime`;
4. explicitly activate exactly one transaction on that Session;
5. transition to `ACTIVE`; and
6. return the active Unit of Work.

Session acquisition and transaction activation are separate events. SQLAlchemy
autobegin is not Yarvis's architectural boundary. Repository access before
`ACTIVE`, after a terminal state, or after disposal fails deterministically.
Re-entry of the same Unit of Work is a lifecycle error.

## 5. Lifecycle Model

```text
NEW → ACTIVE → COMMITTED → DISPOSED
             ↘ ROLLED_BACK → DISPOSED
NEW → FAILED → DISPOSED
ACTIVE → FAILED → DISPOSED
COMMITTED | ROLLED_BACK → FAILED → DISPOSED  # close failure only
```

| State | Meaning and valid next action |
| --- | --- |
| `NEW` | No owned Session or transaction. May enter once or dispose. |
| `ACTIVE` | Owns one Session and one active transaction. May acquire context adapters, commit once, roll back once, or dispose. |
| `COMMITTED` | Commit succeeded. No commit or rollback is valid; only disposal may close the Session. |
| `ROLLED_BACK` | Rollback succeeded. No commit or rollback is valid; only disposal may close the Session. |
| `FAILED` | Activation, commit, rollback, or close processing failed. No business operation, commit, or public rollback is valid; only safe final close cleanup remains. |
| `DISPOSED` | No owned Session remains. Only repeated idempotent disposal is valid. |

Lifecycle misuse raises a typed lifecycle error. Commit and rollback are
non-idempotent: repeated calls and calls after a terminal state fail
deterministically. Disposal is idempotent and never commits.

## 6. Failure and Transaction Semantics

### 6.1 Activation failures

If Session acquisition fails, transition to `FAILED`, preserve and re-raise the
original exception, and perform only safe cleanup for any partially acquired
resource. Do not roll back unless a transaction was actually activated.

If explicit transaction activation fails, transition to `FAILED`, close the
acquired Session, preserve and re-raise the activation exception, and retain a
close failure only as secondary diagnostic context where feasible. Activation
must never be represented as successful.

### 6.2 Commit and rollback

`commit()` is valid only from `ACTIVE` and is attempted once. On success,
transition to `COMMITTED`; Session close remains disposal's responsibility. On
commit failure, transition to `FAILED`, attempt exactly one rollback only when
the transaction state permits, preserve and re-raise the original commit
exception, and retain any cleanup failure as secondary diagnostic context.
Later commit or public rollback is invalid.

`rollback()` is valid only from `ACTIVE` and is attempted once. On success,
transition to `ROLLED_BACK`; disposal remains required. On rollback failure,
transition to `FAILED`, preserve and re-raise that exception, do not retry
rollback, and reject later commit or rollback.

Typed Unit of Work errors describe architectural misuse; database and SQLAlchemy
exceptions remain visible and are never replaced by generic lifecycle errors.

## 7. Context-Manager and Disposal Semantics

`__exit__` never commits implicitly and never suppresses exceptions.

With no body exception, an `ACTIVE` Unit of Work rolls back once, then disposes.
With a body exception, it attempts one rollback if active, disposes, and
propagates the original body exception. That original exception has priority:
rollback or close errors may be chained, attached, logged, or retained as
secondary diagnostic context, but must not replace it. If no body exception
exists, rollback or close failure remains observable.

Disposal behavior is:

| State on disposal | Required behavior |
| --- | --- |
| `NEW` | No rollback or Session close; transition directly to `DISPOSED`. |
| `ACTIVE` | Attempt one rollback, then close Session; transition to `DISPOSED` only if cleanup succeeds, otherwise `FAILED`. |
| `COMMITTED` | Close Session only; transition to `DISPOSED` on success, otherwise `FAILED`. |
| `ROLLED_BACK` | Close Session only; transition to `DISPOSED` on success, otherwise `FAILED`. |
| `FAILED` | Perform only remaining safe close cleanup; never retry commit or rollback; transition to `DISPOSED` if close succeeds or no Session is owned. |
| `DISPOSED` | Do nothing and return successfully. |

Close failure remains observable. Repeated disposal after `DISPOSED` performs no
additional Session, transaction, or Engine operation.

## 8. Operation Scope, Nested Use, and Concurrency

The application or future Dispatch boundary creates one explicit operation-scope
object or token for each accepted command. A Unit of Work receives that scope at
composition. The scope permits at most one active Unit of Work. Entering a
second Unit of Work while one is active raises `NestedUnitOfWorkError`; the
active registration is released on deterministic disposal.

This mechanism must not use a process-global registry, module-global mutable
state, thread-local state, implicit ambient Session state, or global counters.
It distinguishes prohibited nesting within one operation, valid concurrency
across different operation scopes, and invalid re-entry of one Unit of Work.
Separate concurrent operations may each own a distinct Unit of Work and Session.

## 9. Repository Binding

Only these rules are ratified now:

- context-owned infrastructure adapters receive the active owned Session through
  explicit context wiring;
- adapters never acquire a Session, commit, roll back, or close it;
- adapter access before `ACTIVE` or after terminal state/disposal fails; and
- adapters bound to one Unit of Work cannot be reused by another.

Repository attributes, property names, a generic factory shape, and the first
bounded-context repository ports remain deferred. Unit of Work must not become
a generic service locator or a cross-context repository registry.

## 10. F-009 Dispatch Preparation and Legacy Containment

F-009 Dispatch accepts one owner command, creates one operation scope and one
Unit of Work, invokes the owner handler, and leaves the handler responsible for
one explicit local commit or rollback. Dispatch does not create a second Unit
of Work, share one transaction between unrelated commands, or place queries in
the F-008 boundary. Future dispatch/outbox preparation follows a successful
local commit; it is not implemented here.

The transitional legacy route/session adapter is not a canonical write path for
any new command route or command handler after F-008. New canonical writes use:

```text
Dispatch or approved application boundary
  → one operation scope
  → one Unit of Work
  → context repository adapters
  → owned Session
```

The legacy adapter may temporarily support retained routes but must not be
imported by new canonical command handlers, create a competing Unit of Work,
or become F-009's basis. Architecture/conformance tests must enforce this;
retirement occurs through approved bounded-context migration work.

## 11. Typed Error Model

The minimum hierarchy is:

```text
UnitOfWorkError
├── UnitOfWorkLifecycleError
│   └── UnitOfWorkDisposedError
├── NestedUnitOfWorkError
└── RepositoryOwnershipError
```

Lifecycle errors report the attempted operation and current state using safe
technical values. No separate completed-transaction error is required.

## 12. Required Implementation Tests and Acceptance Criteria

F-008 implementation must prove:

1. construction creates no Session or transaction; `__enter__` creates one
   Session and explicitly activates one transaction;
2. access before activation, after terminal state, after disposal, and re-entry
   fails;
3. activation failure transitions to `FAILED` without hiding its cause;
4. one Unit of Work owns one Session; Sessions cannot belong to two Units; and
   distinct applications and concurrent operation scopes remain isolated;
5. nested use in one scope is rejected without global or thread-local tracking;
6. commit and rollback each succeed once, repeated/invalid use fails, and their
   failure paths preserve original infrastructure exceptions;
7. commit failure attempts one cleanup rollback; rollback is never retried;
8. context-manager exit never commits, rolls back active work, preserves body
   exception priority, and disposes deterministically;
9. disposal is idempotent from every lifecycle state, including close failure;
10. repository adapters receive only their owned active Session and cannot be
    reused across Units or own transaction actions;
11. new canonical command paths cannot use the legacy adapter; and
12. PostgreSQL integration, prohibited-import conformance, F-007 migration and
    lifecycle tests, Ruff, format, Pyright, Docker, and smoke validation pass.

F-008 must not introduce repositories, models, tables, migrations, dispatch,
outbox, workers, scheduler, async Unit of Work, automatic commit, automatic
migrations, or legacy-route migration.

## 13. Closing Statement

The canonical Unit of Work is one explicit operation, one context, one Session,
one deliberate terminal transaction decision, and one deterministic cleanup
path. It preserves local atomicity without making persistence authoritative or
allowing transport, repositories, or Dispatch to blur ownership.
