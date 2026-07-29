# Operational Economics Phased Roadmap

**Status:** Draft for Ratification  
**Checkpoint:** OV-001  
**Authority:** [Operational Economics Architecture](OPERATIONAL_ECONOMICS_ARCHITECTURE.md)

## Phase OE-0 — Ratification and Contract Design

Ratify ownership, fact semantics, correction lineage, roll-up safety, authority scopes,
metric catalog, event map, and currency policy. Add proposed contracts to the canonical
catalog only after ratification.

**Exit:** no unresolved owner or double-counting ambiguity.

## Phase OE-1 — Economic Facts Vertical Slice

Implement tenant-scoped append-only Economic Facts for one existing operational
subject, initially Project or Mission Work only after explicit product choice. Include
provenance, idempotency, correction lineage, source-event emission, authorized reads,
and append-only database enforcement.

**Exit:** one economic fact can be recorded, corrected without mutation, retrieved
tenant-safely, and traced to source evidence.

## Phase OE-2 — Metric Projection and Roll-up

Implement explicit roll-up memberships, cycle/one-parent validation, idempotent metric
projection, metric availability states, and the OEM-001 through OEM-014 catalog for a
single currency.

**Exit:** Project and Mission Work metrics are explainable from fact identities with no
double-counting path.

## Phase OE-3 — Process and Future Task Participation

Add Process Instance and future Task as economic subjects only through the existing
fact/reference and roll-up contracts. Do not make Process/Work association an implicit
economic membership.

**Exit:** independent lifecycle tests prove that economic visibility changes neither
Process nor Work state.

## Phase OE-4 — Accounting and Payment Adapters

Add anti-corruption adapters, source mapping/version provenance, verification state,
currency conversion evidence, and reconciliation views. Keep accounting authority
external and prevent adapter imports from overwriting Yarvis facts.

**Exit:** imported facts are attributable, replay-safe, and distinguish observed cash
from revenue/cost interpretation.

## Deferred Deliberately

- General ledger, invoicing, tax, payroll, procurement, AP/AR, and statutory reporting.
- Automated financial action, payment initiation, or purchase authorization.
- Multi-parent allocations, arbitrary split percentages, and unconstrained FX.
- Financial forecasting AI, dashboards, or domain-specific Energy/NetPay economics.

## Migration and Compatibility Gates

Each implementation phase requires a new linear migration, append-only/integrity
tests, tenant concealment tests, idempotency tests, roll-up/double-count tests, and
compatibility proof that existing Project, Work, Process, Timeline, and DomainEvent
contracts remain unchanged.
