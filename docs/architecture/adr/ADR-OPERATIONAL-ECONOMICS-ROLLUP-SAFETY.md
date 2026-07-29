# ADR — Operational Economics Roll-up Safety

**Status:** Proposed  
**Decision:** ADR-OPERATIONAL-ECONOMICS-ROLLUP-SAFETY  
**Checkpoint:** OV-001

## Context

Operational subjects have relationships, but relationship graphs are not necessarily
economic aggregation graphs. Directly summing Project, Work, Process, and Task values
would duplicate facts whenever the same work appears through multiple relationships.

## Proposed Decision

Use explicit temporal `EconomicRollupMembership` records. A child subject has at most
one active parent for the initial `operational` dimension. Facts contribute through a
single declared route and are deduplicated by fact identity. A Process/Work association
does not imply roll-up membership.

Forecast metrics select current non-superseded facts; projected total cost is incurred
cost plus cost to complete, not a sum of estimate, commitment, and incurred values.
Cross-currency totals are unavailable until traceable conversion evidence exists.

## Consequences

- Roll-ups are explainable, temporal, and resistant to accidental double counting.
- Multi-parent allocation and alternate management/reporting dimensions remain future
  capabilities requiring an explicit allocation design.
- Direct parent facts and child facts stay separate assertions rather than copied
  totals.

## Rejected Alternatives

- Infer economic hierarchy from every existing Project, Work, Process, or UI relation.
- Permit arbitrary multi-parent roll-up in the MVP.
- Add all historical estimates, commitments, and incurred costs into one total.
- Convert currencies silently.
