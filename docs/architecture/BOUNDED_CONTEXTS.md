# YARVIS
# Bounded Contexts

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution and Platform Engineering Overview
**Purpose:** Define the proposed bounded-context map by assigning singular ownership of business capabilities, canonical objects, invariants, authoritative transitions, and public contracts.

> **Who is the canonical owner of this part of reality?**

> **Software boundaries exist to preserve conceptual integrity, not organizational convenience.**
>
> **Every business capability has exactly one authoritative owner.**
>
> **Contexts collaborate through explicit contracts, never through shared assumptions.**
>
> **The Reality Graph spans the platform; ownership does not.**

---

# 1. Position and Discovery Method

This document applies `PLATFORM_ENGINEERING_OVERVIEW.md`. It proposes semantic and authority boundaries; it does not prescribe screens, teams, repositories, databases, services, vendors, deployments, current code folders, or temporary workflows.

Discovery evidence: foundational concepts/invariants; capability authority; state transitions; lifecycle and temporal behavior; domain language; consistency needs; governance and regulatory sensitivity; autonomy and rate of change; external boundaries; and current workflows only as evidence, never ownership.

Candidate contexts were evaluated by authority, invariants, lifecycle, language, and consistency. Identity, Governance, Relationship, Observation, Knowledge, Decision, Execution, Automation, Mission Control, Integration, and Domain Operations were assessed; Integration is rejected as a generic truth-owning context and retained as anti-corruption boundaries. Domain Operations is retained as an extensible context family, not one universal business context.

---

# 2. Proposed Context Map

```text
Foundation contracts
    ↓
Identity ─ Governance ─ Relationship
    ↓             ↓
Observation & Evidence → Knowledge → Decision Intelligence → Execution → Automation
                                              ↓                    ↓
Operational Domain Contexts ───────────────────────────────────────┘
    ↓
Mission Control (projections and intervention handoffs)

External systems → explicit Anti-Corruption Boundaries → owning context
```

## Proposed contexts (10)

| Context | Classification | Canonical ownership rationale |
| --- | --- | --- |
| Identity | Core platform | Canonical Party, PartyGroup, identifiers, contact points, tax profiles, identity resolution. |
| Governance | Core platform | Authority, roles, policies, delegation, GovernanceRelationships. |
| Relationship | Core platform | Non-governance relationships and their temporal lifecycle. |
| Observation & Evidence | Core platform | Sources, artifacts, observations, validation, contextualization, evidence lifecycle. |
| Knowledge | Core platform | Knowledge candidates/assertions, facts/inferences, contradictions, promotion, supersession, expiration, retraction. |
| Decision Intelligence | Core platform | Situations, risks, opportunities, candidates, recommendations, approvals, decisions. |
| Execution | Core platform | Plans, authorizations, attempts, executions, execution evidence, outcomes, compensation/reversal semantics. |
| Automation | Supporting platform | Eligibility, automation-policy application, strategy, sessions, tasks, gates, automation evidence. |
| Mission Control | Supporting platform | Awareness projections, attention, priority, queues, handoffs; never governed domain truth. |
| Operational Domain Contexts | Domain context family | Customer, merchant, project, installation, case, service obligation, and domain-specific operational state where applicable. |

---

# 3. Context Definitions and Ownership

Each definition follows: `context_id`, canonical name, purpose, classification, governed reality, capabilities/objects/invariants/transitions owned, commands, queries, events, dependencies, references/projections, guarantees, sensitivities, contracts, prohibited responsibilities, boundaries, questions, status, provenance, metadata.

| Context | Owns | Does not own | Upstream / downstream |
| --- | --- | --- | --- |
| `identity` | Party, PartyGroup, external identifier mapping, ContactPoint, TaxProfile, identity resolution; identity uniqueness/integrity | Authority, non-identity relationships, knowledge, domain customer/merchant semantics | Foundation / all contexts |
| `governance` | Roles, authority, policies, delegation, governance relationships; authorization invariants | Canonical identity, decisions, executions, automation strategy | Identity / Decision, Execution, Automation, Domains |
| `relationship` | Non-governance relationship assertions/lifecycle | Party identity, governance authority, domain state | Identity, Governance / Domains, Knowledge |
| `observation_evidence` | Sources, artifacts, observations, validation, contextualization, evidence | Identity canonicalization, active knowledge, decisions | Identity, Relationship / Knowledge, Domains |
| `knowledge` | Candidates/assertions, fact/inference, contradiction, promotion, supersession, expiration/retraction | Source artifact, identity, decisions | Observation & Evidence / Decision, Mission Control, Domains |
| `decision_intelligence` | Situations, risk/opportunity, candidates, recommendations, approvals, decisions | Governance policy/authority, execution, outcomes | Knowledge, Governance / Execution, Mission Control, Domains |
| `execution` | Plans, execution authorization, attempts/records, execution evidence, outcomes, compensation/reversal | Automation eligibility/session/task, decisions, governance policy semantics | Decision, Governance / Automation, Observation & Evidence, Mission Control |
| `automation` | Eligibility, policy application, strategy, trigger/session/task/gate/timeout/suspension, automation evidence | Decisions, plans, authorization, execution evidence/outcome, policy ownership | Execution, Governance / Execution, Mission Control |
| `mission_control` | Situation/attention/priority/operator projections, queues, alerting, intervention handoffs | Canonical state, domain obligations, decisions, authorization, execution | all contexts / human intervention contracts |
| `operational_domains` | Domain-specific subjects/state/obligations and their invariants | Foundation/platform capability authority | platform contracts / Mission Control, integrations |

---

# 4. Ownership and State Transition Matrix

| Capability or object | Authoritative context | Authoritative transition / invariant |
| --- | --- | --- |
| Canonical identity, external identifiers, identity resolution | Identity | create/resolve/merge/split canonical identity; one Party per real actor |
| Roles, policies, delegation, authority | Governance | grant/revoke/delegate authority; policy lifecycle |
| Non-governance relationships | Relationship | assert/confirm/supersede relationship |
| Source/Artifact/Observation/Evidence | Observation & Evidence | acquire, validate, contextualize, promote evidence |
| Knowledge and contradiction | Knowledge | promote/dispute/supersede/expire/retract knowledge |
| Situation/Risk/Opportunity/Recommendation/Decision | Decision Intelligence | assess/recommend/approve/decide |
| Plan/Authorization/Execution/Evidence/Outcome | Execution | plan/authorize/attempt/execute/interpret outcome |
| Eligibility/Strategy/Session/Task | Automation | assess eligibility, session/task lifecycle, automation evidence |
| Attention/Priority/Queue/Intervention handoff | Mission Control | derive projection, assign awareness, hand off intervention |
| Customer/Merchant/Project/Installation/Case/obligation | Relevant Operational Domain Context | domain-specific lifecycle and obligations |

`CapabilityAssignment`, `CanonicalObjectAssignment`, `InvariantAssignment`, and `StateTransitionAssignment` each record context, assigned object/capability/invariant/transition, rationale, effective time, provenance, and status.

---

# 5. Contracts, Commands, Queries, Events, and References

`ContextCommandOwnership`: `command_id`, target owner, command purpose, required authority, transition, contract, provenance, status. `ContextQueryResponsibility`: `query_id`, answering context, projection/canonical status, freshness, uncertainty, provenance, status. `ContextEventOwnership`: `event_id`, producer owner, asserted transition, temporal/provenance semantics, consumers, status.

`ContextReferenceRule`: source/target contexts, canonical object, reference type, valid time, freshness, permitted use, prohibited mutation, provenance, status. `ContextProjectionRule`: source authority, projection, freshness/synchronization/conflict behavior, local use, prohibited mutation, provenance, status. `ContextDependencyDefinition`: dependent/dependency context, stability/authority direction, interaction mode, contract, fallback, prohibited coupling, status.

Only owners accept mutation commands; queries never mutate; events are produced by the owner asserting the transition. Consumers may project but never claim source ownership. Cross-context mutation uses explicit owner contracts.

Required public contracts include Identity Resolution and Identifier Mapping; Governance Authority/Policy/Delegation; Relationship Reference; Observation/Evidence Handoff; Knowledge Assertion; Situation/Decision; Execution Authorization/Outcome; Automation Handoff; Mission Control Projection/Intervention; and Domain Subject/Obligation contracts.

---

# 6. Dependencies, Stability, and Boundaries

Dependencies point toward greater stability. Foundation-facing contracts are more stable than domain or integration contracts. Operational Domains depend on platform contracts; platform semantics do not depend on vendor terms. Automation coordinates authorized execution but never absorbs domain ownership. Mission Control projects from many contexts but owns no governed condition.

Integration is an anti-corruption boundary pattern, not a generic domain owner. `AntiCorruptionBoundary` and `ExternalSystemBoundary` preserve translation, canonical identity, provenance, confidence, temporal meaning, and governance. External systems own no Yarvis truth.

`ContextContractSummary` preserves provider, consumer, concepts, commands/queries/events, identity/temporal/provenance/error semantics, compatibility, version, status. `ReplicationAgreement` is represented by projection rules: replication never implies ownership or alternative truth. Shared kernels are exceptional; they must exclude mutable business state, authority decisions, context invariants, workflow ownership, and vendor semantics.

---

# 7. Mission Control, Automation, and Modular Monolith

Mission Control work items project domain-owned work where an obligation already exists. Assignment transfers responsibility, never authority; escalation routes attention, never authority. Automation applies Automation Policy but Governance owns policy and authority; Execution owns execution authorization, evidence, and outcome.

**Recommended initial deployment model:** one modular monolith containing these bounded contexts, with explicit internal contracts and conformance tests. This preserves semantic boundaries now while avoiding premature distributed operational complexity. No service, database, API, broker, or deployment topology is selected.

---

# 8. Ownership Conflicts and Open Questions

`OwnershipConflict`: `ownership_conflict_id`, concept/capability, candidate owners, ambiguity source, competing invariants, authority/consistency/governance implications, recommended owner, rationale, alternatives, residual risks, resolution status, provenance, metadata.

All evaluated conflicts have a proposed owner; **open unresolved conflicts: 0**. Decisions recorded:

- Identity Resolution → Identity, because canonical Party integrity is its invariant.
- Evidence → Observation & Evidence; Knowledge receives explicit handoff.
- Situation/Risk/Opportunity → Decision Intelligence, because they frame reasoning, not Knowledge assertion.
- Policy semantics → Governance; Automation only evaluates applicability.
- Execution Authorization → Execution, bounded by Governance authority and Policy.
- Mission Control work → projections/handoffs only; domain obligations remain domain-owned.
- Relationships → separate Relationship context; Governance owns only authority relationships.
- Integrations → anti-corruption boundaries, not a truth-owning context.

---

# 9. Classification, Ratification, and Follow-On Artifacts

`ContextClassificationRecord`: context, classification, rationale, dependencies, sensitivity, provenance, status. `ContextBoundaryDecision`: context, boundary rationale, alternatives, conflicts, authority/invariant effects, provenance, status. `DomainExtensionContext`: domain, proposed context, owned reality/capabilities/invariants, platform contracts, provenance, status. `ContextRatificationRecord`: context, decision, reviewer authority, rationale, effective time, provenance, status.

Ratify in sequence: Identity and Governance; Relationship; Observation & Evidence; Knowledge; Decision Intelligence; Execution; Automation; Mission Control; then each Operational Domain Context. Next artifacts: `CONTEXT_INTERACTION_MODEL.md`, then Application Architecture, Event/Command/Query catalogs, and Technical Blueprint.

---

# 10. Invariants, Non-Goals, and Closing Statement

Every capability, canonical object, invariant, and authoritative state transition has one owner. Participation, visibility, replication, integration, automation, and projection do not create ownership. Foundation distinctions and the three operating pillars remain unchanged.

This artifact does not select technologies, deployment, services, databases, APIs, brokers, languages, frameworks, or final infrastructure. It is a proposed authority map, not an implementation plan.

Yarvis begins Platform Engineering with a comprehensible, authority-centered context map: the Reality Graph spans the platform, while each part of reality has an explicit canonical owner and contract.
