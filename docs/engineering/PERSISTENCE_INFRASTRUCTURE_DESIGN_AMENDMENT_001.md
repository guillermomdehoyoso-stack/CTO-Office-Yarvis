# YARVIS
# Persistence Infrastructure Design Amendment 001

## Status: Ratified Engineering-Design Alignment

## 1. Amendment Identity

**Amendment ID:** `PERSISTENCE-INFRASTRUCTURE-AMENDMENT-001`  
**Affected work package:** F-007 — Persistence Infrastructure  
**Date:** 2026-07-21

## 2. Reason for Amendment

The F-007 Engineering Design Review found that injected
`PersistenceRuntime` ownership was not explicit. Without an ownership rule,
one runtime could be attached to more than one application and be disposed more
than once, violating per-application isolation.

## 3. Amended Ownership Model

Each `PersistenceRuntime` has exactly one owner: one application instance.
Ownership transfers to that application during composition, whether the runtime
is built by the default composition path or explicitly supplied through the
future `persistence=` argument.

After transfer, the runtime must not be composed into another application.
Attempted reuse must fail explicitly and deterministically. No runtime sharing,
reference counting, singleton, process-global runtime, or shared disposal model
is permitted.

## 4. Bootstrap and Lifecycle Semantics

When future `create_app(..., persistence=runtime)` accepts a supplied runtime,
bootstrap accepts exclusive ownership and must reject an already-owned runtime.
Application shutdown disposes only the runtime owned by that application. It
must never dispose a runtime owned by another application.

This amendment defines behavior only. It does not select the implementation
mechanism for recording ownership or detecting reuse.

## 5. Acceptance-Test Addition

F-007 implementation must prove that one runtime cannot attach to two
applications, reuse fails deterministically, and each application disposes only
its owned runtime.

## 6. Scope Preserved

This amendment changes neither PostgreSQL 16, SQLAlchemy 2.x, the synchronous
Engine/Session model, migration strategy, `ApplicationState`, future Unit of
Work integration, nor bootstrap composition order.

No architectural amendment is required. This is a narrow engineering
clarification that preserves the existing per-application isolation principle.

## 7. Closing Statement

F-007 may implement a lifecycle-safe persistence runtime without permitting
shared ownership or duplicate disposal across applications.
