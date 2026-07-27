# Current Sprint

## Identity

**Work package:** WS-004B — Mission Work Queue Frontend

## Goal

Deliver the governed operator surface for Mission Work Items without changing
their backend contracts, ownership, lifecycle, or tenant boundaries.

## Scope

- List Mission Work Items.
- Open a Work Item detail.
- Filter the queue.
- Assign and unassign a Work Item.
- Change status.
- Change priority.
- Navigate from Mission Inbox to related Mission Work.
- Handle governed `404`, `409`, and authorization responses.

## Dependencies

- WS-003 Mission Inbox Projection Foundation.
- WS-004A Mission Work Queue Backend at `c139f74` / `ws004a-backend-complete`.
- Alembic head `20260726_14`.
- Existing interaction contracts and backend authorization boundaries.

## Current Gate

WS-004B may consume the public Mission Work and Mission Inbox interfaces only.
Frontend work must preserve tenant concealment, authorization handling, and the
backend-owned Work Item lifecycle.

## Entry Criteria

- Repository state is verified at session start.
- WS-004A closure baseline is available.
- Backend contracts, authorities, and error semantics are read before UI work.

## Exit Criteria

- Operators can list, filter, open, assign/unassign, reprioritize, and change
  Work Item status through the governed interface.
- Mission Inbox navigation reaches the related Work Item context.
- `404`, `409`, and authorization responses are represented truthfully.
- No excluded capability is introduced.

## Definition of Done

The WS-004B frontend uses the existing governed backend contracts, passes its
applicable tests, and does not redefine Work Item semantics.

## Open Risks

- Verify frontend route, state, and authorization conventions before changes.
- Preserve the distinction between the rebuildable Mission Inbox projection and
  the transactional Mission Work source of truth.

## Explicitly Out of Scope

- SLA.
- Comments.
- Attachments.
- Notifications.
- Automation.
- AI.

## Next Package

Implement WS-004B — Mission Work Queue Frontend.
