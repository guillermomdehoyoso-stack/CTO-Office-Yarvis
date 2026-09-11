# Netpay D2-Lite — Store Portfolio Proposal

Status: **PROPOSED — DRAFT — NO CONTRACT REGISTRATION OR IMPLEMENTATION AUTHORITY**

Draft date: 2026-09-11. Proposed business owner and architectural steward: Netpay Merchant Operations / Architecture Authority.

## 1. Authority, baseline and purpose

Guillermo de Hoyos, acting as Architecture Authority and Business Owner of the Netpay operation, authorized only preparation of this proposal following read-only discovery. Current work package: documentary D2-Lite design. Current gate: proposal preparation only. Next allowed action after delivery: independent review. Repository state must be verified before any later change. This document neither ratifies architecture nor opens an implementation gate.

| Verified baseline | Value |
| --- | --- |
| Local and remote HEAD | `b67fbdc8f87bba84f12c35d0b8a930953e51154f` |
| Branch | `feat/operational-intake-spine` |
| Accepted Boba Tree proposal SHA-256 | `909AE1CDC564FC1703CE61EB3B9F2260C12ADBDCAE394FA303AB93C3F46CE59B` |
| Pre-draft index and worktree | Empty index; only `?? AUDIT_REPORT.md`, not opened |
| Mixue | Discovery left no files or modifications; implementation remains unauthorized |
| Output path | Absent before this proposal was created |

PROJECT_CONTEXT, CURRENT_STATE and CURRENT_SPRINT were read in order for the discovery. Historical summaries are subordinate to applicable ratified documents and explicit authority. Governing sources are [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md), [Amendment 016](IMPLEMENTATION_ROADMAP_AMENDMENT_016.md), [D1 authorization](NETPAY_OPERATIONAL_DATA_D1_IMPLEMENTATION_AUTHORIZATION.md), [Master contract](NETPAY_MVP1_MASTER_CONTRACT.md), [Inbox contract](NETPAY_MVP2_INBOX_CASE_CONTRACT.md), and [ADR-017](../decisions/ADR-017_RATIFY_DISPATCH_HANDLER_FACTORY_COMPOSITION.md). None is modified.

The visible outcome proposed is one read-only Portafolio panel inside `/netpay-data`, showing the most recent available monthly profitability period and the latest accepted upload for that period. Its universe is always `selected_report_only`. It is not the complete Netpay portfolio, Merchant 360, an external lifecycle source or a source of new canonical facts.

## 2. Business confirmations and their limits

The following confirmations were expressly supplied by Guillermo de Hoyos as Architecture Authority and Business Owner for preparation of D2-Lite:

1. Every accepted monthly profitability report is a complete snapshot of the Store IDs included in the reported portfolio for its period, not an incremental change delivery.
2. `volume` represents processed sales denominated in Mexican pesos, `MXN`, for that period.
3. Absence from a later snapshot does not itself establish formal termination, closure or zero volume outside the reported universe.
4. No Uso, external lifecycle, complete Merchant 360, Core/Salesforce, Boba Tree, Mixue, assets and serials remain excluded.
5. Exceptions: None. Downstream authority: None.

These are business semantics for this proposed read profile, not an acceptance or ratification of this document. Currency is explicitly sourced from this confirmation, not a nonexistent database currency column. No historical row, Fact, receipt, fingerprint or period is changed or backfilled. No actual report or confidential business value is reproduced here. Any future fixtures must be synthetic.

## 3. Physical evidence and architectural reconciliation

Paths prefixed S are relative to `apps/api/src/yarvis_api/`; W to `apps/web/src/`.

| Existing evidence | Observed behavior | Design consequence |
| --- | --- | --- |
| S/models/netpay_operational_data.py | Batch, Row, ProfitabilityFact, NoUsageCampaignEntry and receipt models | Reuse D1 ownership and provenance; no new fact table |
| S/api/routes/netpay_data.py:accept_dataset | Accepted rows marked unchanged produce no new Fact | Facts filtered only by selected batch are not a full snapshot |
| Same: upload_dataset, _latest_fingerprint | Controlled payload/fingerprint; prior fact lookup by Store Reference and period | Preserve row membership and prove equivalent prior facts |
| Same: resolve_match | Human matching may select another active reference of the same tenant | UUID match alone does not prove reported Store identity |
| Same: dataset_results | Returns only Facts created by that batch | Existing results route cannot supply the complete portfolio unchanged |
| OperationalDataBatch | created_at/updated_at, no accepted_at or supersedes_batch_id | Define upload ordering explicitly; do not invent acceptance time |
| StoreProfitabilityFact | Float volume, nullable transactions, no currency; no_use_indicator exists | Apply confirmed MXN read semantics and numeric validity controls |
| accept_dataset | no_use_indicator is always None | Do not expose it as available No Uso evidence |
| S/models/netpay_master.py | Tenant-owned Reference/Branch/Company/Client chain | Validate every join and expose only minimal safe labels |
| S/api/routes/netpay_master.py:assign_or_correct_store_reference | Mutates Store ID on the same reference UUID | Preserve reported ID; current-ID mismatch suppresses Master attribution |
| S/bootstrap.py | Includes netpay_data, netpay_master and netpay_inbox routers | Existing router can host a separately authorized read adapter |
| S/canonical_contracts.py | D1 and Inbox metadata RATIFIED/PLANNED; Master RATIFIED/VERIFIED | HTTP existence is not operational promotion |
| W/components/netpay/NetpayDataWorkspace.tsx | Import, profitability, no-use and history tabs | Add an isolated read-only panel; do not alter D1 mutation semantics |

Amendment 016 §3 permits read-only composition of canonical Master and accepted D1 facts. D2-Lite is proposed as the first bounded D2 increment, not fulfillment of the complete D2 evidence criteria in §7. Contacts, RFQ, cases, attention and logistics remain outside this increment. A later AR-001 instrument must expressly approve this incremental gate and its reduced scope before implementation; this proposal does not amend Amendment 016 by itself.

QRY-014 `GetStoreOperational360View` and QRY-015 `ListStoresRequiringAttention` remain separate. The portfolio lists all Stores included in a selected report, including Stores that require no attention. Recasting QRY-015 as that list or QRY-014 as a portfolio would silently expand semantics. A separate Query is therefore proposed in §9.

### 3.1 D1 evidence prerequisite

D1 authorization and implementation commit `6bb2c412232f84b0df516dd5da60af354a3f3d85` exist. The repository contains `apps/api/tests/test_netpay_operational_data.py`, `W/components/netpay/NetpayDataWorkspace.test.tsx` and migration `20260819_41_netpay_operational_data_d1.py` (parent `20260819_40`). Discovery inspected them without executing tests. No dedicated terminal D1 conformance act was located in the permitted repository documentation. Terminal conformance is **NOT VERIFIED**, not presumed absent everywhere and not inferred from a commit or test source.

Before D2-Lite implementation, Architecture Authority must identify and expressly accept a dated D1 evidence record tied to an exact commit/environment: both synthetic dataset shapes; preview and explicit acceptance; reload; same-key replay; tenant/authority rejection; No Uso filtering before persistence; no source binary retention; historical Fact preservation; migration lineage validation; and backend/UI synthetic results. The record must distinguish existing results from tests newly required to substantiate them. Unknown outcomes must remain unknown until demonstrated.

Independent review must also disposition D1 dependencies revealed here: omitted unchanged Facts, mixed periods, source/reference mismatch, acceptance/rejection concurrency and mutable Store references. Read-side containment must be demonstrated; any necessary writer repair is a separate authorized package, not an allowance hidden in this boundary. A D1 evidence acceptance does not promote metadata or authorize real data/production.

## 4. Deterministic report selection and read snapshot

Default selection uses the backend-resolved Organization, `dataset_type=monthly_store_profitability`, and `status=accepted`. There is no separate imported state; Importado is a UI label for accepted.

Every candidate accepted report must have a valid `YYYY-MM` period, at least one row and homogeneous row periods equal to the batch period. It must contain only valid/matched rows, structurally valid Store IDs and unique D1 natural Store/period keys. Recheck these conditions; status alone does not prove all invariants. Multiple rows normalized by D1 to the same Store/period are not summed, even if UEN differs. Reference collisions within a batch are also inconsistent. Mixed-period or structurally invalid accepted reports cause a controlled unsupported/inconsistent-source result; do not silently fall back to older data and label it latest.

After those checks, select `ORDER BY reporting_period DESC, created_at DESC, id DESC`. `created_at` is the persisted upload-registration timestamp, not acceptance time or commit order. UUID descending is a stable tie-breaker, not chronology. Label the selection policy `latest_period_latest_accepted_upload`.

An explicitly supplied `batch_id` must be same-tenant, accepted, profitability and structurally supported. It pins an already selected snapshot across pagination and refreshes. The API may retrieve an older pinned accepted snapshot but must return `is_latest=false` when applicable; the first UI offers no historical selection or comparison. Pending, rejected, unknown and foreign explicit IDs are all concealed as `404 report_not_available` after caller authorization. Default selection with no accepted report returns a typed empty result.

| Condition | Required result |
| --- | --- |
| Older period uploaded later | Does not replace a newer reporting period |
| Two accepted uploads for one period | Latest persisted upload timestamp, then UUID, wins |
| Older upload accepted later | Does not beat a newer accepted upload of that period |
| Corrected snapshot | Select its full membership if it wins the order; never union old and new reports |
| Store omitted in new snapshot | Omitted from this universe; no inferred zero, closure or termination |
| Newer pending/rejected upload | Excluded from default selection |
| Acceptance acknowledgment lost | Read durable accepted state; no assumed success from client outcome |
| Acceptance transaction still in flight | Current read sees its database snapshot; later refresh may select new data |

One request uses one stable database snapshot for selection, row reconstruction, joins, summary, filtered count and page. Prefer one SQL statement/CTE composition under READ COMMITTED; if several SELECTs are required, use one explicitly read-only REPEATABLE READ transaction established before its first query. Do not run separate unconstrained reads for summary and page. No write, flush, business commit, event or receipt is generated by the projection itself. Existing authentication/session-security behavior is not redefined by this statement.

Across requests, pinned batch membership is stable, but Master is current and may change. No cross-request frozen Master snapshot is promised. Each response exposes `evaluated_at` and current Master timestamps; normal refresh may legitimately change links/counts. Strict multi-request snapshot pagination would require a separate design and is not claimed here.

## 5. Reconstructing complete membership and effective metrics

Begin with **all OperationalDataRows of the selected batch**. Do not start with Facts or all active Master Stores. The accepted rows establish selected report membership; typed accepted Facts establish metrics. A staging row alone is not substituted for missing metric evidence.

For each row, require a valid period, reference UUID, row fingerprint and controlled payload. Recompute the D1 canonical fingerprint using the existing deterministic JSON serialization semantics and compare it to the stored fingerprint. Its payload is interpreted internally only; do not return raw JSON, financial components outside this profile or source names.

1. Collect every same-batch ProfitabilityFact for the row's reference and period, with matching Organization and accepted source batch. If there are conflicts in this same-batch set, return unavailable metrics; do not fall back to older evidence.
2. A same-batch Fact must have the same row fingerprint and materially equal fields. It is preferred when valid, regardless of the row's projected_action.
3. Only when no same-batch Fact exists and projected_action is exactly `unchanged`, collect prior accepted Facts with identical Store Reference UUID, reporting period and fingerprint. Require a different source batch, same tenant/type, a strictly earlier `(source_batch.created_at, source_batch.id)` order than the selected batch, and Fact.created_at no later than selected_batch.created_at. These conservative timestamps bound eligibility, not proof of physical commit time.
4. For each prior candidate, validate its accepted source-row evidence using that Fact's source batch, reference, period and fingerprint. The association must be unambiguous. Require material equality among all eligible Facts and with the selected row. An absent, ambiguous or contradictory source association makes reconstruction unavailable; do not hide it using LIMIT 1.
5. When multiple eligible candidates are materially identical and their provenance is valid, they are interchangeable evidence of the same values. Choose the smallest `(fact.created_at, fact.id)` solely for deterministic provenance after equality checks. This is not latest-value inference.
6. If no candidate qualifies, retain the Store row with null metrics and a controlled reason. Never omit it from coverage, create a new Fact, copy staging amounts as accepted facts or invent zero.

Material equality covers all fields represented in the accepted profitability Fact: client_external_reference, period, product_uen, volume, transactions, income, cost, commissions and profitability, preserving null distinctions. D1 controlled-payload equality additionally covers the other allowlisted source slots through fingerprint and source-row checks. Compare canonical normalized values exactly; do not introduce fuzzy amount or identifier equivalence. Invalid/non-finite numeric material invalidates that candidate. no_use_indicator is not consumed. A contradictory accepted Fact is not repaired by this read.

Every reconstructed row retains selected `batch_id`, `source_row_id`, `fact_id` and `fact_batch_id`, with `reused_fact` indicating prior evidence. An accepted batch consisting entirely of unchanged rows must still yield its full Store membership. A Fact from another period or a different reference is never carried forward. The timestamp filter can conservatively reject evidence in unusual concurrent upload histories; the result is explicit unavailable data, not false reconstruction.

## 6. Master relationship and attribution

The only permitted chain is effective Fact → NetpayStoreReference → NetpayBranch → NetpayCompany → NetpayClient, using UUID FKs and Organization equality at every hop. The Row tenant is derived from its selected Batch. Fact/Batch/Reference FKs are not all composite tenant constraints, so explicit tenant predicates remain mandatory. Client external reference is not a replacement join or unique identity proof.

Always display `reported_store_id` from the selected source row. Never substitute the current Reference.store_id. For this minimal profile, require exact equality of the stored source Store ID and current Reference.store_id after no additional normalization; values were already processed by D1 at intake. Non-identical representations fail conservatively as mismatch; neither punctuation removal nor approximate RFC/name matching is introduced. D1's own broader normalization is still used to detect source-key collisions, not to grant canonical attribution.

| master_link.status | Meaning and display |
| --- | --- |
| verified_current | Effective Fact, exact reported/current Store ID and complete tenant-safe chain; reference active; allow safe current Master identity |
| missing | No effective Fact/reference can prove a link; preserve reported row, omit names/navigation |
| inactive_reference | Exact identity and complete chain exist, but reference is inactive; explicit historical-reference marker, no active navigation |
| mismatch | Current reference Store ID differs from original report; omit Master names/IDs/navigation from output |
| inconsistent | Broken chain, ambiguous source relation or inconsistent tenant provenance; omit Master details and return safe reason |

Classification precedence: broken/foreign chain is inconsistent; exact-ID mismatch is mismatch; a valid chain with inactive reference is inactive_reference; otherwise verified_current. Internal foreign IDs are never returned. A missing metric because of numeric invalidity need not erase a separately proven structural link; an unresolvable effective Fact cannot establish one. For inactive_reference, same-tenant canonical IDs may be returned but no names or link are asserted as current.

Master labels, when permitted, are current canonical labels, not historical labels at the sales period. Reference.active is association status, never proof that the external contract is active. No lifecycle is inferred. Manual matching to a different same-tenant reference is a mismatch even if D1 accepted it. The read neither changes the Fact nor repairs the Reference. Names, RFCs and free text are never join keys.

## 7. Metrics, coverage, labels and freshness

Currency is always `MXN` for this profile, with `currency_basis=business_owner_confirmation`. No currency column is added. Use decimal arithmetic derived deterministically from the persisted finite numeric values for aggregation/output; do not round each row before summing. Existing Float storage limits exact historical precision, and the read does not recover lost precision. Decimal strings preserve output precision; UI formatting is not ledger reconciliation.

| Reported activity | Exact rule / UI label |
| --- | --- |
| with_reported_sales | Known finite volume > 0: Con venta reportada |
| without_reported_sales | Known finite volume = 0: Sin venta reportada |
| volume_unavailable | Null or missing metric evidence: Sin información de volumen |
| review_required | Negative finite volume, invalid numeric data or contradictory metric evidence: Revisión requerida |

All rows carry `external_lifecycle=unconfirmed`, rendered Lifecycle externo no confirmado. Do not label contractual lifecycle Activo, Inactivo or Cerrado. Transactions alone do not manufacture volume or override a missing-volume label. Negative transaction counts or non-integral source transaction values are invalid, not zero. No Uso composition is excluded; `no_use_indicator` is always null and rendered No disponible regardless of stored data.

`volume_total` sums known finite values once per selected report Store, including negative finite values with a review flag. It is a subtotal if any row is unavailable/invalid. If no values are known, return null, not zero. A known zero-only set returns zero. Apply the same known-value/coverage distinction to transaction_total; exclude invalid transaction counts and preserve a review count. Completeness and review are independent: a complete set may still contain negative volume requiring review.

Coverage denominators always refer to distinct source Stores of selected_report_only. Report total Stores, metric-covered/uncovered Stores, verified current links and each other link status. Accepted D1 rows were required to be matched; this does not imply today's verified Master coverage is 100%. Do not divide by all Master Stores or return global counts. An empty universe has null percentage, not invented 100%.

Freshness includes loaded_at = selected Batch.created_at, evaluated_at from the server, nonnegative elapsed seconds since load and month lag relative to reporting_period. No accepted_at column exists: acceptance_time is null and acceptance_time_basis is unavailable. updated_at, receipt.created_at, DomainEvent.occurred_at and recorded_at are not relabeled as commit time. No stale threshold is invented; objective ages are displayed and stale_status remains unknown. A future period or load timestamp after evaluation yields freshness status invalid_time and null affected ages, not clamped reassuring values. All timestamps are offset-aware UTC; period remains a monthly business label.

## 8. Closed response shapes and candidate API

All shapes below are closed: reject unknown request fields and return only listed fields. UUIDs are strings; timestamps ISO-8601 UTC; amounts decimal strings or null; counts nonnegative integers unless expressly nullable. No generic dict/raw payload escapes.

| Shape | Fields and types |
| --- | --- |
| StorePortfolioSummary | status: available/partial/empty; batch_id: UUID?; selection_policy: latest_period_latest_accepted_upload; is_latest: bool?; period: YYYY-MM?; universe: selected_report_only; currency: MXN; currency_basis: business_owner_confirmation; reported_store_count, with_reported_sales_count, zero_reported_volume_count, unknown_volume_count, review_required_count: int; volume_total: decimal?; volume_total_kind: total/subtotal/unavailable; transaction_total: int?; transaction_total_kind: total/subtotal/unavailable; totals_require_review: bool; freshness: DataFreshness; coverage: CoverageSummary; items: StorePortfolioRow[]; total_filtered, offset, limit: int |
| StorePortfolioRow | source_row_id: UUID; reported_store_id: string; sales_period: StoreSalesPeriod; master_link: StoreMasterLink; reported_activity: with_reported_sales/without_reported_sales/volume_unavailable/review_required; metric_status: available/partial/unavailable/invalid; reason: none/fact_missing/fact_conflict/provenance_unproven/invalid_numeric; fact_id, fact_batch_id: UUID?; reused_fact: bool; external_lifecycle: unconfirmed |
| StoreSalesPeriod | reporting_period: YYYY-MM; product_uen: string?; volume: decimal?; transaction_count: int?; currency: MXN; no_use_indicator: null |
| StoreMasterLink | status: verified_current/missing/inactive_reference/mismatch/inconsistent; branch_id, company_id, client_id: UUID?; branch_label, company_label, client_label: string?; reference_updated_at, branch_updated_at, company_updated_at, client_updated_at: timestamp?; navigation_url: null |
| DataFreshness | loaded_at, acceptance_time: timestamp?; acceptance_time_basis: unavailable; evaluated_at: timestamp; age_since_load_seconds, months_since_reporting_period: int?; status: available/unavailable/invalid_time; stale_status: unknown |
| CoverageSummary | report_store_count, facts_resolved, facts_unresolved, verified_current_links, missing_links, inactive_reference_links, mismatch_links, inconsistent_links, volume_known, volume_unknown, transactions_known, transactions_unknown: int; master_link_ratio, volume_ratio, transaction_ratio: decimal?; universe: selected_report_only |

Header cards and coverage describe the complete selected report and are explicitly labeled as such. Filters affect items and total_filtered only. This prevents a search from silently changing the report's financial total. Counts of reported-activity categories partition the source Stores. For empty status: no batch/period, zero counts, null amounts/ratios/times except evaluated_at, empty items. Partial status applies to incomplete metrics, unverified Master links or review-required values.

Proposed transport: `GET /netpay/data/store-portfolio`. No POST/PUT/PATCH/DELETE variant, mutation button, export or server-side repair.

| Request field | Constraint |
| --- | --- |
| batch_id | Optional UUID; pinning rules in §4; never an Organization selector |
| search | Optional trimmed string, max 100 characters; literal substring over reported Store ID and permitted verified-current commercial labels; escape wildcard characters; no RFC/contact search |
| link_status | Optional one of the five closed link statuses |
| reported_activity | Optional one of the four closed activity values |
| sort | store_id_asc (default), store_id_desc, volume_asc, volume_desc, freshness_asc, freshness_desc |
| offset | Integer 0..5000 |
| limit | Integer 1..100, default 50 |

Source rows are capped at 5000, matching D1's current intake limit. Exceeding the cap or incompatible source structure returns unsupported_report rather than truncating source membership. Numeric sorts place nulls last in both directions. Every sort ends with bytewise reported_store_id ascending and source_row_id ascending, except primary Store ID descending where only the UUID tie-breaker is appended. Freshness is shared within one batch; ties are expected. UI retains returned batch_id when paging/filtering and offers an explicit refresh to latest; it does not silently mix pages across reports.

Error precedence: authenticate; require both scopes; validate request; resolve tenant-safe report; validate structure; reconstruct/compose. Errors: 401 unauthenticated; 403 insufficient authority; 422 invalid_request; 404 report_not_available for explicit unknown/foreign/noneligible IDs; 409 unsupported_report or inconsistent_report for invalid period/duplicates/structural integrity; 503 source_unavailable for database/repository failure. Default no-report is 200 empty. Per-row missing/contradictory metric evidence is 200 partial, never a fabricated complete total. Errors expose no SQL, identifiers of foreign resources, source filenames or sensitive payloads.

## 9. Query identity, authority and runtime admission

Proposed semantic Query: `ListStorePortfolio`, owner Netpay Merchant Operations. Candidate ID: **IC-NETPAY-QRY-018 — unassigned, unreserved, unregistered**. At the baseline, searches of repository docs and application/test sources found QRY-001..017 references/design allocations, including compact ranges; QRY-018 and ListStorePortfolio were absent. QRY-014/015 retain Amendment 016's distinct purposes. Repeat full collision and allocation review immediately before any registration. This proposal's use of a candidate ID creates no allocation authority.

The Query returns a complete-report summary and a bounded filtered page from one snapshot, with no source mutation. Proposed version is 1.0.0, pending owner/contract review. No idempotency key or command receipt is required for a side-effect-free Query. batch_id pins source selection; it is not an idempotency token.

Authority is explicitly `netpay.inbox.read AND netpay.master.read`, both validated in a freshly resolved backend authority envelope. Organization derives exclusively from that envelope. A request tenant ID, body field, navigation state or capability shown by the browser cannot select a tenant or grant access. No roles, Memberships or role maps are changed. The future admission profile must prevent client-supplied Organization selection; deterministic tests use server-resolved tenant contexts. Canonical labels require the same authority and a proven chain.

Only minimal reviewed business labels may be exposed. Legal/personal names are not assumed non-PII merely because they are stored in Master. No contact names, RFC, address, email, phone, filename or source payload is returned; if a Master label cannot be approved as a safe commercial display value, return null. Search uses only labels eligible for display. No name is used as an identity join. No new sanitization algorithm or real-data policy is authorized here; field-level exposure approval is an implementation prerequisite. Navigation is null in the first increment because no new Branch/Company page is proposed.

D1's HTTP routes use authority_envelope plus direct route services and are composed by bootstrap; they do not obtain admission from the Command Dispatcher. Their canonical definitions remain RATIFIED/PLANNED. The Dispatcher accepts only Commands, non-RETIRED lifecycle and operational status IMPLEMENTED/VERIFIED/PRODUCTION; it rejects PLANNED before creating a UoW. It is not a Query Dispatcher and must not be changed to run this read.

Resolution proposed: a separate authority act must approve the new Query's contract, read-adapter admission/composition and operational metadata lifecycle. Registration may initially be PLANNED; that alone enables no endpoint. Any later operational promotion and release is explicit. Existing D1/Inbox metadata remains unchanged by this increment. Their HTTP/metadata discrepancy is documented as a bounded legacy baseline, not used as permission to repeat implicit promotion. No filter change, monkey-patch, environment switch or test-local status is proposed for this Query. Do not call committing D1/Master wrappers from the read service or introduce nested dispatch/UoWs.

## 10. UI increment

Add Portafolio within `/netpay-data`, using the existing navigation and an independent read-only component. On entry, load the default selected report. Show period, upload date, objective age and selected_report_only scope above the table. Cards show reported Store count, count with reported sales, MXN total/subtotal and metric/Master coverage. When negative values participate, show Revisión requerida next to the subtotal/total.

The table contains reported Store ID, Master relationship status, permitted Branch/Company/Client labels, reported UEN/product, processed sales MXN, transaction count and objective age. Search, closed filters, sort and pagination follow §8. Labels distinguish no information from zero. No Uso is No disponible; external lifecycle is always unconfirmed. Do not invent links or expose unproven labels.

Loading shows a read pending state; errors offer safe retry; empty means no accepted report; partial shows coverage and row-level safe reasons. During report refresh, do not mix old cards with a new page. Keep existing D1 import/history behavior outside the panel; Portafolio calls only its GET endpoint. No comparison history, export, upload, matching, acceptance, rejection or mutation appears inside it.

## 11. Candidate File Boundary — not authorization

Only this proposal is writable during its preparation. The following exact paths are candidates for later separately authorized work; they are not an Authorized File Boundary yet.

| Existing path | Bounded future purpose |
| --- | --- |
| apps/api/src/yarvis_api/api/routes/netpay_data.py | Add read adapter only; no modification of D1 mutation semantics |
| apps/api/src/yarvis_api/canonical_contracts.py | New Query registration/status only under separate contract act |
| docs/architecture/INTERACTION_CONTRACT_CATALOG.md | Explicit new Query catalog entry after allocation |
| apps/web/src/api/netpay.ts | Typed read client and response types |
| apps/web/src/components/netpay/NetpayDataWorkspace.tsx | Isolated panel integration |
| apps/web/src/components/netpay/NetpayDataWorkspace.test.tsx | Existing-page integration regression |

| New proposed path, absent at baseline | Bounded future purpose |
| --- | --- |
| apps/api/src/yarvis_api/services/netpay_store_portfolio.py | Read selection/reconstruction/composition |
| apps/api/src/yarvis_api/schemas/netpay_store_portfolio.py | Closed request/response shapes |
| apps/api/tests/test_netpay_store_portfolio.py | Synthetic Query, security, snapshot and provenance evidence |
| apps/web/src/components/netpay/NetpayStorePortfolio.tsx | Read-only panel |
| apps/web/src/components/netpay/NetpayStorePortfolio.test.tsx | UI and GET-only client evidence |

No migration, model, bootstrap, configuration, role-map or writer change is proposed. The existing router is already composed. Query/schema imports can be bounded to the listed adapter/service files. A necessary extra path, fixture, E2E artifact, index or authority change requires a revised exact boundary and approval, not inferred scope. Governance prerequisite artifacts must be named separately by the later act; this table authorizes none.

## 12. Candidate Evidence Gate

No new test was run or gate passed while preparing this document. Use synthetic data and isolated PostgreSQL for persistence/snapshot claims; no production data or source documents.

| Area | Required future evidence |
| --- | --- |
| Selection | Latest period/latest accepted upload; UUID tie; older period uploaded later; older upload accepted later; pending/rejected excluded; explicit pinned batch; no accepted reports |
| Structure | Homogeneous month; malformed/null/mixed periods; duplicate Store/period; reference collisions; row cap; no silent fallback or truncation |
| Snapshot membership | Corrected complete snapshot excludes absent Stores; no union of historical snapshots; no inferred zero/closure |
| Unchanged | Entirely unchanged and mixed batches retain all rows; same-batch precedence; eligible prior Fact/source-row proof; contradictory candidates rejected before provenance selection |
| Missing facts | Missing/late/ineligible Fact produces partial unavailable metrics; no staging-value fallback; selected batch and fact batch preserved |
| Master | Store ID correction; exact-ID mismatch; manual mismatching; inactive reference; broken chain; foreign reference at each hop; no reattribution or unsafe label/navigation |
| Numeric | Null/zero/negative/non-finite; invalid transactions; MXN confirmation basis; subtotal/total/coverage; no intermediate rounding; Float precision disclosed |
| Read consistency | Concurrent acceptance and Master change cannot split one response's cards/count/page; pinned cross-request limitations explicit |
| API | Both scopes, revoked/foreign authority, no client tenant selection, allowlisted fields/sorts, escaped search, filters, null ordering, stable pagination and max bounds |
| Privacy | No PII/source payload/filename/contact fields in response or logs; unsafe labels null; no global counts; opaque safe errors |
| UI | Loading/error/empty/partial, period/load age visible, MXN formatting, filter versus report-total distinction, no fabricated link or mutation calls |
| Non-expansion | No No Uso join, lifecycle inference, QRY-014/015 change, D1/Inbox promotion, new roles, migration, source mutation or external access |
| Integration | Focused backend/UI regressions, lint/type/build, synthetic browser E2E, independent review and express evidence acceptance |

The synthetic E2E uses the separately approved environment and records its evidence in an authorized artifact or external delivery; it does not justify adding unlisted files. D1 prerequisite acceptance in §3.1 precedes implementation. Passing this gate can establish only D2-Lite conformance, never complete D2/D3, release, production or another package.

## 13. Rollback, residual risks and sequence

Rollback removes/disables the new panel and read adapter and handles the new contract according to its separate retirement/release act. Preserve D1, batches, staging rows, Facts, Events, receipts and Master. No migration or data rewrite is part of this increment. No rollback of a read projection may alter imported history or undo an accepted batch. Deployment/release and its rollback require later authority.

| Residual risk | Containment / prerequisite |
| --- | --- |
| No terminal D1 conformance record located | Identify/accept exact prior evidence before implementation; no assumed closure |
| No accepted_at or supersedes column | Explicit upload-order snapshot policy; null acceptance time; no historical backfill |
| Unchanged provenance is not a direct FK | Verify candidate Facts and source rows; conservative unavailable outcome |
| Timestamps do not prove commit order | No commit-time claims; eligibility filter may reduce coverage |
| Facts/rows lack blanket DB immutability triggers | Respect existing writers; detect contradictions; separate repair package if required |
| Store UUID can retain a changed identifier | Preserve reported ID; suppress unproven Master attribution |
| D1 numeric parser/Float precision | Reject non-finite material; expose partial coverage; no ledger-precision claim |
| Unsafe Master names | Field-level exposure review; null labels when safety not established |
| Accepted D1 state may contain latent inconsistencies | Strict structure/provenance checks; no silent repair or historical merge |
| Performance of reconstruction | Bound selected rows; review query plan with synthetic data; separately authorize any needed index |
| Legacy HTTP versus PLANNED metadata | Explicit new Query admission act; no implied promotion or Dispatcher change |

Proposed sequence: independent review of this proposal; Architecture Authority decision under AR-001 clarifying the D2 increment and Query; acceptance of D1 prerequisite evidence; exact contract/authority/file-boundary and implementation gate; bounded synthetic implementation; independent conformance; separately authorized release if ever requested. These steps are not executed by naming them. Indicative planning is 1–2 design/review sessions, 2 backend sessions, 1–2 UI sessions and 1–2 evidence/review sessions, contingent on source validity and governance decisions.

Excluded: No Uso composition, comparative history, full Merchant 360, QRY-014/QRY-015 implementation, contacts/RFQ/cases, external lifecycle, Core/Salesforce/Gmail, Boba Tree/Mixue implementation, assets/serials, reconciliation, Package B, production and deployment. ADR-019/020, Amendments and accepted proposals remain unchanged. Package B B1/B2/B3 are not opened; Amendment 018 §8.3 remains open and §8.5 and later gates remain closed. No secrets, real documents, fiscal identifiers, confidential prices or source records are copied to Git. Downstream authority is None.

## 14. Independent Review — PENDING

| Field | Value |
| --- | --- |
| Status | PENDING |
| Reviewer | [not recorded] |
| Reviewed version / canonical hash | [not recorded] |
| Review date | [not recorded] |
| Verdict | [not recorded] |
| Mandatory findings / disposition | [not recorded] |

Documentary validation is not independent review, acceptance, conformance or ratification.

## 15. Future Architecture Authority Act

| Field | Value |
| --- | --- |
| Act ID | [not recorded] |
| Architecture Authority | [not recorded] |
| Decision | [not recorded] |
| Decision date | [not recorded] |
| Reviewed proposal version | [not recorded] |
| Reviewed canonical SHA-256 | [not recorded] |
| Independent review reference | [not recorded] |
| Independent review verdict | [not recorded] |
| Accepted scope | [not recorded] |
| Mandatory findings remaining | [not recorded] |
| Contract allocation authority | [not recorded] |
| Implementation work packages | [not recorded] |
| Exact Authorized File Boundary | [not recorded] |
| Evidence Gate | [not recorded] |
| Rollback authority | [not recorded] |
| Release / operation authority | [not recorded] |
| Exceptions | [not recorded] |
| Downstream authority | [not recorded] |

Every value is deliberately unrecorded. Business confirmations and authority to prepare this proposal do not populate a future acceptance, ratification or implementation act.

## 16. Documentary delivery checks

Only this new proposal is created. Verify strict UTF-8 without BOM and LF, headings/tables/fences, exact status, candidate path existence, empty future act, unchanged baseline and Boba Tree hash, empty index and final Git status. Run whitespace checks including the untracked proposal. Report its canonical SHA-256 externally rather than embedding a self-referential hash. No staging, commit or push; stop for independent review.
