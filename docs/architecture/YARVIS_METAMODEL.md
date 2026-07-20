# YARVIS
# Metamodel

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution
**Applies to:** All Yarvis Domain Models and Ontologies

---

# 1. Purpose

This Metamodel defines the universal semantic building blocks from which Yarvis domain models and ontologies shall be constructed.

It is not a business domain. It is the grammar by which business domains describe operational reality in the Yarvis Reality Graph (YRG). It defines meaning, relationships, and invariants; it does not prescribe implementation, storage, APIs, programming languages, frameworks, or deployment models.

---

# 2. Position in the Yarvis Architecture

The Yarvis Constitution is the highest architectural authority. The YRG is the canonical representation of operational reality. This Metamodel governs how every domain extends that representation.

Identity and Governance are platform infrastructure. All domains shall consume and enrich them without redefining them.

```text
Constitution
    ↓
Yarvis Reality Graph
    ↓
Metamodel
    ↓
Domain Models and Ontologies
    ↓
Implementation
```

---

# 3. Metamodel Philosophy

The Metamodel shall model reality before software. Universal concepts represent durable meaning, while domain concepts specialize that meaning for a particular operational context.

A domain may introduce a more precise term, but it must map that term to one or more universal concepts. A domain must not create a competing definition of identity, authority, evidence, decision, time, or reality.

---

# 4. Foundational Axioms

- Reality precedes software.
- Canonical identity precedes identifiers and information.
- Governance precedes legitimate execution.
- Relationships preserve organizational continuity.
- Evidence creates knowledge only when context and provenance are preserved.
- Knowledge enables decisions; decisions do not erase uncertainty.
- Events preserve history; state is derived from history and observations.
- Every domain extends the YRG; no domain may create an isolated competing representation of reality.

---

# 5. Universal Concept Categories

| Category | Universal concepts |
| --- | --- |
| Identity and Actors | Entity, Actor, Party, PartyGroup, Capability |
| Governance and Authority | Authority, GovernanceRelationship, Relationship, Role, Policy, Constraint |
| Operational Context | Context, Site, Timeline, State |
| Resources and Assets | Resource, Asset |
| Knowledge and Evidence | Event, Observation, Evidence, Knowledge, Provenance, Confidence |
| Intent and Decision | Intent, Goal, Risk, Opportunity, Recommendation, Decision |
| Execution and Outcomes | Action, Task, Workflow, Outcome |

---

# 6. Core Concepts

## Identity and Actors

**Entity** is anything that has a distinguishable existence within operational reality. It may be an actor, resource, asset, site, event, decision, or another meaningful subject.

**Actor** is an Entity capable of participation, responsibility, decision, or action. An Actor may be a human, organization, or authorized automation.

**Party** is the canonical identity of exactly one real-world Person or Organization. A Party is a specialized Actor. External identifiers, contact points, and source-system records are observations about a Party; they are not the Party itself.

**PartyGroup** is a meaningful organizational grouping of Parties. It represents context, not necessarily a legal identity. A PartyGroup is not a Party unless it is separately represented by a canonical Party.

**Capability** is an ability that an Actor or authorized automation can possess or exercise. Capability is not a Role: a Role expresses a contextual responsibility or authority relationship; Capability expresses what can be done.

## Governance and Authority

**Authority** is the explicit, evidenced legitimacy to decide, approve, represent, direct, or execute within a defined scope.

**GovernanceRelationship** expresses an Authority relationship among Parties or between a Party and a PartyGroup. It shall state its role, scope, effective period, status, evidence, provenance, and confidence.

**Relationship** is a meaningful connection between Entities. GovernanceRelationship is a specialized Relationship. Membership, ownership, control, representation, commercial association, and operational dependency are distinct relationships and must not be conflated.

Membership denotes participation; it does not imply authority, ownership, control, or responsibility. Ownership denotes economic rights; it does not imply control. Control denotes operational authority; it does not imply representation. Representation authorizes acting on behalf of another and requires explicit evidence.

**Constraint** is a condition that limits what is possible or permitted in a situation. **Policy** is a declared rule that governs behavior or decisions. A Policy may impose Constraints; a Constraint need not arise from a Policy.

## Operational Context and Resources

**Context** is the set of relationships, conditions, and scope that makes an Entity, Event, Observation, Decision, or Action meaningful. Operational Context includes where work occurs, for whom, under which relationships, and during which period.

**Resource** is anything available for use, consumption, allocation, or stewardship. **Asset** is a Resource with an identifiable lifecycle, stewardship, value, or operational role. Every Asset is a Resource; not every Resource is an Asset.

**Site** is a location or operational place where activity occurs. A Site is not a Party, and an address is not identity.

## Knowledge and Evidence

**Event** is an immutable historical fact that something occurred or was asserted to have occurred. An Event records its occurrence and shall not be rewritten; later correction is represented by another Event or Observation with its own provenance.

**Observation** is a recorded perception, measurement, assertion, or extraction about reality, including source-system information. It may be incomplete, conflicting, or uncertain.

**Evidence** is an Observation or collection of Observations that supports or challenges a claim. Evidence must preserve provenance and must not be invented.

**Knowledge** is contextualized, interpreted, and evidenced understanding. Knowledge shall distinguish a validated Fact, an Inference, a Recommendation, and a human or authorized Decision. Evidence is not automatically Knowledge.

**Provenance** identifies how information entered Yarvis: its source, origin, derivation, relevant time, and transformation or confirmation history.

**Confidence** expresses the justified degree of trust in an Observation, Evidence, Inference, relationship, or recommendation. Confidence is not truth and must not conceal uncertainty or conflict.

## Intent and Decision

**Intent** is a declared desired direction or purpose of an Actor. **Goal** is an intended, assessable desired outcome. Intent may be broad; a Goal is sufficiently defined to evaluate progress or completion.

**Risk** is a plausible condition or Event that may adversely affect Goals, constraints, resources, or outcomes. **Opportunity** is a plausible condition or Event that may beneficially affect them. Neither is a confirmed Outcome.

**Recommendation** is a proposed course of action, generated by a human or Artificial Intelligence, with rationale, evidence, confidence, expected impact, and applicable constraints. A Recommendation is not a Decision.

**Decision** is an authorized selection or rejection of a course of action. It shall preserve rationale, authority, supporting evidence, expected impact, relevant constraints, and decision time. A Decision is not an Action.

## Execution and Outcomes

**Action** is an attributable attempt to change, preserve, investigate, or execute operational reality. Every Action shall be attributable to an Actor or authorized automation.

**Task** is an Action with an explicit accountable actor, expected completion condition, and operational context. **Workflow** is an ordered or governed coordination of Actions and Tasks. A Workflow is not a substitute for authority.

**Outcome** is the observed result or effect following an Action, Event, Decision, or Workflow. An Outcome must not be assumed merely because an Action was initiated.

## Time and State

**State** is the current or historical condition of an Entity in a given context. State is derived from Events, Observations, and valid interpretations; it must not silently overwrite history.

**Timeline** is the ordered history of Events, Observations, Decisions, Actions, Outcomes, and state changes relating to an Entity or Context.

---

# 7. Relationships Between Concepts

The following conceptual flow is normative:

```text
Party / PartyGroup ──governed by──> GovernanceRelationship
Entity ──situated in──> Context
Resource ──specialized as──> Asset
Site ──provides──> Operational Context
Event ──is recorded through──> Observation
Observation ──supports or challenges──> Evidence
Evidence ──contextualized as──> Knowledge
Knowledge ──supports──> Recommendation or Decision
Decision ──authorizes──> Action
Action / Workflow ──produces or informs──> Outcome
Events and Observations ──derive──> State and Timeline
```

The flow is not permission to collapse concepts. A fact remains distinct from an inference; a recommendation remains distinct from a decision; a decision remains distinct from its subsequent action and outcome.

---

# 8. Temporal Model

Every material assertion shall support two conceptual times:

- **Valid time:** when the assertion was true, applicable, or effective in operational reality.
- **Record time:** when Yarvis received, recorded, or learned the assertion.

The model shall support correction, supersession, revocation, and historical interpretation without erasing earlier records. It shall preserve who or what supplied information and whether a later assertion supersedes, confirms, or conflicts with an earlier one.

---

# 9. Evidence, Provenance and Confidence

Evidence shall preserve provenance. Provenance shall remain connected to the relevant Observation, derivation, confirmation, and source.

Facts require validated evidence. Inferences shall identify their basis and uncertainty. Recommendations shall identify their evidence, reasoning, confidence, and expected impact. Conflicting evidence shall remain visible until legitimately resolved; it must not be silently overwritten.

---

# 10. Decision and Execution Model

Decision intelligence shall be progressive: evidence and knowledge may support a recommendation; an authorized Actor may make a Decision; a Decision may authorize an Action; an Action may produce an Outcome.

No Action shall be treated as authorized merely because it is recommended. No Outcome shall be treated as achieved merely because an Action was requested or initiated.

---

# 11. Domain Extension Rules

A domain model:

- shall map each domain-specific concept to one or more universal concepts;
- may specialize a universal concept with domain semantics;
- shall preserve the universal concept's invariants;
- shall attach relevant evidence, provenance, confidence, time, and context;
- shall enrich the shared YRG;
- must not redefine Party, PartyGroup, Authority, Evidence, Event, Decision, or State.

---

# 12. Domain Isolation Rules

No bounded context may create an isolated competing representation of operational reality.

Domain boundaries may protect behavior, vocabulary, and responsibilities. They must not duplicate canonical identity, infer governance without evidence, conceal material provenance, or redefine foundational concepts. Integration shall connect observations and relationships to the YRG rather than establish a new canonical reality.

---

# 13. Naming and Semantic Rules

Names shall express the real-world meaning of a concept rather than an implementation mechanism. A domain term shall be singular, unambiguous within its context, and mapped to its metamodel concept.

Terms must not use one word for materially different concepts or multiple words for the same canonical concept without an explicit relationship. Names such as “status,” “owner,” “account,” or “record” require contextual qualification when their meaning could be ambiguous.

---

# 14. Artificial Intelligence Reasoning Rules

Artificial Intelligence may propose classifications, links, identity merges, probable relationships, contradictions, recommendations, and confidence estimates.

Artificial Intelligence may not silently create canonical truth, silently merge Parties, invent Evidence, erase Provenance, rewrite historical Events, convert an Inference into Fact without validation, or execute outside explicit Authority.

Every AI contribution shall be identifiable as an inference or recommendation until validated according to the relevant Governance and Policy.

---

# 15. Domain Invariants

- A Party represents exactly one real-world Person or Organization.
- Identity belongs to the platform, not to individual modules.
- Governance is explicit and evidenced.
- Membership is not Governance; ownership is not control; control is not representation.
- Events are immutable historical facts.
- State is derived from Events and Observations.
- Evidence preserves Provenance.
- Knowledge distinguishes Fact, Inference, Recommendation, and Decision.
- Decisions preserve rationale, Authority, Evidence, and expected impact.
- Actions are attributable to an Actor or authorized automation.
- Domains may specialize universal concepts but must not contradict them.

---

# 16. Example Domain Extensions

These examples illustrate specialization rules only; they do not define those domains.

| Domain | Domain term | Metamodel specialization |
| --- | --- | --- |
| Energy | PV Plant | Asset within Operational Context |
| Energy | Solar Project | Project-like Operational Context with Goals, Constraints, Events, and Relationships |
| Payments / NetPay | Merchant | Organization Party or explicit Party role, never an inferred identity |
| Payments / NetPay | Store | Site with operational relationships and evidence |
| Payments / NetPay | Settlement | Financial Event or Financial Outcome, according to the asserted reality |
| Operational CRM / Case Management | Case | Operational Context with Events, Evidence, Decisions, and Actions |
| Operational CRM / Case Management | Chargeback | Case and Risk Event; it must preserve Evidence, provenance, and timeline |

---

# 17. Non-Goals

This Metamodel does not define database schemas, fields, APIs, services, tables, event formats, code structures, user interfaces, infrastructure, deployment, or vendor integrations.

It does not replace bounded contexts, domain models, or the need for explicit operational policy. It does not authorize automation or infer authority.

---

# 18. Ratification Criteria

This document is ready for ratification when its concepts are consistent with the Constitution, the YRG, and the Identity & Governance Model; when every current domain can map its vocabulary to the Metamodel without contradiction; and when no requirement depends on a particular implementation technology.

Any future amendment shall preserve canonical reality, explicit governance, evidence provenance, temporal continuity, and human accountability.

---

# 19. Closing Statement

The Yarvis Metamodel defines the shared language by which the platform models reality.

It exists so that every domain contributes to one coherent operational understanding: a YRG that preserves what happened, what is known, who has authority, what should happen next, and what actually occurred.
