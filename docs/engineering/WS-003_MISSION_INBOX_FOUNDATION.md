# WS-003 — Mission Inbox Foundation

**Status:** Implemented checkpoint — pending validation and review

## Purpose

WS-003 provides the first reusable, tenant-scoped Mission Inbox read model. It is
not a source of truth and never changes Intake or operational-context authority.

## Sources and Projection

The projection consumes `intake.received` for deterministic Intakes and
`intake.operational_context_associated`. `MissionInboxItem` is keyed by
`(organization_id, source_type, source_id)`. Its initial deterministic Intake
item is `open`, `normal`, with a title from the governed Intake title or the
stable fallback `Deterministic Intake`; summary remains null. Raw source text,
headers, and message bodies are never copied.

`ProjectionCheckpoint` uses the globally monotonic `DomainEvent.event_sequence`
and the global projection name `mission_inbox_v1`; its organization scope is
therefore null. Existing events are backfilled deterministically by
`(occurred_at, recorded_at, id)`, where `id` is the stable tie-breaker.
Projection writes and checkpoint advancement commit atomically. A rebuild clears
only Mission Inbox items and its checkpoint, leaves source-of-truth rows
unchanged, then replays events in event-sequence order.

## Queries

`IC-MISSION-QRY-002 ListMissionInbox` and `IC-MISSION-QRY-003
RetrieveMissionInboxItem` require an authenticated actor with
`mission.inbox.read`. Organization ownership derives only from the principal.
List supports `status`, `priority`, `site_id`, `project_id`, and `source_type`
filters with AND semantics; its sort allowlist is `last_activity_at`,
`received_at`, and `priority`, in descending order with `id` as the stable
tie-breaker. Pagination defaults to `limit=50`, accepts `1..100`, and requires
`offset >= 0`. Cross-tenant and absent details are concealed as
`RESOURCE_NOT_FOUND`.

## Deferred Scope

No Inbox mutation API, assignments, workflow, notifications, automation, AI,
reference CRUD, reassociation, frontend, or production import workflow is
introduced. Future domains may add projection handlers while preserving the
same source-of-truth, checkpoint, tenant-isolation, and rebuild rules.

## Operational Rebuild

The internal `MissionInboxProjectionService.rebuild_projection()` operation is
the governed rebuild procedure. It has no public HTTP endpoint.
