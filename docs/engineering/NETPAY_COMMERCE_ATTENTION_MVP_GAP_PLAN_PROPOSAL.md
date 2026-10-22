# Netpay Commerce Attention MVP — Gap Closure Plan

## Status

**RATIFIED DESIGN INPUT FOR AMENDMENT 025 — NO INDEPENDENT AUTHORITY**

P0/P1 is closed under Amendment 024 and IG-011. This plan does not reopen it
and does not authorize P2–P5, real data, migrations or operational effects.

Concrete proposed successor package: [Amendment 025](IMPLEMENTATION_ROADMAP_AMENDMENT_025.md)
and [IG-012](IG-012_NETPAY_COMMERCE_ATTENTION_P2A_P2B_AUTHORIZATION.md).
Amendment 025 and IG-012 are ratified; this analysis remains a design input and
does not independently expand their authority.

## Current-state classification

| Capability | State | Existing owner/evidence | Gap to MVP |
| --- | --- | --- | --- |
| Master Client/Company/Branch/StoreReference portfolio | Implemented and validated | QRY-023/QRY-024; IG-011 evidence | No MID or terminal source |
| D1 operational data | Implemented outside Portfolio | OperationalDataBatch/Row, StoreProfitabilityFact, NoUsageCampaignEntry; D1 tests | Acceptance validity, supersession, Decimal/currency and reconstruction policy must be ratified |
| Cases, requirements and dossiers | Implemented outside Portfolio | NetpayServiceCase, H2 dossier/checklists and evidence | Read-only aggregates/navigation need Portfolio contracts and disclosure rules |
| Contacts/follow-up | Partly implemented outside Portfolio | Master registered contact; candidate follow-up and case next action | Contact identity, freshness and preferred operational contact remain P4 decisions |
| Terminals/series/shipment | Legacy or incomplete | legacy devices, assignments and shipments exist | No authorized canonical terminal inventory or safe Store link |
| Attention colors | Designed only as future requirement | no ratified evaluator | Deterministic scenarios, priority and thresholds pending P3 |
| Persisted preferences | Not implemented | transient P0/P1 view only | P5 remains closed |

## MVP gap matrix

| Area | Visible behavior | Canonical grain / identity | Contracts and dependencies | Acceptance |
| --- | --- | --- | --- | --- |
| Commerce → stores | Client grouping with Branch rows and Store ID | Client→Company→Branch→StoreReference; Store ID is not MID | Reuse QRY-023/024 | No duplicate Branch; incomplete chains explicit |
| Terminal/series → store | terminal count/detail and shipment evidence | terminal serial plus explicit same-tenant StoreReference assignment | Separate terminal package and query contracts; legacy data cannot become canonical by reuse | exact assignment, history, tenant isolation, no inference by label |
| Monthly sales/activity/no-use | period totals, activity and freshness | StoreReference + closed period + source batch | P2 after D1 remediation; new read contract | accepted effective batch only; reproducible result and provenance |
| Distributor commission | show source field `Rentabilidad` as **Comisión del distribuidor (MXN)**; retain the original field name in provenance | StoreReference + period + MXN + source profile | supplied-field authority; separate formula authority for the derived percentage | never call it Store profit, merchant margin, billing, ROI or merchant rate |
| Requirements/attention | open cases, blockers, dossier completeness | owner IDs and explicit Store/Branch links | read-only case/dossier aggregate contract | counts navigate to exact same-tenant records; no metadata-as-validation |
| Contacts/actions | registered contact, last interaction, next action | explicit source and role; never name matching | P4 contract/privacy authority | contradictory identities remain separate; no communication action |
| Summary/subdashboards | totals and drill-down preserving context | same row identities as detail | composed query contracts, no new Commerce owner by default | totals reconcile with filtered detail |
| Colors | text+icon+color with reasons and timestamp | scenario evaluation over authorized facts | P3 evaluator contract and thresholds | deterministic priority; missing data becomes gray/unknown, never zero |
| Preferences | persisted operator view | operator+organization | P5 only | remains excluded from MVP increments before P5 |

## P2/D1 readiness findings

- Batch status includes `accepted`, but no verified effective-batch/vigency or
  cross-batch supersession policy was found.
- Source hashes, row fingerprints, command receipts and unique batch/store keys
  provide idempotency foundations; current concurrency and replay coverage must
  be rerun under the future gate.
- Matching is explicit (`matched/unmatched/ambiguous`) and uses
  `store_reference_id`; names must remain review signals only.
- Monetary and volume columns use floating point and facts lack an explicit
  currency column. Business authority defines the analyzed monetary sources as
  MXN; P2A must persist that profile metadata and establish Decimal precision
  and rounding before P2 exposes financial totals.
- Facts retain batch, period, row fingerprint and organization, but the API must
  prove indicator-level reconstruction and source freshness.
- Later validation needs synthetic schemas for monthly store performance and
  no-use campaigns, including period, currency, volume, transactions, income,
  cost, commissions, supplied profitability, Store ID and reconciliation cases.
  No real Excel is needed for design or conformance.

## Source-analysis boundary and dictionaries

The authorized read-only inspection covered all three named workbooks. The
global and no-use packages contain one sheet each; the monthly profitability
package contains five visible sheets. None contains formulas, VBA, external
links or workbook connections. The files show structure and observed values;
they do not prove that a delivery is a complete population. A missing row
remains `unknown`, never zero sales or proof of inactivity.

| Source | Observed row grain and identifiers | Period/cutoff and delivery mode | Measures, types and quality | D1 compatibility |
| --- | --- | --- | --- | --- |
| Global Netpay report | 345 populated rows. The repeated grain is terminal/product observation, not one row per commerce. Serial TPV and terminal number each have 137 distinct observed values and a one-to-one observed pairing, although only 209 paired rows use identical text. Commerce number is populated in 327 rows, unique in those rows and stored as mixed numeric/text. One serial-like value relates to many commerce numbers, so serial is not safe commerce authority. `Numero de comercio`, Store ID and MID are not proven equivalent. | No reporting period or source cutoff column. Creation date is partly typed as date and partly as text, spans 2021-04-07 through 2026-07-15 for typed cells, and is an entity creation date rather than an evidenced report period. Snapshot/partial/incremental status remains unproven. | Product and product status are populated; commerce name is sometimes blank. Folio is partially populated. Client/contact/RFC/legal/address columns are present but entirely blank. No sales, transactions, income, commissions, profitability or currency fields. No complete duplicate rows were observed. | Not compatible with either current D1 dataset. It is terminal/product evidence, a scope explicitly excluded from P2. It must not be coerced into StoreReference, MID or performance facts. |
| No-use report | 1,000 numbered template rows, but only 32 rows contain substantive commerce data. Those 32 have distinct Store IDs plus store, master and distributor labels. The observed grain is one campaign entry per supplied Store ID. No duplicate populated Store ID or complete populated row was observed. Labels do not establish a canonical identity relationship. | No period or cutoff column. The filename is insufficient evidence. The populated subset suggests a targeted campaign/extract, but whether it is complete, partial or incremental remains unproven. | `Meses No Uso` is a non-negative whole number in the populated rows; status and alert each use two observed categories. Survey/follow-up columns are mostly empty. There are no sales, transactions, income, commission, profitability or currency fields and no formulas. | Partially compatible in Store ID, months-without-use, status and alert. It lacks the RFC header and explicit campaign period required by the current parser. Importing it unchanged would fail validation; inventing either value is prohibited. |
| Distributor monthly profitability workbook | Five visible sheets: two summaries, a non-natural-category list, a 348-row Store-month profitability base and a 1,130-row transaction-detail base. The Store base has 348 populated, distinct Store IDs and no duplicate complete rows; the transaction base has 154 Store IDs repeated across transaction dimensions. Store ID is structurally compatible with exact `StoreReference.store_id`, but correspondence to the current Master was not queried and is not proven. It is not MID, commerce number or terminal. | Both detailed bases explicitly contain one period: September 2026 (`2026-09`, represented as month end in the Store base). This accredits reporting period, not extraction cutoff. The workbook is scoped to one distributor/Master, so it is partial relative to the global Portfolio; completeness inside that scope and incremental/snapshot delivery remain unproven. | Store-month fields include a supplied no-use flag, volume, rate differential, rent, fixed e-commerce income, cost components, several separately named commission fields, supplied total commissions and source field `Rentabilidad`. Business authority defines `Rentabilidad` as the distributor commission for Store transactions; the other commission fields remain separate and their relationship is not inferred. Transaction detail includes transaction count, volume, income, cost, rate differential and sale/purchase rates. `Rentabilidad` is numeric, may be negative, has two decimals and is not percentage-formatted. No formula cells exist. The workbook lacks a currency column, but business authority defines its monetary fields as MXN. Store and transaction summary controls reconcile exactly for counts and differ by no more than `0.01` for observed monetary aggregates; this is not a universal tolerance. | The current monthly parser can select the Store base because it has Store ID, period and `Rentabilidad`; it can also capture client, UEN and volume. It cannot retain the no-use flag, rent, rate differential, fixed income, cost/commission breakdown or the source precision/MXN profile metadata. Its exact `comisiones` alias does not match the supplied total-commission header; transaction count is only in the repeated transaction-detail grain. Numeric conversion to Float would lose Decimal intent. |

The current D1 monthly parser accepts Store ID, `YYYY-MM`, required
profitability and optional client/product/volume/transaction/income/cost/
commission fields, converts numbers to binary Float and stores no currency. The
future profiles attach `MXN` as traceable batch metadata without requiring an
Excel column and reject a future conflicting currency. Rates, percentages,
counts and months-no-use remain non-monetary. The current no-use parser also
requires an RFC column and explicit period. Synthetic
fixtures prove parser behavior only, not correspondence with these sources.

## Resolved proposal conclusions

- Every monetary field in the analyzed Netpay profiles is `MXN`. The batch
  carries this authority as traceable metadata; the Excel need not contain a
  currency column. A later conflicting currency fails the profile.
- Decimal storage preserves available source precision. Aggregation occurs
  before presentation rounding; the recommended display rule is
  `ROUND_HALF_UP` to two decimals. Reconciliation tolerance is a separate,
  source-specific control and is not inferred universally from the observed
  `0.01` difference.
- Historical Float facts remain immutable and labelled
  `legacy_float_precision_unverified`. They do not enter exact Decimal
  aggregates unless an explicitly linked, re-sourced Decimal fact supersedes
  them. Casting Float to Decimal does not recover precision.
- The effective value is selected by organization, dataset, StoreReference,
  period and metric through an explicit accepted-effective record. A correction
  names the current predecessor, reason, actor and idempotency key and becomes
  effective only through the governed supersession transition. Creation time
  alone never wins.
- All observed deliveries remain partial unless later certification states
  otherwise. Omission means unknown.
- The monthly `Store IDs sin Uso` flag and campaign `Meses No Uso` observation
  are distinct metrics with distinct source profiles and provenance. Neither
  overwrites the other. The campaign observation requires an explicit cutoff.
- Source field `Rentabilidad` is the distributor commission for each Store, not
  Store profit or billing. Other commission fields remain separate because the
  workbook does not establish their equivalence or inclusion.
- **Comisión efectiva sobre ventas (%)** is `Rentabilidad / Volumen * 100` for
  the same Organization, Store, period and compatible effective version.
  Business authority confirms `Volumen` as monthly Store sales in MXN. Missing,
  zero or incompatible volume produces an explicit non-calculable reason.
  Negative commission is retained.
- Transaction count, income and cost require a separate Store-period
  aggregation over the transaction grain. The recommended first increment
  defers them; that aggregation is not a profitability calculation.

The single remaining ratification table is maintained in the P2/D1
authorization draft.

## Proposed subdashboards

| View | Indicators | Source/formula | Filters/navigation | Empty/stale behavior |
| --- | --- | --- | --- | --- |
| General | merchants, branches, stores, reconciliation | P0/P1 counts | hierarchy/status; row detail | distinguish zero from unavailable |
| Sales/activity | volume, transactions, last active period, no-use evidence | accepted D1 facts; no derived profitability | period/store/client; drill to source-safe detail | missing period is unknown |
| Distributor commission | supplied `Rentabilidad` as distributor commission; other commission fields separate | source amount plus separately versioned commission/volume percentage | period/Store; MXN only for amounts | percentage absent with explicit denominator reason |
| Requirements | cases, blockers, completeness, next action | case/dossier owners | state/due date; governed detail | unavailable links stay unlinked |
| Stores/terminals | Store ID, terminal count, serial status, shipment evidence | future terminal owner | store/status; terminal detail | no source = unavailable |
| Reconciliation/quality | unmatched/ambiguous, freshness, conflicts | D1 and pre-Master queues | source/status/age | stale and conflict explicit |

## P3 scenario preparation

| Dimension | Candidate condition | Priority | Required source/freshness | Decision needed |
| --- | --- | --- | --- | --- |
| Commercial | validated negative/under-target performance | unresolved | accepted comparable periods | formula and thresholds |
| Activity | explicit no-use observation | unresolved | campaign/transaction period | inactivity window |
| Documentary | blocker or overdue required item | unresolved | dossier requirement owner | severity mapping |
| Logistics | terminal shipment/assignment exception | unresolved | canonical terminal evidence | exception states |
| Data quality | missing, stale, ambiguous or conflicting | gray/unknown candidate | provenance timestamps | freshness limits |

Concurrent signals must use a ratified deterministic priority and expose every
activated reason. No threshold above is approved.

## Delivery order

1. **P2A D1 readiness/remediation:** effective batches, supersession,
   Decimal/currency/formula provenance and synthetic conformance.
2. **P2B Portfolio performance projection:** read-only qualified no-use and
   supplied monthly MXN metrics, including **Comisión del distribuidor (MXN)**
   and conditional **Comisión efectiva sobre ventas (%)**.
3. **Separate terminal inventory package:** establish canonical terminal/serial
   and shipment ownership before Portfolio composition.
4. **Requirements/contact composition:** read-only case/dossier summaries, then
   P4 contact/follow-up authority.
5. **P3 scenarios**, then **P5 persisted preferences/advanced experience**.

The minimum visible increment is P2A+P2B for qualified no-use and supplied
monthly MXN metrics with explicit quality and provenance. Recalculation of the
source commission and merchant margin/ROI remain outside this proposal.
