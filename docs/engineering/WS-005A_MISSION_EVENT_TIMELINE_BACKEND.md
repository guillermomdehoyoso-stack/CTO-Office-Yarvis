# WS-005A — Mission Event Timeline Backend

**Status:** Implemented Engineering Increment — pending validation

## Purpose

WS-005A introduces the operational Mission Work Event Store and the governed Timeline query. It records lifecycle evidence for a tenant-owned `MissionWorkItem`; it does not create a new workflow, projection, notification mechanism, or user interface.

## Event Store Model

`MissionWorkEvent` is an append-only, tenant-owned evidence record with a stable event identifier, organization, Work Item, occurrence time, event type, optional actor, opaque payload, and per-Work-Item sequence number. The unique identity `(organization_id, work_item_id, sequence_number)` provides a deterministic timeline order. The database rejects update and delete operations through an append-only trigger.

The Event Store records `work_item.created`, `work_item.assigned`, `work_item.unassigned`, `work_item.status_changed`, `work_item.priority_changed`, and `comment.added`. Lifecycle mutations retain the pre-existing generic domain-event publication while recording the corresponding operational timeline evidence in the same Unit of Work.

## Event Store and Timeline

The Event Store is persistence evidence. The Timeline is the governed read model that exposes those records in ascending `sequence_number` order. It returns only event type, occurrence date, actor, payload, and sequence number; it does not interpret, summarize, or derive business conclusions from payloads.

`GET /mission/work-items/{id}/timeline` requires `mission.work.read`, applies the caller organization boundary, and conceals cross-tenant Work Items as `404 RESOURCE_NOT_FOUND`.

## Comments

`POST /mission/work-items/{id}/comments` accepts an internal comment through `AddMissionWorkItemComment`. It is governed by the existing `mission.work.create` authority and appends a `comment.added` event. Comments are not editable or deletable in this increment.

## Interaction Contracts

- `IC-MISSION-CMD-006` — AddMissionWorkItemComment
- `IC-MISSION-QRY-006` — RetrieveMissionWorkTimeline
- `IC-MISSION-EVT-007` — MissionWorkItemCommentAdded

## Temporal and Extension Rules

`occurred_at` preserves the recorded action time; `sequence_number` is the canonical order only within a Work Item and its organization. Future external events, attachments, notifications, automation, SLA interpretation, and UI views may consume timeline evidence, but must append new events rather than mutate prior history.

## Deferred Scope

Timeline UI, SLA, AI interpretation, notifications, attachments, automation, comment editing or deletion, and external events are explicitly deferred.
