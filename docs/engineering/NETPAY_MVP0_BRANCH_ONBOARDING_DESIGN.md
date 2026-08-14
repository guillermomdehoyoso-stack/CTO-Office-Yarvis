# Netpay MVP-0 — Branch Onboarding Design

## Purpose and boundary

This design defines a human-assisted MVP for receiving and operating real
requests to open Netpay branches. It does not automate the Netpay portal,
create a Gmail or WhatsApp integration, or authorize implementation by itself.

Netpay Merchant Operations owns the business meaning of candidate, onboarding
case, channel, checklist, and case state (ADT-DOMAIN-001 and
`IC-NETPAY-CMD-001..004` / `IC-NETPAY-QRY-001..002`). `Organization` remains
the Yarvis tenant and authority boundary; it is not a customer, company,
branch, or Store. Authority remains Principal + active PrincipalMembership +
Organization + persisted permissions resolved by `AuthorityResolutionService`.
Request headers and tokens never grant permissions or choose an Organization,
and `workspace_id` is not part of this design.

The F-011 historical Radar sets (`manual-close-validation`, 11; `netpay-demo`,
51) remain excluded and immutable. They are neither a migration source nor
seed data for onboarding.

## Domain model and ownership

| Entity | Meaning and minimum identity | Boundary |
| --- | --- | --- |
| Client / Cliente | Commercial customer relationship; display name and stable internal identifier. A client can relate to one or more companies. | New Netpay domain state. |
| Company / Razón social | Legal operating entity: legal name, tax identifier when available, and legal/contact data. | New Netpay domain state; never equated automatically to an Organization. |
| Branch / Sucursal | Physical or commercial point to be enabled: commercial name, address/location, operational contact, and lifecycle. | New Netpay domain state, owned by one Company. |
| Store / Store ID Netpay | Netpay-assigned external identifier and its recorded confirmation. It is optional until Netpay confirms it. | New Netpay domain state, attached to a Branch with provenance and effective date. |
| Service / Product | Requested service: `tpv`, `ecommerce`, or `mixed`; a case carries one requested product classification. | Netpay case value, not a generic platform catalog. |
| Onboarding Case / Caso de alta | Tenant-owned aggregate linking Client, Company, Branch, product, state, target date, responsible person reference, checklist, and activity. | New canonical Netpay aggregate. |
| Checklist | Versioned, case-owned requirement snapshot and explicit fulfillment/waiver/rejection state. | New Netpay policy/state; requirements remain explainable. |
| Action | Human-owned next step with due date, priority, assignee, and completion/cancellation evidence. | Initially case-owned; a later mandate may create Mission Work through its public owner contract. |
| Activity / Bitácora | Append-only fact of capture, validation, decision, assignment, status change, external submission, or activation confirmation. | New Netpay case history with actor Principal and correlation/causation. |

**Branch is not Store.** A Branch is a real prospective place or commercial
channel and may be captured, checked, blocked, or cancelled before it has a
Netpay Store ID. A Store ID is an external identifier received only after a
human records Netpay confirmation. It must not be invented from the Branch
name, address, or a header.

The existing `NetpayServiceCase` and its email/shipment records concern legacy
service-case import. They do not provide the tenant-owned onboarding aggregate
or F-011 authority boundary required here, are not the MVP-1 model, and their
existing data is not to be migrated by this MVP. Generic Case and Checklist
models may inform implementation patterns, but do not take over Netpay
onboarding semantics.

## Human-assisted operating flow

`request -> capture -> human validation -> checklist -> follow-up -> external
submission -> activation -> closure`

1. An operator captures the requester, Client, Company, Branch, requested
   product, contact, and source reference.
2. A human validates or corrects identity and branch facts; uncertainty remains
   visible rather than being silently normalized.
3. Opening the Onboarding Case snapshots the selected checklist version and
   records its first activity.
4. The operator works checklist items, next actions, owner, target date, and
   append-only decisions. Missing information produces an explicit action.
5. A person submits through the external Netpay portal outside Yarvis and
   records the external reference, time, and responsible Principal in Yarvis.
6. A person records Netpay's activation confirmation and Store ID, if issued;
   no portal response is assumed or synthesized.
7. The case closes only after human confirmation of activation or an explicit
   cancellation reason.

### Proposed case lifecycle

| State | Allowed next states | Meaning |
| --- | --- | --- |
| `captured` | `validating`, `cancelled` | Request recorded; business facts not yet accepted. |
| `validating` | `information_pending`, `checklist_in_progress`, `blocked`, `cancelled` | Human validates Client, Company, Branch, and product. |
| `information_pending` | `validating`, `checklist_in_progress`, `blocked`, `cancelled` | Required information is explicitly absent. |
| `checklist_in_progress` | `ready_for_submission`, `information_pending`, `blocked`, `cancelled` | Required items are being collected and reviewed. |
| `ready_for_submission` | `submitted_externally`, `information_pending`, `blocked`, `cancelled` | Human gate is satisfied; no external submission has occurred yet. |
| `submitted_externally` | `activation_pending`, `information_pending`, `blocked`, `cancelled` | Person recorded a portal submission/reference. |
| `activation_pending` | `activated`, `information_pending`, `blocked`, `cancelled` | Netpay confirmation is awaited. |
| `activated` | `closed`, `blocked` | Activation and any Store ID confirmation are recorded. |
| `blocked` | prior working state, `information_pending`, `cancelled` | A reason and next owner/date are mandatory. |
| `cancelled` / `closed` | terminal; reopen requires a future contract | Terminal outcome with reason and actor. |

`blocked` and `information_pending` are not synonyms: the former records an
external or operational impediment; the latter identifies missing case data or
evidence. Neither grants an exception to checklist or external confirmation.

## Data required to open a real case

Required at capture/opening:

- tenant Organization selected by resolved membership;
- Client display name and one requester/contact method;
- Company legal name (tax identifier may be explicitly unknown at capture);
- Branch commercial name or unambiguous provisional label and physical or
  commercial location sufficient for operator follow-up;
- requested product (`tpv`, `ecommerce`, or `mixed`);
- source type/reference, capture timestamp, responsible Principal, and initial
  owner or an explicit unassigned state;
- target date or an explicit reason that it is not yet committed.

Optional or subsequently confirmed: tax identifier, legal representative,
settlement account details, technical/integration contact, terminal quantity,
web domain, Store ID, Netpay folio, external submission timestamp, and
activation timestamp. Sensitive financial or identity documents must be held
through an authorized Document Registry path, not in free-text activity.

## Provisional checklist policy

These are operator checklists, not a claim about Netpay's current official
requirements. Items marked **[confirm with business/Netpay]** must be ratified
before MVP implementation or pilot use.

| Product | Initial checklist |
| --- | --- |
| TPV | Company legal/tax data **[confirm]**; branch address and operating contact; legal representative/authorization **[confirm]**; settlement/bank data through approved secure handling **[confirm]**; terminal quantity/connectivity/installation details **[confirm]**; external submission reference; Netpay activation and Store ID confirmation. |
| E-commerce | Company legal/tax data **[confirm]**; operating and technical contact; domain/website control evidence **[confirm]**; integration platform and callback/contact data **[confirm]**; required legal/privacy/refund evidence **[confirm]**; external submission reference; Netpay activation and Store ID/account confirmation **[confirm]**. |
| Mixed | Union of TPV and e-commerce requirements with shared Company record and separately verified branch/terminal and online-integration facts. Any Netpay rule that permits a shared or requires distinct Store IDs is **[confirm]**. |

## Reuse versus new domain work

| Component | Reuse now | Boundary / not reused |
| --- | --- | --- |
| F-011 authority | Resolved envelope, tenant concealment, revocation-before-replay, persisted roles, and command-idempotency patterns. | New Netpay permissions/roles require a separate authority decision; no header adapter may manufacture them. |
| Radar | Tenant-scoped command receipt, append-only activity, target-date/priority dashboard, close/reopen, and cross-organization test patterns. | `RadarMerchant`, `RadarRequest`, `workspace_id`, and Radar contracts are not onboarding aggregate or master data. |
| Mission Work | An eventual assigned action can be represented through Mission Work's public owner contract. | It is not case status, checklist, or source of truth; MVP-1/2 do not depend on its projection. |
| Mission Inbox | Future projection of a captured or attention-worthy case. | It remains rebuildable and cannot own or mutate the case. |
| Document Registry | Versioning, tenant-safe retrieval, provenance, and association patterns for approved files. | Current association subjects do not include an Onboarding Case; direct attachment requires a later bounded contract/model decision. |
| Intake | Manual normalized text/source reference and human confirmation patterns. | No Gmail, WhatsApp, OCR, polling, automatic classifier, or portal adapter in MVP-0–4. |

## MVP contracts, API, and screens

Existing canonical Netpay IDs are the semantic starting surface; route paths
and schemas remain uncommitted until an implementation mandate.

| Cut | Contract/API minimum | Screen minimum |
| --- | --- | --- |
| MVP-1 | `IC-NETPAY-CMD-001` for identify/register candidate; tenant-safe reads for Client, Company, Branch, and Store. | Client/Company/Branch capture, Branch detail, Store-ID confirmation panel. |
| MVP-2 | `IC-NETPAY-CMD-002` open case, `CMD-003` classify product, `CMD-004` evaluate checklist; `QRY-001/002` case and checklist views. | New-case form, case detail, TPV/e-commerce/mixed checklist. |
| MVP-3 | Owner-directed case action, assignment, transition, activity append, and attention query; Netpay events preserve correlation/causation. | My-work/case dashboard; due, blocked, information-pending, and unassigned filters. |
| MVP-4 | Manual capture command for pasted email/text and attachment metadata, then human-confirmed case link. | Assisted intake panel with source text, attachment register, unknown fields, and explicit confirm/link action. |

MVP-4 accepts operator-provided copies of email text and attachment metadata
only. The operator records source provenance and confirms the target case before
any case mutation. Attachments use an approved storage/document path only; no
live mailbox, WhatsApp, external portal, or background worker is introduced.

## Delivery plan and operational acceptance

| Cut | Outcome | Acceptance signal |
| --- | --- | --- |
| MVP-1 | Client -> Company -> Branch -> optional Store master chain. | An operator registers a prospective Branch without a Store ID and retrieves it only inside the resolved Organization. |
| MVP-2 | Product-classified onboarding case and checklist. | A human opens TPV, e-commerce, or mixed case, sees missing/confirmed items, and cannot claim external activation. |
| MVP-3 | Actions, owner, append-only timeline, and attention dashboard. | Operators see due, blocked, information-pending, and unassigned cases with target dates and accountable actor history. |
| MVP-4 | Assisted manual email/attachment intake. | A copied request is retained with provenance and linked only after human confirmation; no external inbox is contacted. |
| MVP-5 | Controlled pilot with real requests. | Named operators complete an auditable sample while business confirms checklist policy and external evidence. |

### Product decisions still required

1. Official, versioned Netpay checklist for TPV, e-commerce, and mixed, and
   which items are mandatory by Company versus Branch.
2. Client/Company matching and duplicate-resolution policy, including whether
   one case can cover multiple Branches.
3. Store-ID cardinality/lifecycle: whether mixed service shares an ID and
   whether reassignment is allowed.
4. Which Principal roles may create, validate, submit externally, confirm
   activation, cancel, and view cases. These are new Netpay authority mappings,
   not permissions inherited from Radar or Mission Work.
5. Retention/classification rules for submitted documents and sensitive bank or
   identity data.

### Recommendation

Start **MVP-1 only**: introduce the tenant-owned Client -> Company -> Branch
master chain with an optional, provenance-bearing Store ID. Do not reuse Radar
records and do not wait for email automation. This is the smallest cut that lets
an operator record a real new-branch request immediately while preserving the
fact that a Branch can exist before Netpay assigns its Store ID.

Any MVP-1 implementation requires a separate mandate to define its Netpay
authority mapping, contracts, migrations, and acceptance tests.
