# WS-006D — Mission Work / Process Association

## Status

Implemented and validation-complete; pending conformance review and commit.

## Design Summary

WS-006D connects independent Mission Work and Process Runtime aggregates through the
Process-owned `ProcessInstanceWorkLink`. The link preserves historical association;
it never transfers Work lifecycle authority to Process or Process lifecycle authority
to Work.

`primary` is a configurable relationship value rather than a closed domain category.
There is at most one active primary link per Process Instance. A Mission Work Item may
have any number of active Process Instances. Unlinking closes a link with
`unlinked_at`; it does not delete history.

## API and Authority

- `POST /process-instances/{id}/work-links` links an instance to a Work Item under
  `process.instance.work.link`.
- `POST /process-instances/{id}/work-links/{link_id}/unlink` closes the active link
  under `process.instance.work.unlink`.
- Process-scoped reads expose primary link and instance history under
  `process.instance.read`.
- `GET /mission/work-items/{id}/process-links` exposes related links through the
  same Process-owned query contract and tenant concealment rules.

Every command uses an idempotency key and request fingerprint. Same-key/same-request
replays the existing link result; a divergent request or active duplicate is a
governed conflict. Cross-tenant and missing resources are concealed with `404`.

## Events and Projection

Association mutations record `process_instance.work_linked` and
`process_instance.work_unlinked` `DomainEvent` assertions in the same Unit of Work as
link state. They include tenant, Process Instance, Work Item, relationship, actor,
correlation, and causation evidence.

`ProcessMissionWorkTimelineProjector` is a Mission Work-owned projection boundary. It
reads Process `DomainEvent` records and appends an ordered `MissionWorkEvent` only when
its `(organization_id, work_item_id, source_domain_event_id)` identity has not already
been projected. It projects start, transition, completion, cancellation, link, and
unlink evidence. Process Runtime does not write Mission Work Timeline rows directly.

When a link is created, existing Process source history may be projected so the Work
Timeline has useful context. After unlinking, subsequent Process lifecycle events are
not projected through the inactive link; the unlink record remains historical evidence.

## Migration

Alembic revision `20260728_18` follows `20260728_17` and creates
`process_instance_work_links`, its active-primary and active-relationship partial
unique indexes, idempotency constraints, and tenant/work/instance indexes. It adds
`source_domain_event_id` plus a partial unique projection identity index to
`mission_work_events`. Downgrade removes these additions without changing historical
migrations.

## Deferred Scope

No frontend, dashboard, notification, scheduler, automation, SLA, BPMN, AI, rigid
process category, automatic Work closure, or automatic Process cancellation is added.
WS-006D intentionally does not synchronize the two aggregate lifecycles.

## Validation Evidence

- Python compilation completed successfully.
- Focused association, Process Runtime, Mission Work Timeline, contract, and
  migration coverage: **46 passed**.
- Full backend suite: **289 passed**, 0 failed.
- Alembic reports one head: `20260728_18`.
- `git diff --check` completed successfully.
