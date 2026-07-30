# ADR — Operational Economics Fact Ownership

**Status:** Accepted for implemented EconomicFact scope; roll-up/snapshot extensions remain deferred.
**Decision:** ADR-OPERATIONAL-ECONOMICS-FACT-OWNERSHIP  
**Checkpoint:** OV-001

## Context

Projects, Mission Work Items, Process Instances, and future Tasks need economic
visibility, but each already owns a distinct operational lifecycle. Embedding revenue,
cost, cash, and forecast fields in each aggregate would duplicate truth, create
incompatible semantics, and make cross-subject reporting unreliable.

## Decision

Operational Economics owns append-only `EconomicFact` and correction lineage.
Operational subjects remain foreign references and retain lifecycle/mutation
authority. OV-002 implements direct-subject facts and summaries; roll-up membership,
metric snapshots, and adapters remain future scoped capabilities.

The core is operational, not accounting. Accounting, payroll, payment, procurement,
and invoicing systems remain external authorities reached through provenance-bearing
adapters.

## Consequences

- One fact model supports Project, Work, Process, and future Task without copying
  monetary fields into every aggregate.
- Facts are historically explainable and tenant-scoped.
- Accounting adapters can be added without making external ledgers canonical Yarvis
  truth.
- The implemented database protects facts against update/delete and correction uses
  supersession lineage.

## Rejected Alternatives

- Per-aggregate revenue/cost/cash columns.
- Making Mission Work Timeline the economics ledger.
- Treating accounting-system records as canonical operational truth.
- Introducing ERP, invoice, tax, payroll, or general-ledger behavior in the MVP.
