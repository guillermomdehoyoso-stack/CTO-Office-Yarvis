# YARVIS
# Dispatch Design

## Status: Ratified Engineering Design — F-009 Dispatch

## 1. Purpose

F-009 defines the minimum canonical synchronous command-dispatch boundary for Yarvis. Dispatch accepts a governed owner-command request, validates the registered interaction contract and owner, selects exactly one registered owner handler, establishes one operation scope and one Unit of Work, and returns a deterministic success or failure. The handler owns application behavior and transaction intent; Unit of Work owns transaction mechanics; Dispatch owns execution orchestration.

Dispatch is application-composition infrastructure. It is neither a universal message bus nor a source of domain authority. It does not interpret business policy, authorize an actor, discover handlers, route HTTP requests, publish events, or perform query or notification dispatch.

## 2. Scope and Architectural Position

F-009 supports only a synchronous `Command` interaction: one contract, one authoritative handler, one operation scope, one Unit of Work, one local transaction, and one synchronous result.

```text
Interface or future worker adapter
        ↓
Dispatch
        ↓
sealed Contract Registry + sealed Handler Registry
        ↓
owner command handler → Unit of Work port → context-owned adapters
        ↓
PersistenceRuntime → SQLAlchemy → PostgreSQL
```

The Contract Registry remains the governed metadata projection; it does not bind implementations itself. Dispatch is application infrastructure using that projection. Domain code remains independent of Dispatch, FastAPI, SQLAlchemy, `PersistenceRuntime`, and registry implementations.

## 3. Canonical Command-Dispatch Model

The canonical target is an immutable, transport-neutral `CommandEnvelope`:

| Field | Meaning |
| --- | --- |
| `interaction_contract_id` | Stable ID of the registered command contract. |
| `payload` | Immutable command value or explicitly isolated snapshot. F-009 does not define its schema. |

Correlation, causation, principal, tenant, authorization, trace, and transport metadata are deliberately deferred. At envelope creation or dispatch acceptance, payload must either be an immutable value object, be copied into an isolated representation, or be guaranteed immutable by a future context schema. Dispatch must not rely on a mutable caller-owned object changing during execution, but F-009 does not mandate universal deep-copy behavior for arbitrary Python objects. A future governed envelope may extend this one without changing its identity or making Dispatch an HTTP abstraction.

The registry definition is the command identity authority. Its identifier is validated by the existing Contract Registry convention. Its type, owner module, owning context, lifecycle, and operational status are read from the sealed registry—not inferred from a handler name, payload, route, or import.

## 4. Structural Dispatchability

F-009 validates structural dispatchability only:

1. the contract exists;
2. its kind is `Command`;
3. it is not `Retired`; and
4. its operational status is `Implemented`, `Verified`, or `Production`.

`Draft`, `Proposed`, `Ratified`, and `Deprecated` remain independent governance states. F-009 does not collapse lifecycle into operational status. A future governance policy may narrow which non-retired lifecycle states are executable; it must do so explicitly. `Planned`, `Suspended`, and `Removed` are not dispatchable. The current Proposed/Planned Tier 1 projection is therefore governed metadata, not an executable command baseline.

F-009 does not implement actor authorization, delegation, tenancy, policy evaluation, rate limiting, idempotency policy, audit persistence, or critical-trace completion. Those are later target-bound controls, not reasons to infer authority at Dispatch.

## 5. Handler Definition and Registry

`HandlerDefinition` is an immutable composition declaration with only:

| Field | Required responsibility |
| --- | --- |
| `interaction_contract_id` | Exact Command contract served. |
| `owner_module_id` | Exact technical owner module. |
| `owning_context` | Exact bounded-context owner. |
| `handler` | One explicitly registered synchronous callable. |
| `handler_name` | Safe diagnostic name. |

`HandlerRegistry` is a per-application, explicit, sealed mapping from command contract ID to one definition. Its justified API is `register`, `register_many`, `get`, `contains`, `list`, `list_by_owner`, `seal`, and `is_sealed`. Registration order is preserved for diagnostics only; lookup is by exact stable contract ID, so dispatch selection has no ordering ambiguity.

Registration occurs after the Module Registry and Contract Registry are sealed, and before Handler Registry sealing. It immediately rejects duplicate command IDs, unknown contracts, non-command contracts, owner-module or owning-context mismatch, invalid/asynchronous callables, and mutation after sealing. Structurally valid but currently non-dispatchable Commands may be registered; Dispatch rejects them until their existing lifecycle/status metadata satisfies the derived dispatchability rule. An absent handler is an execution-time failure rather than an invented placeholder. There is no global registry, decorator registration, package scanning, entry-point discovery, or import-time side effect.

Contract ownership and handler ownership must match exactly on both `owner_module_id` and `owning_context`. A non-owner module cannot register the authoritative handler. `handler` is one synchronous callable, reused across dispatches, and must be stateless with respect to command execution. It may close only over approved immutable application dependencies and must not retain a Unit of Work, Session, scope, payload, or per-dispatch mutable state. Factories, dependency-injection containers, scoped service lifetimes, and stateful shared handlers are deferred. Delegated handling is deferred until governance defines an explicit delegated contract or policy; it must not be simulated by a relaxed owner comparison.

## 6. Handler Interface and Result

The exact synchronous protocol is:

```text
handle(command_envelope: CommandEnvelope, command_unit_of_work: CommandUnitOfWork) -> object | None
```

`CommandUnitOfWork` is a restricted application-facing facade or protocol, not the concrete infrastructure `UnitOfWork`. For F-009 it exposes only `commit()` and `rollback()` to express transaction intent. It exposes neither `dispose()`, `__enter__()`, `__exit__()`, lifecycle ownership operations, Session, transaction object, `PersistenceRuntime`, Engine, session factory, raw SQLAlchemy access, nor operation-scope mutation. Dispatch retains the concrete Unit of Work and its state for verification. Future context-specific repository ports may be introduced only through later bounded-context work.

F-009 introduces no universal result type. A handler may return a typed context-owned result or `None`, but Dispatch returns it unchanged only after `COMMITTED` verification and successful disposal. Result schema validation, serialization, query semantics, and context-defined rejection results belong to later contract binding and interface work.

## 7. Execution Pipeline and Transaction Semantics

The implementation-authoritative pipeline is:

1. Receive one `CommandEnvelope`.
2. Resolve its definition from the sealed Contract Registry.
3. Validate Command kind and structural dispatchability.
4. Resolve exactly one Handler Definition from the sealed Handler Registry.
5. Revalidate exact handler/contract ownership compatibility.
6. Create one new explicit `OperationScope`.
7. Construct one Unit of Work from the application-owned `PersistenceRuntime` and that scope.
8. Enter the Unit of Work; entry is its sole activation path.
9. Invoke the selected handler exactly once.
10. Expose a restricted `CommandUnitOfWork` facade to the handler.
11. Invoke the handler exactly once.
12. If it returns, verify the concrete Unit of Work state inside the active context.
13. Retain a result provisionally only from `COMMITTED`; reject every other state.
14. Exit and dispose deterministically, preserving the primary failure.
15. Release the retained result only after successful disposal.

F-008 is authoritative on transaction completion: the handler owns the completion decision and explicitly requests `unit_of_work.commit()` or, when application behavior requires it, `unit_of_work.rollback()`. `UnitOfWork` alone owns the actual transaction mechanics, Session lifecycle, rollback cleanup, disposal, and state transitions. Dispatch owns validation, handler resolution, scope/UoW construction, lifecycle orchestration, disposal, and failure propagation; it never decides whether work deserves commit.

Dispatch does **not** commit implicitly after a successful handler return, and does not call commit, rollback, dispose, or create a second Unit of Work while a handler is active. Normal return requires `COMMITTED` only. A handler returning with `ACTIVE` work raises `IncompleteTransactionError`, a deterministic programmer error; the context-manager path performs the ratified rollback/disposal cleanup. A handler returning with `ROLLED_BACK` work raises `InvalidCommandCompletionError`; rollback expresses intent not to persist and is never ordinary command success. A handler that rolls back must raise a context/application exception; F-009 introduces no universal rejection-result wrapper.

Failure semantics are explicit:

| Situation | Primary result / exception | Unit of Work state before disposal | Dispatch responsibility |
| --- | --- | --- | --- |
| Handler commits and returns | provisionally retain handler result | `COMMITTED` | Dispose; return only if disposal succeeds. |
| Handler rolls back and raises | original handler/application exception | `ROLLED_BACK` | Preserve exception; dispose only; no result. |
| Handler rolls back and returns | `InvalidCommandCompletionError` | `ROLLED_BACK` | Withhold result; dispose only; never roll back again. |
| Handler throws before completion | original handler exception | `ACTIVE` until F-008 cleanup | Preserve exception; let context-manager rollback and dispose. |
| Handler commits then throws | original handler exception | `COMMITTED` | Preserve exception and dispose; do not attempt compensating rollback. |
| Commit fails | original commit exception | `FAILED` after F-008's permitted cleanup attempt | Preserve the commit failure and dispose. |
| Rollback fails | original rollback exception | `FAILED` | Preserve rollback failure and dispose; never retry rollback. |
| Disposal fails after commit without an earlier primary error | disposal exception; effects may already be durable | `FAILED` | Expose failure, withhold result, and never claim rollback or retry. |
| Disposal fails while another error is primary | original earlier exception | `FAILED` | Preserve earlier exception; retain disposal failure only as secondary context. |
| Handler returns while active | `IncompleteTransactionError` | `ACTIVE` until F-008 cleanup | Reject success inside the context; let cleanup rollback and dispose. |
| Handler returns after hidden transaction failure | `InvalidCommandCompletionError` | `FAILED` | Reject success without replacing an already propagating infrastructure error. |
| Handler disposes early or returns `DISPOSED`/`NEW` | lifecycle or `InvalidCommandCompletionError` | invalid | Reject success; Dispatch retains lifecycle ownership. |

No path gives Dispatch a duplicate rollback or commit responsibility. A close failure after commit can mean **persisted but reported as failure**: callers and operators must not infer non-persistence, Dispatch must not retry automatically, and idempotency, reconciliation, and observability remain future concerns. Commit, rollback, activation, disposal, and database exceptions are not wrapped merely because Dispatch called the handler.

## 8. Failure and Error Model

The minimum typed hierarchy is:

```text
DispatchError
├── DispatchContractError
│   ├── UnknownDispatchContractError
│   ├── UnsupportedContractKindError
│   └── CommandNotDispatchableError
├── HandlerRegistryError
│   ├── DuplicateHandlerError
│   ├── MissingHandlerError
│   └── HandlerRegistrySealedError
├── HandlerOwnershipError
├── IncompleteTransactionError
└── InvalidCommandCompletionError
```

`NestedDispatchError` is not a required F-009 runtime error because F-009 defines no non-ambient execution context that could safely detect every bypass. Invalid handler declarations may use the registry's invalid-definition style. Handler exceptions, Unit of Work errors, and database errors remain visible as their original types. A commit failure remains primary even if F-008 cleanup rollback or disposal also fails. Structural failures are deterministic and contain only safe technical identifiers.

## 9. Operation Scope, Nesting, and Concurrency

Dispatch creates an operation scope per accepted command and passes it only to that command's Unit of Work. Separate accepted commands may run concurrently because each obtains a distinct scope, Unit of Work, and Session. The Dispatcher holds no mutable execution state between calls.

Synchronous nested owner-command dispatch is prohibited structurally through composition and dependency conformance. A canonical handler receives no Dispatcher, Handler Registry, Dispatcher factory, application state, service locator, or other dispatch-capable callable. It may not import Dispatch implementation/composition code, bootstrap state, or a global application accessor, and its registered callable may not capture a Dispatcher directly or indirectly. These restrictions are enforced by composition and architecture-conformance tests.

F-009 does not claim to detect every malicious or manually bypassed nested call at runtime. Manually constructing a second Dispatcher, importing composition internals, or capturing a Dispatcher through an unapproved closure is an architecture violation, not a supported dispatch path. Runtime nested detection is deferred until an explicit non-ambient execution-context model is approved. No global, thread-local, `ContextVar`, or ambient current-command tracker is permitted.

The one registered callable is reused only when it is stateless and safe for separate concurrent synchronous invocation under the repository's supported execution model.

## 10. Application and Module Composition

Each application owns one sealed `HandlerRegistry` and one immutable, stateless-per-execution `Dispatcher`. `ApplicationState` gains typed `handler_registry` and `dispatcher` fields alongside settings, module registry, contract registry, and persistence runtime. It remains a narrow technical root, not a map of arbitrary services; it never holds active scopes, Unit of Work instances, Sessions, repositories, or handler execution state.

The canonical composition order is:

```text
Settings
→ Module Registry
→ Contract Registry
→ PersistenceRuntime
→ Handler Registry
→ Dispatcher
→ ApplicationState
→ middleware, exception handlers, routes
```

Bootstrap remains connection-free and does not create Sessions, Units of Work, handlers' business data, migrations, workers, schedulers, or command execution. The Dispatcher owns no disposable resource. Persistence lifecycle remains with the application-owned `PersistenceRuntime` and lifespan.

Future canonical modules contribute immutable handler-definition collections through explicit bootstrap composition. A module does not self-register, mutate a registry on import, or require a change to F-005's minimal `ApplicationModule` declaration. The composition root receives an explicit handler iterable; the exact factory signature is an F-009 implementation decision, provided it preserves one composition authority and per-application isolation.

## 11. Dependency Direction and Legacy Containment

```text
Domain: independent
        ↑
Application: command models, handler protocol, UnitOfWorkPort
        ↑
Infrastructure: UnitOfWork implementation, context repository adapters
        ↑
Composition: HandlerRegistry, Dispatcher, bootstrap wiring
```

Dispatch must not depend on FastAPI, HTTP, workers, scheduler, repositories, or the legacy `yarvis_api.database` adapter. New canonical command handlers must not import `PersistenceRuntime`, SQLAlchemy, raw sessions, or the legacy adapter. Retained legacy routes remain transitional and cannot become a second dispatch or transaction path.

## 12. Testing Strategy and Acceptance Criteria

F-009 implementation must prove:

1. explicit, per-application handler registration and sealing;
2. deterministic duplicate, wrong-kind, missing-handler, and ownership rejection;
3. unknown and non-dispatchable contract rejection;
4. one accepted command creates exactly one scope, Unit of Work, Session, and handler invocation;
5. one immutable synchronous callable is registered and reused without retaining per-dispatch state;
6. the restricted handler port exposes commit/rollback but not disposal, Session, runtime, or context entry/exit;
7. a handler commits, returns, verifies `COMMITTED`, disposes successfully, and only then releases its unchanged result;
8. rollback plus a handler exception preserves that exception with no second rollback, while rollback plus normal return raises `InvalidCommandCompletionError`;
9. a handler returning with active work raises `IncompleteTransactionError` inside the context and rolls back through F-008 cleanup;
10. hidden `FAILED`, early disposal, `DISPOSED`, or `NEW` states cannot return success;
11. pre/post-commit, post-rollback, commit, rollback, and disposal failures preserve primary errors; post-commit disposal failure returns no result and may be persisted but reported as failure;
12. accepted immutable payloads and explicitly isolated payloads are distinguished from unsafe mutable caller-owned payloads;
13. separate commands and applications isolate state and Sessions;
14. canonical handlers expose no Dispatcher and conformance prohibits Dispatch-composition imports/capture without global or ambient execution tracking;
15. handlers cannot reach raw persistence through their supported interface; and
16. PostgreSQL transaction checks use infrastructure-safe effects only, without business schemas, repositories, or migrations.

Acceptance also requires no automatic discovery, no hidden transaction boundary, no worker/scheduler startup, no command/query/event/notification semantic mixing, and no bootstrap connection or command execution.

## 13. Proposed Repository Layout

```text
apps/api/src/yarvis_api/dispatch/
    __init__.py
    errors.py
    models.py
    registry.py
    dispatcher.py
apps/api/tests/
    test_handler_registry.py
    test_dispatcher.py
docs/engineering/
    DISPATCH_BASELINE.md
```

This is a proposal for F-009 implementation, not a current file creation or a new application layer. Existing `persistence/unit_of_work.py` remains the infrastructure Unit of Work authority.

## 14. Risks, Boundaries, and Deferred Decisions

| Risk | Required mitigation |
| --- | --- |
| Global or import-time handlers | Explicit composition and sealed per-application registry. |
| Duplicate authoritative handler | Exact one-definition-per-command rejection. |
| Owner drift | Exact module/context compatibility at registration and dispatch. |
| Hidden transactions | Explicit handler completion; no Dispatch commit. |
| Nested/shared transaction | One scope/UoW per command; structural composition and conformance prohibition. |
| Exception masking | Preserve handler and Unit of Work primary exceptions. |
| Registry drift | Resolve exact sealed contract ID and handler binding. |
| Premature bus abstraction | Commands only; no queues, events, queries, notifications, or brokers. |
| Legacy persistence leakage | Conformance prohibition on new handlers and Dispatcher. |

Deferred decisions are payload and result schemas; identity, authorization, tenancy, idempotency and trace envelopes; repository ports; event publication and outbox; query/event/notification dispatch; retries; asynchronous work; workflows; and transport bindings. None may be inferred from F-009.

## 15. Implementation-Readiness Conclusion

F-009 is ratified and implementation-authoritative. Its implementation may begin without changing the ratified Contract Registry, Unit of Work, PersistenceRuntime, Module Registry, or architecture, provided it preserves the explicit handler-completion rule established by F-008. No business command, handler, repository, migration, bootstrap behavior, or dispatch runtime is created by this design.
