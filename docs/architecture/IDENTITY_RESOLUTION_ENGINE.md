# YARVIS
# Identity Resolution Engine

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution, Identity & Governance Model, and Platform Overview
**Purpose:** Define the canonical, implementation-neutral platform process for resolving candidate identities found in Observations to canonical entities in the Yarvis Reality Graph (YRG).

---

# 1. Purpose

The Identity Resolution Engine connects subject candidates found in Observations to canonical entities in the YRG while preserving uncertainty, provenance, temporal continuity, and human accountability.

It does not treat an external record, identifier, contact point, tax profile, name, address, email address, or phone number as identity by itself. It evaluates those items as identity signals supporting a governed resolution decision.

The Engine supports candidates concerning Persons, Organizations, Parties, PartyGroups, Sites, Stores, ClientAccounts, Assets, Projects, Cases, ContactPoints, TaxProfiles, and external platform identifiers.

---

# 2. Position in Platform Architecture

Identity Resolution follows Observation and Validation and precedes canonical attachment and downstream Contextualization.

```text
Observation
    ↓
Subject Candidate
    ↓
Identifier Extraction
    ↓
Candidate Search
    ↓
Candidate Scoring
    ↓
Resolution Decision
    ↓
Human Review when required
    ↓
Canonical Link or New Identity Proposal
    ↓
Resolution Record
    ↓
Downstream Contextualization
```

The Engine enriches the Identity, Governance, Relationships, and Operational Context layers of the YRG. It does not establish governance, discover relationships as identity facts, or create an isolated identity store.

---

# 3. Resolution Principles

- Canonical identity is independent from every single external system.
- Observations never silently create or modify canonical identities.
- Identity signals support a resolution; they are not identities by themselves.
- Multiple external records may resolve to one canonical entity.
- One external record must not resolve to multiple canonical entities for the same valid-time interval unless an explicit conflict is preserved.
- Probable and ambiguous matches are not confirmed canonical links.
- Duplicate detection is not identity merging; merging requires explicit policy and is reversible.
- Relationship discovery occurs after identity resolution and must not be confused with identity matching.
- Corrections supersede prior resolution decisions without deleting historical decisions, candidates, signals, or provenance.

---

# 4. Required Distinctions

## Identification and Authentication

**Identification** asks which canonical entity an Observation may concern. **Authentication** asks whether an Actor has proven authority or access. Identity Resolution performs identification; it must not be used as authentication or authorization.

## Identity and Role

**Identity** answers who exists. A **Role** describes a contextual responsibility, capability, or authority relationship. A Party may have multiple Roles; no Role creates or replaces identity.

## Party and PartyGroup

A **Party** is the canonical identity of exactly one Person or Organization. A **PartyGroup** is a meaningful grouping of Parties and may or may not have legal personality. A PartyGroup is not a substitute for a Party.

## Membership and Governance

Membership represents participation. Governance represents explicit authority. Membership must not be used as a matching shortcut for ownership, control, representation, responsibility, or authority.

## Identity Match and Relationship Discovery

An **Identity Match** determines whether a candidate refers to a canonical entity. **Relationship Discovery** determines how already-resolved entities may be connected. The latter requires separate evidence, governance, and review rules.

## Canonical Entity and External Record

A **Canonical Entity** belongs to the YRG and persists independently from its observers. An **External Record** is a source-specific observation or artifact and may be mapped to a canonical entity without becoming it.

## New Identity and New Observation

A **New Observation** is a newly recorded claim. A **New Identity** is a proposed or approved canonical Party or other entity after no appropriate canonical match is found. Recording a new Observation must not automatically create a new identity.

## Duplicate Detection and Identity Merging

**Duplicate Detection** identifies possible redundant canonical entities or external records. **Identity Merging** is an explicit, policy-governed and reversible decision that changes the current canonical interpretation while preserving history.

## Probable and Confirmed Match

A **Probable Match** is a non-final, confidence-bearing candidate. A **Confirmed Match** is a reviewed or policy-authorized canonical link. Probable Matches must not be treated as confirmed links.

## Identity Correction and Historical Deletion

An **Identity Correction** supersedes a prior resolution decision or interpretation. It must preserve prior history, valid time, record time, provenance, and the reason for correction. Historical deletion is prohibited.

---

# 5. Resolution Lifecycle

1. Receive an Observation containing a subject candidate or identity-relevant signal.
2. Extract identifiers and other signals with source, method, provenance, and confidence.
3. Retrieve plausible canonical and external-record candidates.
4. Evaluate signals, conflicts, context, time, and applicable policy.
5. Score or otherwise assess candidates without converting assessment into canonical truth.
6. Produce a Resolution Decision with one required outcome.
7. Require Human Review when policy or risk requires it.
8. Create a canonical link only for a Confirmed Match, or create a New Identity Proposal when no match is appropriate.
9. Persist a Resolution Record and hand the result to downstream Contextualization.

---

# 6. Subject Candidate Model

A **SubjectCandidate** is the unresolved referent named, implied, measured, or extracted in an Observation. It may describe a Person, Organization, Party, PartyGroup, Site, Store, ClientAccount, Asset, Project, Case, ContactPoint, TaxProfile, or external platform record.

Minimum conceptual schema:

| Element | Meaning |
| --- | --- |
| `subject_candidate_id` | Stable identifier for the unresolved candidate. |
| `source_observation` | Observation from which the candidate was derived. |
| `candidate_type` | Proposed entity type or types. |
| `display_representation` | Source representation used for review, without claiming canonicality. |
| `identifier_signals` | Identity signals associated with the candidate. |
| `context_signals` | Time, location, relationship, operational, or artifact context. |
| `valid_time` | When the candidate assertion was applicable, if known. |
| `provenance` | Source and derivation lineage. |
| `confidence` | Confidence in the candidate extraction, not a resolution outcome. |
| `status` | Unresolved, under review, resolved, rejected, or superseded. |

---

# 7. Identifier Model

An **IdentitySignal** is an observed characteristic that may support, challenge, or constrain a match. Signals include external platform identifiers, tax identifiers, contact points, names, addresses, account references, asset references, and contextual attributes.

External IDs, emails, phone numbers, tax IDs, addresses, and names are signals. Their reliability depends on source, validity, time, conflict, and policy; none is identity by itself.

Minimum conceptual schema:

| Element | Meaning |
| --- | --- |
| `signal_id` | Stable identifier for the signal. |
| `signal_type` | External ID, email, phone, tax ID, name, address, or other defined signal. |
| `observed_value` | Value as observed; it is not a canonical value by implication. |
| `normalization_context` | Context needed to compare representations without replacing the original value. |
| `source_observation` | Supporting Observation. |
| `valid_time` | Applicable time interval, if known. |
| `provenance` | Origin and derivation lineage. |
| `confidence` | Confidence in extraction or observation. |
| `sensitivity` | Handling requirements for the signal. |

---

# 8. Candidate Retrieval

Candidate Retrieval identifies canonical entities and relevant external records that may correspond to a SubjectCandidate. It considers entity type, IdentitySignals, valid time, operational context, and conflicting mappings.

Retrieval must be broad enough to preserve ambiguity and narrow enough to avoid treating unrelated entities as candidates. It must preserve why each candidate was retrieved and must not suppress candidates solely because their signal form differs from the source representation.

---

# 9. Match Signals

Match Signals may include:

- external platform identifiers;
- tax and legal identifiers;
- names and alternate representations;
- contact points;
- addresses and Sites;
- Asset, Store, ClientAccount, Project, or Case references;
- temporal overlap or incompatibility;
- source reliability, provenance, and human confirmation;
- known conflicts, revocations, corrections, or prior resolution decisions.

Signals must be evaluated in context. A signal that is strong for one entity type, jurisdiction, or valid-time interval may be weak or contradictory in another.

---

# 10. Scoring and Confidence

Candidate Scoring evaluates the support and challenge presented by Match Signals. It may use deterministic rules, human judgment, or AI assistance.

**Confidence** communicates the justified strength of a proposed resolution. It is not a substitute for policy, authority, evidence, or Human Review.

Scoring shall preserve signals evaluated, their direction, temporal applicability, conflicts, method, and limitations. It must not conceal uncertainty by selecting a single candidate where the evidence is ambiguous.

---

# 11. Resolution Outcomes

Every Resolution Decision shall use one of the following outcomes:

| Outcome | Meaning |
| --- | --- |
| `CONFIRMED_MATCH` | An approved or policy-authorized canonical link exists. |
| `PROBABLE_MATCH` | A plausible candidate exists but is not a confirmed link. |
| `AMBIGUOUS` | More than one candidate remains plausible or evidence conflicts. |
| `NO_MATCH` | No suitable canonical candidate was found under the current evidence. |
| `NEW_IDENTITY_PROPOSED` | A new canonical entity is proposed; it is not created silently. |
| `REJECTED` | The candidate, link, or proposal was rejected with rationale. |
| `SUPERSEDED` | A prior decision remains historical but has been replaced by a later decision. |

---

# 12. Resolution Decision Model

A **ResolutionDecision** records the evaluated outcome for a SubjectCandidate. It is distinct from an operational Decision to act; it records an identity-resolution interpretation.

Minimum conceptual schema:

| Element | Meaning |
| --- | --- |
| `resolution_decision_id` | Stable identifier for the decision record. |
| `subject_candidate` | Candidate being resolved. |
| `resolution_outcome` | Required outcome value. |
| `resolution_candidates` | Entities evaluated and their supporting or challenging signals. |
| `selected_entity` | Canonical entity only when confirmed or otherwise explicitly applicable. |
| `confidence` | Justified confidence in the outcome. |
| `decision_method` | Deterministic, human, AI-assisted, or other approved method. |
| `responsible_actor_or_system` | Accountable human, system, or authorized automation. |
| `review_history` | Required reviews, decisions, and rationale. |
| `valid_time` | Time interval to which the interpretation applies. |
| `recorded_at` | When Yarvis recorded the decision. |
| `provenance` | Supporting Observation and signal lineage. |
| `supersedes` | Prior resolution decision, if any. |

---

# 13. Human Review

Human Review is mandatory for:

- ambiguous matches;
- high-impact identities;
- conflicting tax or legal identifiers;
- merges and splits;
- governance-sensitive cases; and
- confidence below the applicable policy threshold.

Review may confirm, reject, defer, mark ambiguous, request new evidence, approve a new identity proposal, or supersede a prior decision. It shall preserve authority, rationale, time, provenance, and all evaluated candidates.

---

# 14. Canonical Entity Creation

Canonical creation is a governed response to `NO_MATCH` when a new entity is genuinely required. The Engine produces `NEW_IDENTITY_PROPOSED`; it must not silently create a Party, PartyGroup, Site, Asset, Project, Case, or other canonical entity.

Creation shall follow applicable policy, identity type requirements, review, provenance, and authority. A newly created entity begins with the evidence and unresolved uncertainty that justified the proposal; it must not be presented as historically complete.

---

# 15. External Identifier Mapping

An **ExternalIdentifierMapping** associates an external platform identifier with a canonical entity for a defined valid-time interval. It is a resolution result, not identity itself.

Minimum conceptual schema:

| Element | Meaning |
| --- | --- |
| `mapping_id` | Stable mapping identifier. |
| `external_system` | Observer or platform namespace. |
| `external_identifier` | Source-system identifier as observed. |
| `canonical_entity` | Resolved YRG entity. |
| `entity_type` | Type of canonical entity. |
| `valid_time` | Applicable interval. |
| `resolution_decision` | Decision supporting the mapping. |
| `provenance` | Source Observation and signal lineage. |
| `status` | Confirmed, conflicted, superseded, or rejected. |

Multiple external records may map to one canonical entity. One external record must not map to more than one canonical entity in the same valid-time interval unless the conflict is explicit and unresolved.

---

# 16. Merge and Split Rules

An **MergeProposal** identifies a suspected duplicate set of canonical entities and a proposed reversible consolidation. A **SplitProposal** identifies a canonical entity or prior merge that may represent more than one real-world entity.

Merges and splits require explicit policy and Human Review. They must preserve every prior identity, identifier mapping, observation, relationship, resolution decision, valid time, record time, provenance, and conflict.

Minimum conceptual MergeProposal schema:

| Element | Meaning |
| --- | --- |
| `merge_proposal_id` | Stable proposal identifier. |
| `candidate_entities` | Canonical entities considered duplicates. |
| `supporting_signals` | Evidence and conflicts supporting the proposal. |
| `proposed_surviving_interpretation` | Proposed current canonical interpretation. |
| `reversibility_plan` | How history and mappings remain recoverable. |
| `policy_basis` | Applicable authorization and policy. |
| `review_history` | Human review and rationale. |
| `status` | Proposed, approved, rejected, executed, or superseded. |

Minimum conceptual SplitProposal schema:

| Element | Meaning |
| --- | --- |
| `split_proposal_id` | Stable proposal identifier. |
| `source_entity` | Entity or prior merge under review. |
| `proposed_entities` | Proposed distinct canonical interpretations. |
| `partition_rationale` | Evidence and temporal basis for the split. |
| `history_preservation_plan` | How prior observations and decisions remain visible. |
| `policy_basis` | Applicable authorization and policy. |
| `review_history` | Human review and rationale. |
| `status` | Proposed, approved, rejected, executed, or superseded. |

---

# 17. Contradictions and Corrections

Conflicting signals, candidates, mappings, and Resolution Decisions shall coexist until resolved. The Engine shall record conflict rather than force a selection.

Corrections supersede resolution decisions and mappings without erasing prior history. A correction shall state its rationale, supporting signals, applicable valid time, responsible actor or system, and relationship to the superseded interpretation.

---

# 18. Temporal Identity

Identity is permanent, but its observed identifiers, contact points, mappings, relationships, and resolution interpretations are temporally applicable.

The Engine shall preserve:

- **valid time:** when a signal, mapping, or interpretation applied in operational reality;
- **record time:** when Yarvis learned or recorded it; and
- **supersession history:** how current interpretation differs from prior decisions.

Temporal change must not be represented as historical deletion.

---

# 19. Provenance and Auditability

Every resolution shall preserve its source Observation, candidate entities, signals evaluated, confidence, decision method, responsible actor or system, timestamps, review history, conflicts, and supersession lineage.

Auditability must support explaining why an entity was linked, why alternatives were not selected, what remained uncertain, and who authorized a consequential resolution.

---

# 20. Relationship Discovery Handoff

After identity is resolved or explicitly retained as unresolved, downstream capabilities may evaluate possible Relationships: membership, ownership, control, representation, commercial association, operational responsibility, or contextual association.

Relationship discovery is a separate process. A match between two identifiers does not establish ownership, control, membership, representation, authority, or responsibility.

---

# 21. Events Produced

The Engine produces immutable historical Events conceptually, including:

- SubjectCandidate created, updated through supersession, or rejected.
- IdentitySignal extracted, normalized, challenged, or retired through supersession.
- ResolutionCandidate retrieved or excluded with rationale.
- ResolutionDecision proposed, confirmed, rejected, conflicted, or superseded.
- ExternalIdentifierMapping proposed, confirmed, conflicted, rejected, or superseded.
- New Identity Proposal submitted, approved, rejected, or withdrawn.
- MergeProposal or SplitProposal submitted, approved, rejected, executed, or reversed.

These Events preserve history; current resolution state is derived from them.

---

# 22. Failure and Recovery

Failure to extract signals, retrieve candidates, score a match, or obtain review shall produce an explicit unresolved, failed, insufficient-data, or deferred state. It must not create a guessed canonical link.

Recovery may retry safe retrieval or scoring, collect further evidence, request Human Review, or supersede an incomplete decision. Every recovery attempt must retain provenance and must not duplicate historical decisions without explicit re-evaluation.

---

# 23. Idempotency

Repeated processing of the same Observation, SubjectCandidate, and relevant policy context shall not create accidental duplicate Resolution Decisions, mappings, merge proposals, or canonical entities.

Intentional re-evaluation is permitted when evidence, valid time, policy, method, or context changes. It shall create a traceable new or superseding interpretation rather than overwrite the earlier one.

---

# 24. Security and Access Control

Identity signals may contain sensitive personal, legal, financial, contact, or tax information. Access shall follow explicit Authority, least-necessary access, applicable Policy, and source handling constraints.

Restricted signals may be protected while preserving a safe indication that a signal, conflict, or review requirement exists. Security controls must not erase provenance, auditability, or the historical record of an authorized decision.

---

# 25. AI Responsibilities and Limits

Artificial Intelligence may extract identifiers, retrieve candidates, score matches, detect duplicates, identify conflicts, and recommend outcomes.

Artificial Intelligence may not silently merge identities, establish governance, invent identifiers, erase conflicts, create canonical truth, rewrite history, or perform an identity-sensitive or high-impact action outside explicit policy and authorization.

AI output shall remain identifiable as AI-assisted and shall retain its basis, confidence, provenance, and applicable review status.

---

# 26. Domain Extension Rules

Bounded domains may introduce domain-specific entity types, signal types, retrieval criteria, confidence policies, and review thresholds.

They must not redefine Party, PartyGroup, identity, authority, governance, canonicality, external identifier mapping, or the required Resolution Outcomes. Every extension shall preserve temporal continuity, provenance, conflict, explicit governance, and YRG integration.

---

# 27. Invariants

- Canonical identity is independent from any external system.
- Observations do not silently create or modify canonical identity.
- Identity signals are not identities by themselves.
- Probable and ambiguous matches are not confirmed canonical links.
- Canonical attachment requires Identity Resolution.
- One external record does not map to multiple canonical entities in the same valid-time interval without an explicit conflict.
- Merges and splits are policy-governed, reviewed, reversible, and historically preserved.
- Corrections supersede; they do not delete history.
- Relationship discovery follows identity resolution and remains distinct from it.
- AI does not establish canonical truth, governance, or unreviewed identity-sensitive outcomes.

---

# 28. Non-Goals

The Identity Resolution Engine is not an authentication system, authorization service, CRM, contact directory, source-system synchronization mechanism, relationship inference engine, or generic search facility.

It does not prescribe databases, search engines, machine-learning frameworks, APIs, vendors, entity storage, user interfaces, or implementation modules.

---

# 29. Ratification Criteria

This document is ready for ratification when it is confirmed to:

- preserve the Constitution's canonical Party and explicit Governance rules;
- integrate with the Observation Pipeline without treating sources as canonical truth;
- distinguish identity matching from relationship discovery and authentication;
- preserve the required outcomes, temporal continuity, provenance, conflicts, and reversibility;
- require Human Review in the defined sensitive cases; and
- remain implementation-neutral while permitting bounded-domain specialization.

---

# 30. Closing Statement

The Identity Resolution Engine allows Yarvis to connect distributed Observations to canonical operational reality without confusing identifiers with identity or probability with confirmation.

It preserves the evidence and accountability needed to explain who an Observation concerns, what remains uncertain, and why a canonical link, new identity proposal, correction, merge, or split was justified.
