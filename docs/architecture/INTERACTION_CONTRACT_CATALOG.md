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

All entries are version `1.0.0`, lifecycle `Proposed`, operational status `Planned`, and have an architectural steward, except where a later ratified contract amendment records a compatible, versioned profile without changing stable identity or owner. `C` is Critical, `Co` Core, `O` Operational, `I` Informational.

| ID | Type | Owner / capability | Name and semantic purpose | Criticality | Primary consumer/use case |
| --- | --- | --- | --- | --- | --- |
| IC-TASK-CMD-001â€“007 | CMD | Operational Execution / Task lifecycle | Create, plan, assign, transition, complete, cancel, and manage direct Task dependencies | Co | governed Mission Work commitments |
| IC-WORKSPACE-QRY-001 | QRY | Mission Control / operational workspace overview | RetrieveOperationalWorkspaceOverview: retrieve tenant-safe operational workspace composition | Co | Operational Workspace |
| IC-IDENTITY-CMD-001 | CMD | Identity / resolution | ResolveSubjectCandidate: resolve or propose canonical Party/PartyGroup reference | C | intake association |
| IC-IDENTITY-CMD-002 | CMD | Identity / external identity binding | BindExternalIdentity: bind one verified `issuer + normalized_subject` to one canonical Principal | C | productive identity resolution |
| IC-IDENTITY-CMD-003 | CMD | Identity / Person-Principal association | LinkPrincipalToPerson: establish the reviewed canonical Person link for a human Principal | C | productive human authority chain |
| IC-IDENTITY-CMD-004 | CMD | Identity / productive session | StartProductiveSession: create canonical server-side session state after successful technical authentication and authority resolution | C | productive authenticated access |
| IC-IDENTITY-CMD-005 | CMD | Identity / productive session | RevokeProductiveSession: terminally revoke canonical server-side session state | C | logout, administrative revocation, authority loss |
| IC-IDENTITY-CMD-006 | CMD | Identity / bootstrap Person creation | CreatePerson: create one reviewed human Person without credential or Membership authority | C | bounded productive bootstrap |
| IC-IDENTITY-CMD-007 | CMD | Identity / bootstrap Principal creation | CreateHumanPrincipal: create one human Principal for a reviewed Person without external binding or Membership authority | C | bounded productive bootstrap |
| IC-IDENTITY-QRY-001 | QRY | Identity / canonical reference | RetrieveCanonicalIdentity | C | all Tier 1 association |
| IC-IDENTITY-QRY-002 | QRY | Identity / productive Principal resolution | ResolvePrincipal: resolve exactly one active Principal from an active verified binding | C | productive authentication boundary |
| IC-IDENTITY-QRY-003 | QRY | Identity / productive session | GetCurrentSession: retrieve the minimal safe server-side session projection | C | authenticated application boundary |
| IC-IDENTITY-EVT-001 | EVT | Identity / resolution | IdentityResolutionRecorded | C | O&E, Netpay, MC |
| IC-IDENTITY-EVT-002 | EVT | Identity / external identity binding | ExternalIdentityBound: assert a verified, non-conflicting binding transition without raw claims or secrets | C | authority resolution and audit |
| IC-IDENTITY-EVT-003 | EVT | Identity / Person-Principal association | PrincipalLinkedToPerson: assert the reviewed human association | C | authority resolution and audit |
| IC-IDENTITY-EVT-004 | EVT | Identity / productive session | ProductiveSessionStarted: assert canonical session creation using safe opaque references | C | security audit and session administration |
| IC-IDENTITY-EVT-005 | EVT | Identity / productive session | ProductiveSessionRevoked: assert terminal session revocation | C | authorization invalidation and security audit |
| IC-IDENTITY-EVT-006 | EVT | Identity / bootstrap Person creation | PersonCreated: assert one reviewed Person creation using safe opaque references | C | bounded productive bootstrap audit |
| IC-IDENTITY-EVT-007 | EVT | Identity / bootstrap Principal creation | HumanPrincipalCreated: assert one reviewed human Principal creation using safe opaque references | C | bounded productive bootstrap audit |
| IC-GOVERNANCE-CMD-001 | CMD | Governance / Membership | GrantMembership: create one explicitly authorized active PrincipalMembership | C | canonical Organization authority |
| IC-GOVERNANCE-CMD-002 | CMD | Governance / Membership | RevokeMembership: terminally revoke one PrincipalMembership | C | authority withdrawal |
| IC-GOVERNANCE-CMD-003 | CMD | Governance / administrative bootstrap | CloseBootstrapWindow: irreversibly close the bounded bootstrap window under approved policy | C | bootstrap termination |
| IC-GOVERNANCE-CMD-004 | CMD | Governance / administrative bootstrap | OpenBootstrapWindow: open one bounded, expiring, single-success bootstrap window | C | productive bootstrap administration |
| IC-GOVERNANCE-CMD-005 | CMD | Governance / administrative bootstrap | ExecuteBootstrapEnrollment: atomically orchestrate the approved initial canonical identity chain | C | productive bootstrap administration |
| IC-GOVERNANCE-QRY-001 | QRY | Governance / authority | EvaluateAuthority; F-011 profile `1.1.0` ratified by `F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md` | C | target-command authorization |
| IC-GOVERNANCE-QRY-002 | QRY | Governance / policy/delegation | RetrieveApplicableDelegation | Co | work assignment |
| IC-GOVERNANCE-QRY-003 | QRY | Governance / Membership resolution | ResolveEffectiveMembership: resolve active same-Organization Membership and closed role/capabilities without client authority | C | productive authority envelope |
| IC-GOVERNANCE-QRY-004 | QRY | Governance / administrative bootstrap | GetBootstrapEligibility: return a minimal fail-closed eligibility decision under the approved bootstrap policy | C | bounded bootstrap orchestration |
| IC-GOVERNANCE-EVT-001 | EVT | Governance / authority | AuthorityChanged; F-011 profile `1.1.0` ratified by `F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md` | C | Execution, MC |
| IC-GOVERNANCE-EVT-002 | EVT | Governance / administrative bootstrap | BootstrapWindowClosed: assert terminal bootstrap closure without identity evidence, secrets, or PII | C | security audit and bootstrap denial |
| IC-GOVERNANCE-EVT-003 | EVT | Governance / administrative bootstrap | BootstrapWindowOpened: assert bounded bootstrap opening with safe opaque references | C | security audit and bootstrap control |
| IC-GOVERNANCE-EVT-004 | EVT | Governance / administrative bootstrap | BootstrapEnrollmentCompleted: assert terminal successful enrollment without identity evidence or secrets | C | security audit and bootstrap control |
| IC-RELATIONSHIP-CMD-001 | CMD | Relationship / association | EstablishCasePartyRelationship | Co | merchant/case association |
| IC-RELATIONSHIP-QRY-001 | QRY | Relationship / association | RetrieveCaseRelationships | Co | case view |
| IC-RELATIONSHIP-EVT-001 | EVT | Relationship / association | RelationshipRecorded | Co | Netpay, MC |
| IC-EVIDENCE-CMD-001 | CMD | Observation & Evidence / observation | CaptureInboundObservation | C | Inbox First intake |
| IC-EVIDENCE-CMD-002 | CMD | Observation & Evidence / artifact/evidence | RegisterSourceArtifact | C | document or attachment |
| IC-EVIDENCE-CMD-003 | CMD | Observation & Evidence / validation | ValidateEvidence | C | checklist evidence |
| IC-EVIDENCE-QRY-001 | QRY | Observation & Evidence / lineage | RetrieveEvidenceStatus | Co | checklist/case view |
| IC-INBOX-CMD-001 | CMD | Intake / receive | ReceiveIntake: authenticated, organization-owned deterministic inbound intake with idempotent replay | C | governed Inbox intake |
| IC-INBOX-QRY-001 | QRY | Intake / detail retrieval | RetrieveDeterministicIntakeDetail: organization-scoped, authenticated Inbox detail retrieval; cross-organization targets are concealed as not found | C | Inbox operator detail view |
| IC-INBOX-CMD-003 | CMD | Intake / operational context association | AssociateIntakeOperationalContext: immutable, tenant-owned association of a deterministic Intake to a Site, Project, and optional ConnectorMapping | C | governed Inbox context association |
| IC-INBOX-QRY-002 | QRY | Intake / operational context association | RetrieveIntakeOperationalContext: authenticated, organization-scoped association retrieval; absent, legacy, and cross-organization targets are concealed as not found | C | Inbox operator context view |
| IC-INBOX-EVT-001 | EVT | Intake / operational context association | IntakeOperationalContextAssociated: asserted immutable association occurrence with correlation, optional causation, and actor provenance | C | Inbox, projections, and automation |
| IC-MISSION-QRY-002 | QRY | Mission Control / Inbox | ListMissionInbox: tenant-scoped Mission Inbox read model list | C | Mission Inbox operator view |
| IC-MISSION-QRY-003 | QRY | Mission Control / Inbox | RetrieveMissionInboxItem: tenant-scoped Mission Inbox item retrieval with concealed absence | C | Mission Inbox operator view |
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
| IC-MISSION-CMD-002 | CMD | Mission Control / work queue | CreateMissionWorkItemFromInbox | C | operator work creation |
| IC-MISSION-CMD-003 | CMD | Mission Control / work queue | AssignMissionWorkItem | C | operator assignment |
| IC-MISSION-CMD-004 | CMD | Mission Control / work queue | ChangeMissionWorkItemStatus | C | operator work state |
| IC-MISSION-CMD-005 | CMD | Mission Control / work queue | ChangeMissionWorkItemPriority | C | operator prioritization |
| IC-MISSION-CMD-006 | CMD | Mission Control / work timeline | AddMissionWorkItemComment: append an attributable internal comment to a Work Item timeline | C | operator work collaboration |
| IC-MISSION-QRY-004 | QRY | Mission Control / work queue | ListMissionWorkItems | C | operator queue view |
| IC-MISSION-QRY-005 | QRY | Mission Control / work queue | RetrieveMissionWorkItem | C | operator work detail |
| IC-MISSION-QRY-006 | QRY | Mission Control / work timeline | RetrieveMissionWorkTimeline: tenant-scoped append-only evidence ordered by sequence number | C | operator work timeline |
| IC-MISSION-EVT-002 | EVT | Mission Control / work queue | MissionWorkItemCreated | C | projections and automation |
| IC-MISSION-EVT-003 | EVT | Mission Control / work queue | MissionWorkItemAssigned | C | projections and automation |
| IC-MISSION-EVT-004 | EVT | Mission Control / work queue | MissionWorkItemUnassigned | C | projections and automation |
| IC-MISSION-EVT-005 | EVT | Mission Control / work queue | MissionWorkItemStatusChanged | C | projections and automation |
| IC-MISSION-EVT-006 | EVT | Mission Control / work queue | MissionWorkItemPriorityChanged | C | projections and automation |
| IC-MISSION-EVT-007 | EVT | Mission Control / work timeline | MissionWorkItemCommentAdded | C | timeline consumers |
| IC-PROCESS-CMD-001 | CMD | Process / definition | CreateProcessDefinition | C | process administration |
| IC-PROCESS-CMD-002 | CMD | Process / version | CreateProcessVersion | C | controlled process evolution |
| IC-PROCESS-CMD-003 | CMD | Process / stage | AddProcessStage | C | draft graph composition |
| IC-PROCESS-CMD-004 | CMD | Process / stage | UpdateProcessStage | C | draft graph composition |
| IC-PROCESS-CMD-005 | CMD | Process / stage | DeleteProcessStage | C | draft graph composition |
| IC-PROCESS-CMD-006 | CMD | Process / transition | AddProcessTransition | C | draft graph composition |
| IC-PROCESS-CMD-007 | CMD | Process / transition | UpdateProcessTransition | C | draft graph composition |
| IC-PROCESS-CMD-008 | CMD | Process / transition | DeleteProcessTransition | C | draft graph composition |
| IC-PROCESS-CMD-009 | CMD | Process / publication | PublishProcessDefinition | C | governed process activation |
| IC-PROCESS-CMD-010 | CMD | Process / retirement | RetireProcessDefinition | C | governed process withdrawal |
| IC-PROCESS-CMD-011 | CMD | Process / runtime | StartProcessInstance | C | governed process start |
| IC-PROCESS-CMD-012 | CMD | Process / runtime | TransitionProcessInstance | C | governed graph transition |
| IC-PROCESS-CMD-013 | CMD | Process / runtime | CancelProcessInstance | C | accountable terminal cancellation |
| IC-PROCESS-CMD-014 | CMD | Process / work association | LinkProcessInstanceToMissionWork | C | governed historical association |
| IC-PROCESS-CMD-015 | CMD | Process / work association | UnlinkProcessInstanceFromMissionWork | C | governed historical unlink |
| IC-PROCESS-QRY-001 | QRY | Process / definition list | ListProcessDefinitions | C | tenant process administration |
| IC-PROCESS-QRY-002 | QRY | Process / definition detail | RetrieveProcessDefinition | C | tenant process inspection |
| IC-PROCESS-QRY-003 | QRY | Process / runtime | ListProcessInstances | C | tenant runtime inspection |
| IC-PROCESS-QRY-004 | QRY | Process / runtime | RetrieveProcessInstance | C | tenant runtime detail |
| IC-PROCESS-QRY-005 | QRY | Process / runtime timeline | RetrieveProcessInstanceTimeline | C | append-only runtime evidence |
| IC-PROCESS-QRY-006 | QRY | Process / work association | ListMissionWorkProcessLinks | C | tenant-scoped association view |
| IC-PROCESS-QRY-007 | QRY | Process / work association | RetrieveProcessInstancePrimaryWorkLink | C | primary association view |
| IC-PROCESS-QRY-008 | QRY | Process / work association | ListProcessInstanceWorkLinkHistory | C | historical association evidence |
| IC-PROCESS-EVT-001 | EVT | Process / definition | ProcessDefinitionCreated | C | append-only process history |
| IC-PROCESS-EVT-002 | EVT | Process / version | ProcessDefinitionVersionCreated | C | append-only process history |
| IC-PROCESS-EVT-003 | EVT | Process / publication | ProcessDefinitionPublished | C | append-only process history |
| IC-PROCESS-EVT-004 | EVT | Process / retirement | ProcessDefinitionRetired | C | append-only process history |
| IC-PROCESS-EVT-005 | EVT | Process / runtime | ProcessInstanceStarted | C | runtime source event |
| IC-PROCESS-EVT-006 | EVT | Process / runtime | ProcessInstanceTransitioned | C | runtime source event |
| IC-PROCESS-EVT-007 | EVT | Process / runtime | ProcessInstanceCompleted | C | terminal runtime source event |
| IC-PROCESS-EVT-008 | EVT | Process / runtime | ProcessInstanceCancelled | C | terminal runtime source event |
| IC-PROCESS-EVT-009 | EVT | Process / work association | ProcessInstanceWorkLinked | C | source event for Work Timeline projection |
| IC-PROCESS-EVT-010 | EVT | Process / work association | ProcessInstanceWorkUnlinked | C | source event for Work Timeline projection |
| IC-ECONOMICS-CMD-001 | CMD | Operational Economics / facts | RecordEconomicFact | C | append-only, provenance-bearing economic fact |
| IC-ECONOMICS-CMD-002 | CMD | Operational Economics / facts | CorrectEconomicFact | C | append-only supersession with reason |
| IC-ECONOMICS-QRY-001 | QRY | Operational Economics / summary | RetrieveOperationalEconomics | C | direct-subject deterministic metrics by currency |
| IC-ECONOMICS-QRY-002 | QRY | Operational Economics / facts | RetrieveEconomicFactHistory | C | tenant-scoped append-only fact lineage |
| IC-DOCUMENT-CMD-001–006 | CMD | Document Registry / document lifecycle | Create, update metadata, add immutable version, archive, link, and unlink historical association | C | governed Document Registry |
| IC-DOCUMENT-QRY-001–004 | QRY | Document Registry / document views | Retrieve document, versions, associations, and documents by subject | C | tenant-safe Document Registry views |
| IC-ECONOMICS-EVT-001 | EVT | Operational Economics / facts | EconomicFactRecorded | C | source event for future economics projections |
| IC-ECONOMICS-EVT-002 | EVT | Operational Economics / facts | EconomicFactCorrected | C | source event for correction lineage |
| IC-MISSION-QRY-007 | QRY | Mission Control / operational workspace | RetrieveOperationalWorkspace | C | bounded, tenant-safe composition of existing owner read models |
| IC-NETPAY-CMD-001 | CMD | Netpay Merchant Operations / merchant candidate | IdentifyOrRegisterMerchantCandidate | C | inbox association |
| IC-NETPAY-CMD-002 | CMD | Netpay Merchant Operations / case | OpenNetpayOnboardingOrServiceCase | C | TPV/e-commerce service case |
| IC-NETPAY-CMD-003 | CMD | Netpay Merchant Operations / case classification | ClassifyNetpayChannel | Co | TPV, e-commerce, or mixed |
| IC-NETPAY-CMD-004 | CMD | Netpay Merchant Operations / checklist | EvaluateChecklistAndSetPendingAction | C | missing-document detection; invokes owner contracts |
| IC-NETPAY-CMD-005 | CMD | Netpay Merchant Operations / master | CreateNetpayClient | C | tenant-owned Client master |
| IC-NETPAY-CMD-006 | CMD | Netpay Merchant Operations / master | CreateNetpayCompany | C | same-tenant Company under Client |
| IC-NETPAY-CMD-007 | CMD | Netpay Merchant Operations / master | CreateNetpayBranch | C | same-tenant Branch; Store ID optional |
| IC-NETPAY-CMD-008 | CMD | Netpay Merchant Operations / master | AssignCorrectOrRemoveNetpayStoreReference | C | optional Store Reference lifecycle within Branch |
| IC-NETPAY-QRY-001 | QRY | Netpay Merchant Operations / case view | RetrieveMerchantCase | Co | case handling |
| IC-NETPAY-QRY-002 | QRY | Netpay Merchant Operations / checklist view | RetrieveChecklistAndPendingActions | Co | operator view |
| IC-NETPAY-QRY-003 | QRY | Netpay Merchant Operations / master view | ListSearchNetpayMaster | Co | tenant-scoped master search |
| IC-NETPAY-QRY-004 | QRY | Netpay Merchant Operations / master view | RetrieveNetpayMasterDetail | Co | Client -> Company -> Branch -> Store Reference |
| IC-NETPAY-EVT-001 | EVT | Netpay Merchant Operations / case | NetpayCaseOpened | C | Execution, MC |
| IC-NETPAY-EVT-002 | EVT | Netpay Merchant Operations / case | NetpayCaseStatusChanged | C | MC, notification |
| IC-NETPAY-NTF-001 | NTF | Netpay Merchant Operations / communication | NotifyCaseActor | O | assigned/relevant actor |

**Tier 1 effective totals:** 146 contracts — 66 Commands, 39 Queries, 39 Events, and 2 Notifications. These totals are computed from every individual ID represented by the registry rows, including compact ranges; the prior declared `116` total undercounted the pre-AUTH-CONTRACT-001 effective registry of 122 by six. The 16 AUTH-CONTRACT-001 additions and 8 AUTH-BOOTSTRAP-CONTRACT-002 additions are ratified contractual definitions but remain unimplemented and absent from the immutable Runtime Baseline V1 projection until a later implementation gate explicitly authorizes a prospective projection update.

### 7.1 Verified WS-001 Inbox Binding

`IC-INBOX-CMD-001` is the mutating `ReceiveIntake` command at `POST /intake/deterministic`. It requires an authenticated actor, `inbound.intake` authority, a trusted `principal.organization_id`, and an idempotency key. The trusted principal is the only ownership source: the command persists that value to `IntakeItem.organization_id`; request-body data cannot supply or override it.

Its idempotency identity is `(organization_id, idempotency_key)`. An equivalent retry replays the original intake result; conflicting content for the same organization/key is rejected; the same key in another organization creates a separate intake. Intake, message, and the `intake.received` and `message.registered` events persist atomically. Correlation and optional causation are recorded in the created events and trace metadata.

On success the boundary returns the deterministic intake detail (`201`). Missing or insufficient authenticated authority, absent or unrecognized trusted organization, and invalid input are rejected; conflicting idempotency reuse returns a conflict. The companion `IC-INBOX-QRY-001` is non-mutating and separately requires `inbound.read`; it returns only same-organization governed details and conceals cross-organization, legacy, and nonexistent targets as not found.

### 7.2 WS-002A Intake Operational Context Association Binding

`IC-INBOX-CMD-003` associates a deterministic Intake to the canonical hierarchy `Organization -> Site -> Project -> ConnectorMapping (optional)`. Deterministic eligibility is the persisted `IntakeItem.intake_mode = deterministic` invariant; it is not inferred from incidental request, source, trace, or idempotency metadata. The authenticated principal's `organization_id` remains the exclusive tenant ownership source; the request never supplies or overrides it. Site, Project, and ConnectorMapping are minimal canonical references: a Site belongs to its Organization, a Project belongs to its Site and Organization, and a ConnectorMapping belongs to its Project and Organization. PostgreSQL composite foreign keys enforce those ownership and hierarchy relationships in addition to application validation.

The association is a separate, immutable Inbox aggregate. One association is permitted per Intake. No reassociation, clearing, deletion, update, or supersession is defined in WS-002A. Missing, legacy-null, cross-tenant, or hierarchy-inconsistent Intake and reference targets are all concealed as `RESOURCE_NOT_FOUND`.

The idempotency namespace is `(organization_id, idempotency_key)`. Its command fingerprint includes Intake, Site, Project, optional ConnectorMapping, and correlation. An equivalent retry returns the original association without a duplicate event; a conflicting reuse, or an existing association under a different idempotency key, returns `CONFLICT`. `IC-INBOX-EVT-001` records the association atomically with its command and contains only identifiers, correlation, optional causation, and actor provenance. `IC-INBOX-QRY-002` requires `inbound.read` and returns only the same-organization association.

## 8. Coverage and Ownership Matrices

| Context | Tier 1 contracts | Coverage result |
| --- | --- | --- |
| Identity | CMD 001–007; QRY 001–003; EVT 001–007 | covered; AUTH-CONTRACT-001 and AUTH-BOOTSTRAP-CONTRACT-002 additions are ratified/planned only |
| Governance | CMD 001–005; QRY 001–004; EVT 001–004 | covered; AUTH-CONTRACT-001 and AUTH-BOOTSTRAP-CONTRACT-002 additions are ratified/planned only |
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
| Governance | Governance / Governance / Governance / — | target verifies authority; Membership and bootstrap mutations remain gate-closed until implemented |
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

Tier 2 contains **6 Draft candidate families**, not ratified contracts: (1) Decision Intelligence recommendation/approval contracts; (2) Automation eligibility/session/task contracts; (3) advanced Governance delegation commands beyond the assigned Membership/bootstrap minimum; (4) expanded Identity merge/split/rotation contracts; (5) execution authorization and external execution contracts; and (6) future operational-domain families such as Energy. They remain Draft until a real use case or architectural dependency requires them.

## 11. Contract Dependency, Criticality, Lifecycle, and Compatibility

Dependencies follow greater architectural stability: Netpay depends on platform contracts; platform semantics do not depend on Netpay. Critical contracts are Identity resolution/reference, authority evaluation/change, evidence capture/validation, pending-action lifecycle, Netpay candidate/case/checklist/state, and their events. Critical contracts require trace propagation, evidence/provenance where applicable, compatibility assessment, and observability/conformance records.

All Tier 1 entries are Proposed/Planned and initially compatible only with their own `1.0.0` semantic baseline, except the ratified `1.1.0` F-011 profiles of `IC-GOVERNANCE-QRY-001` and `IC-GOVERNANCE-EVT-001` recorded by `F-011_GOVERNANCE_CONTRACT_AMENDMENT_001.md`, the Ratified/Planned AUTH-CONTRACT-001 definitions recorded by `AUTH_CONTRACT_001_PRODUCTIVE_IDENTITY_AND_SESSION_CONTRACTS.md`, and the Ratified/Planned AUTH-BOOTSTRAP-CONTRACT-002 definitions recorded by that document's prospective 2026-08-22 supplement. No replacement exists. A later compatibility/replacement matrix must state producer/consumer versions, change class, migration, deprecation window, and replacement identifier. No dependency cycle is accepted; no version may be embedded in an identifier.

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
