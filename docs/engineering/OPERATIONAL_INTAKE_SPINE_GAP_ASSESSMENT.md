# Operational Intake Spine — Gap Assessment

**Assessment date:** 2026-08-19

**Scope:** Static read-only assessment of the manual Netpay registration spine:
`Client → Requisition → Event → Evidence → Task/Next Action`.

**Recommendation:** **Pilot now; authority gap in parallel.** The manual
Master/Inbox circuit is largely implemented and reusable. An operable governed
Document Registry link for a `NetpayServiceCase` is not established, but the
existing safe evidence-reference path supports a bounded manual pilot without
real attachments. A true document attachment or association requires separate
authority/contract confirmation before any code.

## 1. Current gate and authority boundary

`IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` ratifies the Netpay Inbox case
contracts and explicitly keeps Gmail, WhatsApp, automation, document ownership
changes, and implementation authorization out of scope. The reconciled current
state records Netpay Master/Inbox as implemented evidence but opens no successor
implementation package. F-011 provides the existing persisted Principal,
Organization, Membership, server-derived permission, tenant-concealment, and
`AuthorityChanged` boundary.

This assessment grants no implementation, migration, contract allocation,
Gmail, OAuth, or external action.

## 2. Capability inventory

| Capability | Classification | Existing evidence and disposition |
| --- | --- | --- |
| Client | **Existing and reusable** | `NetpayClient`, `NetpayCompany`, `NetpayBranch`, and optional `NetpayStoreReference` are tenant-owned Master records. APIs and the Inbox creation modal search/create the Master hierarchy. |
| Requisition / Case | **Existing and reusable** | `NetpayServiceCase` is the tenant-owned Inbox aggregate with product, case type, state, priority, Master references, provenance, assignment, and target date. |
| Event | **Existing and reusable** | `NetpayCaseActivity` is append-only through case routes; safe DomainEvents are emitted for creation, state change, and activity. |
| Evidence / Document | **Partial** | Checklist has `safe_evidence_reference`; `NetpayCaseDocumentReference` exists. No inspected Inbox endpoint/UI creates document references, and Document Registry associations do not list `netpay_inbox_case` as a subject type. |
| Task / Next Action | **Existing and reusable** | `NetpayCaseNextAction` enforces at most one open action per case, with responsible Principal and due date. It is the correct spine commitment; Operational Task/Mission Work must not be created implicitly. |
| Checklist | **Existing and reusable** | Case type/template, tenant-scoped snapshot, checklist item status, and safe evidence reference exist. |
| Timeline | **Existing and reusable** | Case activities are ordered and returned in case detail; the Inbox UI renders activity. Do not create a second timeline. Mission Work timeline is separate and not required for an Inbox case. |
| Dashboard | **Existing and reusable** | `NetpayInboxWorkspace` displays attention, overdue, information-pending, blocked, and unassigned counts plus a filtered queue. |
| Authority / audit | **Existing and reusable** | `netpay_inbox_viewer` / `netpay_inbox_operator`, F-011 envelope, tenant-scoped targets, idempotency receipts, correlation/causation, and safe events are present. New document-link behavior lacks confirmed authority. |
| Legacy `NetpayServiceCase` import path | **Legacy — do not reuse** | The earlier legacy service-case/shipment evidence is expressly retained and encapsulated; it is not the tenant-owned Inbox aggregate and must not be imported or backfilled. |
| Mission Work / Operational Task automation | **Exists but not authorized** | Both aggregates exist, but Amendment 012 forbids implicit creation from an Inbox case. They are not necessary for the manual next-action spine. |

## 3. Current relationship map

```text
Organization
  ├─ NetpayClient
  │   └─ NetpayCompany
  │       └─ NetpayBranch ── optional NetpayStoreReference
  └─ NetpayServiceCase
        ├─ client_id / company_id / branch_id / optional store_reference_id
        ├─ NetpayCaseChecklistItem (case_id)
        ├─ NetpayCaseNextAction (case_id; one open action)
        ├─ NetpayCaseActivity (case_id; safe timeline)
        ├─ NetpayCaseDocumentReference (case_id; existing but no inspected write surface)
        └─ Principal references: created_by, updated_by, responsible
```

All Master/Inbox tenant references are constrained by `organization_id` in the
relevant models/routes. Document Registry owns Documents and its generic
association model currently allows Organization, Site, Project, Mission Work,
Operational Task, and Process Instance subjects—not an Inbox case.

## 4. Golden manual workflow

The same manual spine supports **alta TPV** and **alta e-commerce**; product and
case type select the difference, while case ownership remains Netpay Inbox.

1. **Locate or register Client:** search tenant-scoped Netpay Master; if absent,
   manually create Client → Company → Branch and optional Store Reference.
2. **Create requisition:** create a `NetpayServiceCase` with manual source,
   description, expected outcome, product (`tpv` or `ecommerce`), priority, and
   provenance.
3. **Select type:** use `tpv_activation` or `ecommerce_activation` (or the
   applicable onboarding type); snapshot the approved checklist template.
4. **Register event:** append safe case activity for reception, follow-up,
   decision, or external safe reference; it becomes the case timeline.
5. **Attach/link evidence:** for the constrained present path, set checklist
   `safe_evidence_reference` and/or record a safe activity reference. A true
   Document Registry association remains a gap, not a shortcut.
6. **Checklist:** update required items and evidence status manually.
7. **Responsible and date:** assign a same-tenant active Principal, then set one
   open next action with responsible Principal and due date.
8. **Progress:** transition through `received → triage → ready → in_progress →
   submitted/completed`, using `information_pending` or `blocked` when needed.
9. **Close:** completion/cancellation enforces the existing state policy;
   terminal closure remains timeline-auditable.

The UI already contains a three-step creation modal, Inbox filters, attention
dashboard, case detail, checklist, assignment, next-action, state, and activity
controls. It does not establish a real document-link control.

## 5. Gaps and their operational boundary

| Area | Blocking gap | Why it blocks |
| --- | --- | --- |
| Domain | No additional aggregate is required. | Reusing Master and `NetpayServiceCase` avoids duplicate ownership. |
| API | No inspected command/route for `NetpayCaseDocumentReference`; Document Registry does not accept the case as an association subject. | Blocks a durable governed evidence/document link; it does **not** block the no-attachment manual pilot. |
| UI | No evidence/document-link panel for an Inbox case. | Operators can enter safe text references but cannot link a governed Document; this does **not** block the no-attachment manual pilot. |
| Authority | Amendment 012 prohibits Document Registry ownership changes and allocates no explicit case-document link mutation. | Extending association ownership or an evidence-link command needs separate authority. It must not be implemented now and is only a conditional Gmail dependency if a future intake needs to link documents. |
| Tests | Existing Inbox/Master/UI tests cover core flow; no focused document-link case test was found. | A future link must prove same-tenant association, safe payload, replay, and no duplicate timeline. |
| Data / migrations | `NetpayCaseDocumentReference` already exists. | A minimal safe-reference UI/API may need no migration; a real Document Registry association may require an authorized schema/subject decision. |

## 6. Mandatory reuse boundaries

- Extend `NetpayClient` / Company / Branch / Store Reference; do not create a
  second Client or Master.
- Extend `NetpayServiceCase`, its single next action, checklist, activity, and
  Inbox workspace; do not create a second Inbox or case timeline.
- Keep Document Registry as Document owner. Do not create a parallel file
  import/store or copy document bytes into Inbox.
- Use current manual source/provenance and existing case activity; do not create
  automatic channel ingestion or out-of-authority automation.
- Do not convert an Inbox case into Mission Work or Operational Task implicitly.

## 7. Manual pilot now; durable-link slice only after authority

**Manual pilot available now:** manual TPV/e-commerce case capture through the
existing Master, `NetpayServiceCase`, checklist, safe textual activity,
assignment, one next action, due date, state, activity timeline, Inbox
dashboard, and closure. It uses no real attachments or durable document link.

**Separate future slice:** one governed evidence-link surface only after a
separate authority decision confirms the permitted case-document boundary.

Likely affected components, only if separately authorized:

- `apps/api/src/yarvis_api/api/routes/netpay_inbox.py` and
  `schemas/netpay_inbox.py`: expose a bounded same-tenant evidence-reference or
  document-link action using the existing case reference model;
- `apps/web/src/api/netpay.ts` and
  `components/netpay/NetpayInboxWorkspace.tsx`: evidence/link control and detail
  display;
- `apps/api/tests/test_netpay_inbox.py` and
  `apps/web/src/components/netpay/NetpayInboxWorkspace.test.tsx`: TPV and
  e-commerce manual golden paths, replay, tenant isolation, required next
  action, and timeline assertions;
- migration: **not necessary** for a safe existing case-reference action;
  **TO BE DECIDED under authority** for any Document Registry subject/association
  change.

**Manual pilot plan (not executed):**

1. Locate or create an authorized client in the existing Master hierarchy.
2. Open one TPV or e-commerce case.
3. Complete its checklist and register a safe activity without unnecessary PII.
4. Assign the responsible same-tenant Principal; set one next action and due
   date.
5. Advance the state, verify its timeline and Inbox dashboard, then close it or
   leave it correctly pending with the next action, responsible, and date.

This plan contains no attachment, real document, Gmail/WhatsApp, automation, or
authority change.

## 8. Operational success criteria

- Every requisition has a state.
- Every non-terminal requisition has one open next action, responsible, and due
  date; otherwise Inbox attention exposes the gap.
- Case activity is tenant-scoped and recoverable as a timeline.
- The manual pilot uses only structured evidence status and safe text
  references; durable evidence linkage awaits separate authority.
- Pending, overdue, blocked, and unassigned filters remain usable.
- No case is created automatically from Gmail, WhatsApp, or another channel.
- Tenant isolation, envelope-based authority, idempotency, and safe audit events
  are preserved.

## 9. Pilot metrics and guards

**Metrics:** percentage of cases with a next action; percentage with a
responsible and due date; time to locate case state; pending cases/documents;
lost requests; rework; and cycle time.

**Guards:** no real attachments/documents; no Gmail or WhatsApp; no automation;
no new Inbox, Master, or timeline; and no authority change.

## 10. Explicitly outside this assessment slice

Gmail, WhatsApp, OAuth, biometrics/passkeys, autonomous automation, the new
identity foundation, new verticals, advanced analytics, legacy case migration,
and automatic Mission Work/Operational Task creation are out of scope.

## 11. Two-sprint maximum plan

| Sprint | Scope | Gate-dependent output |
| --- | --- | --- |
| A — manual circuit | Run the separately authorized no-code manual pilot using the existing Master/case/checklist/assignment/next-action/state/timeline flow; collect the defined metrics. In parallel, seek no implementation authority for the durable evidence-link boundary. | A demonstrated tenant-scoped TPV and e-commerce circuit with no automation and no real documents. |
| B — follow-up/dashboard and Gmail preparation | If separately authorized, decide the durable evidence-link boundary; otherwise harden pending/overdue views and pilot reporting. Document Gmail boundary readiness only. | Better manual follow-up dashboard and a non-executing readiness input for the separately governed Gmail cycle. |

## 12. Final recommendation

**Pilot now; authority gap in parallel.** The existing manual Master and Inbox
circuit supports a bounded no-code TPV/e-commerce pilot now. Do not claim
durable Document Registry evidence linkage or use real attachments until a
separate authority decision confirms the permitted case-document boundary.
That decision is a blocker only for durable evidence and a conditional future
dependency for Gmail if that intake needs document linkage; it is not a blocker
for this manual pilot.

## 13. Review closure

`OPERATIONAL_INTAKE_SPINE_GAP_ASSESSMENT_REVIEW.md` MAJOR M-001 is **Closed**
by this correction: the recommendation and plan now distinguish the available
no-attachment manual pilot from the separately governed durable-document gap.
Its OBSERVATION O-001 remains non-blocking: runtime authorization of the
operator and responsible Principal must be verified when a separately
authorized pilot is actually run.

## Explicit non-effects

This assessment creates no design generalization, contract ID, catalog change,
code, migration, configuration, data, Principal, Membership, Gmail/OAuth action,
or external request. It does not modify or stage
`apps/api/src/yarvis_api/api/authentication.py`, and it creates no commit or
push.
