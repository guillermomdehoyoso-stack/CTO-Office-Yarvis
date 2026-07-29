# WS-006F — Operational Workspace UI

## Status

Implemented frontend increment; validation evidence is recorded with the change.

## Purpose

WS-006F exposes one tenant-scoped, read-only operational view for a Mission Work
Item. It consumes the existing `GET /mission/work-items/{id}/workspace?currency=MXN`
read model and does not create a new ownership boundary or persistence projection.

## User Experience

The Mission Work detail now provides an **Abrir espacio operativo** navigation
action. The workspace presents the Work Item's identity, status, priority,
assignee, participants, last activity, process-instance counts, related active
and historical process instances, and the unified Mission Work timeline.

Economic values are displayed exactly from the direct summaries returned by the
backend: one for the Mission Work Item and one per related Process Instance. The
frontend performs presentation formatting only; it does not roll up, convert, or
derive economic values.

## States and Tenant Safety

- Loading shows an explicit workspace loading state.
- An empty process or Timeline collection is shown as an empty state, not as
  missing data.
- `404` remains a concealed unavailable/not-owned resource response.
- `403` reports unavailable authority without exposing data.
- Network failures are shown without fabricating a workspace.
- The existing Mission Work access context and `mission.work.read` authority are
  sent by the existing governed API client.

## Scope Boundaries

This increment adds no backend behavior, lifecycle synchronization, economic
calculation, Task, Checklist, SLA, Waiting, Document, automation, or AI surface.
It does not add a parallel Mission Work route; it is reached from the existing
Mission Work detail and can navigate back to the existing queue.

## Tests

Focused frontend coverage verifies the full workspace read model, empty states,
tenant-safe `404`, network failure, and governed API authority header.
