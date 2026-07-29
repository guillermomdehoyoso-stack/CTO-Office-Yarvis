# ADR — Operational Economics Fact Ownership

**Status:** Proposed  
**Decision:** ADR-OPERATIONAL-ECONOMICS-FACT-OWNERSHIP  
**Checkpoint:** OV-001

## Context

Projects, Mission Work Items, Process Instances, and future Tasks need economic
visibility, but each already owns a distinct operational lifecycle. Embedding revenue,
cost, cash, and forecast fields in each aggregate would duplicate truth, create
incompatible semantics, and make cross-subject reporting unreliable.

## Proposed Decision

Create an Operational Economics core that owns append-only `EconomicFact`, correction
lineage, roll-up membership, metric policy, and derived metric snapshots. Operational
subjects remain foreign references. Their owners retain lifecycle and mutation
authority.

The core is operational, not accounting. Accounting, payroll, payment, procurement,
and invoicing systems remain external authorities reached through provenance-bearing
adapters.

## Consequences

- One fact model supports Project, Work, Process, and future Task without copying
  monetary fields into every aggregate.
- Facts are historically explainable and tenant-scoped.
- Accounting adapters can be added without making external ledgers canonical Yarvis
  truth.
- A future implementation must provide append-only database protection and governed
  correction semantics.

## Rejected Alternatives

- Per-aggregate revenue/cost/cash columns.
- Making Mission Work Timeline the economics ledger.
- Treating accounting-system records as canonical operational truth.
- Introducing ERP, invoice, tax, payroll, or general-ledger behavior in the MVP.
