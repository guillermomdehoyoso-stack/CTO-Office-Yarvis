# Implementation Roadmap Amendment 016

## Netpay Operational Data, Store 360 and Terminal Logistics

## Status

**RATIFIED — CONTRACTUAL DESIGN AUTHORITY — IMPLEMENTATION REQUIRES SEPARATE D1, D2 AND D3 GATES**

This amendment ratifies contractual design only. It does not register a
contract, authorize code, migration, upload, storage, data import, carrier
access, or a runtime change. It does not modify Amendment 015. Ratification is
not implementation authorization.

## 1. Purpose and scope

This proposal defines a tenant-scoped Netpay Control Tower centered on the
active, normalized `NetpayStoreReference` Store ID. It is delivered only in
three progressively authorized gates:

1. **D1 — Operational Data Intake** for versioned, human-reviewed operational
   datasets;
2. **D2 — Store Operational 360 partial** for a read-only composition; and
3. **D3 — Terminal Logistics** for a future canonical logistics source.

The Store 360 view is a projection, never a new source of truth. Master owns
commercial identity; the existing authorized contact source owns contacts;
`CommercialIntakeItem` owns pre-Master activity; tenant-owned
`NetpayServiceCase` owns operational cases, next actions, and timeline; D1
owns imported/versioned operational facts; and D3, if implemented, owns
terminal logistics. Every displayed block retains its source aggregate or
entity, source batch where applicable, and `updated_at`.

No information is inferred. Missing information is rendered as **No
disponible**. All reads, matches, and projections are tenant-scoped and
backend-authorized. Legacy `NetpayShipment`, `NetpayDeviceAssignment`, and
legacy `NetpayServiceCase` remain historical evidence only and are never a
canonical source, migration input, or 360 projection source.

## 2. D1 — Operational Data Intake

### 2.1 Initial datasets

| Dataset type | Minimum controlled facts |
| --- | --- |
| `monthly_store_profitability` | Exact Store ID and reporting period; Client ID; product/UEN; volume and transactions; income, cost, commissions, and profitability; no-use indicator. |
| `no_usage_campaign` | Exact Store ID and campaign period; merchant status; months without use; alert; no-use reason; billing commitment; rent choice; cancellation; controlled outcome/follow-up. |

Preparation evidence established only the following structural facts, without
reproducing real values: Store ID joins the two report shapes; the authorized
No Uso example rows each had a corresponding profitability Store ID; Client ID
may be matched explicitly to `NetpayClient.external_reference`; and names are
not reliable keys.

### 2.2 Proposed aggregates

| Aggregate | Proposed responsibility |
| --- | --- |
| `OperationalDataBatch` | Tenant owner, dataset type, reporting period, sanitized filename, source hash, lifecycle status, controlled row counts, uploader, and timestamps. |
| `OperationalDataRow` | Batch-owned source row number, controlled staging fields, validation and match states, and allowlisted error codes. |
| `StoreProfitabilityFact` | Tenant-owned immutable fact for one accepted batch, Store Reference, optional Client ID, reporting period, and normalized metrics. |
| `NoUsageCampaignEntry` | Tenant-owned immutable fact for one accepted batch, Store Reference, campaign period, months without use, merchant status, alert, and controlled outcome/follow-up. |

The proposed batch lifecycle is `uploaded -> validating -> needs_review ->
accepted | rejected`. Acceptance is explicit. Historical facts are appended by
accepted batch and never overwritten.

### 2.3 D1 invariants

- Preview/dry-run precedes acceptance.
- Idempotency is scoped to Organization, dataset type, and source hash;
  conflicting replay fails closed.
- Automatic matching is restricted to an exact active Store ID in the same
  tenant. Missing or ambiguous rows remain for human review.
- D1 creates no case, RFQ, next action, task, or opportunity automatically.
- `/data-intake` and its legacy `DocumentRecord` pipeline are not a D1 owner
  or authority. Existing parser, checksum, preview, storage, and receipt
  patterns may be reused only after an implementation gate.
- The original file is immutable when retained through the authorized storage
  boundary; row staging and accepted facts retain batch provenance.

### 2.4 No Uso privacy boundary

RFC is an ephemeral tenant-filter parameter only. It is not authentication and
must not be persisted, logged, emitted, previewed, or displayed. Filtering
occurs before preview and persistence; inability to prove that filter is
fail-closed. The future D1 design must select either restricted temporary
quarantine of the complete original or verified discard after controlled
extraction. It must never expose another distributor's rows.

Financial previews, events, and health records use closed allowlists and omit
names, amounts, RFC, complete identifiers, and raw payloads.

## 3. D2 — Store Operational 360 partial

`GetStoreOperational360View` is the sole proposed Store projection query;
`GetStoreOperationalView` is intentionally not proposed or reserved.

| View block | Composed canonical source and rules |
| --- | --- |
| Commercial identity | Netpay Client, Company/legal name, authorized commercial holder if present in Master, Branch, Store ID, product/UEN, status, provenance, and update date. “Holder” never means bank-account holder. |
| Contactability | Only authorized contacts from their canonical source, with name/function, telephone, email, or preferred channel where that source and authority permit. Never infer from free text; never display banking data. |
| Commercial activity | Related `CommercialIntakeItem` records: kind, qualification state, assignee, next action, and due date. |
| Operational cases | Related tenant-owned `NetpayServiceCase` records: open/in-progress/closed counts, type, state, priority, responsible Principal, next action, due date, and links to the existing detail/timeline. The projection does not duplicate either aggregate or authority. |
| Operational data | Most recent accepted period, volume, transactions, profitability, permitted financial components, months without use, alert, and controlled follow-up. Period comparison requires at least two accepted batches. |
| Attention | Boolean plus only: no use, negative profitability, overdue case, blocked case, no assignee, no next action, unlinked data, and logistics exception only when D3 exists. It also supplies current responsible Principal and nearest action/due date. |

The future UI is a **Datos Netpay** tab with batches, profitability, no-use
stores, one Store 360 view, attention list, and unlinked rows. It remains a
read model; no source aggregate is copied merely for UI convenience. A Store
may have multiple contacts, opportunities, cases, and logistics movements.
Open/in-progress cases and overdue actions take visual priority.

## 4. D3 — Terminal Logistics

### 4.1 Proposed aggregate

`TerminalLogisticsMovement` is a future, tenant-owned canonical aggregate. It
contains Organization, Store Reference, optional tenant-owned Service Case,
operation reference, movement type, carrier, protected tracking reference,
terminal count, protected optional terminal reference, normalized status,
controlled carrier status, operational reason, optional responsible Principal,
next action, due date, created/shipped/estimated/completed timestamps,
controlled exception code, provenance, and audit timestamps.

Its proposed movement types are `shipment`, `collection`, `replacement`, and
`return`. For a replacement operation, the physical legs are always separate
`shipment` and `collection` movements sharing `operation_reference`;
`replacement` is an operation classification or explicit source mapping and
must not stand in for a single completed physical leg. Its proposed initial lifecycle is `pending`, `guide_created`,
`in_transit`, `delivered`, `collection_requested`, `collected`, `exception`,
and `cancelled`; the permitted transitions are subject to ratification of this
amendment and later implementation conformance.

### 4.2 D3 invariants

- A movement binds explicitly to the same-tenant Store Reference and, when
  relevant, a same-tenant `NetpayServiceCase`.
- One case may have multiple movements. A replacement comprises separate
  shipment and collection movements joined by `operation_reference`.
- Delivery of the new terminal does not complete a replacement while its prior
  terminal collection remains pending.
- D3 never closes a case automatically and does not query a carrier API.
- Carrier status is mapped explicitly to a controlled value; no delivery or
  collection is inferred from free text.
- Tracking and serial are controlled references. Address, telephone, and
  recipient are excluded from dashboard, events, logs, metrics, and health;
  any direct access requires a separate authority.
- Events and health contain only allowlisted statuses, dates, error/exception
  codes, and redacted references.

The D2 logistics summary, once D3 exists, shows pending shipments, deliveries,
pending collections, exceptions, most recent movement, and nearest logistics
action. It contributes attention only for overdue/no-movement records,
exceptions, delivered-replacement-with-pending-collection, missing assignee, or
missing next action.

## 5. Proposed contractual allocations

The following IDs were searched in the current canonical catalog, repository
code, and repository documentation and were absent. They are consecutive and
are ratified as contractual design allocations **pending catalog assignment**;
this amendment does not register them or make them dispatchable.

| Proposed ID | Semantic operation |
| --- | --- |
| `IC-NETPAY-CMD-026` | `UploadOperationalDataset` |
| `IC-NETPAY-CMD-027` | `ValidateOperationalDataset` |
| `IC-NETPAY-CMD-028` | `AcceptOperationalDataset` |
| `IC-NETPAY-CMD-029` | `RejectOperationalDataset` |
| `IC-NETPAY-CMD-030` | `ResolveOperationalRowMatch` |
| `IC-NETPAY-CMD-031` | `CreateTerminalLogisticsMovement` |
| `IC-NETPAY-CMD-032` | `UpdateTerminalLogisticsMovement` |
| `IC-NETPAY-CMD-033` | `LinkTerminalLogisticsMovementToCase` |
| `IC-NETPAY-CMD-034` | `CancelTerminalLogisticsMovement` |
| `IC-NETPAY-QRY-011` | `PreviewOperationalDataset` |
| `IC-NETPAY-QRY-012` | `GetOperationalDatasetBatch` |
| `IC-NETPAY-QRY-013` | `ListOperationalDatasetBatches` |
| `IC-NETPAY-QRY-014` | `GetStoreOperational360View` |
| `IC-NETPAY-QRY-015` | `ListStoresRequiringAttention` |
| `IC-NETPAY-QRY-016` | `GetStoreTerminalLogistics` |
| `IC-NETPAY-QRY-017` | `ListTerminalLogisticsRequiringAttention` |
| `IC-NETPAY-EVT-015` | `OperationalDatasetUploaded` |
| `IC-NETPAY-EVT-016` | `OperationalDatasetValidated` |
| `IC-NETPAY-EVT-017` | `OperationalDatasetAccepted` |
| `IC-NETPAY-EVT-018` | `OperationalDatasetRejected` |
| `IC-NETPAY-EVT-019` | `OperationalRowMatchResolved` |
| `IC-NETPAY-EVT-020` | `TerminalLogisticsMovementCreated` |
| `IC-NETPAY-EVT-021` | `TerminalLogisticsMovementChanged` |
| `IC-NETPAY-EVT-022` | `TerminalLogisticsExceptionDetected` |
| `IC-NETPAY-EVT-023` | `TerminalLogisticsMovementCompleted` |

Existing legacy contracts are not reused or reinterpreted. The future catalog
step must reconfirm availability immediately before registration.

## 6. Mandatory implementation sequence and gates

Ratification alone grants no implementation authority. The required order is:

1. human ratification of Amendment 016;
2. separate canonical catalog assignment;
3. separate D1 implementation gate and synthetic E2E;
4. separate D2 implementation gate and synthetic E2E; and
5. separate D3 implementation gate and synthetic E2E.

D1 does not depend on D3. D2 may operate without D3 and display logistics as
**No disponible**. D3 completes only the logistics component of Store 360.

Each future gate must state its branch/base, authority, rollback plan,
migration scope, environment, and acceptance evidence. It may authorize only
its named stage.

## 7. Future acceptance criteria

| Gate | Required evidence |
| --- | --- |
| D1 | Synthetic fixtures for both dataset shapes; filter No Uso before preview/persistence; preview and explicit acceptance; exact Store ID matching; replay idempotency; reload; zero cross-tenant rows; zero historical overwrite. |
| D2 | Synthetic Store ID composition with Master, authorized contact, RFQ, cases, and accepted operational facts; open/in-progress counts; responsible/action/due date; absent values rendered as “No disponible”; reload, tenant isolation, and no duplicated source data. |
| D3 | Synthetic shipment tied to Store/case; collection paired to replacement; delivered terminal with pending collection; exception produces attention; tracking, address, and PII absent from events/logs. |
| All | Reversible migrations; focused backend and frontend tests; web build; browser E2E; synthetic data only. |

## 8. Explicit exclusions and no implied authority

This proposal authorizes no code, migration, catalog change, SQL, data,
fixture, real file, storage write, carrier API, Gmail, OAuth, WhatsApp API, or
automation. It does not copy or move real XLSX/CSV files into Git, fixtures,
events, or documentation. It neither touches nor stages `authentication.py`.

No contract name, proposed lifecycle, status, projection, field, or acceptance
criterion grants authority by implication.

## 9. Human ratification record

| Field | Value |
| --- | --- |
| Decision | RATIFY |
| Ratified by | Guillermo Mario De Hoyos Olivera |
| Ratified at | 2026-08-19 |
| Ratified pending catalog assignment | `IC-NETPAY-CMD-026..034`; `IC-NETPAY-QRY-011..017`; `IC-NETPAY-EVT-015..023` |
| Effective commit | |
