# IG-011 — Netpay Commerce Attention Portfolio P0/P1 Authorization

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY OPEN FOR P0/P1 ONLY**

**Effective date:** 2026-10-19
**Requires:** ratified [Amendment 024](IMPLEMENTATION_ROADMAP_AMENDMENT_024.md)
**Design:** [Netpay Commerce Attention Portfolio Design](NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DESIGN.md)
**Privacy:** [Portfolio Data, Privacy and Assurance Matrix](NETPAY_COMMERCE_ATTENTION_PORTFOLIO_DATA_PRIVACY_MATRIX.md)

## Authorized gate

IG-011 authorizes implementation and isolated validation of P0/P1 for
**Cartera operativa reportada**: tenant-scoped, read-only list/detail;
deterministic search, allowlisted filters and sorting; pagination 50 by default
and 100 maximum; neutral source availability; reconciliation states; and a
separately authorized reconciliation queue. Implementation has not started.

QRY-023 and QRY-024 are ratified and registered. No write contract or runtime
effect is authorized by their registration.

## Permission boundary

The implementation shall add and enforce the following scopes using the
existing `netpay.<resource>.<action>` convention:

- `netpay.portfolio.read`: minimized portfolio and masked RFC;
- `netpay.portfolio.sensitive.read`: full RFC/phone/email in authorized detail
  fields only;
- `netpay.portfolio.reconciliation.read`: safe unlinked pre-Master queue data.

Existing `netpay.master.read` and `netpay.inbox.read` are not substitutes: each
protects a broader and differently shaped surface. The future role-map change
must be explicit. General Portfolio read is initially eligible for the Master
viewer/operator and operations operator roles; sensitive and reconciliation
read are initially eligible only for the operations operator role. Eligibility
is not a grant until implementation changes and tests the role map.

Each route must fail closed and resolve Organization at the backend. Mandatory
negative tests cover missing permission, wrong permission, forged headers,
cross-tenant record IDs, sensitive-field redaction/omission and aggregate-count
leakage. No permission enables communication, export, mutation, promotion or
merge.

## Contract schemas

QRY-023 accepts a structured request with `global_search`, allowlisted filters,
allowlisted sort, direction, page/cursor and page size. It returns minimized
rows, neutral source badges, total permitted catalog count, permitted filtered
count, pagination metadata and evaluation timestamps. Rows contain the lowest
available entity scope and canonical IDs, level-specific labels, masked RFC,
reconciliation state, availability reasons, minimized registered-contact
status, source quality and freshness. Counts never include records outside the
caller's permissions.

QRY-024 accepts one same-tenant canonical row identity and returns the same
identity plus source-specific detail blocks. Full RFC, phone or email is
omitted or redacted unless `netpay.portfolio.sensitive.read` is present. Safe
unlinked reconciliation blocks require
`netpay.portfolio.reconciliation.read`. It returns no Gmail body, attachment
content, D1 metrics, colors, terminals, contact action or mutation affordance.

## Authorized implementation allowlist

Only these future paths may change under IG-011:

```text
apps/api/src/yarvis_api/api/routes/netpay_commerce_attention.py
apps/api/src/yarvis_api/application/authority.py
apps/api/src/yarvis_api/application/netpay_portfolio_authority.py
apps/api/src/yarvis_api/bootstrap.py
apps/api/src/yarvis_api/schemas/netpay_commerce_attention.py
apps/api/src/yarvis_api/services/netpay_commerce_attention.py
apps/api/tests/test_authority_resolution.py
apps/api/tests/test_netpay_commerce_attention.py
apps/api/tests/test_productive_auth.py
apps/api/tests/test_local_netpay_authority.py
apps/web/src/App.tsx
apps/web/src/api/netpay.ts
apps/web/src/components/netpay/NetpayCommerceAttentionPortfolio.tsx
apps/web/src/components/netpay/NetpayCommerceAttentionPortfolio.test.tsx
apps/web/src/style.css
apps/web/e2e/netpay-commerce-attention.spec.ts
docs/engineering/evidence/netpay-commerce-attention-p0-p1-<date>.txt
```

The implementation shall replace `<date>` with the actual evidence date.
Models, migrations, dependencies, configuration, Gmail routes, existing
historical evidence and canonical contract registration are outside this
future implementation boundary.

## Evidence gate

- exact universe and lowest-unit row selection, including incomplete chains;
- list/detail schemas and QRY-023/QRY-024 conformance;
- permission, least-disclosure and cross-tenant negative tests;
- masked RFC and omitted/redacted sensitive detail without sensitive scope;
- independently protected reconciliation queue and leakage-safe counts;
- deterministic OR-within/AND-between filters, sort and pagination limits;
- explicit unavailable MID/terminal/D1 states and contact role non-inference;
- frontend functional/accessibility coverage and list-detail-return browser
  restoration;
- proof of zero source writes, receipts, events, contacts or side effects;
- configured static, build, documentation and `git diff --check` gates;
- final diff restricted to this allowlist.

## Exclusions

P2–P5, D1 use, attention colors, expanded contacts/follow-up, terminal
inventory, server preferences, export, communications, automatic actions,
bulk edits, overrides, D3, D2-Lite, Gmail/OAuth, pilot access, real data and
production publication remain closed.
