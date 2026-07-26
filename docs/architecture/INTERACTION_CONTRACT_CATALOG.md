# YARVIS
# Interaction Contract Catalog

## Version 1.0

**Status:** Draft for Ratification
**Authority:** Derived from the Yarvis Constitution and ratified architectural baselines
**Purpose:** Create the canonical, governed, and versionable registry of the operational language through which Yarvis actors, contexts, modules, and external systems request action, obtain governed information, assert occurrences, or communicate non-authoritative information.

> **What is the canonical contract through which each governed Yarvis interaction is requested, answered, asserted or communicated?**

## 1. Authority, Position, Scope, and Non-Goals

> **No later artifact may redefine the semantics of a ratified artifact; it may only specialize them, implement them or demonstrate their conformance.**

This catalog follows the Reality Graph, bounded contexts, Context Interaction Model, and Application Architecture. It is the canonical registry of interaction semantics, not a transport inventory, API specification, queue/topic catalog, database design, framework choice, endpoint definition, vendor decision, or implementation plan.

```text
Reality → Bounded Context → Capability → Interaction Contract
                                      ├─ Command
                                      ├─ Query
                                      ├─ Event
                                      └─ Notification
```

It defines a complete governance model and a minimum Tier 1 baseline for **Yarvis Inbox First — Netpay Merchant Operations**. It does not invent future business operations. Tier 2 is a Draft family backlog, not ratified scope.

## 2. Canonical Interaction Contract Abstraction

An Interaction Contract has exactly one owning context and one owning capability. It communicates semantics; it never transfers ownership. Its four classifications are:

| Type | Meaning |
| --- | --- |
| Command | Governed intent directed to an authoritative owner. Submission does not imply acceptance; acceptance does not imply execution success; execution success does not imply business outcome. |
| Query | Request for governed information with no authoritative side effect. It declares whether its result is authoritative, projected, derived, cached, historical, or uncertain. |
| Event | Assertion that an owner-governed occurrence happened. Consumption conveys no mutation authority. |
| Notification | Informational communication, never an authoritative domain assertion. |

A Notification does not create domain truth, prove a state transition, or grant mutation authority. It may reference an Event, Command, Query, Situation, Task, or Outcome and may be delivered by any channel. Delivery never proves business completion; it remains informative until an owning context separately validates it.

## 3. Identity, Version, Lifecycle, Operational Status, and Criticality

The stable semantic identifier is globally unique and uses `IC-{OWNING-CONTEXT}-{TYPE}-{SEQUENCE}`; examples are `IC-IDENTITY-QRY-001`, `IC-GOVERNANCE-EVT-001`, `IC-EXECUTION-CMD-001`, `IC-MISSION-NTF-001`, and `IC-NETPAY-CMD-001`. It identifies the semantic concept and never embeds its version.

`Version` uses a semantic evolution value such as `1.0.0`, `1.1.0`, or `2.0.0`. Compatible evolution retains the stable identifier. Material semantic or ownership change requires major version analysis or a new contract; ownership change is never ordinary compatible change.

| Dimension | Allowed values | Meaning |
| --- | --- | --- |
| Lifecycle | Draft, Proposed, Ratified, Deprecated, Retired | Architectural governance state. |
| Operational status | Planned, Implemented, Verified, Production, Suspended, Removed | Availability in operation. |
| Criticality | Critical, Core, Operational, Informational | Architectural and operational impact, not popularity. |

Lifecycle and operational status are independent: Ratified may be Planned; Deprecated may remain Production. Retired contracts accept no new interactions. Historical records remain interpretable under their producing version.

## 4. Canonical Schema and Specialized Schemas

`InteractionContract`: `interaction_contract_id`, stable semantic identifier, name, contract type, owning context, owning capability, semantic purpose, version, lifecycle, operational status, criticality, provider, permitted consumers, initiating actor or context, target canonical object when applicable, identity requirements, authorization requirements, governance requirements, input semantics, output semantics, asserted occurrence when applicable, non-authoritative communication semantics when applicable, preconditions, invariants involved, temporal semantics, valid-time semantics, transaction-time semantics, consistency expectations, idempotency semantics, correlation requirements, causation requirements, provenance requirements, evidence references, uncertainty semantics, failure semantics, privacy classification, compatibility policy, deprecation policy, replacement contract, dependencies, resulting contracts, use-case references, application-module references, conformance rules, status rationale, architectural steward, created_at, ratified_at, deprecated_at, retired_at, metadata.

`CommandContract` adds expressed business intent, authoritative target owner, target canonical object, permitted initiators, required authority, preconditions, invariant checks, acceptance/rejection/deferral/cancellation/expiration semantics, idempotency-key semantics, resulting transition/events, execution and compensation expectations.

`QueryContract` adds governed information, answering context, result classification, permitted consumers, freshness and temporal interpretation, uncertainty, privacy/authorization constraints, response, empty-result and unavailable-result semantics, and prohibited side effects.

`EventContract` adds asserted occurrence, asserting context, originating object/transition, event and recording times, identity/authority/provenance/evidence references, confidence when derived, ordering/duplication/replay expectations, consumer obligations, and compatibility expectations.

`NotificationContract` adds informational purpose, originating context, intended recipients, referenced contract/event/command/query/situation/task/outcome, delivery intent, urgency, channel neutrality, delivery status, acknowledgement and expiration semantics, privacy classification, prohibited authoritative interpretation, and failure-to-deliver semantics.

`ContractVersion`, `ContractLifecycleRecord`, `ContractOperationalStatusRecord`, `ContractDependency`, `ContractCoverageRecord`, `ContractConformanceRule`, `ContractCompatibilityRecord`, `ContractChangeProposal`, `ContractDeprecationRecord`, `ContractReplacementRecord`, `DerivedContractView`, and `InteractionContractArchitectureFinding` record respectively version, lifecycle, operational availability, dependencies, coverage, validation rule, compatibility, proposed change, deprecation, replacement, non-authoritative view, and architecture finding with steward/provenance/temporal metadata.

## 5. Common Contract Semantics

Every contract preserves applicable identity, authority, governance, provenance, valid/transaction/record time, correlation, causation where known, uncertainty, privacy classification, and evidence lineage. Provider is the contract publisher; permitted consumers may rely on its declared semantics but never receive ownership.

Commands identify target owner and object, authority, preconditions, invariants, idempotency, resulting transition, and compensation. Queries declare freshness, result classification, empty/unavailable result, and no side effects. Events identify owner and asserted transition, time, replay/duplication/order behavior, evidence and confidence when derived. Notifications explicitly state non-authority, recipient, privacy, acknowledgement, expiry, and delivery failure.

Consistency is owner-defined and eventual consistency is explicit. Failure distinguishes rejection, validation/invariant failure, authorization failure, unavailable dependency, stale projection, uncertain result, execution failure, and absence of information. Contract representations in API, message, UI, or file bindings are derived bindings, never the canonical contract.

## 6. Governance, Compatibility, Approval, and Conformance

Contract approval follows the owning context and applicable Governance authority. Every contract has an architectural steward. Critical contracts require explicit traceability and observability requirements. A breaking change requires rationale, impact analysis, migration policy, compatibility assessment, and architectural approval. Deprecated contracts may operate while a replacement migrates; replacement/supersession preserves historical interpretability. Splitting or merging contracts is allowed only when ownership, semantics, lifecycle, temporal behavior, failure semantics, and consumers justify it.

Conformance rules: one owner and one capability per contract; no reused identifier; no ownerless contract; Commands target owners; Events originate with transition owners; Queries declare classification/freshness and do not mutate; Notifications remain non-authoritative; no breaking version is labeled compatible; retired contracts accept no new interactions; critical contracts provide traceability and observability; no Tier 1 contract/use case/capability is orphaned; no context boundary is bypassed.

## 7. Tier 1 Ratification Baseline — Contract Master Registry

All entries are version `1.0.0`, lifecycle `Proposed`, operational status `Planned`, and have an architectural steward. `C` is Critical, `Co` Core, `O` Operational, `I` Informational.

| ID | Type | Owner / capability | Name and semantic purpose | Criticality | Primary consumer/use case |
| --- | --- | --- | --- | --- | --- |
| IC-IDENTITY-CMD-001 | CMD | Identity / resolution | ResolveSubjectCandidate: resolve or propose canonical Party/PartyGroup reference | C | intake association |
| IC-IDENTITY-QRY-001 | QRY | Identity / canonical reference | RetrieveCanonicalIdentity | C | all Tier 1 association |
| IC-IDENTITY-EVT-001 | EVT | Identity / resolution | IdentityResolutionRecorded | C | O&E, Netpay, MC |
| IC-GOVERNANCE-QRY-001 | QRY | Governance / authority | EvaluateAuthority | C | target-command authorization |
| IC-GOVERNANCE-QRY-002 | QRY | Governance / policy/delegation | RetrieveApplicableDelegation | Co | work assignment |
| IC-GOVERNANCE-EVT-001 | EVT | Governance / authority | AuthorityChanged | C | Execution, MC |
| IC-RELATIONSHIP-CMD-001 | CMD | Relationship / association | EstablishCasePartyRelationship | Co | merchant/case association |
| IC-RELATIONSHIP-QRY-001 | QRY | Relationship / association | RetrieveCaseRelationships | Co | case view |
| IC-RELATIONSHIP-EVT-001 | EVT | Relationship / association | RelationshipRecorded | Co | Netpay, MC |
| IC-EVIDENCE-CMD-001 | CMD | Observation & Evidence / observation | CaptureInboundObservation | C | Inbox First intake |
| IC-EVIDENCE-CMD-002 | CMD | Observation & Evidence / artifact/evidence | RegisterSourceArtifact | C | document or attachment |
| IC-EVIDENCE-CMD-003 | CMD | Observation & Evidence / validation | ValidateEvidence | C | checklist evidence |
| IC-EVIDENCE-QRY-001 | QRY | Observation & Evidence / lineage | RetrieveEvidenceStatus | Co | checklist/case view |
| IC-INBOX-CMD-001 | CMD | Intake / receive | ReceiveIntake: authenticated, organization-owned deterministic inbound intake with idempotent replay | C | governed Inbox intake |
| IC-INBOX-QRY-001 | QRY | Intake / detail retrieval | RetrieveDeterministicIntakeDetail: organization-scoped, authenticated Inbox detail retrieval; cross-organization targets are concealed as not found | C | Inbox operator detail view |
| IC-EVIDENCE-EVT-001 | EVT | Observation & Evidence / observation | ObservationCaptured | C | identity and Netpay intake |
| IC-EVIDENCE-EVT-002 | EVT | Observation & Evidence / evidence | EvidenceValidated | C | Knowledge, Netpay |
| IC-KNOWLEDGE-CMD-001 | CMD | Knowledge / promotion | ActivateCaseKnowledge | Co | governed case facts |
| IC-KNOWLEDGE-QRY-001 | QRY | Knowledge / assertion | RetrieveActiveCaseKnowledge | Co | Netpay case handling |
| IC-KNOWLEDGE-EVT-001 | EVT | Knowledge / assertion | KnowledgeActivated | Co | Netpay, MC |
| IC-EXECUTION-CMD-001 | CMD | Execution / work | CreatePendingAction | C | missing-document work |
| IC-EXECUTION-CMD-002 | CMD | Execution / assignment | AssignPendingAction | Co | operator responsibility |
| IC-EXECUTION-CMD-003 | CMD | Execution / work state | ResolvePendingAction | C | complete, cancel, or escalate action |
| IC-EXECUTION-QRY-001 | QRY | Execution / work state | RetrievePendingActionStatus | Co | case and MC views |
| IC-EXECUTION-EVT-001 | EVT | Execution / work | PendingActionStateChanged | C | Netpay, MC |
| IC-EXECUTION-EVT-002 | EVT | Execution / activity | WorkActivityRecorded | O | case history |
| IC-MISSION-CMD-001 | CMD | Mission Control / acknowledgement | AcknowledgeAttentionItem | O | human acknowledgement |
| IC-MISSION-QRY-001 | QRY | Mission Control / attention projection | RetrieveCaseAttention | Co | operator work surface |
| IC-MISSION-EVT-001 | EVT | Mission Control / projection | AttentionPublished | O | operator surfaces |
| IC-MISSION-NTF-001 | NTF | Mission Control / communication | NotifyAttentionRecipient | I | relevant actor |
| IC-NETPAY-CMD-001 | CMD | Netpay Merchant Operations / merchant candidate | IdentifyOrRegisterMerchantCandidate | C | inbox association |
| IC-NETPAY-CMD-002 | CMD | Netpay Merchant Operations / case | OpenNetpayOnboardingOrServiceCase | C | TPV/e-commerce service case |
| IC-NETPAY-CMD-003 | CMD | Netpay Merchant Operations / case classification | ClassifyNetpayChannel | Co | TPV, e-commerce, or mixed |
| IC-NETPAY-CMD-004 | CMD | Netpay Merchant Operations / checklist | EvaluateChecklistAndSetPendingAction | C | missing-document detection; invokes owner contracts |
| IC-NETPAY-QRY-001 | QRY | Netpay Merchant Operations / case view | RetrieveMerchantCase | Co | case handling |
| IC-NETPAY-QRY-002 | QRY | Netpay Merchant Operations / checklist view | RetrieveChecklistAndPendingActions | Co | operator view |
| IC-NETPAY-EVT-001 | EVT | Netpay Merchant Operations / case | NetpayCaseOpened | C | Execution, MC |
| IC-NETPAY-EVT-002 | EVT | Netpay Merchant Operations / case | NetpayCaseStatusChanged | C | MC, notification |
| IC-NETPAY-NTF-001 | NTF | Netpay Merchant Operations / communication | NotifyCaseActor | O | assigned/relevant actor |

**Tier 1 totals:** 39 contracts — 15 Commands, 11 Queries, 11 Events, and 2 Notifications. Each has an owner, capability, consumer/use case, steward, traceability requirement, and planned conformance obligations.

### 7.1 Verified WS-001 Inbox Binding

`IC-INBOX-CMD-001` is the mutating `ReceiveIntake` command at `POST /intake/deterministic`. It requires an authenticated actor, `inbound.intake` authority, a trusted `principal.organization_id`, and an idempotency key. The trusted principal is the only ownership source: the command persists that value to `IntakeItem.organization_id`; request-body data cannot supply or override it.

Its idempotency identity is `(organization_id, idempotency_key)`. An equivalent retry replays the original intake result; conflicting content for the same organization/key is rejected; the same key in another organization creates a separate intake. Intake, message, and the `intake.received` and `message.registered` events persist atomically. Correlation and optional causation are recorded in the created events and trace metadata.

On success the boundary returns the deterministic intake detail (`201`). Missing or insufficient authenticated authority, absent or unrecognized trusted organization, and invalid input are rejected; conflicting idempotency reuse returns a conflict. The companion `IC-INBOX-QRY-001` is non-mutating and separately requires `inbound.read`; it returns only same-organization governed details and conceals cross-organization, legacy, and nonexistent targets as not found.

## 8. Coverage and Ownership Matrices

| Context | Tier 1 contracts | Coverage result |
| --- | --- | --- |
| Identity | CMD 001; QRY 001; EVT 001 | covered |
| Governance | QRY 001–002; EVT 001 | covered |
| Relationship | CMD/QRY/EVT 001 | covered |
| Observation & Evidence | CMD 001–003; QRY 001; EVT 001–002 | covered |
| Knowledge | CMD/QRY/EVT 001 | covered |
| Decision Intelligence | none required: first slice uses deterministic domain validation, not an explicit decision | explicitly out of Tier 1 |
| Execution | CMD 001–003; QRY 001; EVT 001–002 | covered |
| Automation | none required: no eligible automation is required in first slice | explicitly out of Tier 1 |
| Mission Control | CMD/QRY/EVT/NTF 001 | covered |
| Netpay Merchant Operations | CMD 001–004; QRY 001–002; EVT 001–002; NTF 001 | covered |

The capability-to-contract and application-module-to-contract mappings are identical to the owning-context mapping unless a module contains more than one internal component. Use-case coverage is: intake/artifact/observation (Evidence); resolve identity/relationship/merchant (Identity, Relationship, Netpay); validate and activate governed facts (Evidence, Knowledge); open/classify/check case (Netpay); pending-action lifecycle and assignment/activity (Execution); attention/acknowledgement (Mission); notification (Mission/Netpay). No Tier 1 capability or contract is orphaned.

| Contract family | Command owner / Query answerer / Event producer / Notification origin | Boundary rule |
| --- | --- | --- |
| Identity | Identity / Identity / Identity / — | foreign references only |
| Governance | — / Governance / Governance / — | target verifies authority |
| Relationship | Relationship / Relationship / Relationship / — | no identity duplication |
| Evidence | O&E / O&E / O&E / — | no active Knowledge promotion |
| Knowledge | Knowledge / Knowledge / Knowledge / — | no decision creation |
| Execution | Execution / Execution / Execution / — | no automation bypass |
| Mission | Mission / Mission / Mission / Mission | projection, acknowledgement, notification only |
| Netpay | Netpay / Netpay / Netpay / Netpay | owns merchant/case/checklist semantics |

## 9. Netpay Inbox First End-to-End Contract Chain

| Step | Contract | Type / owner | Affected state and resulting contract | Style, uncertainty, failure, trace |
| --- | --- | --- | --- | --- |
| Inbound email/message/upload/document | IC-EVIDENCE-CMD-002 then CMD-001 | CMD / O&E | artifact and immutable observation; EVT-001 | immediate acceptance; malformed input/rejection explicit; intake correlation/provenance |
| Identify actor/merchant candidate | IC-IDENTITY-CMD-001; IC-NETPAY-CMD-001 | CMD / Identity, Netpay | candidate/reference; Identity EVT-001 | ambiguity retained, human review where required; same correlation |
| Associate parties/case | IC-RELATIONSHIP-CMD-001 | CMD / Relationship | governed association; EVT-001 | explicit authority; relationship provenance |
| Open case and classify channel | IC-NETPAY-CMD-002 then CMD-003 | CMD / Netpay | case; classification; EVT-001 | synchronous acceptance, uncertain facts visible |
| Register/validate evidence and activate fact | IC-EVIDENCE-CMD-003; IC-KNOWLEDGE-CMD-001 | CMD / O&E, Knowledge | validated evidence; active knowledge; Evidence/Knowledge events | validation failure distinct; lineage retained |
| Evaluate checklist and missing documents | IC-NETPAY-CMD-004; QRY-002 | CMD/QRY / Netpay | checklist and required owner command request | no hidden cross-context mutation; stale view explicit |
| Create, assign, record and resolve pending work | IC-EXECUTION-CMD-001/002/003; EVT-001/002 | CMD/EVT / Execution | action ON/OFF and activity; state event | owner verifies authority; cancellation/escalation traceable |
| Publish and acknowledge attention | IC-MISSION-EVT-001; QRY-001; CMD-001 | EVT/QRY/CMD / Mission | projected attention/acknowledgement | async projection; freshness/uncertainty explicit |
| Update final case status and notify | IC-NETPAY-EVT-002; NTF-001 or IC-MISSION-NTF-001 | EVT/NTF / Netpay, Mission | case state; non-authoritative communication | delivery failure not completion; causation/evidence retained |

Every row carries the same correlation id from intake, immediate causation reference to its predecessor where known, source/artifact/evidence provenance, valid and recording time where applicable, and an InteractionTrace. The chain is therefore covered end to end without treating a notification as outcome proof.

## 10. Tier 2 Candidate Backlog

Tier 2 contains **6 Draft candidate families**, not ratified contracts: (1) Decision Intelligence recommendation/approval contracts; (2) Automation eligibility/session/task contracts; (3) advanced Governance delegation/revocation commands; (4) expanded Identity merge/split contracts; (5) execution authorization and external execution contracts; and (6) future operational-domain families such as Energy. They remain Draft until a real use case or architectural dependency requires them.

## 11. Contract Dependency, Criticality, Lifecycle, and Compatibility

Dependencies follow greater architectural stability: Netpay depends on platform contracts; platform semantics do not depend on Netpay. Critical contracts are Identity resolution/reference, authority evaluation/change, evidence capture/validation, pending-action lifecycle, Netpay candidate/case/checklist/state, and their events. Critical contracts require trace propagation, evidence/provenance where applicable, compatibility assessment, and observability/conformance records.

All Tier 1 entries are Proposed/Planned and initially compatible only with their own `1.0.0` semantic baseline. No replacement exists. A later compatibility/replacement matrix must state producer/consumer versions, change class, migration, deprecation window, and replacement identifier. No dependency cycle is accepted; no version may be embedded in an identifier.

## 12. Derived Non-Authoritative Views

The following are non-authoritative projections of `INTERACTION_CONTRACT_CATALOG.md`: Command Catalog View, Query Model View, Event Catalog View, Notification Catalog View, Public API View, Domain Event View, Application Service View, Conformance View, Observability View, and Documentation View. They may be generated or explicitly governed by this catalog; none is an independent source of authority.

## 13. Risks, Findings, Open Questions, and Ratification

| Finding | Severity | Family/context | Evidence and control | Steward | Prior amendment |
| --- | --- | --- | --- | --- | --- |
| ICC-001 | NONE | Tier 1 | No orphan contract/capability, owner ambiguity, non-owner command/event, or hidden query mutation found. | Catalog Steward | No |
| ICC-002 | MINOR | Mission and Netpay projections | Freshness, source authority, and uncertainty must be enforced in derived query views. | Query and Projection Contract Steward | No |
| ICC-003 | MINOR | O&E / Netpay external inputs | Inbound messages require validation and responsible owner assertion before event truth. | Event Contract and ACL Steward | No |
| ICC-004 | MINOR | Tier 1 lifecycle | Proposed/Planned baseline needs implementation conformance before operational availability. | Application Architecture Steward | No |

There are **0 BLOCKER**, **0 MAJOR**, and **3 MINOR** findings. Open questions are exact contract payload shape, privacy classes by consumer, freshness thresholds, and detailed dependency/replay policy; these belong to later bindings and must not redefine catalog semantics.

The baseline is ready for formal review when the 37 Tier 1 entries remain owner-directed, non-orphaned, and covered by the chain; critical contracts retain conformance/observability obligations; and the three MINOR controls are accepted with traceable stewardship.

## 14. Required Follow-On Artifact and Closing Statement

The required next artifact is `INTERACTION_CONTRACT_REVIEW.md`. It must review this catalog before `ARCHITECTURAL_DECISION_TRACE.md`, then `TECHNICAL_BLUEPRINT.md`. The catalog makes Yarvis operational language governable across implementation changes: commands request, queries answer, events assert, notifications inform, and all preserve ownership, authority, provenance, time, and traceability.
