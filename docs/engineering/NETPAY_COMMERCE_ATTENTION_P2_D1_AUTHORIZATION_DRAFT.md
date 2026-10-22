# Netpay Commerce Attention P2/D1 Readiness Authorization Draft

## Status

**RATIFIED DESIGN INPUT FOR AMENDMENT 025 — NO INDEPENDENT AUTHORITY**

The concrete proposed package is [Amendment 025](IMPLEMENTATION_ROADMAP_AMENDMENT_025.md)
and [IG-012](IG-012_NETPAY_COMMERCE_ATTENTION_P2A_P2B_AUTHORIZATION.md).
Those governing documents are ratified. This draft records their design input
but does not independently grant or expand implementation authority.

## Business authority resolved for this proposal

All monetary amounts in the analyzed Netpay sources are denominated in Mexican
pesos (`MXN`). Each source profile attaches `MXN` as immutable, traceable batch
metadata; no currency column is required in the workbook. A future source that
declares another currency is incompatible with these profiles and must be
rejected or governed by a new profile. Rates, percentages, counts, flags and
months-no-use remain non-monetary and must not be converted to MXN amounts.

Source field `Rentabilidad` is the commission received by the distributor for
transactions of each Store. P2B labels the supplied amount **Comisión del
distribuidor (MXN)** while preserving `Rentabilidad` as the original source
field name in provenance. It is neither Store profit nor Store billing. Other
commission fields in the workbook remain distinct supplied fields; their names
do not prove equivalence, summation or inclusion in `Rentabilidad`.

The derived metric is **Comisión efectiva sobre ventas (%)** = distributor
commission divided by source field `Volumen` for the same Organization, Store,
period and compatible effective version, multiplied by 100. `Volumen` is the
monthly Store sales amount in MXN. Negative commissions
remain negative. The metric is not merchant margin, Store profit, ROI or the
rate charged to the merchant. Missing, zero or incompatible volume produces
`not_calculable` with a specific reason and is never replaced by `0%`.

Store ID is the canonical Netpay business identifier shared by source reports
and `NetpayStoreReference.store_id`. Technical UUIDs remain internal. Matching
is exact within Organization; pending records receive no fabricated Store ID
and remain in reconciliation. Names, MID and terminal identifiers never merge
or create Store identity.

The no-use report is produced by Netpay Operations and delivered through the
regional commercial manager. Its data cutoff is **NOT CONFIRMED**. Reception,
source generation when present and data cutoff are separate timestamps. The
assumption that it covers the immediately preceding month is not a rule. A batch
without confirmed cutoff stays `metadata_pending` and contributes no effective
indicator or temporal total. This does not block the monthly source whose
September 2026 period is evidenced by its contents.

## Proposed increment

Authorize two sequential gates:

1. **P2A source integrity:** define separate no-use and monthly-performance
   source profiles, governed cutoffs, effective accepted observations,
   row/metric supersession, exact Decimal handling, reproducible StoreReference
   matching, provenance and reconstruction.
2. **P2B read-only projection:** expose qualified no-use observations and the
   monthly Store metrics explicitly allowed below, with quality, freshness and
   source-reported/calculated labels.

P2A is an integrity and traceability prerequisite. No P2B indicator may be
exposed merely because a numeric column currently exists.

## Included

- synthetic source profiles and fixtures for no-use and monthly Store performance;
- explicit StoreReference matching and separate unresolved queue;
- immutable source/batch/row provenance and freshness;
- read-only no-use/performance filters, freshness and provenance drill-down;
- least-disclosure permissions and aggregate leakage tests;
- idempotency, concurrency, tenant isolation and effective-batch tests.

## Excluded

Real Excel/data, automatic imports, unlisted financial metrics, recomputation
of source field `Rentabilidad`, destructive Float rewrite, D2-Lite, Gmail/OAuth, MID inference,
terminals/series, colors, communications, export, mutations, P3–P5 and a new
Commerce entity/materialized projection.

Existing Store ID-to-`StoreReference` links may be used under their current
authority. MID and terminal identifiers remain outside this increment unless a
later mandate explicitly names an already-authorized reference and its owner.

## Contracts and permissions proposed for reuse

No new contract or permission identifier is needed:

- D1 reuses `IC-NETPAY-CMD-026` through `030`, `IC-NETPAY-QRY-011`
  through `013`, and `IC-NETPAY-EVT-015` through `019`;
- Portfolio reuses `IC-NETPAY-QRY-023` and `024` for list/detail composition;
- D1 reads/mutations retain `netpay.inbox.read` / `netpay.inbox.manage`; and
- P2 display/reconciliation uses `netpay.portfolio.read` /
  `netpay.portfolio.reconciliation.read`.

`netpay.portfolio.sensitive.read` is unnecessary for these business metrics.
The ratification extends existing contract schemas/semantics without changing
their owners.

## Possible persistence changes

A focused migration after current head `20261014_52` is proposed as
`20261021_53_netpay_operational_data_p2a.py` for source profile/cutoff, MXN,
exact Decimal values, source/effective times, metric identity and predecessor/
superseded fact linkage. Historical Float facts must not be silently rewritten:
conversion does not recover precision already lost. They require explicit
precision classification and a separately authorized re-source/backfill policy.

## Candidate file boundary

- D1 models/services/schemas/routes and focused migrations if ratified;
- Portfolio service/schema/API/component additions;
- authority map and exact negative tests;
- backend, frontend and browser tests;
- new evidence and current-state documents only at closure.

Exact paths are enumerated by proposed IG-012 before any implementation.

## P2A acceptance criteria

- each source profile identifies row grain, headers, governed cutoff,
  completeness status, units and duplicate policy without relying on filenames;
- one deterministic effective observation exists per organization, dataset,
  StoreReference, period and metric, with explicit predecessor/supersession and
  no deletion inferred from omission;
- batch, controlled row, match, receipt, fact and supersession are
  reconstructable without retaining prohibited source content;
- months-no-use accepts only the ratified non-negative integer range; status and
  alert preserve controlled source values;
- monetary values use Decimal with batch currency `MXN` and preserved source
  scale; aggregation precedes presentation rounding using `ROUND_HALF_UP` to two
  decimals. Reconciliation uses a separately ratified source-profile tolerance
  and never treats the observed `0.01` difference as universal;
- source field `Rentabilidad` remains a supplied distributor commission,
  distinct from other commission fields and every calculated metric;
- legacy Float facts remain immutable and marked
  `legacy_float_precision_unverified`; they are excluded from exact Decimal
  aggregates unless an explicitly linked, re-sourced Decimal fact supersedes
  them, and casting never counts as precision recovery;
- one effective value per organization, dataset, StoreReference, period and
  metric is selected by explicit governed status. A correction identifies the
  expected predecessor, reason, actor and idempotency key; creation time alone
  does not establish precedence;
- equal replay is idempotent and conflicting replay is rejected;
- concurrent accept/supersede operations serialize to one explainable effective
  result without partial facts;
- cross-organization lookup, replay, matching and supersession are rejected;
- late correction, closed-period and freshness behavior follows the ratified
  calendar and source profile.

## P2B acceptance criteria

- P2A has passed for every metric exposed by P2B;
- one deterministic effective value is returned per organization, Portfolio
  row, period and exposed metric, with provenance and freshness;
- only P2A-qualified values are exposed; missing coverage, stale data and
  conflicts are distinct from numeric zero or active use;
- direct candidates are supplied months-no-use/status/alert, monthly volume,
  rate differential and **Comisión del distribuidor (MXN)** sourced from field
  `Rentabilidad`; other commission fields are not combined with it;
- conformance tests prove that total or component commission fields neither
  substitute for nor contribute to source field `Rentabilidad` without a later
  independently ratified semantic rule;
- **Comisión efectiva sobre ventas (%)** is returned only when the authorized
  same-Store, same-period monthly-sales denominator is present, compatible
  and non-zero; otherwise its value is absent with reason
  `volume_missing`, `volume_incompatible` or
  `volume_zero`. Negative commission produces a negative percentage;
- transaction count, income and cost derived from transaction detail remain
  absent unless their aggregation formula/grain is versioned and reconciled;
- matching never uses name similarity as composition authority;
- filters, totals and detail reconcile against the same effective observations;
- backend, UI and browser tests prove organization isolation and least
  disclosure, including aggregate leakage negatives;
- Portfolio remains read-only and produces no communication or operational case;
- synthetic readback does not mutate D1 or Master records;
- synthetic backend/frontend/browser, contract and static gates pass.

## Ratified decision record

| Decision | Ratified rule | Consequence |
| --- | --- | --- |
| Monthly-sales denominator | `Volumen` is monthly Store sales in MXN. Use the same Organization, Store, period and compatible effective version. | P2B calculates **Comisión efectiva sobre ventas (%)**; missing, zero or incompatible values are not calculable. Totals use ratio of sums and disclose coverage. |
| Presentation rounding and reconciliation threshold | Ratify `ROUND_HALF_UP` to two decimals for presentation after aggregation. Define `0.01 MXN` only as the proposed tolerance for the currently analyzed monthly source profile; other profiles require their own evidence and threshold. | Presentation is stable while reconciliation remains an independent quality control rather than hidden rounding. |
| Correction authority and period policy | Permit only an authorized D1 operator to supersede the explicit current predecessor with reason and idempotency key. Preserve reporting/campaign period, received time and effective time; define the business close/reopen window. | Later uploads do not win by creation time, and every correction remains reconstructable. |
| Campaign no-use cutoff completion | Ratify `metadata_pending` for receipt without an audited data cutoff, with no effective indicators or temporal totals until an authorized operator completes that metadata. Keep `Meses No Uso` distinct from the monthly Store-no-use flag. | Monthly performance can advance independently while the campaign remains quarantined from current metrics. |
| Transaction-derived metrics in the first increment | Defer transaction count, income and cost from the first P2B increment. They add a second grain and versioned aggregation without being required to expose the Store-level supplied metrics. | Initial delivery stays smaller; a later sub-gate can add Store-period sums with control reconciliation. The requested commission/volume percentage remains a separate derived ratio, not a reconstruction of `Rentabilidad`. |

## Dependencies that block implementation authority

No unresolved business decision blocks synthetic implementation. Productive
source import/backfill and activation of a real no-use campaign remain outside
authority; the latter also requires its audited cutoff.

Completeness certification and transaction-derived metrics do not block this
bounded increment: sources default to partial and those derived metrics are
deferred. A productive import or historical backfill is also outside this gate
and requires separate operational authority.

After ratification of the unresolved business choices, the exact implementable
scope would be **P2A source integrity** for no-use and monthly Store performance:
governed cutoffs, exact StoreReference matching, row/metric supersession,
retained history, Decimal/MXN/rounding, source precision classification,
reconstruction/freshness, control reconciliation and synthetic PostgreSQL
tests. **P2B read-only projection** would expose supplied no-use observations
and, after P2A, monthly sales volume,
rate differential, **Comisión del distribuidor (MXN)** from source field
`Rentabilidad`, and **Comisión efectiva sobre ventas (%)**, each with period,
MXN metadata where monetary, provenance, quality and freshness.
Transaction-derived count, income and cost are deferred from this increment.

The next Amendment/IG would exclude the global terminal report, recomputation
of source field `Rentabilidad`, combination with other commission fields,
merchant margin/ROI, silent Float rewrite, MID, terminals, inference
from omissions, colors, communications, export, real-data import, D2-Lite and
P3–P5. It would authorize implementation and synthetic validation only; any
productive import/backfill would require a later operational authorization.

Amendment 025 and IG-012 ratify this bounded P2A/P2B implementation scope.
