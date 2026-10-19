# Netpay Candidate Human Follow-up Design

**Status: RATIFIED — IMPLEMENTATION AUTHORITY VIA IG-009**

**Ratified 2026-10-11 against proposal SHA-256:**
`37eb2c050b768e45364065f24e759ae28e89715e67d34cb8111ea001675ce076`.

## 1. Purpose and boundary

This design adds an append-only human follow-up chronology to an existing
`NetpayIntakeCandidate`. It records operator-reported meetings, calls,
agreements, pending items and general follow-up without changing Gmail source
evidence, deterministic extraction, candidate disposition or an owner record.

Rock N' Wok is the motivating example: an operator must be able to record that
a client conversation occurred and that an internal operational form was
prepared, while leaving ticket existence, submission, approval, application and
resolution explicitly unconfirmed unless later evidence establishes them.

The capability belongs to Netpay Merchant Operations. It does not extend Gmail
access. IG-008 Gates A/B/C remain PASS and the productive Gmail boundary remains
the already approved ten-message pilot.

## 2. Existing mechanisms reviewed

| Mechanism | Reusable part | Why it is insufficient alone |
| --- | --- | --- |
| `NetpayIntakeCandidate` and candidate review endpoint | Tenant-owned target; existing read/manage authority; idempotent command receipts | `edit` changes the projection and state. It has no append-only attributed note read model. Its `reason` is command metadata, not a chronology entry. |
| `NetpayCaseActivity` / `IC-NETPAY-CMD-015` | Append-only activity pattern, actor attribution and safe event payload | Requires a verified service case. A candidate may be unlinked and must not be forced into a case. |
| Commercial Intake timeline | Readable temporal projection from domain events | Requires a Commercial Intake owner and does not retain the human note body as a candidate-owned record. |
| `DomainEvent` | Safe audit signal, correlation and causation | Event payloads must not become the primary note store or contain operational note text. |
| `NetpayGmailCommandReceipt` | Organization-scoped idempotency, actor and replay/conflict semantics | May be reused for command execution, but the receipt is not the chronology read model. |

No existing contract meets all requirements without transferring ownership or
conflating human context with source evidence.

## 3. Proposed contracts and verified free identifiers

Repository-wide inspection found the current Netpay maxima at
`IC-NETPAY-CMD-036`, `IC-NETPAY-QRY-019` and `IC-NETPAY-EVT-026`.
The following identifiers are free in the inspected tree and are proposed, not
allocated, until ratification and catalog registration:

| Identifier | Name | Purpose |
| --- | --- | --- |
| `IC-NETPAY-CMD-037` | `RecordNetpayCandidateFollowUp` | Append one operator-reported follow-up entry. |
| `IC-NETPAY-QRY-020` | `ListNetpayCandidateFollowUps` | Return the candidate chronology in stable recorded order. |
| `IC-NETPAY-EVT-027` | `NetpayCandidateFollowUpRecorded` | Emit a safe audit fact without note content. |

The command requires existing `netpay.inbox.manage`; the query requires
`netpay.inbox.read`. No new global role or permission is proposed.

## 4. Owned data

Proposed `NetpayCandidateFollowUp` fields:

| Field | Contract |
| --- | --- |
| `id` | Internal UUID. |
| `organization_id` | Required; derived only from the authority envelope. |
| `candidate_id` | Required same-Organization candidate; no owner link required. |
| `kind` | Closed enum: `meeting`, `call`, `agreement`, `pending_item`, `general_follow_up`. |
| `note` | Required safe operator text, 1–4000 characters. It is never copied into source facts or Events. |
| `provenance_kind` | Fixed value `operator_reported`; clients cannot override it. |
| `occurred_at` | Optional timezone-aware event time. Null means “Fecha del evento no proporcionada.” |
| `recorded_at` | Required server time. |
| `created_by_principal_id` | Required actor from the authority envelope. |
| `correlation_id` | Required canonical trace identifier. |

Entries are immutable: no update or delete command is introduced. Corrections
are new entries that refer in prose to the earlier record without mutating it.
The candidate and its Gmail source remain unchanged. The implementation must not
derive an event date from message time, current time, wording or UI state.

The schema uses an Organization-scoped candidate foreign key/check enforced in
the command transaction. The implementation gate must re-run `alembic heads`
before selecting a revision parent. At design time the actual graph reports one
head, `20261008_49`; this document does not assign a revision identifier.

## 5. Command semantics

`RecordNetpayCandidateFollowUp` accepts `candidate_id`, `kind`, `note` and
nullable `occurred_at`. Organization, actor, provenance and recorded time are
server-owned.

The command:

1. resolves active authority and `netpay.inbox.manage` before receipt replay;
2. resolves the candidate in the envelope Organization;
3. fingerprints command, candidate and normalized payload;
4. replays the same idempotency key and fingerprint without a second row/event;
5. rejects key reuse with a different fingerprint;
6. appends one follow-up and `IC-NETPAY-EVT-027` atomically; and
7. never changes candidate state, owner, disposition, next action, source or
   extraction data.

The safe Event contains follow-up ID, candidate ID, kind, actor principal ID,
`occurred_at_present`, correlation and causation. It excludes note text, source
content, Gmail IDs, addresses, subjects and attachment metadata.

## 6. Query and chronology

`ListNetpayCandidateFollowUps` resolves the candidate within the authority
Organization and returns entries ordered by `(recorded_at, id)` ascending. The
UI displays event time separately when present; it never reorders audit history
as though an operator-supplied event time were the recording time.

Each row displays:

- Spanish kind label;
- operator identity using the existing safe Principal display contract;
- recorded date/time;
- optional event date/time or the explicit missing-date fallback;
- `Reportado por operador`; and
- note text with wrapping and no raw JSON in the primary view.

Cross-Organization candidate IDs return not found without revealing existence.
Pagination must be bounded and deterministic.

## 7. Minimum interface journey

1. The operator opens a candidate and sees **Seguimiento humano** after the
   operational summary and before technical evidence.
2. Existing entries appear as a readable chronology. Email evidence remains in
   its own collapsed section.
3. **Registrar seguimiento** opens a form with kind, optional event date and
   note. The form states that the entry is append-only and operator-reported.
4. Event date is blank by default. No candidate/source value prepopulates it.
5. A review screen shows the exact note and distinguishes recorded time from
   optional event time.
6. One submission is protected against double click and uses an idempotency key.
7. Success shows confirmation and the persisted entry after API readback.
8. Reload reproduces the entry. No Accept, Link, ticket creation or Gmail action
   is triggered.

For the motivating example, the operator may record the confirmed conversation
and jointly prepared internal form. Unknown ticket, submission, approval,
application and resolution remain absent or explicitly unconfirmed. Follow-up
about verifying the form belongs in the note or existing proposed-next-action
field; neither establishes completion.

## 8. Acceptance criteria

The slice passes only if:

1. an unlinked candidate accepts a follow-up without creating an owner;
2. actor, server recorded time and `operator_reported` are server-controlled;
3. omitted `occurred_at` persists and renders as null with a clear fallback;
4. supplied `occurred_at` is preserved exactly and shown separately;
5. same key/same payload creates one row and one safe Event;
6. same key/different payload conflicts without mutation;
7. cross-Organization command and query fail closed before replay;
8. chronology order is stable across reload and fresh database sessions;
9. note/source/candidate/disposition hashes or relevant fields prove that Gmail
   source, extraction, decision, owner and next action were not modified;
10. Event and logs contain no note text or Gmail content;
11. no update/delete endpoint exists for a follow-up;
12. UI labels, empty-date fallback, wrapping, double-click protection and
    confirmation pass component and real-browser checks;
13. migration upgrade/downgrade is proven from the actual Alembic graph;
14. relevant backend/frontend regressions, build and static checks pass; and
15. Gmail/OAuth is not called and A/B/C evidence remains unchanged.

## 9. Explicit exclusions

No case or Commercial Intake creation, automatic linking, Gmail read or
mutation, attachment access, AI analysis, notification, reminder, scheduler,
worker, webhook, Pub/Sub, D3, D2-Lite, note editing/deletion, decision rewrite or
source/extraction mutation is included.
