# Operational Intake Spine — Adversarial Review

**Review date:** 2026-08-19
**Scope:** Read-only adversarial review of
`OPERATIONAL_INTAKE_SPINE_GAP_ASSESSMENT.md`. This review creates no authority
and does not execute a pilot.

## Decision

**Amendment Required.** The factual inventory supports a manual pilot now, but
the assessment's final recommendation, **“Authority gap first,”** incorrectly
treats the durable-document boundary as the ordering gate for a pilot that
expressly excludes durable attachments. The corrected recommendation is:

> **Pilot now; authority gap in parallel.**

Only the MAJOR finding below requires amendment of the assessment. It prevents
acceptance of its recommendation, not a bounded manual pilot. No BLOCKER was
found for that pilot.

## Finding count

| Severity | Count |
| --- | ---: |
| BLOCKER | 0 |
| MAJOR | 1 |
| MINOR | 0 |
| EDITORIAL | 0 |
| OBSERVATION | 1 |

## Verification of existing operational capacity

| Capability | Result | Read-only evidence |
| --- | --- | --- |
| Client → Company → Branch → Store Reference | Confirmed | Tenant-owned Netpay Master models and the Inbox creation flow search/create this hierarchy. |
| Tenant-scoped case | Confirmed | `NetpayServiceCase` and its related aggregates use `organization_id`; route target resolution and authority envelope are tenant-scoped. |
| Manual TPV / e-commerce creation | Confirmed | The Inbox modal creates a manual case and exposes TPV/e-commerce product/type selection. |
| Checklist | Confirmed | Checklist snapshot/items and the checklist update route exist, including a safe evidence reference. |
| Responsible and one next action | Confirmed | Assignment validates an active member; the partial unique index permits at most one open `NetpayCaseNextAction` per case. |
| State, activity, and timeline | Confirmed | State transition and activity commands append ordered `NetpayCaseActivity` entries rendered as the case timeline. |
| Inbox dashboard | Confirmed | The workspace reports attention, overdue, pending, blocked, and unassigned cases and provides filtered queue views. |
| Isolation, receipts, and events | Confirmed | Organization-scoped receipt uniqueness, authority envelopes, correlation/causation, and case DomainEvents are present. |

## Golden workflow without Document Registry

**Confirmed feasible.** A bounded operational case can be completed without a
durable document attachment by using structured case data, the approved
checklist, a safe text reference/activity, responsible Principal, due date,
one next action, state transitions, the activity timeline, and closure. This is
consistent with Amendment 012: `ManageNetpayCaseChecklist` records a safe
evidence reference and explicitly does not store document bytes.

The pilot must not claim that a text reference is a governed document link, and
it must not accept or copy real document contents into Inbox.

## Document-boundary assessment

| Question | Determination |
| --- | --- |
| `NetpayCaseDocumentReference` | Exists as a persistence model and is returned in case detail. |
| Existing mutation surface | No Inbox API/UI for creating a document reference was found in the inspected routes/workspace. |
| Document Registry association | Its allowed association subjects omit `netpay_inbox_case`. |
| Operational-pilot blocker | **No**, where the pilot uses only structured fields, checklist state, and safe text references, with no durable attachment. |
| Durable-evidence blocker | **Yes.** A governed durable case-document link needs separate contract/authority confirmation and, only then, an authorized implementation path. |
| Future Gmail Intake blocker | **Conditional future blocker only.** It matters if a later, separately governed Gmail flow requires durable case-document association; it does not authorize or block the independent Gmail design/gates today. |

No authority is inferred for a document-link command, Document Registry subject
change, API/UI, migration, or implementation.

## Findings

### MAJOR M-001 — pilot ordering contradicts the verified constrained path

- **Evidence:** The assessment says safe evidence references support a
  constrained manual demo and describes a complete Master/Inbox/checklist/
  next-action/timeline/closure path, but recommends “Authority gap first” and
  frames Sprint A around confirming the evidence-link authority.
- **Impact:** It needlessly defers a no-code manual pilot that the existing
  capability and Amendment 012 safe-reference boundary already support.
- **Required correction:** Split the document gap into (a) not a blocker for
  the no-attachment manual pilot, (b) a blocker for durable governed document
  evidence, and (c) a conditional future Gmail dependency. Replace the final
  recommendation and Sprint A ordering with **“Pilot now; authority gap in
  parallel.”**
- **Affected gate:** Operational pilot planning only. It does not open the
  authority, implementation, or Gmail gates.

### OBSERVATION O-001 — pilot entry conditions must remain runtime-authorized

The proposed run correctly requires an authorized real client and a same-tenant
active responsible Principal. Those conditions must be verified by the existing
runtime authority at execution time; this review neither determines a Principal
nor grants a role. This is not a blocker to the documented pilot plan.

## Permitted immediate manual-run plan (not executed)

1. Use an already authorized operator and a real client within the authorized
   tenant; locate the client or register its Master hierarchy through the
   existing manual flow.
2. Open one TPV or e-commerce case with `manual` source and minimal structured
   operational data.
3. Apply the approved checklist and record only a safe textual activity or
   safe evidence reference—no document upload, document bytes, or durable
   document association.
4. Assign an existing same-tenant active responsible Principal; set exactly one
   next action and its due date.
5. Move the case through an allowed state; confirm the timeline and attention
   dashboard/queue reflect it.
6. Close it or leave it non-terminal with its responsible, next action, and due
   date intact.

## Pilot metrics and guards

Measure: cases captured; cases with a next action; cases with responsible and
due date; client-location time; documents pending; lost requests; rework; and
cycle time.

Guards: minimize PII; use no real documents while the durable link is absent;
do not use Gmail, WhatsApp, OAuth, or automation; do not create another
Inbox/Master/timeline; and do not alter authority, contracts, catalogue, code,
migrations, or configuration.

## Non-effects and validation

This review does not authorize a pilot, implementation, contracts, a document
association, Gmail, OAuth, provisioning, or any external action. No database,
Docker, SQL, Gmail, or OAuth operation was performed. `authentication.py` was
not modified or staged. `git diff --check` is required before handoff.
