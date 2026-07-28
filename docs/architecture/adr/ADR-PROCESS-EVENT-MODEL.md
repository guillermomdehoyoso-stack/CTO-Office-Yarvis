# ADR — Process Event Model

**Status:** Proposed for Ratification
**Decision:** ADR-PROCESS-EVENT-MODEL
**Related design:** [Process Runtime Design](../PROCESS_RUNTIME_DESIGN.md)

## Context

The repository has a generic `DomainEvent` stream for cross-context source assertions and an append-only `MissionWorkEvent` store for an aggregate-local Timeline. Process Runtime needs both integration evidence and a strictly ordered local history.

## Decision

Each Process lifecycle mutation writes, in one Process Unit of Work:

1. Process Instance state;
2. one or more immutable `ProcessInstanceEvent` records; and
3. corresponding `DomainEvent` source assertions.

`ProcessInstanceEvent` is append-only, protected against database update/delete, and ordered by a positive, unique sequence per Process Instance. The Process Timeline reads these events ascending by sequence.

A terminal transition emits `process_instance.transitioned` first and `process_instance.completed` second. They have consecutive sequence numbers and are committed atomically with the completed aggregate state.

Domain Events are sources for foreign projections. A Process service does not write directly to `MissionWorkEvent`; WS-006D introduces a Mission Work-owned, idempotent Timeline projection from Process source events.

## Consequences

- Timeline order and aggregate history do not rely on timestamp ordering.
- A completed transition is reconstructable without hiding its final edge.
- Cross-context consistency remains explicit and eventually consistent where a projection is involved.
- The known generic `DomainEvent` database append-only gap remains a separate technical-debt item.
