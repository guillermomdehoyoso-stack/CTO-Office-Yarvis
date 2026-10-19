# Implementation Roadmap Amendment 021 — Netpay Candidate Human Follow-up

**Status: RATIFIED — NETPAY CANDIDATE HUMAN FOLLOW-UP AUTHORIZED**

**Ratified 2026-10-11 against proposal SHA-256:**
`5a6c86c6314e6edfb2cc8dc20f1110d527a609c951a2b4f2482f359797897ccd`.

## 1. Decision requested

Authorize a bounded Netpay Merchant Operations slice that adds append-only,
operator-attributed follow-up notes to existing Gmail intake candidates, subject
to `NETPAY_CANDIDATE_HUMAN_FOLLOW_UP_DESIGN.md` and a separate IG-009 gate.

This amendment preserves IG-008 Gates A/B/C as PASS. It does not reopen or
expand the Gmail pilot and grants no D3 or D2-Lite authority.

## 2. Scope

The authorized candidate package, if ratified, is limited to:

- one candidate-owned append-only follow-up model and migration;
- meetings, calls, agreements, pending items and general follow-up;
- server-owned actor, recorded time and `operator_reported` provenance;
- optional operator-supplied event time;
- idempotent append and tenant-scoped chronological query;
- safe audit Event without note or Gmail content;
- minimum create/read chronology UI; and
- tests and evidence in the companion gate.

It does not require an owner link and cannot create one.

## 3. Proposed identifiers

Repository inspection on branch `feat/netpay-gmail-intake-sentinel` found these
identifiers free. Ratification authorizes their later canonical registration:

- `IC-NETPAY-CMD-037` — `RecordNetpayCandidateFollowUp`;
- `IC-NETPAY-QRY-020` — `ListNetpayCandidateFollowUps`; and
- `IC-NETPAY-EVT-027` — `NetpayCandidateFollowUpRecorded`.

Amendment 021 and IG-009 are also free in the inspected repository. No numerical
gap implies any additional reservation.

## 4. Authority and ownership

Netpay Merchant Operations owns the follow-up record. Existing
`netpay.inbox.manage` authorizes append; `netpay.inbox.read` authorizes query.
Identity comes only from the active authority envelope. Domain Events provide
safe audit, not note storage. Case Activity remains owned by an existing case
and is not reused for unlinked candidates.

## 5. Safety invariants

- Source Gmail rows and extracted facts are immutable and separate.
- Candidate state, disposition, owner, next action and review decision do not
  change when a follow-up is appended.
- Entries cannot be edited or deleted.
- Missing event dates remain null.
- Note text never enters Domain Events, logs, fixtures or evidence.
- Same-tenant checks precede receipt replay.
- No Gmail/OAuth call occurs in this slice.

## 6. Dependency and migration rule

The design-time Alembic graph has one actual head, `20261008_49`. The
implementation must verify the graph again immediately before creating a
migration and must parent the then-current real head. This amendment does not
reserve a revision number.

## 7. Evidence and completion

Completion requires every criterion in the design and IG-009, including
idempotent replay/conflict, cross-tenant failure, append-only proof, real browser
reload, fresh-session readback, migration round trip, negative source/decision/
Gmail mutation checks and safe evidence review.

## 8. Exclusions

Automatic case creation/linking, changes to human decisions, Gmail access or
mutation, AI, reminders, automation, scheduler, worker, Pub/Sub, webhook, D3 and
D2-Lite remain unauthorized.

## 9. Proposed ratification statement

`RATIFY AMENDMENT 021 — NETPAY CANDIDATE HUMAN FOLLOW-UP DESIGN AUTHORIZED; IMPLEMENTATION REQUIRES IG-009 RATIFICATION. IG-008 GATES A/B/C REMAIN PASS. D3 AND D2-LITE REMAIN UNAUTHORIZED.`
