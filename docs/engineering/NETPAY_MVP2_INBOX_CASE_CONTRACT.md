# Netpay MVP-2A — Inbox and Service Case Contract

## Status

**DESIGN PROPOSAL — REQUIRES INDEPENDENT CONTRACT AND AUTHORITY RATIFICATION BEFORE MVP-2B**

MVP-2 is a human-operated, tenant-owned Netpay service Inbox. Authority remains
Principal + active PrincipalMembership + Organization + persisted permissions
resolved by `AuthorityResolutionService`; headers, token claims, payloads,
Store IDs, and workspace values never grant authority or select tenancy.

## Canonical owner and legacy disposition

MVP-2B creates a new tenant-owned `NetpayServiceCase` aggregate with `id`,
non-null `organization_id`, immutable human folio, `client_id`, `company_id`,
optional `branch_id` and `store_reference_id`, request type, original
description, expected outcome, product (`tpv`, `ecommerce`, `mixed`,
`not_applicable`), state, priority, responsible Principal, target date, current
next action, source channel/reference, checklist template version, provenance,
timestamps, and canonical actor references. Master links are same-tenant links,
not ownership transfers.

The current `netpay_service_cases` is an incompatible legacy email/logistics
import aggregate: global folio and email keys, nullable tenancy, raw parser and
shipment/device fields, and unauthenticated import routes. It is retained and
encapsulated, never reused, migrated, linked, or backfilled. MVP-2B names and
namespaces the new aggregate explicitly to avoid a table/model collision.

## Request catalog and composite case

The configurable, versioned initial catalog is: `merchant_onboarding`,
`branch_onboarding`, `tpv_activation`, `ecommerce_activation`,
`bank_account_change`, `document_submission`, `legal_entity_change`,
`franchisee_change`, `store_deactivation`, `terminal_replacement`,
`support_incident`, and `unclassified`. It controls display name, active flag,
allowed products, default template version, and completion policy; case text,
outcome, priority, source, and decisions remain data. No type creates a rigid
separate workflow.

`franchisee_change` is one parent outcome with ordered internal
`NetpayCaseStep` children: validate new franchisee, collect evidence, process
former Store deactivation when needed, create/link Master records, request a
new Store, confirm activation, then close. Steps are not independently
addressable subcases and append activity; they cannot overwrite historical
Company, Branch, Store, or former-franchisee facts.

## State, checklist, next action, and activity

| State | Allowed next states | Meaning |
| --- | --- | --- |
| `received` | `triage`, `cancelled` | captured, not assessed |
| `triage` | `information_pending`, `ready`, `blocked`, `cancelled` | classify and set outcome/template |
| `information_pending` | `triage`, `ready`, `blocked`, `cancelled` | known required input absent |
| `ready` | `in_progress`, `information_pending`, `blocked`, `cancelled` | inputs sufficient to work |
| `in_progress` | `submitted`, `information_pending`, `blocked`, `completed`, `cancelled` | human work underway |
| `submitted` | `in_progress`, `information_pending`, `blocked`, `completed`, `cancelled` | human submitted externally; no automation implied |
| `blocked` | `triage`, `ready`, `in_progress`, `cancelled` | documented impediment |
| `completed` / `cancelled` | none | terminal |

Only Inbox manage authority mutates. Completion requires an expected outcome,
completion reference/note, no unresolved required checklist item or required
step; cancellation requires a reason. `information_pending` differs from
`blocked`: the former identifies missing input; the latter identifies an
impediment. Reopen is excluded pending a separate contract.

`NetpayChecklistTemplate` is versioned. Classification snapshots it into
`NetpayCaseChecklistItem` with `missing`, `received`, `under_review`,
`confirmed`, `rejected`, `not_applicable`, or `expired`; required/conditional
rule, actor, timestamps, and safe evidence reference are preserved. Templates:

| Template | Minimum checks |
| --- | --- |
| TPV | legal identity, branch/location, contact, banking authorization, activation confirmation **(confirm with Netpay)** |
| E-commerce | legal identity, contact, website/domain, settlement authorization, activation confirmation **(confirm with Netpay)** |
| Mixed | TPV plus e-commerce, with shared evidence linked once |
| Bank account change | authorized request, legal identity, evidence, effective-date confirmation **(confirm with Netpay)** |
| Document submission | requested type, receipt, human validation, rejection/expiry |
| Franchisee change | franchisee validation, former Store evidence, Master link, Store/activation confirmation **(confirm with Netpay)** |

One current `NetpayCaseNextAction` has description, responsible Principal, due
date, `open/done/cancelled/overdue`, human/suggested origin, and provenance.
Replacement/completion closes its version and appends activity; `overdue` is
derived when due date is past. It is not an Operational Task. `NetpayCaseActivity`
is append-only: actor, timestamp, safe summary/type, state/assignee/action
delta, safe external reference, correlation and causation. It never includes
tokens, banking values, file bodies, full documents, or copied email bodies.

## Documents and Inbox query

MVP-2B stores only requirement status and a safe future Document Registry
`document_id`/version or external-evidence reference. Inbox owns neither bytes
nor files. A later ratified Document Registry subject/association for
`netpay_service_case` may link a validated document without moving ownership.

The Inbox is a tenant-scoped case query, not `MissionInboxItem` (a rebuildable
Intake projection). It filters attention, state, product, type, responsible
Principal, Client, Branch, Store Reference, overdue, blocked, and information
pending. `requires_attention` is true for a non-terminal case that is
unassigned, lacks an open action, has an overdue action, is information pending,
or is blocked. Order: attention, overdue action, priority `urgent/high/normal/low`,
target date (null last), oldest activity, UUID; offset/limit pagination is stable.

Mission Work and Operational Task are not implicitly created. They may later
consume a case event through their own ratified owner contracts. Radar supplies
only receipt/activity test patterns; it owns no case data.

## Proposed contracts and authority

Inspection confirms these IDs are free and require ratification:

| ID | Contract |
| --- | --- |
| `IC-NETPAY-CMD-009..015` | Create; classify/update; manage checklist; assign; set next action; transition; record activity |
| `IC-NETPAY-QRY-005..006` | List Inbox; retrieve case detail |
| `IC-NETPAY-EVT-003..006` | Case created; classified; state changed; activity recorded |

Definitive names: `CreateNetpayServiceCase`,
`ClassifyAndUpdateNetpayServiceCase`, `ManageNetpayCaseChecklist`,
`AssignNetpayServiceCase`, `SetNetpayCaseNextAction`,
`TransitionNetpayServiceCase`, `RecordNetpayCaseActivity`,
`ListNetpayServiceInbox`, `RetrieveNetpayServiceCaseDetail`,
`NetpayServiceCaseCreated`, `NetpayServiceCaseClassified`,
`NetpayServiceCaseStateChanged`, and `NetpayServiceCaseActivityRecorded`.

| Role | Permission | Scope |
| --- | --- | --- |
| `netpay_inbox_viewer` | `netpay.inbox.read` | list/detail only |
| `netpay_inbox_operator` | `netpay.inbox.read`, `netpay.inbox.manage` | all MVP-2 case commands and queries |

No Master, Radar, Intake, Mission, Document, Task, Process, Economics,
Governance, or Workspace role receives Inbox permission incidentally.

All commands require `Idempotency-Key`, Organization + contract + key receipt,
functional fingerprint, authority revalidation before lookup/replay, and atomic
aggregate/child/receipt/event persistence. Mismatched replay is `409`; revoked
or missing authority denies before replay; unknown/foreign targets are concealed;
local mutation failure rolls back. Event payloads contain IDs, codes, actor,
correlation, and causation only.

## Delivery and recommendation

- **MVP-2B:** backend case, state machine, checklist snapshot, next-action
  history, activity, receipts, events, and Inbox queries.
- **MVP-2C:** Inbox, manual capture, detail, checklist, next-action/activity UI.
- **MVP-2D:** governed document references and assisted upload after Document
  Registry association ratification.
- **MVP-2E:** controlled real-request pilot; no portal automation.

MVP-2B needs an independent amendment/ratification for the seven commands, two
queries, four events, two permissions, and two roles. It must not add legacy
backfill, expand Master roles, create Mission Work/Task automatically, integrate
Gmail/WhatsApp/OCR, or alter the 62 excluded F-011 historic rows.

**Recommendation:** ratify this dedicated Inbox contract/authority matrix, then
implement MVP-2B as a new tenant-owned case vertical; keep the legacy importer
encapsulated and defer UI/document linkage.
