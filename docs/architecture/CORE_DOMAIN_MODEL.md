# YARVIS
# Core Domain Model

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution, Yarvis Reality Graph, and Metamodel
**Applies to:** Canonical operational concepts shared by all bounded domains

---

# 1. Purpose

The Core Domain Model defines the first operational specialization of the Yarvis Metamodel. It provides a canonical model for representing operational work without redefining the universal concepts established by the Constitution, the Yarvis Reality Graph (YRG), the Identity & Governance Model, or the Metamodel.

Its purpose is to ensure that every future domain can describe who is involved, what exists, what happened, what is known, what is intended, what was decided, and what was executed within one coherent operational reality.

This document is implementation-neutral. It defines domain meaning and invariants, not schemas, APIs, services, code, or storage.

---

# 2. Position within the Architecture

The Core Domain Model is derived from the foundational hierarchy:

```text
Yarvis Constitution
    ↓
Yarvis Reality Graph (YRG)
    ↓
Yarvis Metamodel
    ↓
Identity & Governance Model
    ↓
Core Domain Model
    ↓
Bounded Domain Models
    ↓
Implementation
```

**Operational Reality Graph** names the architectural pattern: a coherent representation of operational reality.

**Yarvis Reality Graph (YRG)** names Yarvis's canonical representation of that pattern. The Core Domain Model enriches the YRG; it does not create a second graph or source of truth.

---

# 3. Domain Philosophy

Operational work is not defined by a task list or a source application. It is defined by real actors, things, facts, and intentions in context.

The Core Domain Model organizes these four conceptual groups:

| Group | Question | Purpose |
| --- | --- | --- |
| Actors | Who participates or has authority? | Connect work to canonical identity and explicit governance. |
| Things | What exists or is operated? | Represent operational context, resources, assets, sites, and cases. |
| Facts | What happened or is known? | Preserve events, observations, evidence, knowledge, provenance, and confidence. |
| Intentions | What should happen next? | Represent goals, constraints, risk, opportunity, recommendations, decisions, and work. |

The model preserves the ratified conceptual sequence:

```text
Reality
    ↓
Observation
    ↓
Evidence
    ↓
Knowledge
    ↓
Understanding
    ↓
Decision
    ↓
Execution
```

In this model, **Understanding** is the contextually interpreted operational meaning of Knowledge. It is not a replacement for Knowledge and must remain traceable to the Evidence and reasoning that support it.

**Execution** is the attributable performance of authorized Actions, Tasks, and Workflows. It does not imply success; an Outcome must be observed separately.

---

# 4. Universal Concepts Used by the Core Domain

The Core Domain uses, and does not redefine, the following Metamodel concepts:

| Core use | Metamodel concept | Core interpretation |
| --- | --- | --- |
| Canonical participant | Party | The identity of a Person or Organization involved in operations. |
| Organizational context | PartyGroup | A meaningful grouping relevant to work, without assumed authority. |
| Legitimate authority | Authority, GovernanceRelationship | Explicit authority to decide, approve, represent, direct, or execute. |
| Operational connection | Relationship | A meaningful connection among actors, things, and contexts. |
| Work setting | Context, Site | The operational situation and place in which work occurs. |
| Operated thing | Resource, Asset | A usable resource or lifecycle-bearing operational asset. |
| Historical record | Event, Observation, Evidence | What occurred, was observed, or supports a claim. |
| Operational understanding | Knowledge, Provenance, Confidence | Evidenced interpretation with traceability and uncertainty. |
| Direction and control | Intent, Goal, Constraint, Policy | Desired outcome and the conditions governing it. |
| Decision intelligence | Risk, Opportunity, Recommendation, Decision | What may matter, what is proposed, and what was authorized. |
| Work and result | Action, Task, Workflow, Outcome | Authorized execution and its observed effect. |
| Continuity | State, Timeline | Derived condition and ordered operational history. |

---

# 5. Core Aggregate Roots

Aggregate roots are conceptual boundaries for maintaining coherent operational meaning. They do not prescribe persistence, transactions, or code structure.

## Operational Context

**OperationalContext** specializes the Metamodel Context. It is the primary container for related work, facts, intentions, and timeline entries concerning a bounded operational matter.

An OperationalContext may be specialized by a future bounded domain as a Project, Case, Service Engagement, Site Operation, Opportunity, Incident, or another domain-specific context. Such specializations must retain their relationship to Parties, governance, facts, intentions, and time.

## Work Item

**WorkItem** specializes Task. It represents accountable operational work within an OperationalContext.

A WorkItem shall identify its accountable Actor, intended completion condition, governing constraints and policies, and relevant authority. It may be coordinated through a Workflow. It must not imply that the accountable Actor has authority beyond an explicit GovernanceRelationship or authorized Capability.

## Decision Record

**DecisionRecord** specializes Decision. It preserves an authorized selection, deferral, rejection, or escalation of a course of action within an OperationalContext.

A DecisionRecord shall retain rationale, authority, supporting Evidence, expected impact, relevant constraints, and decision time. It must not be replaced by a Recommendation or inferred from a subsequent Action.

## Knowledge Record

**KnowledgeRecord** specializes contextualized Knowledge for an OperationalContext. It relates validated Facts, Inferences, Evidence, Confidence, and Provenance without collapsing them into one assertion.

A KnowledgeRecord may support Understanding, Recommendations, and Decisions. It must not convert an Inference into a Fact without validation.

---

# 6. Relationships

The Core Domain requires the following relationships to be explicit:

- An OperationalContext is related to one or more relevant Parties, PartyGroups, Sites, Resources, Assets, or other contexts.
- A Party's authority within an OperationalContext is expressed only through GovernanceRelationship and applicable Policy.
- A WorkItem belongs to an OperationalContext and is accountable to an Actor.
- A DecisionRecord belongs to an OperationalContext and is made by an authorized Actor.
- A KnowledgeRecord belongs to an OperationalContext and is supported or challenged by Evidence.
- An Asset or Resource may be situated at a Site and operated, controlled, owned, or represented by different Parties through distinct Relationships.
- A Workflow coordinates WorkItems and Actions; it does not grant authority by itself.

Membership, ownership, control, representation, responsibility, and operational participation are separate relationships. The Core Domain shall not infer one from another.

---

# 7. Events

Events are immutable historical facts in the sense defined by the Metamodel. The Core Domain uses Events to preserve that something happened, or that an assertion was made, in an OperationalContext.

Core event families include:

- Context established, changed, suspended, or closed.
- Relationship asserted, confirmed, superseded, or revoked.
- Asset or Resource assigned, installed, transferred, inspected, or retired.
- Observation received, Evidence attached, or Knowledge validated.
- Risk or Opportunity identified, changed, or resolved.
- Recommendation issued, Decision made, Action authorized, or Action performed.
- WorkItem created, accepted, blocked, completed, cancelled, or escalated.
- Outcome observed or corrected.

Event names may be specialized by a bounded domain. Events shall retain valid time, record time, provenance, and relevant operational context. Correction or supersession shall create new historical records rather than rewrite history.

---

# 8. Decisions

Decision intelligence is a distinct part of the Core Domain:

```text
Knowledge and Understanding
    ↓
Risk / Opportunity assessment
    ↓
Recommendation
    ↓
Authorized Decision
    ↓
Authorized Action
    ↓
Observed Outcome
```

A Recommendation may be generated by a human or Artificial Intelligence. It is advisory until an authorized Decision is made.

A Decision may approve, reject, defer, escalate, or otherwise select a course of action. It shall identify the decision-maker's authority, rationale, evidence, expected impact, constraints, and temporal applicability.

---

# 9. Work Management

Work management is the coordination of authorized execution within OperationalContext.

**Action** describes an attributable attempt to act. **WorkItem** specializes Task and makes accountable work visible. **Workflow** coordinates WorkItems and Actions under applicable policies and constraints. **Outcome** records what was actually observed.

Work management shall preserve the distinction between planned work, authorized work, performed work, and achieved outcome. A completed WorkItem does not prove a desired Outcome without corresponding evidence.

---

# 10. Knowledge Objects

The Core Domain uses the following knowledge objects:

- **Observation:** an incoming perception, measurement, assertion, or extraction about an OperationalContext.
- **Evidence:** an Observation or set of Observations supporting or challenging a claim.
- **KnowledgeRecord:** contextualized and evidenced understanding represented as Facts or Inferences.
- **Understanding:** the operational interpretation drawn from Knowledge in a specific Context; it remains explainable through Evidence, Provenance, and Confidence.
- **Recommendation:** an explainable proposal that uses Understanding but does not create authority.

Documents, conversations, external reports, events, and human confirmations may supply Observations. They are not automatically Facts. Conflicts and unresolved identity shall remain visible rather than being silently normalized.

---

# 11. Operational Context

Operational Context is the shared layer in which resources, assets, sites, projects, cases, and opportunities are modeled. They are not independent YRG layers.

- **Assets** and **Resources** are things with operational use or lifecycle.
- **Sites** are places where operational activity occurs.
- **Projects** and **Cases** are domain specializations of OperationalContext.
- **Opportunities** are potential beneficial conditions associated with Goals, Context, and Decision Intelligence.

Every such specialization shall remain connected to relevant Parties, GovernanceRelationships, Facts, Intentions, State, Timeline, and Provenance.

---

# 12. Temporal Model

The Core Domain applies the Metamodel's temporal model to every material assertion:

- **Valid time** expresses when something was true, applicable, or effective in operational reality.
- **Record time** expresses when Yarvis learned, received, or recorded it.

OperationalContexts, Relationships, WorkItems, Decisions, State, and KnowledgeRecords shall preserve temporal applicability and change history. State is derived from Events and Observations; it shall not silently overwrite historical facts.

Timelines order the material Events, Observations, Decisions, Actions, Outcomes, corrections, and supersessions related to an OperationalContext.

---

# 13. Domain Invariants

- The Core Domain shall extend the YRG and must not create an isolated representation of reality.
- Party and PartyGroup retain the meanings defined by the Identity & Governance Model.
- Authority is explicit, evidenced, scoped, and temporally applicable.
- An OperationalContext does not grant authority; governance does.
- Observations are distinct from Evidence; Evidence is distinct from Knowledge.
- Facts are distinct from Inferences; Inferences retain confidence and provenance.
- Recommendations are distinct from Decisions; Decisions are distinct from Actions; Actions are distinct from Outcomes.
- Events are immutable; corrections and supersessions create new records.
- State is derived from Events and Observations.
- Every material knowledge claim, decision, and outcome retains appropriate provenance and temporal context.
- Every Action is attributable to an Actor or authorized automation.

---

# 14. AI Reasoning Rules

Artificial Intelligence may propose classifications, links, probable relationships, contradictions, risks, opportunities, confidence estimates, and Recommendations.

Artificial Intelligence may assist in forming Understanding from Knowledge when the underlying Evidence, Provenance, Confidence, and reasoning remain inspectable.

Artificial Intelligence must not create canonical Parties, infer Authority as fact, silently merge identity, invent Evidence, erase Provenance, rewrite Events, convert Inference into Fact without validation, make an authorized Decision, or execute outside explicit authority.

---

# 15. Domain Extension Rules

Future bounded domains shall specialize the Core Domain rather than duplicate it.

For example, a Payments domain may specialize OperationalContext as Merchant Operation, Site as Store, Asset as Terminal, and WorkItem as Recovery Task. An Energy domain may specialize OperationalContext as Solar Project, Asset as PV Plant, and WorkItem as Field Intervention. These examples preserve the common semantics while allowing domain-specific rules.

Every extension shall:

- map its terms to the Metamodel and Core Domain concepts;
- preserve canonical identity and explicit governance;
- preserve Evidence, Provenance, Confidence, State, and Timeline;
- distinguish facts, inferences, recommendations, decisions, actions, and outcomes;
- enrich the YRG instead of creating a competing domain reality.

---

# 16. Closing Statement

The Core Domain Model provides the shared operational language for every future Yarvis domain.

It connects Actors, Things, Facts, and Intentions in the Yarvis Reality Graph so that operational work remains explainable, historically continuous, governed by explicit authority, and directed toward better decisions.
