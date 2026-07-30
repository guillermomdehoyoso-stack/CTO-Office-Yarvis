# Operational Economics Event Map

**Status:** Implemented fact/correction event evidence; deferred entries are explicitly marked.
**Checkpoint:** OV-001 design / OV-002 implementation
**Authority:** [Operational Economics Architecture](OPERATIONAL_ECONOMICS_ARCHITECTURE.md)

The fact events below are implemented as canonical interaction contracts by OV-002.
Membership and snapshot entries remain deferred and are not runtime events.

| Proposed event | Owner | Source assertion | Required payload minimum | Consumers |
| --- | --- | --- | --- | --- |
| `economic_fact.recorded` | Operational Economics | An immutable fact was accepted. | fact ID, organization, subject, kind, state, amount, currency, effective/record time, source, actor, authority, correlation/causation. | Authorized audit views; future projections. |
| `economic_fact.corrected` | Operational Economics | A new fact supersedes another fact. | prior and new fact IDs, rationale, corrected measure, provenance, authority. | Authorized audit views; future projections. |
| `economic_rollup_membership.created` | Deferred | A child may contribute to one parent scope. | Not implemented. | Future metric projector. |
| `economic_rollup_membership.closed` | Deferred | Contribution interval ended without history deletion. | Not implemented. | Future metric projector. |
| `economic_metric_snapshot.refreshed` | Deferred projection | A derived metric view was refreshed. | Not implemented. | Future Mission Control/Decision consumers. |
| `economic_metric_snapshot.unavailable` | Deferred projection | Required metric inputs cannot support a result. | Not implemented. | Future Mission Control/Decision consumers. |

## Projection Rules

1. The implemented fact/correction mutation and its source DomainEvent commit in one
   local Operational Economics Unit of Work.
2. Current direct summaries are synchronous deterministic queries, not snapshots or
   cross-subject projections.
3. Future projections must consume source identity idempotently and carry contributing
   fact identities, policy, scope, currency, as-of time, and freshness.
4. Mission Control and Decision Intelligence may not mutate Economics, Project, Work,
   Process, or Task state from a projection alone.
5. Technical retries, transport diagnostics, and adapter processing noise are not
   operating economic events unless they assert a governed economic fact.
