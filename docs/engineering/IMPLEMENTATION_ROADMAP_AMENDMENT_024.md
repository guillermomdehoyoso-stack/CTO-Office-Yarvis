# YARVIS
# Implementation Roadmap Amendment 024

## Netpay Commerce Attention Portfolio — reported operational portfolio

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY LIMITED TO P0/P1**

**Effective date:** 2026-10-19
**Authority:** Guillermo de Hoyos, Architecture Authority
**Authority basis:** [ADR-021](../decisions/ADR-021_RISK_PROPORTIONATE_ASSURANCE_FOR_YARVIS_MODULES.md) and [Amendment 023](IMPLEMENTATION_ROADMAP_AMENDMENT_023.md)
**Gate:** [IG-011](IG-011_NETPAY_COMMERCE_ATTENTION_PORTFOLIO_P0_P1_AUTHORIZATION.md)
**Design:** [Netpay Commerce Attention Portfolio Design](NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DESIGN.md)
**Privacy:** [Portfolio Data, Privacy and Assurance Matrix](NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DATA_PRIVACY_MATRIX.md)

## 1. Decision and boundary

This amendment authorizes implementation of P0/P1 for the read-only **Cartera
operativa reportada**. It creates no Commerce entity or materialized read model
and changes no owner. Netpay Master remains authoritative for the initial
universe. Records lacking an explicit same-tenant canonical link remain in a
separate **Registros por conciliar** surface.

The universe contains all active Netpay Master records, including incomplete
chains. One row represents the lowest available operational unit: Branch when
present, optional StoreReference attached to that Branch, or Company/Client
when no lower level exists. Every row carries `entity_scope`, `client_id`,
optional `company_id`, `branch_id` and `store_reference_id`,
`reconciliation_status`, and `availability_reasons`. The UI may group rows by
Client without changing their identity.

Labels retain their source levels: commerce is `Client.display_name`, legal
name is `Company.legal_name`, branch name is the NetpayBranch name, and Store
ID is `StoreReference.store_id`. A difference between levels is not a conflict.
Fallbacks are explicit and never copy a value into another level. Store ID is
not MID; MID remains unavailable.

## 2. Authorized P0/P1 behavior

P0/P1 authorizes tenant-scoped list and detail queries, global search,
allowlisted filters and sorting, server-side pagination, neutral source
availability and reconciliation states, and read-only navigation. Default page
size is 50 and maximum page size is 100. Values within one filter use OR;
different filters use AND.

Allowed filters are global search, `entity_scope`, reconciliation status, and
presence of Company, Branch, StoreReference or registered contact. Allowed
sorts are commerce label, legal name, branch name, Store ID, reconciliation
status and last update. Search and filters operate only on fields the caller is
authorized to receive.

Source badges may report counts for Master, available cases, linked pre-Master
records and unlinked records. They indicate availability, not health. D1 is
reported as **No incorporado en P0/P1**. P0/P1 has no attention colors; it uses
only neutral availability and reconciliation labels.

## 3. Permissions

The existing namespace uses `netpay.<resource>.<action>`. Existing
`netpay.master.read` protects Master routes but also exposes existing Master
schemas with RFC/contact fields, so it is not an exact least-disclosure grant
for this projection. Existing `netpay.inbox.read` protects Inbox, Gmail
candidate, CommercialIntakeItem and dossier reads; it grants more Inbox/Gmail
surface than the reconciliation queue needs. Neither is reused as the new
Portfolio authorization boundary.

This amendment authorizes the future implementation of these minimum scopes:

| Permission | Data enabled | Data excluded | Future routes | Initially eligible roles |
| --- | --- | --- | --- | --- |
| `netpay.portfolio.read` | Minimized Master hierarchy, masked RFC, redacted/minimized registered-contact presence, neutral availability and permitted aggregates | Full RFC, full phone/email, unlinked record detail, D1, colors, terminals, mutations | QRY-023 and minimized QRY-024 | `netpay_master_viewer`, `netpay_master_operator`, `netpay_operations_operator` after explicit role-map change |
| `netpay.portfolio.sensitive.read` | Full RFC, phone or email only inside QRY-024 fields explicitly allowed by its schema | Reconciliation queue, contact action, export, communication, unrelated Inbox/Gmail data | Sensitive block of QRY-024 only | `netpay_operations_operator` only after explicit role-map change and negative-test review |
| `netpay.portfolio.reconciliation.read` | Safe unlinked Candidate, CommercialIntakeItem and Dossier identifiers, labels, state, controlled reasons, source and freshness | Gmail content, attachment content, full contact PII, Master mutation, promotion or merge | Reconciliation block/list under QRY-023/QRY-024 | `netpay_operations_operator` only after explicit role-map change and negative-test review |

All three require backend-resolved organization isolation, fail-closed route
guards and negative tests for missing permission, forged authority,
cross-tenant IDs and aggregate-count leakage. A role receives none of these
permissions until the authorized future implementation updates the closed role
map and its tests. Master permission alone never grants sensitive or
reconciliation access. Aggregate counts exclude records outside the caller's
permissions.

RFC is masked in list responses and never appears complete in logs, reasons,
metrics or URLs. QRY-024 omits or redacts full RFC, phone and email unless
`netpay.portfolio.sensitive.read` is present; UI hiding is insufficient.

## 4. Contact and source rules

The only P0/P1 label is **Contacto registrado**. It carries source level,
available verification and freshness. It does not infer holder, owner, legal
representative or branch manager. The list minimizes contact data; full phone
or email requires the sensitive permission and detail query. There is no
contact action.

Candidate, CommercialIntakeItem and Dossier stay pre-Master unless explicitly
linked. Names, RFC, email and phone never merge identities. Exact canonical IDs
or recorded human confirmation are the only allowed composition authority.

## 5. Contracts

This amendment ratifies:

- `IC-NETPAY-QRY-023` — `ListCommerceAttentionPortfolio`;
- `IC-NETPAY-QRY-024` — `GetCommerceAttentionDetail`.

They are stable read boundaries owned by Netpay Merchant Operations and are
registered as RATIFIED/PLANNED. No Command, Event or Notification is added.

## 6. Exclusions and later phases

P2 and use of D1 inside Portfolio remain closed. P3 and every attention color
or rule remain closed. P4 expanded contacts/follow-up, P5 preferences and
advanced experience, terminals, D3, D2-Lite, export, communications, bulk
edits, overrides, automatic actions and every mutation remain closed.

No additional ADR is required while implementation preserves current owners,
trust boundaries and persistence. A new entity, materialized projection,
ownership change or broader trust boundary requires renewed architectural
assessment.
