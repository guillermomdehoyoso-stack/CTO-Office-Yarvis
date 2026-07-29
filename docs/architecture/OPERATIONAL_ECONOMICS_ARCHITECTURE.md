# Operational Economics Architecture

**Status:** Draft for Ratification  
**Checkpoint:** OV-001  
**Authority:** Derived from the Yarvis Constitution, Reality Graph, Identity and Governance Model, Platform Engineering Overview, Context Interaction Model, and Application Architecture.  
**Purpose:** Define a small, cross-cutting Operational Economics core that makes economic operating conditions traceable and comparable without becoming accounting or ERP.

> **Operational Economics records economically relevant operational facts, derives governed metrics from them, and never substitutes for an accounting ledger.**

## 1. Scope and Position

Operational Economics is a proposed cross-cutting core. It records the economic
meaning of work while preserving the canonical owner of the underlying Project,
Mission Work Item, Process Instance, or future Task. It does not own project
lifecycle, work status, process state, task state, contracts, invoices, payments,
general ledger postings, tax treatment, or legal accounting truth.

```text
Operational subject owner
  -> authorized Economic Fact command
  -> append-only Economic Fact
  -> governed metric projection
  -> Decision Intelligence / Mission Control

Accounting or payment systems
  -> anti-corruption adapter
  -> provenance-bearing Economic Fact
```

The proposed core belongs beside the existing Operational Domain Context family. It
consumes explicit references and governed events; it does not receive write access to
foreign aggregates.

## 2. Canonical Ownership

| Reality | Canonical owner | Operational Economics responsibility |
| --- | --- | --- |
| Project lifecycle and hierarchy | Relevant operational domain | Reference a Project as an economic subject or roll-up scope. |
| Mission Work lifecycle, priority, assignment, Timeline | Mission Control / Mission Work | Reference Work; publish derived economics only as a projection. |
| Process lifecycle and stage | Process | Reference Process Instance; never transition it. |
| Future Task lifecycle | Future Task owner | Reference Task under the same rules. |
| Economic assertion, correction lineage, metric definition, roll-up policy | Operational Economics | Own and govern these records. |
| Accounting entries, invoices, tax books, settlement authority | External accounting/payment owner | Translate observed evidence; never replace source accounting authority. |

An `EconomicFact` is the sole canonical Yarvis assertion of one economic measure in
one operational scope. It may reference foreign objects, but those references never
transfer their ownership.

## 3. Proposed Domain Model

### 3.1 EconomicFact

`EconomicFact` is immutable, tenant-scoped, evidence-bearing, and append-only.

| Field | Meaning |
| --- | --- |
| `economic_fact_id` | Stable fact identifier. |
| `organization_id` | Tenant boundary. |
| `economic_subject_type`, `economic_subject_id` | One canonical operating subject: Project, MissionWorkItem, ProcessInstance, or future Task. |
| `economic_kind` | `revenue`, `cost`, `labor_cost`, `cash_in`, or `cash_out`. |
| `economic_state` | `expected`, `contracted`, `estimated`, `committed`, `incurred`, or `forecast_to_complete`, as allowed by kind. |
| `amount`, `currency` | Signed economic quantity and declared currency. Positive amounts are required; direction is expressed by kind. |
| `effective_at`, `recorded_at` | Valid time in operational reality and record time in Yarvis. |
| `source_type`, `source_id` | Provenance source, including a future accounting adapter identity. |
| `evidence_references` | Evidence or source artifacts supporting the assertion. |
| `actor_subject_id`, `authority_scope` | Accountable actor and authority basis. |
| `correlation_id`, `causation_id` | Cross-context traceability. |
| `supersedes_fact_id`, `correction_reason` | Optional immutable correction lineage. |
| `metadata` | Restricted, non-authoritative operational detail. |

Allowed initial combinations are deliberately small:

| Economic kind | Allowed states | Meaning |
| --- | --- | --- |
| `revenue` | `expected`, `contracted` | Anticipated or committed commercial value; not cash. |
| `cost` | `estimated`, `committed`, `incurred`, `forecast_to_complete` | Non-labor cost at its known operational state. |
| `labor_cost` | `estimated`, `committed`, `incurred`, `forecast_to_complete` | Time or labor valuation, with quantity/rate provenance when available. |
| `cash_in` | `incurred` | Observable received cash. |
| `cash_out` | `incurred` | Observable paid cash. |

`expected` and `contracted` revenue are distinct. Cash is distinct from revenue and
cost. A payment, settlement, or bank movement is not silently interpreted as revenue
or cost without an explicit fact and source classification.

### 3.2 EconomicRollupMembership

`EconomicRollupMembership` is an explicit, temporal, tenant-scoped parent relation
between economic subjects. It is not inferred from a Process/Work association,
assignment, visibility, or UI nesting.

| Field | Meaning |
| --- | --- |
| `membership_id` | Stable membership identifier. |
| `organization_id` | Tenant boundary. |
| `child_subject_type`, `child_subject_id` | Subject whose facts may contribute upward. |
| `parent_subject_type`, `parent_subject_id` | Roll-up scope. |
| `rollup_dimension` | Initially `operational`. Future dimensions require explicit ratification. |
| `effective_from`, `effective_to` | Validity interval. |
| `recorded_at`, `provenance`, `authority` | Accountable temporal lineage. |
| `supersedes_membership_id` | Optional replacement lineage; no destructive edit. |

The MVP permits at most one active parent per child per roll-up dimension. A Project
can therefore aggregate Work, Process, or Task economics through explicit membership,
without creating a diamond or an implicit many-path roll-up.

### 3.3 EconomicMetricSnapshot

`EconomicMetricSnapshot` is a derived, rebuildable read model. It stores a metric
result, calculation policy/version, input fact identities, scope, currency,
as-of time, freshness, and provenance. It is never an alternative fact source and
may be deleted and rebuilt without deleting Economic Facts.

## 4. Invariants

1. Economic Facts are append-only. Correction, reversal, or reclassification creates
   a new fact linked to prior history; it never mutates or deletes a prior fact.
2. Every fact has one Organization, one economic subject, one kind/state combination,
   one currency, valid/recorded time, source provenance, and accountable authority.
3. A foreign subject must belong to the same Organization; a missing or cross-tenant
   subject is concealed as `404`.
4. A Process/Work link is not an economic roll-up membership. Economic contribution
   needs its own governed membership or an explicit subject-level fact.
5. A child has no more than one active parent in the same roll-up dimension. A fact is
   included once per requested scope, by fact identity, never once per relationship
   path or screen.
6. A fact directly recorded on a parent is not re-recorded on its child or ancestor.
   Related-object references are informational only and do not create a second fact.
7. A metric must state its fact-selection policy, currency handling, as-of time, and
   missing-data condition. Unknown is not zero.
8. Cash, revenue, cost, labor cost, forecast, and accounting evidence remain distinct.
9. Cross-currency aggregation is unavailable in the MVP unless a policy-approved FX
   fact or adapter supplies a traceable conversion. It must not silently add amounts.
10. Operational Economics never creates accounting postings, invoice status, payment
    authorization, tax liability, or legal financial truth.

## 5. Metric Semantics

Metric definitions are canonicalized in
[Operational Economics Metric Catalog](OPERATIONAL_ECONOMICS_METRIC_CATALOG.md).
The core calculation policy is:

```text
revenue_basis = contracted revenue when present; otherwise expected revenue
projected_total_cost = incurred cost + current cost to complete
expected_final_profit = revenue_basis - projected_total_cost
expected_final_margin = expected_final_profit / revenue_basis
current_net_cash = cash in - cash out
```

`current cost to complete` is a current forecast, not the historical sum of every
forecast. `current` selection follows correction/supersession lineage and declared
as-of time. The model does not assume that incurred cost plus original estimate is a
valid projected total; doing so would double-count completed work.

## 6. Roll-up and Double-counting Rules

1. A query identifies one scope, one roll-up dimension, a fact-selection policy, an
   as-of time, and one currency.
2. It selects direct facts for the scope plus facts of descendants reachable through
   active, temporally valid roll-up memberships.
3. It deduplicates by `economic_fact_id`, not by amount, description, or source text.
4. The single-active-parent invariant prevents the same descendant from arriving by
   two operational paths. Invalid cyclic membership is rejected.
5. The query never adds a Project fact merely because the fact also references a Work
   under that Project. Only the fact's economic subject and roll-up membership decide
   contribution.
6. A fact superseded by a correction is excluded from current-value metrics but stays
   in historical/audit metrics. Reversals use an explicit relationship and are shown
   in lineage.
7. Roll-up output identifies included fact IDs, excluded facts, missing currencies,
   policy version, and freshness so a consumer can explain its total.

## 7. Contracts and Authorization (Proposed)

No contract ID is added to the ratified catalog until this checkpoint is ratified.
The proposed public surface is:

| Interaction | Required authority | Purpose |
| --- | --- | --- |
| RecordEconomicFact | `economics.fact.record` | Create an append-only fact for an authorized subject. |
| CorrectEconomicFact | `economics.fact.correct` | Create a superseding or reversing fact with rationale. |
| DefineEconomicRollupMembership | `economics.rollup.manage` | Create temporal roll-up membership. |
| CloseEconomicRollupMembership | `economics.rollup.manage` | End a membership without deleting history. |
| RetrieveOperationalEconomics | `economics.read` | Return governed metrics, inputs, gaps, and freshness. |
| RetrieveEconomicFactHistory | `economics.read` | Return authorized append-only fact lineage. |

The target Operational Economics boundary validates the principal Organization and
authority. It exposes `404` rather than `403` for another tenant's subject or fact,
unless governance later explicitly defines a safe discoverability exception.

## 8. Events and Projections

Economic Facts and memberships produce owner-governed Domain Events. Metric snapshots
and Mission Control indicators consume those events as projections. They do not feed
back to mutate Project, Work, Process, or Task state.

See [Operational Economics Event Map](OPERATIONAL_ECONOMICS_EVENT_MAP.md).

```text
EconomicFact / Membership mutation
  -> Economic DomainEvent (same Unit of Work)
  -> Economics metric projector
  -> EconomicMetricSnapshot
  -> governed Decision / Mission Control projection
```

## 9. Future Accounting and Payment Adapters

An adapter translates an external accounting, payroll, procurement, banking, or
payment-system observation into a provenance-bearing Economic Fact. It must retain:
external system identity, external record identity, observed time, source artifact or
evidence, mapping policy/version, currency, and confidence/verification state.

Adapters cannot overwrite a fact, assign economic authority to an external system,
or treat an import as an accounting reconciliation. Reconciliation, chart of accounts,
invoices, taxes, payable/receivable subledgers, and settlement execution remain out of
scope unless separately designed.

## 10. Migration and Compatibility Assessment

No runtime migration is proposed by OV-001. A future implementation should add one
linear migration after the then-current Alembic head, creating Economic Facts,
roll-up memberships, source/idempotency uniqueness, tenant/scope/as-of indexes, and
append-only database protection. It must not reinterpret historical Project, Mission
Work, Process, Task, DomainEvent, or MissionWorkEvent rows.

Compatibility rules:

- Existing Project, Work, and Process APIs remain unchanged.
- Existing event payloads remain valid; economics consumes explicit references or
  new events only after contract ratification.
- Existing Mission Work Timeline remains operational evidence; an economics snapshot
  may be referenced or projected later, but is not backfilled as hidden Work facts.
- Unknown historical financial information stays unknown. No inferred zero-value facts
  or speculative backfill is permitted.

## 11. Non-goals

This core is not an ERP, general ledger, invoicing system, tax engine, payroll
system, procurement system, payment processor, budgeting suite, forecasting model,
or automatic financial-close mechanism. It does not define a database, queue,
framework, vendor, UI, report layout, FX provider, accounting policy, or vertical
process template.

## 12. Ratification Criteria

Ratification requires agreement that the core preserves singular ownership,
append-only evidence, explicit authority, tenant isolation, roll-up transparency,
currency safety, no-double-counting rules, and accounting-boundary separation.

## Closing Statement

Operational Economics makes cost, revenue, cash, forecast, and margin visible as
traceable operating reality. It gives Yarvis a disciplined economic lens without
confusing operational decision support with accounting truth.
