# WS-004B — Mission Work Queue Frontend

## Status

Implemented and validated: focused and complete frontend test suites pass, and
the production build passes.

## Purpose

WS-004B makes the governed Mission Work Queue operational through the existing
Mission Work API. It does not introduce a new backend contract or redefine the
Mission Inbox and Work Queue ownership established by WS-003 and WS-004A.

## Screens and Flows

`/mission-work` provides a queue list with status, priority, and assignee
filters, using the API pagination result. Selecting an item opens its governed
detail. The detail allows assignment or unassignment, status transition, and
priority change only through the existing public endpoints.

The same surface includes a Mission Inbox section. An authorized operator can
create a Work Item for an Inbox item, then opens the returned Work Item. If the
API reports a duplicate conflict, the frontend uses the existing governed list
query with the Inbox item's stable `source_type` and `source_id`; it opens the
item only when the API returns it and the operator has read authority. It never
derives or guesses an identifier, and does not use the rebuildable Inbox ID as
the post-rebuild recovery criterion.

## Permissions

The frontend sends the actor, organization, token, and one required authority
with each request. Controls are disabled or unavailable when the configured
authorities do not include:

- `mission.work.read` for queue and detail reads;
- `mission.work.create` for Inbox creation;
- `mission.work.assign` for assignment;
- `mission.work.status.change` for status changes;
- `mission.work.priority.change` for priority changes;
- `mission.inbox.read` for the Inbox section.

The backend remains authoritative for all authorization decisions.

## UI States and Errors

The queue and Inbox expose loading, empty, and visible error states. `404
RESOURCE_NOT_FOUND` is presented as unavailable or outside the organization;
`409` as a governed state conflict; `403` as an authorization denial; and
transport failures as an API connection error. Mutating controls are disabled
while any mutation is in progress, preventing duplicate submissions.

## Deferred Scope

WS-004B deliberately excludes SLA, comments, attachments, notifications,
automation, AI, bulk actions, new endpoints, and broad visual redesign.
