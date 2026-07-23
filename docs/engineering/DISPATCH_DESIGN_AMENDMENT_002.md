# YARVIS
# Dispatch Design Amendment 002

## Status: Engineering Design Amendment

## 1. Amendment Identity

**Amendment ID:** `DISPATCH-DESIGN-AMENDMENT-002`  
**Affected work package:** F-009 — Dispatch  
**Phase:** Design Amendment

## 2. Findings Resolved

This amendment resolves the independent F-009 review findings without
redesigning Dispatch, Unit of Work, PersistenceRuntime, or the Contract
Registry. It closes ambiguity around normal completion after rollback, handler
lifetime, restricted Unit of Work access, nested-dispatch enforcement, payload
ownership, and disposal failure after commit.

## 3. Committed-Only Completion and Explicit Rollback

A handler result is a normal command result only when the concrete Unit of Work
is `COMMITTED`. Dispatch verifies that state inside the active context, retains
the result provisionally, exits and disposes, then releases the result only if
disposal succeeds.

`ROLLED_BACK` is never normal command completion. Explicit rollback expresses
the handler's intent not to persist. After requesting rollback, a handler must
raise a context/application exception. F-009 creates no universal rejection
result. A handler that rolls back and returns normally causes
`InvalidCommandCompletionError`; the result is withheld and no second rollback
is attempted.

`ACTIVE` at normal return causes `IncompleteTransactionError` inside the Unit
of Work context. `FAILED`, `DISPOSED`, and `NEW` cannot produce normal success;
they cause a terminal-state or lifecycle failure as appropriate.

## 4. Handler Lifetime and Restricted Surface

`HandlerDefinition` contains exactly one synchronous callable. It is explicitly
registered, immutable after registration, reused across dispatches, and must be
stateless with respect to execution. It may close only over approved immutable
application dependencies. It must not retain command payloads, operation
scopes, Sessions, Unit of Work instances, or other per-dispatch mutable state.
Factories, dependency-injection containers, scoped lifetimes, and stateful
shared handlers remain deferred.

The exact handler shape is:

```text
handle(command_envelope, command_unit_of_work) -> object | None
```

The complete transport-neutral envelope contains the contract ID and isolated
payload. `CommandUnitOfWork` is a narrow facade/protocol exposing only
`commit()` and `rollback()` in F-009. It does not expose disposal, context
entry/exit, Session, transaction object, SQLAlchemy, runtime/engine/factory,
or operation-scope ownership. Dispatch owns concrete Unit of Work construction,
entry, verification, exit, disposal orchestration, and result release; Unit of
Work owns transaction mechanics, cleanup, and Session close.

## 5. Nested Dispatch and Payload Ownership

Nested owner-command dispatch is prohibited structurally, not by an unratified
ambient runtime tracker. Canonical handlers receive and capture no Dispatcher,
Handler Registry, Dispatcher factory, application state, service locator, or
dispatch-capable callable. Composition and architecture-conformance tests
prohibit imports of Dispatch composition internals and unapproved Dispatcher
capture. F-009 makes no claim to detect malicious/manual bypass at runtime;
that is an architecture violation. `NestedDispatchError` is therefore removed
from the required F-009 hierarchy until a future explicit non-ambient execution
context exists.

Payload must be immutable, explicitly isolated/snapshotted, or protected by a
future context-defined immutable schema. F-009 prefers immutable values and
does not require universal deep copies for arbitrary Python objects. Dispatch
must not rely on mutable caller-owned state changing during execution.

## 6. Persisted but Reported as Failure

If a handler commits and disposal/Session close then fails, transaction effects
may already be durable. Dispatch reports the disposal failure, releases no
handler result, makes no rollback claim, and does not retry automatically.
Callers and operators must not infer non-persistence from that reported failure.
Idempotency, reconciliation, observability, and retry policies remain deferred.

## 7. Revised Pipeline and Error Model

```text
validate isolated payload → resolve/validate contract → resolve compatible handler
→ create scope and concrete Unit of Work → enter → expose restricted facade
→ invoke handler → verify COMMITTED on normal return → exit/dispose → release result
```

The required errors are `DispatchError`, contract errors, handler-registry
errors, `HandlerOwnershipError`, `IncompleteTransactionError`, and
`InvalidCommandCompletionError`. Handler, Unit of Work, SQLAlchemy, and
database exceptions remain unwrapped and retain primary-exception priority.

Handler registration occurs only after Module and Contract Registries seal. It
immediately validates contract existence, `Command` kind, owner equality,
synchronous callable validity, and duplicate absence. Structurally valid but
currently non-dispatchable Commands may register; Dispatch rejects them until
existing metadata makes them dispatchable.

## 8. Acceptance Additions and Unchanged Decisions

Implementation must test callable reuse and statelessness, restricted facade
surface, committed-only result release, rollback-plus-raise, rollback-plus-
return rejection, active/failed/disposed terminal states, post-commit disposal
failure, payload isolation, and structural nested-dispatch conformance.

This amendment preserves synchronous owner-command Dispatch, one handler per
contract, sealed per-application composition, one scope/UoW/Session per
accepted command, handler-owned transaction intent, Unit-of-Work transaction
mechanics, Dispatch's prohibition from commit/rollback, no request-wide
transaction, and no query/event/notification dispatch. It introduces no
repositories, business behavior, runtime code, tests, async execution,
factories, service locator, automatic retry, or ambient execution tracking.

## 9. Implementation Readiness

The consolidated F-009 design is implementation-authoritative and ready for
independent review. No architecture amendment is required.
