# WS-007A — Operational Task Runtime Foundation

**Status:** Implemented pending environment validation

## Scope

WS-007A introduces the tenant-owned `OperationalTask` aggregate and direct,
finish-to-start `TaskDependency` edges. Every Task has one immutable Mission Work
owner. Process association is optional planning context and never synchronizes
Task, Process, or Mission Work lifecycles.

## Delivered Boundary

- Task creation, tenant-safe retrieval and deterministic per-Work listing.
- Planning updates while `planned`, primary assignment, lifecycle transition,
  explicit completion, explicit cancellation, and direct dependency management.
- `planned`, `ready`, `in_progress`, `completed`, and `cancelled` only; the last
  two are terminal.
- Same-Organization Work, Process Instance, and stage validation; 404 concealment
  for unavailable tenant-owned targets.
- Direct-edge uniqueness, self-edge rejection, and transaction-local graph
  traversal for cycle rejection.
- Source `DomainEvent` assertion and an operator-facing Mission Work Timeline
  projection in the same Unit of Work.

## Explicit Deferrals

Idempotency receipts/replay storage, Task-local append-only history, and the
separate idempotent Timeline projector require focused conformance coverage before
the runtime can be ratified. This baseline does not add Task economics, frontend,
Checklists, Waiting, SLA, Documents, Work Sessions, time tracking, automation, or
AI.

## Migration

`20260730_20_operational_task_runtime` follows `20260729_19` and creates
`operational_tasks` plus direct `task_dependencies`. It does not alter historical
migrations.
