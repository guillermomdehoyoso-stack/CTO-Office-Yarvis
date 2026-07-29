# ADR — Process Work Association and Timeline Projection

**Status:** Accepted for WS-006D implementation
**Decision:** ADR-PROCESS-WORK-ASSOCIATION-PROJECTION
**Related design:** [Process Runtime Design](../PROCESS_RUNTIME_DESIGN.md)

## Context

Mission Work owns an operational matter and its Timeline. Process owns the governed
execution of a procedure. A relationship is needed without transferring lifecycle,
state, or persistence authority between those contexts.

Earlier WS-006B draft language described one active association on each side. WS-006D
clarifies the product rule: a Process Instance has at most one active *primary* Work
link, while a Mission Work Item may have zero or many active Process Instances.

## Decision

`ProcessInstanceWorkLink` is a Process-owned, tenant-scoped historical association.
It references exactly one Process Instance and one Mission Work Item in the same
Organization. It has a configurable, non-enumerated `relationship_type`; `primary`
is the initial semantic used for the one-active-link constraint.

- An active primary link is unique per Process Instance.
- No maximum active-link cardinality is imposed on a Mission Work Item.
- Unlinking sets `unlinked_at`; it never deletes or silently rewrites history.
- Link and unlink are idempotent, request-fingerprinted commands and emit
  `process_instance.work_linked` and `process_instance.work_unlinked` Domain Events
  in the same Unit of Work as association state.

Mission Work owns Timeline projection. `ProcessMissionWorkTimelineProjector` consumes
Process `DomainEvent` source assertions and appends `MissionWorkEvent` records with
the source Domain Event identity as its idempotency identity. Process Runtime never
writes `MissionWorkEvent` directly.

On linking, the projector may project the existing Process Instance source history to
give operators an operationally useful Timeline. After unlinking, later Process
events are not projected through that inactive link. The unlink event itself remains
projected as historical evidence.

## Consequences

- Work and Process lifecycles remain independent.
- An association is reconstructible from source events and durable link history.
- Timeline writes are tenant-aware, idempotent, ordered by the Mission Work aggregate,
  and independently rebuildable.
- There is no implicit completion, cancellation, assignment, or status synchronization.

## Rejected Alternatives

- A mutable `process_instance_id` field on `MissionWorkItem`.
- One active Process Instance limit per Mission Work Item.
- Process Runtime writing Mission Work Timeline rows directly.
- Deleting historical associations on unlink.
