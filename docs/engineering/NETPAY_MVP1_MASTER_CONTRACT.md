# Netpay MVP-1A — Master Contract and Authority Design

## Status and purpose

**DESIGN PROPOSAL — REQUIRES CONTRACT AND AUTHORITY RATIFICATION BEFORE MVP-1B**

MVP-1 establishes only tenant-owned Netpay master data: Client -> Company ->
Branch, with an optional Netpay Store ID. It creates no onboarding case,
checklist, action, document, external integration, dashboard, or portal
automation. It is the minimum master needed to record a real prospective branch
before Netpay has assigned a Store ID.

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

## Canonical master model

All aggregates own a UUID primary key, non-null `organization_id`,
`created_at`, `updated_at`, `created_by_principal_id`, and
`updated_by_principal_id`. `organization_id` is a tenant boundary resolved
from the authority envelope, never supplied as a trusted body/header value.
Display values retain the operator-entered text; separate normalized keys are
used only for matching and uniqueness.

| Aggregate | Minimum fields | Relationship and cardinality |
| --- | --- | --- |
| `NetpayClient` | `id`, `organization_id`, `display_name`, `normalized_name`, optional `external_reference`, optional primary contact name/email/phone, `status`. | One Client has zero or more Companies. It is the commercial relationship, not a Person or an Organization. |
| `NetpayCompany` | `id`, `organization_id`, `client_id`, `legal_name`, `normalized_legal_name`, nullable `tax_identifier`, optional legal/contact address, `status`. | One Company belongs to one Client in MVP-1; one Company has zero or more Branches. A future many-to-many commercial relationship is not implied. |
| `NetpayBranch` | `id`, `organization_id`, `company_id`, `commercial_name`, `normalized_commercial_name`, `branch_kind` (`physical` or `commercial`), address/locality/state/postal-code fields when physical, operator contact, `status`. | One Branch belongs to one Company and has zero or one current Store reference. A Branch exists independently of a Store ID. |
| `NetpayStoreReference` | `id`, `organization_id`, `branch_id`, `store_id`, `normalized_store_id`, `source_type`, `source_reference`, `assigned_at`, `confirmed_at`, `confirmed_by_principal_id`, `updated_at`. | One current reference per Branch in MVP-1. A Store ID belongs to at most one Branch within an Organization. |

`NetpayStoreReference` is preferred over an inline Branch field because Store ID
assignment is external, optional, and must retain its source and confirmation
metadata. MVP-1 does not support reassignment between Branches. An update is a
correction to the same Branch and records actor, source, and timestamp; a
cross-Branch move requires a future explicitly ratified lifecycle.

Required persistence constraints and indexes:

- foreign-key pairs include `organization_id` where a child references Client,
  Company, or Branch, preventing cross-tenant linkage;
- one active/current Store reference per Branch;
- unique `(organization_id, normalized_store_id)` for non-null Store IDs;
- indexed `(organization_id, normalized_name)` for Client search,
  `(organization_id, client_id, normalized_legal_name)` for Company search,
  and `(organization_id, company_id, branch_match_key)` for Branch lookup;
- all master retrieval filters by `organization_id` before exposing any record.

No automatic relationship is made between a Store ID and `RadarMerchant`, a
Radar request, Workspace Platform, Opportunity, or legacy Netpay service
case/import tables. Future reconciliation is a separately governed operation
with evidence and human confirmation.

## Dedupe and coexistence policy

Normalization is Unicode case folding, accent/whitespace/punctuation reduction,
and domain-specific canonicalization for email, phone, tax identifier, and
Store ID. The raw value is never overwritten by its normalized match key.

| Entity | Natural match key | Conflict | Warning | Coexistence |
| --- | --- | --- | --- | --- |
| Client | normalized display name plus the same normalized primary email or phone when provided; otherwise name-only candidate search. | Same normalized name and same supplied contact is a duplicate conflict unless the idempotent command replays. | Same name with different/absent contact is a possible duplicate. | Homonymous Clients may coexist after an operator confirms they are distinct. |
| Company | `(organization_id, normalized_tax_identifier)` when tax ID is known. Without it: `(client_id, normalized_legal_name)` candidate search. | Same non-null tax ID is a hard conflict. | Same legal name without tax ID, or same name under a different Client, is a review warning. | Legal-name homonyms without a tax ID may coexist with explicit operator confirmation. |
| Branch | physical: Company plus normalized commercial name and normalized address/locality/postal fingerprint; commercial: Company plus normalized commercial name and operator-confirmed location/contact fingerprint. | Exact Company + branch-match-key is a hard conflict. | Same Company + name but different/incomplete location is a possible duplicate. | Same-named branches at distinct verified locations coexist. |
| Store reference | `(organization_id, normalized_store_id)`. | A Store ID already held by another Branch is a hard conflict. | Existing Store ID on the same Branch is an idempotent replay or no-op confirmation. | No cross-Branch coexistence inside the same Organization. |

This policy permits one Company to own many Branches and never creates a Store
ID merely to resolve a name/address ambiguity. Search returns tenant-scoped
candidate matches with enough metadata for a human decision; it does not merge
records automatically.

## MVP-1 contract surface

The current catalog reserves `IC-NETPAY-CMD-001` for
`IdentifyOrRegisterMerchantCandidate`, but has no allocated master-data
commands or queries for independent Client, Company, Branch, and Store
operations. `IC-NETPAY-QRY-001..002` are case/checklist views, not master
views. MVP-1B requires the following proposed allocation before implementation;
this document does not edit the catalog.

| Proposed contract | Operation | Required behavior |
| --- | --- | --- |
| `IC-NETPAY-CMD-005` | CreateNetpayClient / UpdateNetpayClient | Create or edit a Client after dedupe evaluation. |
| `IC-NETPAY-CMD-006` | CreateNetpayCompany / UpdateNetpayCompany | Create/edit a Company under a same-tenant Client; enforce tax-ID conflict. |
| `IC-NETPAY-CMD-007` | CreateNetpayBranch / UpdateNetpayBranch | Create/edit a Branch under a same-tenant Company; allow absent Store ID. |
| `IC-NETPAY-CMD-008` | AssignOrUpdateNetpayStoreReference | Assign/correct a Store reference for the Branch; reject a same-tenant duplicate Store ID. |
| `IC-NETPAY-QRY-003` | SearchNetpayMaster | Tenant-scoped candidate search by Client, Company, Branch, tax ID, and Store ID. |
| `IC-NETPAY-QRY-004` | RetrieveNetpayMasterDetail | Tenant-scoped Client/Company/Branch detail with current Store reference. |

Commands require an idempotency key and use an organization + contract ID + key
unique receipt with a request fingerprint. Authority is re-resolved before a
receipt/replay is returned; revocation cannot disclose or mutate through a
previously valid key. A mismatched replay conflicts. Unknown, foreign, and
cross-organization resource IDs are concealed as `404`; authenticated callers
without required permission are denied; validation and duplicate conflicts are
explicit `4xx` outcomes. Queries are side-effect free and deterministic.

## Proposed minimum authority matrix

No `netpay.master.*` permission or persistent Netpay master role exists in the
current closed `ROLE_PERMISSIONS` matrix. This allocation is therefore a
ratification prerequisite, not implementation authority.

| Role | Permission | Allowed operations | Explicit denial |
| --- | --- | --- | --- |
| `netpay_master_viewer` | `netpay.master.read` | Search and retrieve Client, Company, Branch, and Store reference in its resolved Organization. | All creates, edits, and Store assignment. |
| `netpay_master_operator` | `netpay.master.read`, `netpay.master.manage` | Create/edit Client, Company, and Branch; assign/correct Store reference; execute only the four master commands above. | Onboarding case, checklist, action, document, Inbox, Mission Work, Radar, and external-portal actions. |

`netpay.master.manage` does not imply any future case, service, checklist,
document, task, or external-execution permission. Existing Radar, Mission,
Document, Intake, Economics, Task, and Process roles receive no Netpay master
permission incidentally. Fixtures must persist Principal, Organization, active
PrincipalMembership, and the exact role; local/test tokens identify a subject
only.

## Boundaries and discarded overlaps

| Existing area | Decision |
| --- | --- |
| Radar | Reuse receipt, append-only activity, priority, and tenancy test patterns only. `RadarMerchant` has optional legacy `workspace_id` and is a request-tracking aggregate, not Client/Company/Branch master data. |
| Opportunity and Workspace Platform | Not reused. Opportunity expresses a confirmed business intent; Opportunity Workspace is its bounded execution context, neither a physical Branch nor a Store. |
| Organization and Person | Not reused as business entities. Organization is the tenant; Person is generic contact data and does not establish Netpay Client or Company ownership. |
| Legacy `NetpayServiceCase` / shipment / device assignment | Not reused or migrated. They capture legacy imported service/email/shipment evidence and are not a tenant-scoped onboarding master. |
| Document Registry | Reuse tenant/provenance approach later only. Its current subject enum lacks an onboarding/master subject, so MVP-1 stores no attachments/documents. |
| Mission Work, Mission Inbox, Intake | No master ownership. They may consume future public events/projections only after a later mandate. |

## Explicit MVP-1 exclusions

- onboarding/service case, product classification, checklist, actions,
  assignment, activity/timeline, dashboard, documents, email, WhatsApp, OCR,
  external portal, synchronization, and automation;
- UI beyond API/contracts and persistence required by MVP-1B;
- historical edits, links, backfill, or durable seed data;
- `workspace_id`, a replacement workspace header, and header/token-based
  authority or Organization selection.

## Exact MVP-1B implementation plan

MVP-1B may start only after the contract allocation and authority matrix are
independently ratified, followed by a separate implementation mandate.

| Area | Predictable files / work |
| --- | --- |
| Domain/persistence | New `apps/api/src/yarvis_api/models/netpay_master.py` (or focused extension of `models/netpay.py`) and tenant-safe repositories/services; no Radar model alteration. |
| API | New Netpay master schemas and route module, router registration, resolved-envelope dependency, and narrow master command/query adapters only. |
| Authority | Ratified roles/permissions added only to `application/authority.py`; no changes to `authentication.py`. |
| Migration | One linear, reversible migration after `20260813_37` creating master tables, tenant-paired foreign keys, unique constraints, search indexes, and command-idempotency storage. Downgrade drops only new empty MVP-1 objects; rollback after real writes requires an approved data-preservation procedure, not silent deletion. |
| Tests/fixtures | `test_netpay_master.py`, authority/replay/cross-organization tests, and migration round-trip test. Fixtures create isolated Principal, Organization, active Membership, and only viewer/operator roles; no durable seed/historical mutation. |

Focused evidence must cover: Branch without Store ID; Store-ID uniqueness per
Organization; many Branches per Company; dedupe conflict/warning/coexistence;
idempotent create/update; replay after revocation denial; cross-organization
concealment; forged header/token denial; migration upgrade/downgrade/re-upgrade;
and unchanged 11/51 historical rows. The proportional regression target is the
new master suite plus authority-resolution, migration, Radar-boundary, and
affected API-conformance tests; an integral suite remains a release-gate choice.

## Decision and recommendation

**Ratification required:** allocate the six Netpay master contracts above and
ratify exactly `netpay.master.read` / `netpay.master.manage` with
`netpay_master_viewer` / `netpay_master_operator`. No Amendment is created
by this design phase because it does not itself change the catalog or role
matrix.

After that narrow ratification, execute MVP-1B as one bounded vertical:
persist Client -> Company -> Branch first, make Store reference optional, and
add Store assignment only after the Branch exists. Do not start cases, products,
checklists, documents, or UI expansion in the same mandate.
