# IG-012 — Netpay Commerce Attention P2A/P2B Authorization

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY FOR P2A/P2B**

**Ratified date:** 2026-10-21
**Roadmap authority:** [Amendment 025](IMPLEMENTATION_ROADMAP_AMENDMENT_025.md)
**Predecessor:** IG-011 P0/P1 closed

## 1. Authorized objective

Implement P2A source integrity and P2B read-only composition for:

- the evidenced monthly Store source; and
- the no-use campaign, whose unconfirmed cutoff keeps it non-effective until
  metadata completion.

The work uses synthetic fixtures only. It authorizes no productive import,
historical backfill or mutation of a real source.

## 2. Gate sequence

| Gate | Scope | Exit condition |
| --- | --- | --- |
| A — Contract/schema preflight | Reconcile reused contract metadata, schemas, migration graph and permissions. | One Alembic head; no new contract ID or permission; exact allowlist confirmed. |
| B — P2A monthly | Parse synthetic monthly Store facts, Decimal/MXN, canonical Store ID, provenance, effective selection and supersession. | P2A monthly criteria pass on isolated PostgreSQL. |
| C — P2B monthly | Add read-only Portfolio fields and commission/volume percentage behavior. | Backend, UI and browser tests pass; no Portfolio writes. |
| D — No-use isolation | Accept safe synthetic receipt/validation and quarantine missing-cutoff batches. | `metadata_pending` feeds no effective metric or temporal total; monthly gates remain independent. |
| E — No-use activation | Exercise metadata completion with a synthetic authorized cutoff. | Distinct no-use metrics, supersession, readback and isolation pass. This gate may remain pending without invalidating B/C closure. |

## 3. Contracts and permissions

Reuse only:

- `IC-NETPAY-CMD-026` UploadOperationalDataset;
- `IC-NETPAY-CMD-027` ValidateOperationalDataset;
- `IC-NETPAY-CMD-028` AcceptOperationalDataset;
- `IC-NETPAY-CMD-029` RejectOperationalDataset;
- `IC-NETPAY-CMD-030` ResolveOperationalDataRow;
- `IC-NETPAY-QRY-011` through `013` for D1 preview/batch/list;
- `IC-NETPAY-EVT-015` through `019` for existing D1 facts; and
- `IC-NETPAY-QRY-023`/`024` for Portfolio list/detail.

Use existing `netpay.inbox.manage`, `netpay.inbox.read`,
`netpay.portfolio.read` and `netpay.portfolio.reconciliation.read` according to
their current owners. No sensitive permission is required for these metrics.

## 4. Implementation allowlist

Backend implementation may modify only:

- `apps/api/src/yarvis_api/models/netpay_operational_data.py`;
- `apps/api/src/yarvis_api/schemas/netpay_operational_data.py`;
- `apps/api/src/yarvis_api/api/routes/netpay_data.py`;
- `apps/api/src/yarvis_api/schemas/netpay_commerce_attention.py`;
- `apps/api/src/yarvis_api/services/netpay_commerce_attention.py`;
- `apps/api/src/yarvis_api/api/routes/netpay_commerce_attention.py`;
- `apps/api/src/yarvis_api/services/store_profile_builder.py` only if reused for
  the read projection without transferring ownership;
- `apps/api/src/yarvis_api/canonical_contracts.py` and
  `docs/architecture/INTERACTION_CONTRACT_CATALOG.md` only to record the
  ratified extension of existing contract semantics;
- one migration after `20261014_52`, proposed as
  `apps/api/migrations/versions/20261021_53_netpay_operational_data_p2a.py`;
- focused backend tests including `test_netpay_operational_data.py`,
  `test_netpay_d1_conformance.py`, `test_netpay_commerce_attention.py`, contract
  tests and migration tests.

Frontend implementation may modify only:

- `apps/web/src/api/netpay.ts`;
- `apps/web/src/components/netpay/NetpayCommerceAttentionPortfolio.tsx`;
- its unit test; and
- `apps/web/e2e/netpay-commerce-attention.spec.ts`.

Closure may add a new dated evidence record and then update current-state
documents. Historical evidence is never rewritten.

## 5. Required behavior

- Source monetary values use Decimal and batch currency `MXN`.
- Source field `Rentabilidad` is returned as **Comisión del distribuidor (MXN)**
  with original field name and lineage.
- Other commission fields remain independently named and cannot be combined or
  substituted without a later rule.
- **Comisión efectiva sobre ventas (%)** uses source field `Volumen`, ratified
  as monthly Store sales in MXN, at the same Organization, StoreReference,
  period and compatible effective version. Missing, zero or incompatible volume
  returns no numeric result and an
  explicit reason. Negative commission remains negative. It is never labelled
  merchant margin, Store profit, billing, ROI or merchant rate.
- Portfolio totals divide the sum of compatible distributor commissions by the
  sum of compatible monthly sales. They never average Store percentages and
  report included/excluded coverage.
- Store identity uses exact same-tenant `NetpayStoreReference.store_id`; no
  synthetic business Store ID is created.
- One value becomes effective only through explicit organization/dataset/Store/
  period/metric selection. Corrections identify predecessor, actor, reason and
  idempotency key. Creation time is not precedence.
- Sources are partial unless certified; omission is unknown.
- Monthly Store-no-use and campaign months-no-use remain separate metrics.
- No-use source producer/channel are retained as provenance. Reception,
  generation and cutoff are separate; filename and receipt never infer cutoff.

## 6. Acceptance tests

P2A synthetic PostgreSQL tests must cover:

1. exact Store ID match, unmatched/ambiguous reconciliation, cross-tenant denial
   and absence of name/MID/terminal matching;
2. MXN metadata, incompatible-currency rejection and non-monetary field types;
3. Decimal boundary precision, negative commission and preservation of source
   scale;
4. `ROUND_HALF_UP` presentation and a distinct source-profile reconciliation
   control if that recommendation is ratified;
5. equal replay, conflicting replay, concurrent acceptance/supersession,
   predecessor conflict and unrelated-integrity-error propagation;
6. effective selection independent of creation order and complete provenance;
7. immutable legacy Float classification with no silent exact aggregation;
8. partial-source omission remaining unknown;
9. no-use `metadata_pending`, metadata completion and zero contribution before
   confirmed cutoff; and
10. independent monthly progress while no-use is pending.

P2B backend/frontend/browser tests must cover:

1. QRY-023/QRY-024 readback of amount, field provenance, period, MXN, quality
   and freshness;
2. commission/volume percentage success only after denominator ratification;
3. zero, missing and incompatible denominator reasons, with no substitution by
   `0%`;
4. negative commission percentage and explicit absence of merchant-margin,
   profit, billing, ROI and merchant-rate labels;
5. separation of every commission field, including proof that `Rentabilidad`
   is neither substituted by nor combined with total or component commission
   fields, and separation of both no-use metrics;
6. list/detail totals, filters and navigation using the same effective facts;
7. permission and cross-tenant negative cases, including reconciliation-count
   concealment; and
8. absence of D1, Master or Portfolio mutation from P2 queries.

Required gates include focused and full affected backend tests, canonical
contract/duplicate validation, migration round-trip, Pyright, Ruff, compileall,
Vitest, canonical TypeScript control if configured, production build,
Playwright and `git diff --check`, all on disposable synthetic infrastructure.

## 7. Closure and stop conditions

Stop without closure for a branched migration graph, contract/permission
collision, unresolved Store isolation, silent Float mixing, implicit cutoff,
commission-field conflation or failed mandatory test. Gate E may remain pending
for source metadata without blocking separately evidenced monthly Gates B/C.

Do not declare P2 closed from partial tests. Do not update canonical current
state until the applicable gates pass and closure evidence exists.
