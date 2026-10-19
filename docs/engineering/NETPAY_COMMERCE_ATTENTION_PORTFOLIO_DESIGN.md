# Netpay Commerce Attention Portfolio — Lean Design

## Status

**RATIFIED — P0/P1 DESIGN BASELINE**

**Effective date:** 2026-10-19
**Roadmap authority:** [Amendment 024](IMPLEMENTATION_ROADMAP_AMENDMENT_024.md)
**P0/P1 gate:** [IG-011](IG-011_NETPAY_COMMERCE_ATTENTION_PORTFOLIO_P0_P1_AUTHORIZATION.md)
**Data/privacy matrix:** [Portfolio Data, Privacy and Assurance Matrix](NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DATA_PRIVACY_MATRIX.md)

## 1. Product and architecture boundary

**Cartera operativa reportada** is a read-only, non-authoritative projection
over existing owners. It creates no Commerce aggregate, table or migration and
performs no repair, promotion or source mutation. Every adapter resolves the
Organization at the backend.

```text
HTTP QRY-023/QRY-024 route
          |
Portfolio query service
  | Netpay Master adapter (authoritative universe)
  | Inbox availability adapter
  | Pre-Master reconciliation adapter
          |
Minimized response with source, quality and freshness
```

D1 is not an adapter in P0/P1. Its status is **No incorporado en P0/P1**.

## 2. Universe and identity

All active Master records participate, including incomplete chains. One row is
the lowest operational unit available:

1. Branch, with optional active StoreReference;
2. Company when it has no Branch;
3. Client when it has no Company.

Every row exposes `entity_scope`, `client_id`, optional `company_id`,
`branch_id`, `store_reference_id`, `reconciliation_status`, and
`availability_reasons`. Detail uses canonical IDs, never a name, RFC, phone or
email. UI grouping by Client does not alter row identity.

Commerce label is `Client.display_name`; legal name is `Company.legal_name`;
branch name comes from NetpayBranch; Store ID is
`NetpayStoreReference.store_id`. Missing levels remain absent and fallback is
labelled explicitly. Differences between levels are not conflicts. Store ID is
not MID; MID is `No disponible`.

Only same-tenant canonical IDs or recorded human confirmation may compose a
pre-Master source into a Master row. Names, RFC, email and phone are review
signals only. `probable_match`, `conflict` and `unreconciled` records stay in
the independently protected queue.

## 3. Permissions and disclosure

P0/P1 introduces three future permissions under the existing namespace:

- `netpay.portfolio.read` for minimized rows, masked RFC, permitted neutral
  badges and minimized registered-contact presence;
- `netpay.portfolio.sensitive.read` for full RFC/phone/email in detail only;
- `netpay.portfolio.reconciliation.read` for safe unlinked pre-Master records.

`netpay.master.read` and `netpay.inbox.read` are not reused because their
current routes grant broader and differently shaped data. Authorization is
enforced by the API schema and query, not only by UI visibility. Without the
sensitive scope, fields are omitted or schema-redacted. Without reconciliation
scope, queue rows and their counts are absent. Every count is permission
filtered before aggregation.

RFC is always masked in list output and never complete in logs, reasons,
metrics or URLs. Contact fields are labelled **Contacto registrado**, with
source level, verification state when available and freshness. They imply no
legal or ownership role and provide no contact action.

## 4. QRY-023 list schema

The structured request contains:

- optional global search;
- multi-value filters for `entity_scope` and reconciliation status;
- boolean presence filters for Company, Branch, StoreReference and contact;
- one allowlisted sort and `asc`/`desc` direction;
- page/cursor and page size, default 50 and maximum 100.

Values within one filter use OR; different filters use AND. Allowlisted sorts
are commerce label, legal name, branch name, Store ID, reconciliation status
and last update. Search covers only authorized display values.

The response contains minimized rows; total permitted catalog and filtered
counts; pagination metadata; neutral counts for Master, available cases,
linked pre-Master and authorized unlinked records; source timestamps; quality
and freshness. Badges report availability, not health. No color count exists.

## 5. QRY-024 detail schema

The request identifies one row by its canonical scope and UUIDs. The response
repeats row identity and level-specific labels, then exposes permitted blocks
for Master identity, masked legal data, registered contact, neutral source
availability, reconciliation, quality and freshness. Full RFC, phone or email
requires `netpay.portfolio.sensitive.read`. Safe unlinked queue data requires
`netpay.portfolio.reconciliation.read`.

Missing data is `without_data`; contradictory source observations remain
`conflict` and never overwrite one another. The response contains no Gmail
body, attachment content, D1 metric, attention color, terminal inventory,
communication action, export or mutation control.

## 6. Experience and navigation

P0/P1 provides list/detail, global search, visible removable filters,
deterministic sorting, pagination, total/filtered counts and navigation that
restores filters, sort, page and scroll position. Accessibility covers table
semantics, keyboard navigation, visible focus and text labels. No status relies
only on color.

Column reordering/resizing, persisted preferences, export, advanced filter
construction and every color interaction remain later P5/P3 scope.

## 7. Contracts and acceptance criteria

The only contracts are `IC-NETPAY-QRY-023`
`ListCommerceAttentionPortfolio` and `IC-NETPAY-QRY-024`
`GetCommerceAttentionDetail`. Filters and navigation remain behavior within
those boundaries.

P0/P1 evidence must demonstrate:

1. exact same-tenant universe and incomplete-chain row policy;
2. no writes, receipts, events or source changes;
3. fail-closed separation of general, sensitive and reconciliation scopes;
4. masking/redaction and no unauthorized count leakage;
5. deterministic filters, sorting, pagination and stable navigation;
6. explicit missing/conflict/freshness/source behavior;
7. Store ID never labelled MID and explicit D1/terminal unavailability;
8. contact role non-inference and absence of communication actions;
9. representative backend, frontend, accessibility and browser tests.

## 8. Implementation allowlist

The exact future allowlist is maintained by IG-011. It includes the new route,
schema, service and authority projection; the existing closed role map and its
tests; frontend list/detail and browser coverage; bootstrap wiring; and a new
dated evidence record. It excludes models, migrations, dependencies,
configuration, Gmail routes and historical evidence.

## 9. Closed later scope

P2/D1 composition, P3 colors and rules, P4 expanded contacts/follow-up, P5
advanced experience/preferences, terminals, D3, D2-Lite, export,
communications, overrides and every mutation require later authority.
