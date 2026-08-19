# YARVIS
# Implementation Roadmap Amendment 015

## Status

**RATIFIED — CONTRACTUAL DESIGN AUTHORITY — IMPLEMENTATION REQUIRES THE SEPARATE GATE DEFINED HEREIN**

This ratification establishes contractual design authority for a bounded Netpay Commercial Intake pre-Master slice. It is not an implementation authorization and does not modify the canonical catalog, roles, permissions, code, data, migrations, or existing authorities.

## 1. Purpose and demonstrated gap

`NetpayServiceCase` requires same-tenant Netpay Master references and cannot represent an initial commercial contact, RFQ, or opportunity before a Client, Company, Branch, or Store Reference exists.

Generic Intake and Mission Inbox are not substitutes: neither owns the required Netpay commercial lifecycle, pre-Master conversion trace, or tenant-scoped operator surface. Radar remains historical and is not an owner or implementation source for this scope.

This amendment ratifies the following minimum independent aggregate design:

`CommercialIntakeItem -> [qualified, explicit conversion] -> Netpay Master + NetpayServiceCase`

The proposal is limited to **Netpay Commercial Intake — Pre-Master**. It does not change the existing known-client service-case flow.

## 2. Proposed aggregate and ownership

`CommercialIntakeItem` is a Netpay-owned, tenant-scoped aggregate that exists before and independently of Netpay Master. Its `organization_id` is resolved only from the backend authority envelope; requests, headers, tokens, visible workspace values, or provisional data may not select or override it.

| Field | Proposed semantics |
| --- | --- |
| `organization_id` | Required tenant owner, resolved by backend authority. |
| `kind` | `initial_contact`, `rfq`, `commercial_opportunity`, or `unclassified`. |
| `channel` | `call`, `email`, `whatsapp`, `referral`, or `manual`. |
| `received_at` | Required receipt time of the human-recorded commercial signal. |
| `provisional_company_name` | Optional provisional commercial data; not a Master record. |
| `provisional_contact_name` | Optional provisional commercial data; not a Person, Principal, or identity binding. |
| `product_interest` | `tpv`, `ecommerce`, or `other`. |
| `summary` | Required safe commercial summary; no document body, raw email body, token, or credential. |
| `priority` | Existing Netpay vocabulary: `urgent`, `high`, `normal`, or `low`. |
| `assignee_principal_id` | Optional same-tenant Principal reference; it grants no authority. |
| `next_action` | Optional current human next action. |
| `due_date` | Optional target date for that action. |
| `status` | `new`, `qualifying`, `qualified`, or `discarded`. |
| `created_at` / `updated_at` | Auditable creation and latest-update timestamps. |

No item requires, creates, assumes, or backfills a Client, Company, Branch, Store ID, Master record, Person, Principal, Membership, role, or identity. Provisional values are not canonical identity evidence and may not infer identity, authority, Membership, or role. `whatsapp` is only a controlled channel value; it authorizes neither API nor integration, synchronization, transmission, or external action.

## 3. Lifecycle, conversion, and frozen boundaries

The only proposed lifecycle is `new -> qualifying -> qualified | discarded`.

Only a `qualified` item may be converted. A discarded item retains safe audit evidence, is not deleted, and creates no cascade to Master, service case, identity, documents, or other aggregates.

Conversion is one local, atomic, and idempotent operation:

1. resolve a same-tenant existing Master or create the required new Master through its already-owned Master operations;
2. create one same-tenant `NetpayServiceCase` through its owner;
3. persist an immutable trace from the case and Master operation to the source `CommercialIntakeItem`; and
4. persist the conversion result and receipt in the same transaction.

The receipt is scoped by Organization, contract, idempotency key, and functional fingerprint. A matching retry returns the deterministic prior result; a conflicting replay fails closed. A failure rolls back all local conversion effects. Retrying must not duplicate a Master or service case. The source item remains a commercial record after conversion; its trace does not transfer ownership or create a second Master, Inbox, or timeline.

## 4. Ratified contractual design allocations

The following IDs were checked as absent from the current canonical catalog, repository code, and repository documentation at preparation time. This ratification approves their contractual design allocation. Catalog registration remains a required separate procedural step; this amendment itself does not modify the catalog or make an operation implementation-dispatchable.

| Proposed ID | Semantic name | Boundary |
| --- | --- | --- |
| `IC-NETPAY-CMD-020` | `CreateCommercialIntake` | Create one tenant-owned pre-Master item with idempotent receipt and sanitized creation fact. |
| `IC-NETPAY-CMD-021` | `UpdateCommercialIntakeQualification` | Update permitted qualification data and transition only `new -> qualifying -> qualified`. |
| `IC-NETPAY-CMD-022` | `AssignCommercialIntake` | Set or change a same-tenant assignee without granting authority. |
| `IC-NETPAY-CMD-023` | `SetCommercialIntakeNextAction` | Set the one current next action and optional due date; history is auditable. |
| `IC-NETPAY-CMD-024` | `DiscardCommercialIntake` | Terminally discard while retaining safe audit evidence and without deletion or cascades. |
| `IC-NETPAY-CMD-025` | `ConvertCommercialIntakeToServiceCase` | Atomically and idempotently convert one qualified item to an existing or newly created same-tenant Master and one `NetpayServiceCase`, preserving source trace. |
| `IC-NETPAY-QRY-009` | `GetCommercialIntake` | Read one tenant-scoped item and its safe timeline and trace. |
| `IC-NETPAY-QRY-010` | `ListCommercialIntake` | List/search the tenant-scoped commercial queue, pending actions, status, product interest, priority, assignee, and due-date attention. |
| `IC-NETPAY-EVT-011` | `CommercialIntakeCreated` | Sanitized creation fact: safe identifiers/codes, Organization, actor, correlation, and causation. |
| `IC-NETPAY-EVT-012` | `CommercialIntakeChanged` | Sanitized qualification, assignment, next-action, or lifecycle change; no free-form source bodies. |
| `IC-NETPAY-EVT-013` | `CommercialIntakeConverted` | Sanitized source-to-Master-and-case trace fact with safe IDs/codes and correlation. |
| `IC-NETPAY-EVT-014` | `CommercialIntakeDiscarded` | Sanitized terminal discard fact, actor, approved reason code if any, and trace. |

`IC-NETPAY-CMD-001` (`IdentifyOrRegisterMerchantCandidate`) is not reused, reinterpreted, or expanded by this amendment. It remains outside this slice. This proposal also does not alter the Gmail-design proposal range `IC-NETPAY-CMD-016..019`, `IC-NETPAY-QRY-007..008`, or `IC-NETPAY-EVT-007..010`.

## 5. Authority, audit, privacy, and isolation invariants

All future commands require backend authority resolution and revalidation before receipt lookup or replay. The authority matrix, role changes, and exact permission bindings remain subject to the separate canonical-contract/catalog procedure; this amendment assigns none now.

Every future mutation must have a canonical actor, Organization, correlation, causation, idempotency receipt, timestamp, and sanitized event. Tenant filters apply to every read, write, lookup, association, and conversion target. Unknown, foreign, missing-authority, invalid-state, duplicate, or replay-mismatch conditions fail closed.

The slice records no document bytes, attachments, copied email bodies, credential material, OAuth tokens, raw provider payloads, or external-message content. It does not make provisional contact values an identity source.

## 6. Proposed operator surface and compatibility

After a future implementation gate, `/netpay-inbox` remains the sole canonical Netpay operational surface. It may expose two separate human actions:

1. **Registrar contacto / RFQ** — the pre-Master `CommercialIntakeItem` flow.
2. **Nuevo caso Netpay** — the existing known-client `NetpayServiceCase` flow.

The known-client flow remains unchanged in behavior, with these human labels:

| Semantic key | Human label |
| --- | --- |
| `merchant_onboarding` | Alta de comercio |
| `branch_onboarding` | Alta de sucursal |
| `tpv_activation` | Activación TPV |
| `ecommerce_activation` | Activación e-commerce |
| `bank_account_change` | Cambio de cuenta bancaria |
| `document_submission` | Entrega de documentos |
| `legal_entity_change` | Cambio de razón social |
| `franchisee_change` | Cambio de franquiciatario |
| `store_deactivation` | Baja de comercio |
| `terminal_replacement` | Reposición de terminal |
| `support_incident` | Incidente de soporte |
| `unclassified` | Por clasificar |

The future pre-Master queue must be visible through the existing Netpay Inbox surface, pending-action view, search/filters, dashboard, and auditable timeline. It must not create a second Inbox, Master, Radar flow, or timeline.

## 7. Separate future implementation gate

Only after both human ratification of this amendment and canonical catalog assignment of the listed contracts may a separate implementation gate authorize one bounded vertical slice. That gate must name the exact branch, base, environment, rollback plan, and validation evidence. It may authorize:

- one focused, reversible Alembic migration only if no already-authorized persistence capability can represent the aggregate safely;
- backend and UI implementation inside `/netpay-inbox`;
- atomic, idempotent conversion to existing Netpay Master and `NetpayServiceCase`; and
- focused tests and a fully synthetic E2E demonstration.

The gate acceptance criteria are:

1. create an Initial Contact or RFQ without Master;
2. recover it after reload;
3. show it in Inbox, search, dashboard, pending work, and timeline;
4. assign a responsible Principal, next action, and target date;
5. transition it through `qualifying` and `qualified`;
6. create or link a same-tenant Master during conversion;
7. create the associated `NetpayServiceCase` and preserve source trace;
8. repeat conversion without duplicating Master or case;
9. preserve the existing known-client flow; and
10. render human Spanish labels rather than raw enum values.

## 8. Explicit exclusions and no implied authority

This amendment does not authorize implementation, code, tests, migrations, schema changes, catalog changes, role or permission changes, data creation, SQL, or runtime configuration. It does not authorize Gmail, OAuth, WhatsApp API, documents, attachments, external-message bodies, automation, identity provisioning, or external access.

No proposed ID, field, state, UI label, future gate, or reference grants authority by implication. A future conversion cannot proceed without applicable Master and Inbox ownership/authority checks plus the future Commercial Intake authority established by the catalog procedure.

## 9. Human ratification record

| Field | Value |
| --- | --- |
| Decision | RATIFY |
| Ratified by | Guillermo Mario De Hoyos Olivera |
| Ratified at | 2026-08-19 |
| Effective commit | |
