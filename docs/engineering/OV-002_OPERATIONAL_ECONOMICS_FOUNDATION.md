# OV-002 — Operational Economics Foundation

**Status:** Implemented backend thin slice — pending validation evidence  
**Authority:** OV-001 Operational Economics Architecture and its ADRs

## Purpose

OV-002 establishes one tenant-scoped, append-only source of operational economic
facts. It does not make Yarvis an accounting system, ERP, payment processor, or
financial-close system.

## Implemented Scope

- `EconomicFact` records one positive monetary assertion for one Project, Mission
  Work Item, Process Instance, or future Task-compatible subject reference.
- Facts record effective time, source type/reference, evidence references, actor,
  authority, correlation, causation, and idempotency metadata.
- A correction creates a new fact linked through `supersedes_fact_id`; the original
  fact is never changed or deleted.
- The database rejects updates and deletes on economic facts.
- Direct-subject summaries use one requested currency and exclude superseded facts.
- Recording/correction and their `DomainEvent` commit in the same Unit of Work.

## Public Contracts

| Contract | Endpoint | Authority |
| --- | --- | --- |
| `IC-ECONOMICS-CMD-001` | `POST /operational-economics/facts` | `economics.fact.record` |
| `IC-ECONOMICS-CMD-002` | `POST /operational-economics/facts/{id}/corrections` | `economics.fact.correct` |
| `IC-ECONOMICS-QRY-001` | `GET /operational-economics/subjects/{type}/{id}/summary?currency=...` | `economics.read` |
| `IC-ECONOMICS-QRY-002` | `GET /operational-economics/subjects/{type}/{id}/facts` | `economics.read` |

Cross-organization subjects and facts are concealed as `404`. Commands require an
idempotency key. Reusing a key with a different command payload returns the governed
conflict response.

## Deterministic Metrics

For direct facts only, and only in the requested currency:

```text
revenue basis = contracted revenue when present; otherwise expected revenue
projected total cost = incurred cost + current cost to complete
net cash position = cash in - cash out
expected final profit = revenue basis - projected total cost
expected final margin = expected final profit / revenue basis
```

The response exposes all requested component values and the included fact IDs. It
does not silently aggregate related Work, Process, Project, or future Task facts.
No FX conversion is attempted.

## Explicitly Deferred

- `EconomicRollupMembership` and all cross-subject roll-up behavior.
- Metric snapshots and projection handlers.
- FX conversion, invoices, taxes, payroll, ledger, ERP, UI, AI, and automatic
  accounting adapters.

## Validation Expectations

Focused coverage must establish append-only protection, correction lineage,
idempotent replay/conflict behavior, tenant concealment, direct-only summaries,
currency separation, and atomic fact-plus-DomainEvent persistence. The linear
Alembic head must include migration `20260729_19`.
