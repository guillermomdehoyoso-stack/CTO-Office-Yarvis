# Operational Economics Event Map

**Status:** Draft for Ratification  
**Checkpoint:** OV-001  
**Authority:** [Operational Economics Architecture](OPERATIONAL_ECONOMICS_ARCHITECTURE.md)

The following are proposed owner-governed events. They are not ratified interaction
contracts and must not be added to the canonical contract registry until ratification.

| Proposed event | Owner | Source assertion | Required payload minimum | Consumers |
| --- | --- | --- | --- | --- |
| `economic_fact.recorded` | Operational Economics | An immutable fact was accepted. | fact ID, organization, subject, kind, state, amount, currency, effective/record time, source, actor, authority, correlation/causation. | Metric projector, authorized audit views. |
| `economic_fact.corrected` | Operational Economics | A new fact supersedes or reverses another fact. | prior and new fact IDs, rationale, corrected measure, provenance, authority. | Metric projector, audit views. |
| `economic_rollup_membership.created` | Operational Economics | A child may contribute to one parent scope. | membership, child, parent, dimension, validity, authority. | Metric projector. |
| `economic_rollup_membership.closed` | Operational Economics | Contribution interval ended without history deletion. | membership, effective end, actor, authority, correlation/causation. | Metric projector. |
| `economic_metric_snapshot.refreshed` | Operational Economics projection | A derived metric view was refreshed. | scope, policy/version, as-of time, inputs, freshness, availability state. | Mission Control, Decision Intelligence. |
| `economic_metric_snapshot.unavailable` | Operational Economics projection | Required metric inputs cannot support a result. | scope, missing inputs/currency/policy reason, freshness. | Mission Control, Decision Intelligence. |

## Projection Rules

1. The fact or membership mutation and its source DomainEvent commit in one local
   Operational Economics Unit of Work.
2. Metric projection consumes source event identity idempotently. A retry cannot create
   a second Economic Fact or a double-counted metric contribution.
3. Projected values carry their contributing fact IDs, policy version, scope, currency,
   as-of time, and freshness.
4. Mission Control and Decision Intelligence may display or reason over projections;
   neither may mutate Economics, Project, Work, Process, or Task state from a
   projection alone.
5. Technical retries, transport diagnostics, and adapter processing noise are not
   operating economic events unless they assert a governed economic fact.
