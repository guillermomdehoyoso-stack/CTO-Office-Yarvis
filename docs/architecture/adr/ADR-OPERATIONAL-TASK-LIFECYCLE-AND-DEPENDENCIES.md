# ADR — Operational Task Lifecycle and Dependencies

**Status:** Accepted OE-001 Decision
**Decision:** ADR-OPERATIONAL-TASK-LIFECYCLE-AND-DEPENDENCIES
**Related design:** [Operational Execution Architecture](../OPERATIONAL_EXECUTION_ARCHITECTURE.md)

## Decision

The initial Task lifecycle is `planned`, `ready`, `in_progress`, `completed`, and `cancelled`. Completion and cancellation are explicit, accountable actions; `completed` and `cancelled` are terminal and reopening is not supported. `blocked`, `waiting`, and `overdue` are not lifecycle states.

Dependencies are explicit, tenant-safe, same-Mission-Work finish-to-start relations. Persistence stores direct edges only; it does not create a closure table or persisted transitive graph. Cycles are prevented transactionally through graph traversal. Readiness is constrained by active lifecycle and completed predecessors; it may be represented in a read model as a derived condition.

## Consequences

- Dependency failure is visible without conflating an explanation with Task state.
- Graph validation and concurrency protection are required before dependency writes.
- A cancelled predecessor never automatically cancels its successors.

## Rejected Alternatives

- A generic `blocked` state for every dependency or waiting condition.
- Cross-Work dependencies in the initial implementation.
- Completion inferred from Process, Timeline, or evidence activity.
