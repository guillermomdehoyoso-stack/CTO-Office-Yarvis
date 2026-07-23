# YARVIS
# Dispatch Baseline

## Status: Ratified Engineering Baseline — F-009 Dispatch

## 1. Identity and Authorization

**Work package:** F-009 — Dispatch.

This baseline ratifies the canonical synchronous owner-command execution boundary. F-009 implementation is authorized beneath the Contract Registry, Persistence Infrastructure, Unit of Work, Module Registry, and Application Bootstrap baselines.

## 2. Responsibility Model

| Participant | Responsibility |
| --- | --- |
| Dispatcher | Validate request and contract, resolve/validate handler, create scope and concrete UoW, expose the facade, invoke, verify terminal state, orchestrate exit/disposal, release result, and report structural failures. |
| Handler | Application behavior and transaction intent through explicit commit or optional rollback request. |
| Unit of Work | Session ownership, transaction mechanics, lifecycle, commit/rollback, cleanup rollback, close, and disposal. |
| Repository | Future persistence operations only; never Session acquisition, completion, or disposal. |

Dispatch never commits or rolls back and does not decide whether work deserves persistence.

## 3. Command Envelope and Handler Definition

`CommandEnvelope` is an immutable, transport-neutral container for a canonical interaction-contract ID and an isolated payload. It is not an HTTP, authorization, trace, or universal-message envelope. Payload must be immutable, explicitly isolated/snapshotted, or protected by a later context-defined immutable command schema. Universal deep-copying and serialization are excluded.

`HandlerDefinition` is immutable per-application composition metadata: one contract ID, owner module ID, owning context, diagnostic name, and exactly one explicitly registered synchronous callable. The callable is reused after sealing, may close only over approved immutable dependencies, and must retain no command-specific mutable state, scope, UoW, or Session. Factories, scoped construction, dependency injection, service locators, and stateful shared handlers are deferred.

The handler interface is:

```text
handle(command_envelope, command_unit_of_work) -> object | None
```

The complete envelope is passed. `CommandUnitOfWork` is a restricted facade/protocol exposing only `commit()` and `rollback()` in F-009. It excludes disposal, context entry/exit, Session, transaction objects, runtime, engine, SQLAlchemy, session factory, and operation-scope/ownership mutation. Dispatch retains the concrete UoW for lifecycle inspection.

## 4. Handler Registry

`HandlerRegistry` is explicit, sealed, per application, and contains one authoritative definition per Command contract. No globals, decorators, import-time registration, or automatic discovery are permitted.

Module and Contract Registries seal before handler registration. Registration immediately validates contract existence and Command kind, owner module/context equality, supported synchronous callable, and duplicate absence. Structurally valid but operationally inactive Commands may register; Dispatcher evaluates dispatchability at invocation. Sealing prevents later mutation.

## 5. Dispatcher Pipeline

1. Receive one CommandEnvelope and validate payload isolation.
2. Resolve the sealed Contract Registry definition.
3. Verify Command kind and derived dispatchability from lifecycle/status metadata.
4. Resolve exactly one handler and verify exact owner/context compatibility.
5. Create one OperationScope and one concrete UoW; enter through `__enter__` only.
6. Expose the restricted facade and invoke the callable once.
7. If it returns, inspect concrete UoW state inside the active context.
8. Retain a result only from `COMMITTED`; exit and dispose.
9. Release the unchanged result only after successful disposal.

Separate calls receive separate scopes, UoWs, and Sessions. Dispatcher retains no active execution state or disposable database resource.

## 6. Transaction, Failure, and Result Rules

Normal result release requires `COMMITTED` only.

| State after normal handler return | Required behavior |
| --- | --- |
| `COMMITTED` | Retain result provisionally; release after successful disposal. |
| `ROLLED_BACK` | Raise `InvalidCommandCompletionError`; withhold result; no second rollback. |
| `ACTIVE` | Raise `IncompleteTransactionError` inside the context; F-008 cleanup rolls back once. |
| `FAILED` | Never release success; preserve an active infrastructure error or raise invalid completion if concealed. |
| `DISPOSED` / `NEW` | Reject as lifecycle/ownership violation. |

Explicit rollback means do not persist, not normal success. A handler that rolls back must raise a context/application exception; F-009 supplies no universal rejection result. Handler, UoW, SQLAlchemy, and database exceptions remain visible. F-008 preserves exception priority, cleanup rollback, and disposal semantics.

After a handler commits and returns, disposal failure withholds the result and reports failure even though effects may already be durable: **persisted but reported as failure**. Dispatch neither claims rollback nor retries automatically. Idempotency, reconciliation, observability, and retry policy remain deferred.

## 7. Nesting, State, Bootstrap, and Dependencies

Nested owner-command dispatch is prohibited structurally. Approved handlers do not receive or capture Dispatcher, HandlerRegistry, ApplicationState, a dispatch callback, or a service locator, and do not import Dispatch composition or bootstrap state. Conformance tests enforce this. F-009 claims no general runtime detection of deliberate bypass and permits no global, thread-local, `ContextVar`, or ambient current-command state.

ApplicationState gains typed, per-application `handler_registry` and `dispatcher` fields, but stores no active scope, UoW, Session, command, or result. Bootstrap order is Settings → sealed Module Registry → sealed Contract Registry → PersistenceRuntime → Handler Registry and explicit definitions → sealed Handler Registry → Dispatcher → ApplicationState → interface composition. Bootstrap creates no connection, Session, UoW, migration, handler invocation, or command execution.

Domain is independent. Application handlers depend only on envelope and restricted port. Infrastructure provides concrete UoW and future repository adapters. Composition owns registration, Dispatcher, and bootstrap wiring. Dispatcher and canonical handlers must not use `yarvis_api.database`, raw Sessions, PersistenceRuntime, SQLAlchemy, HTTP, or a second transaction path.

## 8. Errors, Tests, and Exclusions

The minimum error concepts are `DispatchError`, `DispatchContractError`, `HandlerRegistryError`, `HandlerOwnershipError`, `IncompleteTransactionError`, and `InvalidCommandCompletionError`. Narrow subclasses may distinguish unknown/wrong-kind/non-dispatchable contracts and duplicate/missing/sealed/invalid handlers. Handler, UoW, SQLAlchemy, and database errors are not wrapped.

Implementation tests must cover registration/sealing/ownership, payload isolation, restricted facade surface, committed-only release, rollback and active-return errors, exception priority, disposal-after-commit, application and command isolation, PostgreSQL effects without business schema, and conformance for no discovery, legacy persistence path, non-command dispatch, or ambient tracking.

F-009 excludes business commands/handlers, repositories, query/event/notification dispatch, asynchronous work, workers, scheduler, queues, retries, idempotency, reconciliation, identity, authorization, tenancy, tracing, correlation, outbox/inbox, workflows, sagas, factories, dependency injection, and runtime nested-dispatch detection.

## 9. Closing Statement

F-009 makes command execution explicit and locally transactional without turning Dispatch into a universal bus or authority source. Handlers state transaction intent, Unit of Work realizes it, and Dispatch governs deterministic execution.
