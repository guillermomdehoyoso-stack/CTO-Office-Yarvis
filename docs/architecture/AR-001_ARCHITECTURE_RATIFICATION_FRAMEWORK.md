# AR-001 Architecture Ratification Framework

**Status:** Ratified governance framework
**Authority:** Permanent governance process derived from the Yarvis Constitution and authority hierarchy.
**Scope:** All future architecture work, including WS, UX, PX, DI, CN, AI, and other work-package families.

## Purpose

AR-001 establishes the permanent process by which architectural proposals become implementation authority. It prevents a proposal, discovery, checkpoint, review, roadmap, or implementation artifact from being mistaken for a ratified architectural decision.

Architecture governs implementation; implementation demonstrates conformance and never silently redefines architecture.

## Lifecycle

| State | Meaning | Implementation authority |
| --- | --- | --- |
| Proposed | A bounded architectural direction under development or submitted for review. It identifies intent, scope, evidence, invariants, non-goals, and open decisions. | None. Documentation, discovery, and review only. |
| Ratified | An explicit Architecture Decision Record records approval of a specific, reviewed architectural scope and its effective version. | Only the explicitly authorized implementation work package(s), within stated scope and prerequisites. |
| Deprecated | The architecture remains historically interpretable but should not be selected for new work; a replacement or retirement path is identified. | No new implementation except approved migration, compatibility, or removal work. |
| Superseded | A later ratified decision replaces the architecture for new work while preserving historical interpretation and transition obligations. | No new implementation against the superseded scope except the approved transition. |

A document's displayed status is evidence of intent, but a ratification ADR is the authoritative approval record. AR-001 does not retroactively rewrite existing documents. The Architecture Index records the currently effective status where an ADR has ratified a proposal.

## Roles and authority

Any contributor may propose architecture, provided the proposal states its scope, source authority, ownership boundaries, invariants, non-goals, impact, and unresolved questions.

The accountable architectural steward prepares or sponsors the review. The **Architecture Authority**—the CTO Office or an explicitly documented delegate with equivalent architectural authority—may ratify through an Accepted ADR. A review may recommend ratification but cannot ratify by itself. Implementers, reviewers, product stakeholders, and automated agents may supply evidence, but may not infer approval.

A ratification ADR must identify the proposal/version, decision-maker or delegated authority, rationale, accepted risks, effective date, affected contracts/bounded contexts, and the exact implementation work package(s) authorized.

## Required path

```mermaid
flowchart LR
    Research --> Proposal
    Proposal --> Review
    Review --> ADR
    ADR --> RatifiedArchitecture["Ratified Architecture"]
    RatifiedArchitecture --> RuntimeImplementation["Runtime Implementation"]
    RuntimeImplementation --> Validation
    Validation --> Production
```

Research produces evidence, not authority. Proposal records a bounded design. Review records findings and recommendation. An Accepted ADR ratifies the reviewed proposal. Ratified Architecture authorizes only named implementation scope. Runtime Implementation must preserve the ADR and governing contracts. Validation supplies conformance evidence. Production is authorized only by the applicable operational/release governance; successful tests alone do not make architecture ratified or production-ready.

## Ratification gate

Before an ADR can ratify an architecture, the review record must establish:

- conformance with the Constitution and higher authority;
- singular ownership, explicit boundaries, and no unauthorized canonical-state transfer;
- applicable interaction contracts, authority, tenant, provenance, temporal, security, and failure implications;
- implementation scope, prerequisites, acceptance evidence, and explicit non-goals;
- migration, compatibility, and deprecation effects where applicable;
- zero unresolved BLOCKER or MAJOR findings, unless the ADR explicitly accepts a named exception with authority and containment;
- traceability from proposal to ADR and, after implementation, to validation evidence.

## Implementation-authority rule

Runtime work is authorized only when all of the following are true:

1. The relevant architecture is Ratified by an Accepted ADR.
2. The ADR names the intended implementation work package and bounds its permitted changes.
3. The current engineering gate or an explicit follow-on work package allows that implementation.
4. Required contract allocation, design/baseline, and prerequisite approvals are complete.
5. The implementation preserves the ratified ownership, authority, and non-goals.

Ratification does not authorize adjacent work. For example, ratifying document architecture and authorizing DI-002 does not authorize uploads, storage adapters, Gmail, WhatsApp, AI, frontend work, or DI-003+ scope.

## Relationship to ADRs, implementation, validation, and production

An ADR is the durable decision record that can ratify, deprecate, or supersede architectural scope. It must link to the architectural proposal and state the operational effect. Implementation creates code and migrations only within an authorized work package. Validation verifies conformance through review, tests, migrations, security checks, and operational evidence. Production requires separate release/operational approval and does not ratify unfinished or unrelated architecture.

If implementation evidence conflicts with ratified architecture, implementation must change or a new ADR must explicitly amend/supersede the architecture. Historical proposals and ADRs remain readable; they are not silently rewritten.

## Status convention for future architecture documents

Future architecture documents should include a visible Status section containing:

- lifecycle state;
- owning steward;
- authority/source documents;
- proposal or ADR identifier;
- effective date when ratified;
- implementation authorization, if any;
- supersedes/superseded-by relationship where applicable.

This convention is prospective. AR-001 does not rewrite the status metadata of existing documents.

## Records and review expectations

The Architecture Index is the navigation record for effective architectural status. The roadmap records sequence and does not itself grant implementation authority. Current State/Sprint records the active engineering gate and may constrain an otherwise ratified package. Each implementation package should cite its authorizing ADR and report conformance evidence before completion.

## Non-goals

AR-001 does not replace the Constitution, change bounded-context ownership, create a new permission system, define release policy, or ratify any architecture except where a separate Accepted ADR explicitly does so.
