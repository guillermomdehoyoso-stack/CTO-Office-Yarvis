# YARVIS
# Implementation Roadmap Amendment 011

## Status

**PROPOSED — PENDING INDEPENDENT REVIEW AND RATIFICATION**

This proposal formalizes only the Netpay master contract and authority decisions
required before MVP-1B. It does not ratify itself and does not authorize
implementation, catalog changes, roles, routes, models, migrations, fixtures,
UI, data creation, or external integration.

## 1. Scope and demonstrated gap

[Netpay MVP-0 Branch Onboarding Design](NETPAY_MVP0_BRANCH_ONBOARDING_DESIGN.md)
and [MVP-1 Master Contract](NETPAY_MVP1_MASTER_CONTRACT.md) define the minimum
tenant-owned chain required to record a prospective branch:

`NetpayClient -> NetpayCompany -> NetpayBranch -> optional NetpayStoreReference`

The canonical contract catalog currently reserves Netpay commands
`IC-NETPAY-CMD-001..004` and queries `IC-NETPAY-QRY-001..002` only. It has no
master-data contract allocation, and the closed `ROLE_PERMISSIONS` matrix has
no `netpay.master.*` permission or Netpay master role. The proposed IDs below
were checked against the catalog and repository references: all six are free.

This amendment does not change the F-011 disposition of
`manual-close-validation` (11) or `netpay-demo` (51). Both remain retained,
unlinked, invisible to canonical authority, and immutable.

## 2. Proposed Netpay master contracts

| ID | Definitive semantic name | Owner and exact scope |
| --- | --- | --- |
| `IC-NETPAY-CMD-005` | `CreateNetpayClient` | Netpay Merchant Operations creates a tenant-owned Client. It performs the ratified duplicate evaluation and may return a deterministic replay. |
| `IC-NETPAY-CMD-006` | `CreateNetpayCompany` | Netpay Merchant Operations creates a tenant-owned Company linked to a same-tenant Client. |
| `IC-NETPAY-CMD-007` | `CreateNetpayBranch` | Netpay Merchant Operations creates a tenant-owned Branch linked to a same-tenant Company. Branch creation does not require a Store ID. |
| `IC-NETPAY-CMD-008` | `AssignCorrectOrRemoveNetpayStoreReference` | Netpay Merchant Operations assigns, corrects, or removes the optional external Store ID reference of a same-tenant Branch. |
| `IC-NETPAY-QRY-003` | `ListSearchNetpayMaster` | Tenant-scoped list/search of Client, Company, Branch, and Store Reference candidates. |
| `IC-NETPAY-QRY-004` | `RetrieveNetpayMasterDetail` | Tenant-scoped canonical detail of Client -> Company -> Branch -> current Store Reference. |

MVP-1B may expose bounded corrections to Client, Company, and Branch only
through the same aggregate's command version and authority, without reparenting
a Company or Branch. Such correction must preserve the natural-key and
tenant rules below. A separate semantic contract is required before any
reparenting, merger, Store transfer between Branches, or lifecycle beyond the
initial master scope.

## 3. Frozen master rules

- Every aggregate is tenant-owned through non-null `organization_id`, resolved
  from the authority envelope.
- A Branch may exist with no Store ID.
- A Store ID is an optional external reference, never Branch identity.
- An active Store ID may not be assigned to two Branches in the same
  Organization. Removing it ends the active reference; it does not assign it
  elsewhere.
- Client, Company, Branch, and Store values retain provenance plus
  creation/update timestamps and actor Principal references.
- Store ID does not create a Radar merchant, a Radar receipt/event, an
  Opportunity, a Workspace, or an association to `NetpayServiceCase`.
- Radar, Opportunity, Workspace Platform, and `NetpayServiceCase` are neither
  owners nor substitutes for the master.
- No historical record receives an Organization, master link, backfill, or
  retrospective Store mapping.

## 4. Proposed authority matrix

| Proposed role | Validated permissions | Allowed contracts | Deliberate non-grants |
| --- | --- | --- | --- |
| `netpay_master_viewer` | `netpay.master.read` | `IC-NETPAY-QRY-003`, `IC-NETPAY-QRY-004` | all master commands; Radar, Intake, Mission, Document, Economics, Task, Process, Governance, Workspace, cases, checklists, documents, and external actions |
| `netpay_master_operator` | `netpay.master.read`, `netpay.master.manage` | all six MVP-1 master contracts | all capabilities outside the Netpay master scope |

Viewer can list/search/retrieve and cannot create, correct, or remove. Operator
can administer only the master and can also read it. No existing role acquires
a Netpay permission incidentally.

Effective authority derives exclusively from active persisted Principal, active
Organization, active PrincipalMembership, the closed server role-to-permission
matrix, and `AuthorityResolutionService`. Tokens identify a subject only.
Headers, token claims, payloads, fixed Organization IDs, and legacy workspace
inputs must not grant permissions or select an Organization.

A transitional adapter, if later necessary, may receive only an already-resolved
`IdentityAuthorityEnvelope`; it must preserve Principal and Organization,
project only validated Netpay master permissions, and must not read
headers/tokens, synthesize/elevate permissions, or replace
`AuthorityResolutionService`.

## 5. Command, query, and tenancy invariants

- Commands require an idempotency key scoped by Organization and contract ID,
  with a request fingerprint and durable success receipt.
- Authority is resolved and revalidated before every command, receipt lookup,
  or replay response. Revoked membership and missing permission deny before
  replay may disclose or mutate.
- A mismatched replay conflicts without side effects.
- Unknown, foreign, and cross-Organization targets are concealed according to
  the canonical query/command pattern.
- Queries are side-effect free, deterministically ordered, and filter by the
  resolved Organization before returning detail or search candidates.
- Fixtures must persist Principal, Organization, active Membership, and only
  the minimal viewer/operator role. Forged headers and token claims cannot
  elevate authority or select tenancy.

## 6. Explicit exclusions

This proposal does not authorize:

- onboarding/service cases, product classification, checklist, actions,
  assignments, timeline/activity, dashboard, documents, email, WhatsApp, OCR,
  external portal, synchronization, automation, or a new UI;
- modification of the interaction catalog, `ROLE_PERMISSIONS`, existing
  Amendments, `authentication.py`, historical data, or F-011 closure records;
- migrations, models, routes, tests, fixtures, durable seed data, backfill,
  push, or merge.

## 7. Required ratification and next step

Independent review must confirm:

1. the six IDs remain free and the semantic names/ownership above do not
   overlap the existing Netpay case/checklist contracts;
2. viewer/operator separation grants no incidental cross-domain capability;
3. Store removal/correction preserves the one-active-reference rule;
4. all authority and tenancy invariants remain consistent with F-011.

If ratified unchanged, a separate MVP-1B implementation mandate may add only
the master persistence, reversible migration, narrow APIs, ratified roles,
fixtures, and focused validation described in
`NETPAY_MVP1_MASTER_CONTRACT.md`. It must not expand into case onboarding or
external integration.
