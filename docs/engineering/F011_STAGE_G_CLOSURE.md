# F-011 Stage G Closure

## Status

**G COMPLETE — VALIDATED NO-OP**

## Purpose and G0 scope

Stage G established whether the legacy Radar history could be safely included in
the F-011 canonical command model. G0 was bounded to read-only discovery of the
durable `yarvis` database. It performed no cutover, backfill, replay, data
repair, or schema change.

## Historical inventory

| Workspace | Merchants | Requests | Activities | Checklist items | Total records |
| --- | ---: | ---: | ---: | ---: | ---: |
| `manual-close-validation` | 1 | 1 | 9 | 6 | 11 |
| `netpay-demo` | 7 | 8 | 36 | 39 | 51 |

All 62 historical Radar records have `organization_id = NULL`. There are no
historical `RadarCommandReceipt` records or Radar `DomainEvent` records, and no
persisted Principal or PrincipalMembership provenance for the historical data.
The historical activity actors are strings only: `validacion`, `demo-seed`, and
`Guillermo`. Merchant, request, and activity links are structurally present,
but they do not supply canonical authority, receipt, event, replay, or cutover
provenance. Two `netpay-demo` requests have no checklist items.

## Decision

- `manual-close-validation` is excluded and immutable.
- `netpay-demo` is excluded and immutable.
- There are zero canonical candidates eligible for cutover or backfill.
- G performed zero data mutations.

Amendment 003 expressly requires both sets to remain retained, unlinked,
invisible to canonical authority, and without transformation. It is neither
safe nor authorized to invent retrospective organization, Principal,
Membership, command, or idempotency mappings.

## Closure consequences

G requires no migration, backfill, schema change, public contract, or
additional Amendment. The following F-011 invariants remain in force:

- Authority derives only from persisted Principal, Organization, active
  PrincipalMembership, and permissions resolved by AuthorityResolutionService.
- Headers and tokens do not grant authority or select an organization.
- The 62 historical records remain unaltered.
- Replay cannot duplicate receipts, activities, events, or causal chains.

## F-011 status and next step

- F: **COMPLETE — VALIDATED**
- G: **COMPLETE — VALIDATED NO-OP**
- H: pending
- I: pending
- F-011: **IN PROGRESS**

H requires a separate discovery and design mandate, without assuming that it
can transform the excluded historical sets.
