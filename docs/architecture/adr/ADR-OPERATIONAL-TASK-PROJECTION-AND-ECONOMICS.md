# ADR — Operational Task Projection and Economics

**Status:** Accepted OE-001 Decision
**Decision:** ADR-OPERATIONAL-TASK-PROJECTION-AND-ECONOMICS
**Related design:** [Operational Execution Architecture](../OPERATIONAL_EXECUTION_ARCHITECTURE.md)

## Decision

Operational Execution writes Task-local append-only evidence and `DomainEvent` source assertions in its own Unit of Work. Mission Work receives operator-relevant Task history through an idempotent, tenant-aware projection; Operational Execution never writes `MissionWorkEvent` directly. Completion notes use Task authorization and tenant visibility; document/file evidence remains deferred to the Document Registry.

Operational Economics remains the only owner of Economic Facts, correction lineage, currency policy, and calculations. The `task` subject value is reserved but unsupported until a Task subject resolver and same-Organization validation exist. Time, work sessions, and completion never create cost automatically.

## Consequences

- Work Timeline remains projection evidence, not Task source truth.
- Task/Work/Process relations cannot double-count economics.
- UI can compose Task facts without gaining write ownership.

## Rejected Alternatives

- Use the Mission Work Timeline as the Task event store.
- Infer cost from duration, completion, or Process association.
- Infer an economic roll-up from a Task's parent Work or related Process.
