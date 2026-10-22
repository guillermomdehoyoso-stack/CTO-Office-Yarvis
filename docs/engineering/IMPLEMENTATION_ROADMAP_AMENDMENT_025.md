# Implementation Roadmap Amendment 025 — Netpay Portfolio P2A/P2B

## Status

**RATIFIED — IMPLEMENTATION AUTHORITY FOR P2A/P2B**

**Ratified date:** 2026-10-21
**Predecessor:** Amendment 024 and closed IG-011 P0/P1
**Implementation gate:** [IG-012](IG-012_NETPAY_COMMERCE_ATTENTION_P2A_P2B_AUTHORIZATION.md)
**Design inputs:** [MVP gap plan](NETPAY_COMMERCE_ATTENTION_MVP_GAP_PLAN_PROPOSAL.md) and [P2/D1 draft](NETPAY_COMMERCE_ATTENTION_P2_D1_AUTHORIZATION_DRAFT.md)

Ratified by explicit requester instruction on 2026-10-21. This amendment opens
only IG-012 P2A/P2B implementation and synthetic conformance; it authorizes no
productive import or backfill.

## 1. Ratified decision

Add two sequential, independently closable Portfolio increments:

1. **P2A source integrity** for monthly Store performance and the no-use
   campaign; and
2. **P2B read-only projection** over P2A-qualified observations.

The monthly source may advance because its September 2026 period is evidenced.
The no-use campaign advances only to safe receipt/validation while its cutoff is
unconfirmed. A campaign batch without cutoff remains `metadata_pending`, cannot
be effective and contributes no indicator or temporal total.

## 2. Confirmed business rules

- Store ID is the single canonical Netpay business identifier. Sources compose
  only through exact same-Organization `NetpayStoreReference.store_id`.
- Pending records receive no fabricated Store ID. Names, MID and terminal are
  never merge keys; discrepancies remain in reconciliation.
- Monetary source values are MXN, recorded as batch metadata. A future source
  declaring another currency is incompatible with this profile.
- Rates, percentages, counts, flags and months-no-use are non-monetary.
- Source field `Rentabilidad` is the distributor commission for transactions of
  each Store. UI label: **Comisión del distribuidor (MXN)**. Provenance retains
  the original field name. It is not Store profit, billing, merchant margin,
  ROI or the rate charged to the merchant.
- Other commission fields remain separate; their relationship to `Rentabilidad`
  is not inferred.
- Derived metric: **Comisión efectiva sobre ventas (%)** =
  `Rentabilidad / Volumen * 100` for the same Organization, Store, period and
  compatible effective version. `Volumen` is monthly Store sales in MXN. Zero,
  missing or incompatible volume yields
  an absent value and explicit reason. Negative commission remains negative.
- The no-use report producer is Netpay Operations and its delivery channel is
  the regional commercial manager. Reception, generation and data cutoff are
  separate. The cutoff is unconfirmed; “previous month” remains a hypothesis.
- Monthly Store-no-use flag and campaign `Meses No Uso` are distinct metrics and
  never overwrite one another.
- Every observed source is partial unless later certified complete. Omission is
  unknown, never zero or inactive.

## 3. Ratified decisions

The decisions recorded in the
[P2/D1 authorization draft](NETPAY_COMMERCE_ATTENTION_P2_D1_AUTHORIZATION_DRAFT.md)
are ratified. Presentation uses `ROUND_HALF_UP` to two decimals after
aggregation. The `0.01 MXN` reconciliation tolerance applies only to defined
controls of the analyzed monthly profile. Corrections require an authorized
operator, explicit predecessor, reason and idempotency key; late corrections
use explicit supersession. Transaction count, income and cost remain deferred.

## 4. Contracts and permissions

No new interaction IDs are proposed. Existing boundaries are reused:

- D1: `IC-NETPAY-CMD-026` through `030`, `IC-NETPAY-QRY-011` through `013`,
  and `IC-NETPAY-EVT-015` through `019`;
- Portfolio: `IC-NETPAY-QRY-023` and `IC-NETPAY-QRY-024`.

`IC-NETPAY-CMD-028 AcceptOperationalDataset` gains the governed
accepted-effective/supersession requirements without changing its owner.
QRY-023/QRY-024 gain optional P2 fields while retaining their read-only owner.

Existing permissions are sufficient and no new scope is proposed:

- `netpay.inbox.manage` for existing D1 mutations;
- `netpay.inbox.read` for existing D1 batch reads;
- `netpay.portfolio.read` for qualified P2 metrics; and
- `netpay.portfolio.reconciliation.read` for safe D1 discrepancies and counts.

`netpay.portfolio.sensitive.read` is not required for P2 metrics.

## 5. Persistence and compatibility

P2A may add a migration after current head `20261014_52`, proposed filename
`20261021_53_netpay_operational_data_p2a.py`, for:

- source profile and `MXN` currency metadata;
- received/generated/cutoff timestamps and `metadata_pending` state;
- exact Decimal source values and precision classification;
- effective status, predecessor/supersession linkage, reason and actor; and
- metric identity needed to select one effective organization/Store/period/
  metric observation.

Existing Float facts remain immutable and marked
`legacy_float_precision_unverified`. Casting does not restore precision. They
cannot mix silently into exact Decimal aggregates; only an explicitly linked,
re-sourced Decimal observation may supersede one.

## 6. Excluded

Productive source import, historical backfill, transaction-derived count/income/
cost, recalculation of `Rentabilidad`, combination of commission fields, global
terminal report, MID, terminals, P3 colors, P4/P5, D2-Lite, export,
communications, Gmail/OAuth and every Portfolio mutation remain excluded.

## 7. Ratification effect

Together with ratified IG-012, this amendment authorizes only implementation
and synthetic conformance inside the enumerated allowlist.
