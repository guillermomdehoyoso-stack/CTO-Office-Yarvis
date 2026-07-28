# WS-006C — Process Runtime Backend

## Status

Implemented engineering increment; pending validation and review.

## Purpose

WS-006C implements the tenant-owned Process Runtime defined by
[`PROCESS_RUNTIME_DESIGN.md`](../architecture/PROCESS_RUNTIME_DESIGN.md). It turns a
published Process Definition version into governed, append-only Process Instance
history without coupling Process lifecycle to Mission Work.

## Scope Delivered

- `ProcessInstance` is a Process-owned aggregate with `active`, `completed`, and
  `cancelled` lifecycle states.
- `ProcessInstanceEvent` is an append-only, ordered Process-local event store and
  Timeline source.
- Authorized users can start an instance from a published definition, transition it
  through its published graph, cancel an active instance with a reason, and read its
  tenant-scoped list, detail, and Timeline.
- Each successful lifecycle mutation writes aggregate state, Process-local evidence,
  and `DomainEvent` evidence in the same Unit of Work.
- A terminal transition appends `process_instance.transitioned` followed immediately
  by `process_instance.completed`.
- The Alembic migration `20260728_17` is linear from `20260727_16`.

## Ownership and Invariants

`ProcessInstance` belongs to exactly one Organization and permanently references the
published definition version and current stage from which it was created. An instance
is independent of Mission Work in WS-006C; WS-006D may introduce its governed link.

- Draft and retired definitions cannot start instances. Retiring a definition does
  not invalidate instances that already started from it.
- A transition is valid only from the current stage and only within the instance's
  definition and Organization.
- Completed and cancelled instances are final. Completed instances cannot be
  cancelled.
- Cancellation requires a nonblank, accountable reason.
- `expected_version` and a row lock serialize lifecycle mutations. Each successful
  command increments aggregate version once.
- Sequence numbers are positive, unique, and consecutive per Process Instance. The
  locked aggregate serializes writers; database uniqueness provides a second guard.
- Process Instance Events are database-protected against update and delete.

## Contracts and API

| Contract | Endpoint | Authority |
| --- | --- | --- |
| `IC-PROCESS-CMD-011` StartProcessInstance | `POST /process-instances` | `process.instance.start` |
| `IC-PROCESS-CMD-012` TransitionProcessInstance | `POST /process-instances/{id}/transitions` | `process.instance.transition` |
| `IC-PROCESS-CMD-013` CancelProcessInstance | `POST /process-instances/{id}/cancel` | `process.instance.cancel` |
| `IC-PROCESS-QRY-003` ListProcessInstances | `GET /process-instances` | `process.instance.read` |
| `IC-PROCESS-QRY-004` RetrieveProcessInstance | `GET /process-instances/{id}` | `process.instance.read` |
| `IC-PROCESS-QRY-005` RetrieveProcessInstanceTimeline | `GET /process-instances/{id}/timeline` | `process.instance.read` |

The Process runtime emits `IC-PROCESS-EVT-005` through `IC-PROCESS-EVT-008`:
`process_instance.started`, `process_instance.transitioned`,
`process_instance.completed`, and `process_instance.cancelled`.

## Idempotency, Concurrency, and Errors

Start idempotency is Organization-scoped by start key and request fingerprint.
Transition and cancellation idempotency are scoped by Organization, Process Instance,
and Process Instance Event key. Same-key/same-request replays return the established
instance; a changed request is a governed `409` conflict.

Missing idempotency is rejected by the existing command boundary. Stale versions,
invalid graph transitions, final lifecycle mutations, and divergent idempotency are
`409` conflicts. Cross-organization resources are concealed as `404`; insufficient
authority is `403`.

## Deferred Scope

WS-006C deliberately excludes Process Instance to Mission Work association, Work
Timeline projections, frontend, automation, scheduler execution, SLA, and BPMN.
Those capabilities must not infer or alter Process lifecycle without a later governed
increment.

## Validation Evidence

- Focused Process Runtime, Process Definition, and application-contract tests cover
  published start, idempotency replay, graph transitions, terminal completion order,
  retirement, cancellation, tenant concealment, authority, and append-only storage.
- Migration tests verify upgrade, downgrade, re-upgrade, constraints, and the linear
  `20260728_17` head.
- The complete backend suite and formatting/type checks remain required before
  commit readiness is declared.
