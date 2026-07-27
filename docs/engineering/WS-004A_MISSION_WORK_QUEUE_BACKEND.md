# WS-004A — Mission Work Queue Backend

Mission Work is the transactional source of truth for operator work. A Work Item
is created only by an explicit, tenant-scoped command from a Mission Inbox item;
Inbox remains a rebuildable projection and never owns assignment or lifecycle
state.

`MissionWorkItem` snapshots only the governed Inbox source identity, title,
summary, and priority. It excludes raw Intake content, messages, headers,
credentials, payloads, and checkpoint data. `inbox_item_id` is a durable,
validated reference rather than a database foreign key: an Inbox rebuild deletes
projection rows, while Work Items must survive unchanged and retain snapshot
identity for later correlation. Both the tenant/Inbox reference and the
tenant/source identity are unique, so an Inbox rebuild with a new projection UUID
cannot create a second Work Item for the same source.

Statuses are `open`, `assigned`, `in_progress`, `waiting`, `resolved`, and
`cancelled`. The explicit transition policy is implemented in the service.
The complete allowed matrix is: `open -> assigned|in_progress|waiting|cancelled`;
`assigned -> open|in_progress|waiting|cancelled`; `in_progress ->
assigned|waiting|resolved|cancelled`; `waiting ->
assigned|in_progress|resolved|cancelled`; and `resolved -> open` and
`cancelled -> open`. Every other status change is a governed conflict and leaves
the aggregate and event stream unchanged.
Assignment of an open item changes it to assigned; unassignment is permitted
only from assigned and returns it to open; unassignment from `in_progress`,
`waiting`, `resolved`, or `cancelled` is rejected. Reassignment within
`assigned` preserves that status. No-op assignment, status, and priority
requests do not emit events, increment the version, or change timestamps.
`assigned_at` is set by assignment and cleared by explicit unassignment;
`started_at` is set only on first entry to `in_progress`; `resolved_at` is set
on resolve and cleared when a resolved item reopens. Each effective mutation
increments the monotonically increasing version exactly once. WS-004A
intentionally defers a client-supplied optimistic concurrency token.

Commands require `mission.work.create`, `mission.work.assign`,
`mission.work.status.change`, or `mission.work.priority.change`; queries require
`mission.work.read`. The authenticated principal is the exclusive Organization
and creator source. Missing and cross-tenant Work Items or Inbox items are
concealed as `RESOURCE_NOT_FOUND`.

Routes are `POST /mission/work-items`, list/detail reads, and assignment,
status, and priority mutation routes beneath `/mission/work-items/{id}`. Lists
support tenant-scoped AND filters for status, priority, assignee, Inbox identity,
source type, and source identity. Pagination has a default `limit` of 50, a
maximum of 100, and a default `offset` of 0. Allowlisted descending sorts are
`updated_at`, `created_at`, `priority`, and `status`, always with the durable ID
as tie-breaker. All read and mutation routes require the authority named by
their interaction contract; missing or cross-tenant targets are concealed as
`RESOURCE_NOT_FOUND`.

Mutations and their minimal immutable `mission.work_item_*` DomainEvents commit
in one Unit of Work. Deferred scope includes frontend, notifications, SLA,
automation, AI, comments, attachments, subtasks, bulk actions, workflow
templates, and external writes.

Migration `20260726_14` creates `mission_work_items` from parent
`20260726_13`. It includes the organization foreign key, durable
organization/Inbox and organization/source unique constraints, status and priority check constraints, and
tenant-oriented status, assignee, priority, source, and Inbox indexes. It never
creates an Inbox foreign key, preserving rebuild survival: an Inbox projection
can be rebuilt while a Work Item, its governed source snapshot, timestamps, and
version remain intact. The migration downgrade removes only this table and a
subsequent upgrade recreates it.
