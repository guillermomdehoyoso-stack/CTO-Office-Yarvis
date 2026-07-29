# WS-006E — Operational Workspace Read Model

**Status:** Implemented backend read model — pending validation evidence  
**Owner:** Mission Control read composition

## Purpose

The Operational Workspace provides one tenant-safe, read-only response for an
existing `MissionWorkItem`. It composes existing authoritative records; it does not
persist another aggregate, transfer ownership, or synchronize lifecycle state.

## Endpoint and Authority

`GET /mission/work-items/{work_item_id}/workspace?currency=MXN` implements
`IC-MISSION-QRY-007` and requires `mission.work.read`. Missing and cross-tenant
Work Items are concealed as `404`.

## Response Composition

- Mission Work identity, state, priority, assignee, and deterministic participants.
- Unified Mission Work Timeline, ordered by its existing sequence number.
- Related active and historical Process Instances through retained Process-owned
  links. Each includes definition/version, current stage, lifecycle, last transition,
  and link history.
- Direct-only `EconomicSummary` for the Work Item and for every related Process
  Instance, using the canonical Operational Economics calculation policy.
- Derived active/historical Process counts and a latest observed activity timestamp.

The implementation uses bounded queries: one Work query, one Timeline query, one
joined Process/link query, and one batched Economic Fact query. It does not issue one
query per Process Instance.

## Explicit Absences

Tasks, checklists, SLA, waiting/snoozed semantics, documents, UI, write commands,
economic roll-ups, lifecycle synchronization, automation, and new economics
calculations are absent. A Process/Work association remains an association only; its
facts are never included in the Work summary unless a future ratified roll-up model
explicitly permits it.
