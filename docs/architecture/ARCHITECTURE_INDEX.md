# YARVIS
# Architecture Index

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution
**Purpose:** Provide the canonical navigation map and authority hierarchy for Yarvis architecture.

---

# 1. Purpose

This Index is the canonical navigation map for Yarvis architecture. It identifies the authoritative reading path, the relationship between architectural layers, and the documents that are planned but not yet authoritative.

It introduces no new architectural concepts. It organizes the existing Foundation and Platform documents so that contributors can locate the governing artifact before deriving architecture, applications, or implementation.

For implementation evidence after `ws006f-operational-workspace-ui-complete`, read
[Architecture Checkpoint 002](YARVIS_ARCHITECTURE_CHECKPOINT_002.md). AC-002 does
not supersede higher authority; it supersedes AC-001 only as the current As-Is
navigation point.

---

# 2. Architectural Authority

The **Yarvis Constitution** is the highest architectural authority.

Every lower-level document shall conform to the documents above it. If a conflict exists, the higher-level document prevails. A lower-level artifact may extend a higher-level artifact only within the semantic and governance boundaries already established.

```text
Reality
    ↓
Foundation
    ↓
Operating Memory
    ↓
Operating Reasoning
    ↓
Operating Execution
    ↓
Applications
    ↓
Implementation
```

---

# 3. Document Hierarchy

```text
YARVIS_CONSTITUTION.md
    ↓
REALITY_GRAPH.md
    ↓
YARVIS_METAMODEL.md
    ↓
IDENTITY_AND_GOVERNANCE_MODEL.md
    ↓
CORE_DOMAIN_MODEL.md
    ↓
Platform capabilities
    ↓
Bounded contexts and applications
    ↓
Technical architecture and implementation
```

`FOUNDATION_V1_CANDIDATE.md` and `FOUNDATIONAL_ARCHITECTURE_REVIEW.md` govern Foundation consolidation and ratification readiness. They do not supersede the Constitution.

---

# 4. Platform Pillars

Yarvis is organized around three platform capabilities:

```text
Operating Memory
    ↓
Operating Reasoning
    ↓
Operating Execution
```

- **Operating Memory** preserves and structures operational reality from Observations through Knowledge.
- **Operating Reasoning** interprets Knowledge into governed, explainable, and authorized Decisions.
- **Operating Execution** materializes authorized Decisions and records resulting Outcomes.

The pillars operate over the Yarvis Reality Graph (YRG). They do not create competing representations of reality.

---

# 5. Document Map

## 5.1 Foundation

| Document | Role | Authority status |
| --- | --- | --- |
| `YARVIS_CONSTITUTION.md` | Highest architectural authority; mission, axioms, governance, and architectural integrity. | Foundational authority |
| `REALITY_GRAPH.md` | Defines the Yarvis Reality Graph and its stable conceptual layers. | Foundation candidate |
| `IDENTITY_AND_GOVERNANCE_MODEL.md` | Defines canonical identity and explicit authority as shared infrastructure. | Foundation candidate |
| `YARVIS_METAMODEL.md` | Defines the universal semantic grammar for domain models and ontologies. | Foundation candidate |
| `CORE_DOMAIN_MODEL.md` | Defines the first operational specialization of the Metamodel. | Foundation candidate |
| `FOUNDATION_V1_CANDIDATE.md` | Defines Foundation composition, stability, and ratification gate. | Candidate for ratification |
| `FOUNDATIONAL_ARCHITECTURE_REVIEW.md` | Records coherence review findings and required alignment decisions. | Review authority for ratification |

## 5.2 Operating Memory

| Document | Role | Authority status |
| --- | --- | --- |
| `PLATFORM_OVERVIEW.md` | Describes the conceptual operation of Yarvis as a platform. | Draft for ratification |
| `OBSERVATION_PIPELINE.md` | Defines how external source material becomes traceable Observations and Evidence. | Draft for ratification |
| `IDENTITY_RESOLUTION_ENGINE.md` | Defines resolution of subject candidates to canonical YRG entities. | Draft for ratification |
| `KNOWLEDGE_LIFECYCLE.md` | Defines promotion, review, contradiction, and preservation of Knowledge. | Draft for ratification |

## 5.3 Operating Reasoning

| Document | Role | Authority status |
| --- | --- | --- |
| `DECISION_INTELLIGENCE.md` | Defines how Knowledge becomes explainable, governed, and authorized Decisions. | Draft for ratification |

## 5.4 Operating Execution

| Document | Role | Authority status |
| --- | --- | --- |
| `EXECUTION_MODEL.md` | Defines authorized execution, execution evidence, outcomes, and feedback to Operating Memory. | Draft for ratification |
| `AUTOMATION_ENGINE.md` | Defines policy-constrained automation of authorized Execution Plans. | Draft for ratification |
| `MISSION_CONTROL_ARCHITECTURE.md` | Defines the human situational-awareness and authorized-intervention layer. | Draft for ratification |
| `OPERATING_EXECUTION_REVIEW.md` | Records the RC2 consistency review of Operating Execution. | Architecture review for RC2 |

## 5.5 Platform Structure

| Document | Role | Authority status |
| --- | --- | --- |
| `PLATFORM_ENGINEERING_OVERVIEW.md` | Defines ownership and contract rules for Platform Engineering. | Draft for ratification |
| `BOUNDED_CONTEXTS.md` | Defines the proposed bounded-context map and canonical ownership assignments. | Draft for ratification |
| `CONTEXT_INTERACTION_MODEL.md` | Defines governed interaction contracts among bounded contexts. | Draft for ratification |

## 5.6 Application and Technical Architecture

| Document | Role | Authority status |
| --- | --- | --- |
| `APPLICATION_ARCHITECTURE.md` | Defines application composition over platform capabilities and bounded contexts. | Existing artifact; consult its declared status |
| `TECHNICAL_BLUEPRINT.md` | Defines the technical blueprint derived from ratified architecture. | Existing artifact; consult its declared status |

## 5.7 Current Architecture Evidence

| Document | Role | Authority status |
| --- | --- | --- |
| `YARVIS_ARCHITECTURE_CHECKPOINT_002.md` | Current repository-evidence checkpoint for the Core after Process Runtime, Operational Economics, and Operational Workspace implementation. | Evidence-based; subordinate to ratified architecture |
| `YARVIS_AS_IS_ARCHITECTURE.md` | Current Core implementation view. | Evidence-based companion view |
| `YARVIS_TARGET_ARCHITECTURE.md` | Bounded extension constraints, not implementation authorization. | Derived target view |
| `YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md` | Implemented sequence, approved future boundaries, and technical debt. | Planning/evidence view |
| `OPERATIONAL_EXECUTION_ARCHITECTURE.md` | Accepted OE-001 Task bounded-context decisions and integration boundaries with Mission Work, Process, Timeline, and Economics. | Accepted OE-001 architecture decision |
| `ADR-OPERATIONAL-TASK-*.md` | Accepted OE-001 ownership, lifecycle/dependency, and projection/economics decisions for Operational Tasks. | Accepted OE-001 ADRs |
| `YARVIS_EXPERIENCE_ARCHITECTURE.md` | UX-001 product-experience hierarchy, cellular visual language, accessibility, and non-authoritative projection boundaries. | Proposal; not ratified implementation authority |
| `OPERATIONAL_WORKSPACE_EXPERIENCE_DISCOVERY.md` | WS-008B repository discovery and future Workspace/Document Registry decision preparation. | Discovery; not ratified implementation authority |
| `DATA_INTAKE_AND_DOCUMENT_ARCHITECTURE.md` | DI-001 provider-neutral intake, preservation, Document Registry, storage, connector, and Inbox boundary. | Ratified for DI-002 by [ADR-001](../decisions/ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md) |
| `AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md` | Permanent lifecycle, review, ADR, and implementation-authority process. | Ratified governance framework |
| `ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md` | Applies AR-001 to ratify DI-001 and authorize DI-002 only. | Accepted; implementation authority record |
| `NETPAY_DI003_C09_AMENDMENT_001.md` | Bounded Netpay DI-003 Manual Document Intake and C09 typed Radar Document Association design. | Ratified architectural design; no implementation authority |
| `ADR-013_NETPAY_DOCUMENT_INTAKE_ORGANIZATIONAL_AUTHORITY.md` | Ratifies the Netpay document design and requires F-011 organizational authority before implementation. | Accepted; no implementation authority |
| `IG-005_NETPAY_DOCUMENT_INTAKE_IMPLEMENTATION_AUTHORIZATION.md` | Candidate gate for the ratified Netpay document design. | Proposed; explicitly not authorized |
| `F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_001.md` | Principal, Membership, active-Organization, authority-envelope, and Radar-migration design. | Ratified architectural design; no implementation authority |
| `F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_002.md` | Resolves E–I authorization conflict for the existing Radar authority migration. | Ratified scope clarification; no new product capability |
| `ADR-014_PRINCIPAL_MEMBERSHIP_ACTIVE_ORGANIZATION_AUTHORITY.md` | Ownership and authority decision for F-011. | Accepted; no implementation authority |
| `F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md` | Compatible F-011 profiles for Governance authority evaluation and authority-change contracts. | Ratified contract amendment; Planned runtime |
| `F-011_IDENTITY_AUTHORITY_ENVELOPES_IMPLEMENTATION_DESIGN.md` | Reviewed F-011 persistence, authority-resolution, Radar-transition, migration, and test design. | Approved implementation design; no implementation authority |
| `IG-006_F011_IDENTITY_AUTHORITY_ENVELOPES_IMPLEMENTATION_AUTHORIZATION.md` | Candidate F-011 implementation gate. | Proposed; explicitly not authorized |

## 5.8 Architectural Decisions

Architecture Decision Records record bounded, durable decisions that refine the Foundation and Platform without contradicting them. ADRs are authoritative only within their declared scope and only when consistent with higher-level architecture.

## 5.9 Implementation

Code, configuration, tests, deployments, and operational procedures implement architecture. They are not architectural authority. When implementation conflicts with ratified architecture, implementation shall change unless an explicit architectural ratification changes the governing documents.

---

# 6. Reading Paths

## Executive / Product

1. `YARVIS_CONSTITUTION.md`
2. `REALITY_GRAPH.md`
3. `FOUNDATION_V1_CANDIDATE.md`
4. `PLATFORM_OVERVIEW.md`
5. `DECISION_INTELLIGENCE.md`

This path explains what Yarvis is, why it exists, what it represents, and how it transforms operational memory into decisions.

## Architect / Technical Lead

1. `YARVIS_CONSTITUTION.md`
2. `FOUNDATIONAL_ARCHITECTURE_REVIEW.md`
3. `REALITY_GRAPH.md`
4. `YARVIS_METAMODEL.md`
5. `IDENTITY_AND_GOVERNANCE_MODEL.md`
6. `CORE_DOMAIN_MODEL.md`
7. `PLATFORM_OVERVIEW.md`
8. `OBSERVATION_PIPELINE.md`
9. `IDENTITY_RESOLUTION_ENGINE.md`
10. `KNOWLEDGE_LIFECYCLE.md`
11. `DECISION_INTELLIGENCE.md`

This path establishes the authority hierarchy before any bounded-context, application, or technical design is derived.

## Developer / AI Coding Agent

1. `YARVIS_CONSTITUTION.md`
2. This Index
3. The relevant platform capability document
4. `YARVIS_METAMODEL.md`
5. `CORE_DOMAIN_MODEL.md`
6. `IDENTITY_AND_GOVERNANCE_MODEL.md` when identity, identifiers, authority, or relationships are involved
7. Applicable ADRs and bounded-context documents when ratified

This path ensures implementation work begins with the governing semantics and constraints rather than local code structure.

---

# 7. Change Rules

- Foundation changes require explicit architectural ratification.
- Platform documents may extend Foundation concepts but must not redefine them.
- Planned documents are not authoritative until created and ratified according to their declared status.
- Lower-level documents shall state their authority and scope.
- Superseded or legacy documents must not silently remain in the canonical reading path. They shall be explicitly marked, redirected, or removed through an authorized architectural change.
- Implementation changes must preserve the authority hierarchy and must not introduce competing canonical reality.

---

# 8. Ratification Status

The Foundation and Platform documents listed in this Index are currently candidates or drafts as declared in their own metadata. This Index does not ratify them.

Ratification proceeds through explicit architectural review. Until then, contributors shall treat the Constitution as highest authority and resolve conflicts according to the hierarchy in this document.

---

# 9. Planned Artifacts

## Phase IV — Platform Engineering

| Document | Role | Authority status |
| --- | --- | --- |
| `PLATFORM_ENGINEERING_OVERVIEW.md` | Defines the ownership and contract rules used to discover bounded contexts. | Draft for ratification |
| `BOUNDED_CONTEXTS.md` | Assigns canonical ownership, context boundaries, contracts, and dependencies. | Draft for ratification |
| `CONTEXT_INTERACTION_MODEL.md` | Defines interaction contracts, flows, and boundaries among proposed contexts. | Draft for ratification — active Phase IV artifact |
| `PLATFORM_ENGINEERING_REVIEW.md` | Records the coherence review of Phase IV ownership and interaction artifacts. | Draft for ratification — review artifact |
| `APPLICATION_ARCHITECTURE.md` | Defines modular-monolith application organization over bounded-context contracts. | Draft for ratification — active Phase IV artifact |
| `APPLICATION_ARCHITECTURE_REVIEW.md` | Records the joint coherence review of the application-structure baseline. | Draft for ratification — review artifact |
| `INTERACTION_CONTRACT_CATALOG.md` | Canonical governed registry of Command, Query, Event, and Notification semantics. | Ratification recommended by Interaction Contract Review |
| `INTERACTION_CONTRACT_REVIEW.md` | Records review and ratification recommendation for the Interaction Contract Baseline v1.0. | Draft for ratification — review artifact |
| `ARCHITECTURAL_DECISION_TRACE.md` | Traces ratified architectural decisions to required technical controls and conformance evidence. | Draft for ratification — active architecture artifact |
| `TECHNICAL_BLUEPRINT.md` | Concrete engineering mechanisms subordinate to ratified architecture, contracts, and decision trace. | Draft for Engineering Review |
| `TECHNICAL_BLUEPRINT_REVIEW.md` | Formal Engineering Review of the Technical Blueprint. | Technical Blueprint v1.0 — Ratified with Accepted MINOR Findings |

The following artifacts are planned and not yet authoritative:

1. `TECHNICAL_BLUEPRINT.md` — next artifact; subordinate to ratified architecture, Interaction Contracts, and the Decision Trace
2. `REFERENCE_IMPLEMENTATION_GUIDE.md` — follows the Technical Blueprint

Their future scope must conform to the Foundation, Operating Memory, and Operating Reasoning documents already identified here.

---

# 10. Non-Goals

This Index does not redefine architecture, select technologies, define implementation modules, prescribe APIs, replace ADRs, or approve planned artifacts.

It is a navigation and authority map, not an application, technical, or deployment architecture document.

---

# 11. Closing Statement

Yarvis architecture is read from reality and foundational meaning toward platform capabilities, applications, and implementation.

This Index keeps that path explicit so every contributor can determine which document governs a decision, what remains planned, and where new work belongs.
