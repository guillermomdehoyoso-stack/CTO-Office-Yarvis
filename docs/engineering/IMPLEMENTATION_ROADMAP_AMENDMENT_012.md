# YARVIS
# Implementation Roadmap Amendment 012

## Status

**PROPOSED — PENDING INDEPENDENT REVIEW AND RATIFICATION**

This proposal formalizes only the MVP-2 Inbox and Service Case contracts,
events, authority matrix, and frozen boundaries defined by the
[Netpay MVP-2A Inbox and Service Case Contract](NETPAY_MVP2_INBOX_CASE_CONTRACT.md).
It does not authorize implementation.

## 1. Scope and demonstrated contractual gap

MVP-1B provides the tenant-owned Netpay master, but it does not provide a
tenant-owned operational Inbox case aggregate, its commands, queries, events,
or authority. The MVP-2A design specifies a new `NetpayServiceCase` aggregate
for that purpose and identifies the following unallocated IDs. They were
checked against the canonical interaction catalog and repository references:
all are available at the time of this proposal.

This proposal retains the F-011 disposition of `manual-close-validation` (11)
and `netpay-demo` (51). Those 62 historical rows remain immutable, unlinked,
and excluded from canonical authority. The incompatible legacy
`netpay_service_cases` aggregate remains retained and encapsulated; it is not
reused, migrated, linked, or backfilled.

## 2. Proposed MVP-2 Inbox contracts

| ID | Definitive semantic name | Responsibility, inputs, result, and boundary |
| --- | --- | --- |
| `IC-NETPAY-CMD-009` | `CreateNetpayServiceCase` | Creates a tenant-owned `NetpayServiceCase` from same-tenant Netpay Master references, request type, original description, expected outcome, product, priority, source channel/reference, and provenance. It returns the created case/folio through a deterministic replay when applicable; it does not create Mission Work, Operational Tasks, documents, or external portal actions. |
| `IC-NETPAY-CMD-010` | `ClassifyAndUpdateNetpayServiceCase` | Classifies and updates the case in triage, including its request type, allowed product, expected outcome, priority, and checklist template version. It snapshots the selected versioned template into case checklist items and returns the updated case; it does not alter Master ownership or create a separate workflow. |
| `IC-NETPAY-CMD-011` | `ManageNetpayCaseChecklist` | Updates a case checklist item's documented status and safe evidence reference, preserving the versioned checklist snapshot, required/conditional rule, actor, and timestamps. It returns the updated checklist state; it does not store file bytes or documents. |
| `IC-NETPAY-CMD-012` | `AssignNetpayServiceCase` | Assigns or changes the responsible Principal for a same-tenant case and records the resulting append-only activity. It returns the updated assignment; it does not create an Operational Task or grant authority to the assignee. |
| `IC-NETPAY-CMD-013` | `SetNetpayCaseNextAction` | Sets the single current next action with description, responsible Principal, due date, origin, and provenance; replacement or completion closes the prior version and appends activity. It returns the current action/history; it is not an Operational Task. |
| `IC-NETPAY-CMD-014` | `TransitionNetpayServiceCase` | Transitions a case only through the MVP-2A state machine, enforcing completion/cancellation preconditions and appending the transition activity. It returns the resulting case state; it does not reopen a terminal case, which requires a separate contract. |
| `IC-NETPAY-CMD-015` | `RecordNetpayCaseActivity` | Appends a safe case activity with canonical actor, timestamp, summary/type, permitted deltas, safe external reference, correlation, and causation. It returns the appended activity; it never stores tokens, banking values, file bodies, full documents, or copied email bodies. |
| `IC-NETPAY-QRY-005` | `ListNetpayServiceInbox` | Returns a tenant-scoped, deterministically ordered Inbox list filtered by attention, state, product, type, responsible Principal, Client, Branch, Store Reference, overdue, blocked, and information-pending status. It is side-effect free and does not expose foreign cases. |
| `IC-NETPAY-QRY-006` | `RetrieveNetpayServiceCaseDetail` | Returns tenant-scoped canonical detail for one `NetpayServiceCase`, including its safe checklist, next-action history, and append-only activity. It is side-effect free and conceals unknown or foreign cases. |

All seven mutating contracts require an `Idempotency-Key`, a receipt scoped by
Organization, contract, and key, a functional fingerprint, authority
revalidation before receipt lookup or replay, and atomic persistence of the
aggregate, child state, receipt, and events. A mismatched replay is `409`; a
revoked or missing authority denies before replay; local mutation failure rolls
back atomically.

## 3. Proposed Inbox events

| ID | Definitive semantic name | Resulting fact and minimum payload boundary |
| --- | --- | --- |
| `IC-NETPAY-EVT-003` | `NetpayServiceCaseCreated` | Records creation of a case with safe identifiers/codes, canonical actor, Organization, correlation, and causation. |
| `IC-NETPAY-EVT-004` | `NetpayServiceCaseClassified` | Records case classification/update with safe identifiers/codes, canonical actor, Organization, correlation, and causation. |
| `IC-NETPAY-EVT-005` | `NetpayServiceCaseStateChanged` | Records an allowed state transition with safe identifiers/codes, canonical actor, Organization, correlation, and causation. |
| `IC-NETPAY-EVT-006` | `NetpayServiceCaseActivityRecorded` | Records an appended safe activity with safe identifiers/codes, canonical actor, Organization, correlation, and causation. |

Event payloads contain no secrets or complete documents.

## 4. Frozen Inbox ownership and operational rules

- The new tenant-owned `NetpayServiceCase` is the aggregate owner of the
  Inbox. It references same-tenant Netpay Master records without acquiring
  ownership of Client, Company, Branch, or Store Reference.
- `franchisee_change` is one principal case with ordered internal
  `NetpayCaseStep` steps. The steps are not autonomous subcases.
- The request-type catalog and checklist templates are versioned. A classified
  case snapshots its selected template.
- Every case has at most one current next action. Case history and activity are
  append-only.
- `requires_attention` applies only to non-terminal cases that are unassigned,
  have no open next action, have an overdue next action, are in
  `information_pending`, or are `blocked`.
- Document Registry remains the owner of files. A case retains only safe
  document/evidence references and document-status information.
- Mission Work, Operational Task, and Radar neither acquire case ownership nor
  are created implicitly.
- Cross-Organization targets remain concealed.

## 5. Proposed authority matrix

| Proposed role | Validated permissions | Allowed contracts | Deliberate non-grants |
| --- | --- | --- | --- |
| `netpay_inbox_viewer` | `netpay.inbox.read` | `IC-NETPAY-QRY-005`, `IC-NETPAY-QRY-006` | all Inbox commands; `netpay.master.manage`; Radar, Intake, Mission, Document, Economics, Task, Process, Governance, and Workspace permissions |
| `netpay_inbox_operator` | `netpay.inbox.read`, `netpay.inbox.manage` | all nine MVP-2 Inbox command/query contracts | `netpay.master.manage` and every capability outside the Inbox scope |

Netpay Master roles receive no Inbox permission, and Inbox roles receive no
Netpay Master management permission. No Radar, Intake, Mission, Document,
Economics, Task, Process, Governance, or Workspace role receives an Inbox
permission incidentally.

Effective authority derives exclusively from persisted Principal, Organization,
active PrincipalMembership, persisted role permissions, and
`AuthorityResolutionService`. A token identifies a subject only. Headers,
token claims, payloads, Store IDs, and workspace values neither grant authority
nor select an Organization. Any transitional adapter may accept only an
already-resolved `IdentityAuthorityEnvelope`; it must preserve Principal and
Organization, project only validated Inbox permissions, and must not read
headers/tokens or synthesize/elevate permission.

## 6. Explicit MVP-2B exclusions

This proposal does not authorize:

- Gmail, WhatsApp, OCR, Netpay portal automation, synchronization, or other
  external automation;
- file storage, Document Registry ownership changes, or document bytes;
- reparenting or merges in the Netpay Master, direct Store ID transfer, or
  automatic Mission Work or Operational Task creation;
- an expanded analytical dashboard, legacy migration, historical backfill, or
  transformation of the 62 F-011 historical rows;
- implementation code, models, routes, migrations, fixtures, tests, UI,
  production catalog changes, `ROLE_PERMISSIONS`, or changes to prior
  Amendments.

## 7. Required ratification and next step

This proposal requires independent review and ratification. It does not
authorize implementation. MVP-2B may proceed only under a separate bounded
implementation mandate after ratification, and any future expansion of case
types, permissions, or events requires a separate evaluation.
