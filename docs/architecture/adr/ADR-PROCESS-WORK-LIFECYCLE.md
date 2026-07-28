# ADR — Process and Work Lifecycle Independence

**Status:** Proposed for Ratification
**Decision:** ADR-PROCESS-WORK-LIFECYCLE
**Related design:** [Process Runtime Design](../PROCESS_RUNTIME_DESIGN.md)

## Context

Mission Work currently owns assignment, priority, work status, and append-only Work Timeline evidence. Process Runtime introduces an independent lifecycle: `active`, `completed`, and `cancelled`.

## Decision

Work and Process lifecycles remain independent.

- A Process transition does not silently create, assign, resolve, cancel, or reprioritize a Work Item.
- A Work status change does not silently transition, complete, or cancel a Process Instance.
- Completed and cancelled Process Instances are final; a completed instance cannot be cancelled.
- A Work association is explicit, Process-owned, tenant-scoped, and historical.

If later policy requires coordinated behavior, it must be introduced through explicit owner contracts, source events, authorization, idempotency, and a documented consistency model. It cannot be inferred from the association itself.

## Consequences

- A Work Item can remain open while a Process completes, and a Process can remain active while linked Work changes state.
- Operators see the relationship without confusing task management with Process authority.
- Automation cannot infer a lifecycle action merely because two aggregates are linked.
