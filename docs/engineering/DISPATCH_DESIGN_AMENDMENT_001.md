# YARVIS
# Dispatch Design Amendment 001

## Status: Engineering Design Amendment

## 1. Amendment Identity

**Amendment ID:** `DISPATCH-DESIGN-AMENDMENT-001`  
**Affected work package:** F-009 — Dispatch  
**Phase:** Design Amendment

## 2. Reason

The original F-009 design correctly preserved F-008's explicit transaction
completion rule, but this amendment makes the responsibility boundary explicit
and internally consistent. A handler does not operate persistence mechanics;
it decides the transaction intent for its owner application behavior. Unit of
Work realizes that decision mechanically. Dispatch orchestrates the accepted
command execution without deciding its business outcome.

## 3. Revised Ownership Model

| Participant | Canonical responsibility |
| --- | --- |
| Dispatch | Dispatch and contract validation, handler resolution, operation-scope creation, Unit of Work construction, deterministic disposal, and failure propagation. |
| Handler | Application behavior, transaction completion decision, explicit `commit()`, and optional explicit `rollback()`. |
| Unit of Work | Session lifecycle, transaction mechanics, lifecycle enforcement, failure cleanup rollback, and disposal. |
| Repository | Persistence operations only; no Session acquisition, commit, rollback, or disposal. |

This does not transfer Session or transaction mechanics to the handler. The
handler can express intent only through the narrow Unit of Work port.

## 4. Revised Execution Pipeline

```text
Dispatch validates command and resolves exactly one owner handler
        ↓
Dispatch creates one OperationScope and one Unit of Work
        ↓
Dispatch enters the Unit of Work
        ↓
Handler performs application behavior
        ↓
Handler explicitly commits or optionally rolls back
        ↓
Handler returns
        ↓
Dispatch verifies a terminal transactional state
        ↓
Dispatch disposes and returns the handler result
```

Dispatch never automatically commits. It never decides whether business work
merits commit, rollback, or a domain-specific failure result.

## 5. Incomplete Transaction Rule

If a handler returns while its Unit of Work remains `ACTIVE`, Dispatch raises
`IncompleteTransactionError`. This is deterministic programmer error, never a
successful command result. The F-008 context-manager cleanup then owns the one
permitted rollback and deterministic disposal.

## 6. Rollback and Failure Semantics

The handler may explicitly roll back where application behavior requires it.
If it throws before completion, F-008 cleanup rolls back active work. If it
commits and later throws, Dispatch preserves the handler exception and does not
invent a compensating rollback. Commit failure remains primary; Unit of Work may
perform only its ratified cleanup rollback. Rollback failure remains primary and
is never retried. Disposal failure is primary only when no earlier exception
exists; otherwise it is secondary diagnostic context.

## 7. Revised Error and Test Requirements

The minimal Dispatch error model includes `DispatchError`, contract and handler
registry errors, `HandlerOwnershipError`, `IncompleteTransactionError`, and
`NestedDispatchError`. Handler, Unit of Work, and database exceptions remain
visible in their native types.

F-009 implementation must test explicit commit, explicit rollback, active
return rejection, pre-commit and post-commit handler failures, commit/rollback
failures, deterministic disposal, and the absence of implicit or second commit
or rollback by Dispatch.

## 8. Unchanged Decisions

This amendment preserves one OperationScope per accepted command, one Unit of
Work per scope, one Session per Unit of Work, synchronous execution, explicit
commit, no request-wide transaction, nested-dispatch prohibition, no concrete
repositories, and no query or event dispatch. It does not redesign Unit of
Work, PersistenceRuntime, Contract Registry, bootstrap, or the module model.

## 9. Implementation Readiness

F-009 remains ready for independent engineering review and subsequent
implementation. No architecture amendment is required. This amendment creates
no runtime code, tests, handlers, repositories, or bootstrap changes.
