# YARVIS
# Contract Registry Baseline Metadata Decision 001

## Status

**Ratified**

This ratified decision supplies the individual metadata evidence incorporated
by the F-006/F-013 Runtime Baseline V1 reconciliation. It creates no runtime
implementation authority. It does not modify the
catalog, the canonical projection, tests, migrations, C06, or Amendment 003.

## 1. Scope and Decision Rule

The scope is limited to the 55 identities and order already enumerated in
`CONTRACT_REGISTRY_BASELINE_RECONCILIATION_AMENDMENT_001.md` section 4. It does
not change their IDs, types, owners, capabilities, lifecycle, operational
status, composition, or the 61 catalogued exclusions.

The following matrix fixes four metadata fields for each V1 member:

- `name`;
- `semantic_purpose`;
- `criticality`; and
- `primary_consumer_or_use_case`.

**Existing Authority** means the value is reproduced literally from the named
current document. **Proposed by Decision 001** means no current authoritative
document states that value individually; the value is a new, explicit proposal.
`canonical_contracts.py` was consulted only as auxiliary implementation evidence
to avoid semantic contradiction. It is not asserted to be the prior authority
for any proposed value.

## 2. Authoritative Sources and Evidence Boundary

The sources used are:

- `INTERACTION_CONTRACT_CATALOG.md` section 7 for catalog rows, criticality,
  and primary consumer/use-case text;
- `IG-001_DI002_IMPLEMENTATION_AUTHORIZATION.md` “Contract allocation” table
  for the ten Document Registry names; and
- `OPERATIONAL_EXECUTION_ARCHITECTURE.md`, an Accepted OE-001 Architecture
  Decision, for the seven Task names and command responsibilities; and
- `ADR-OPERATIONAL-TASK-LIFECYCLE-AND-DEPENDENCIES.md`, an accepted decision,
  for the direct finish-to-start dependency semantics; and
- the existing V1 inventory in Baseline Reconciliation Amendment 001 only for
  its fixed identity, order, type, owner, capability, and projection-state
  scope.

For Task ranges and Document Registry ranges, the Catalog's aggregate row does
not individually assign all names and purposes. For historical rows whose
combined “Name and semantic purpose” cell supplies only a name, no separate
purpose is inferred from that cell. Those gaps are the 46 values explicitly
proposed below.

## 3. V1 Metadata Matrix

Sources are given in every cell as `EA:` (Existing Authority) or `PD1:`
(Proposed by Decision 001). `Catalog §7` means the exact Master Registry row
for the named identity unless a range is named. Criticality preserves the
Catalog's declared value and expansion (`C` = Critical; `Co` = Core).

| # | Contract ID | Name | Semantic purpose | Criticality | Primary consumer or use case |
| ---: | --- | --- | --- | --- | --- |
| 1 | IC-WORKSPACE-QRY-001 | RetrieveOperationalWorkspaceOverview — EA: Catalog §7 | Retrieve tenant-safe operational workspace composition — EA: Catalog §7 | Core (Co) — EA: Catalog §7 | Operational Workspace — EA: Catalog §7 |
| 2 | IC-TASK-CMD-001 | CreateOperationalTask — EA: Operational Execution Architecture, Task command responsibility table | Create one Task under one Mission Work Item. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 3 | IC-TASK-CMD-002 | UpdateOperationalTaskPlanningFields — EA: Operational Execution Architecture, Task command responsibility table | Update neutral planning fields and optional Process Instance/stage association while status is `planned`. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 4 | IC-TASK-CMD-003 | AssignOperationalTask — EA: Operational Execution Architecture, Task command responsibility table | Set or clear the optional primary assignee. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 5 | IC-TASK-CMD-004 | TransitionOperationalTask — EA: Operational Execution Architecture, Task command responsibility table | Perform the allowed non-terminal lifecycle transitions. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 6 | IC-TASK-CMD-005 | CompleteOperationalTask — EA: Operational Execution Architecture, Task command responsibility table | Explicitly complete from `in_progress` with accountable result and optional completion note. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 7 | IC-TASK-CMD-006 | CancelOperationalTask — EA: Operational Execution Architecture, Task command responsibility table | Explicitly cancel a non-terminal Task with a nonblank reason. — EA: Operational Execution Architecture, Task command responsibility table | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 8 | IC-TASK-CMD-007 | ManageOperationalTaskDependencies — EA: Operational Execution Architecture, Task command responsibility table | Add or close one direct finish-to-start edge after tenant and cycle validation. — EA: Operational Execution Architecture, Task command responsibility table; ADR Operational Task Lifecycle and Dependencies (Accepted) | Core (Co) — EA: Catalog §7 Task range | governed Mission Work commitments — EA: Catalog §7 Task range |
| 9 | IC-IDENTITY-CMD-001 | ResolveSubjectCandidate — EA: Catalog §7 | resolve or propose canonical Party/PartyGroup reference — EA: Catalog §7 | Critical (C) — EA: Catalog §7 | intake association — EA: Catalog §7 |
| 10 | IC-IDENTITY-QRY-001 | RetrieveCanonicalIdentity — EA: Catalog §7 | Provide the canonical identity reference for a resolved subject. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | all Tier 1 association — EA: Catalog §7 |
| 11 | IC-IDENTITY-EVT-001 | IdentityResolutionRecorded — EA: Catalog §7 | Record that identity resolution has been determined. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | O&E, Netpay, MC — EA: Catalog §7 |
| 12 | IC-GOVERNANCE-QRY-001 | EvaluateAuthority — EA: Catalog §7 | Determine whether an actor holds authority for a governed target action. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | target-command authorization — EA: Catalog §7 |
| 13 | IC-GOVERNANCE-QRY-002 | RetrieveApplicableDelegation — EA: Catalog §7 | Provide the delegation applicable to a requested work assignment. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | work assignment — EA: Catalog §7 |
| 14 | IC-GOVERNANCE-EVT-001 | AuthorityChanged — EA: Catalog §7 | Record that an authority or delegation state has changed. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | Execution, MC — EA: Catalog §7 |
| 15 | IC-RELATIONSHIP-CMD-001 | EstablishCasePartyRelationship — EA: Catalog §7 | Establish an accountable association between a case and a party. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | merchant/case association — EA: Catalog §7 |
| 16 | IC-RELATIONSHIP-QRY-001 | RetrieveCaseRelationships — EA: Catalog §7 | Provide the relationships recorded for a case. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | case view — EA: Catalog §7 |
| 17 | IC-RELATIONSHIP-EVT-001 | RelationshipRecorded — EA: Catalog §7 | Record that a case-party relationship has been established. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | Netpay, MC — EA: Catalog §7 |
| 18 | IC-EVIDENCE-CMD-001 | CaptureInboundObservation — EA: Catalog §7 | Record an inbound observation with its source context. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | Inbox First intake — EA: Catalog §7 |
| 19 | IC-EVIDENCE-CMD-002 | RegisterSourceArtifact — EA: Catalog §7 | Register a source artifact for evidence lineage. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | document or attachment — EA: Catalog §7 |
| 20 | IC-EVIDENCE-CMD-003 | ValidateEvidence — EA: Catalog §7 | Record the outcome of evidence validation. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | checklist evidence — EA: Catalog §7 |
| 21 | IC-EVIDENCE-QRY-001 | RetrieveEvidenceStatus — EA: Catalog §7 | Provide current validation and lineage status for evidence. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | checklist/case view — EA: Catalog §7 |
| 22 | IC-EVIDENCE-EVT-001 | ObservationCaptured — EA: Catalog §7 | Record that an observation was captured. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | identity and Netpay intake — EA: Catalog §7 |
| 23 | IC-EVIDENCE-EVT-002 | EvidenceValidated — EA: Catalog §7 | Record the governed outcome of evidence validation. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | Knowledge, Netpay — EA: Catalog §7 |
| 24 | IC-KNOWLEDGE-CMD-001 | ActivateCaseKnowledge — EA: Catalog §7 | Promote validated case knowledge to an active governed assertion. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | governed case facts — EA: Catalog §7 |
| 25 | IC-KNOWLEDGE-QRY-001 | RetrieveActiveCaseKnowledge — EA: Catalog §7 | Provide the active governed knowledge for a case. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | Netpay case handling — EA: Catalog §7 |
| 26 | IC-KNOWLEDGE-EVT-001 | KnowledgeActivated — EA: Catalog §7 | Record that a knowledge assertion became active. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | Netpay, MC — EA: Catalog §7 |
| 27 | IC-EXECUTION-CMD-001 | CreatePendingAction — EA: Catalog §7 | Create a pending action for governed work. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | missing-document work — EA: Catalog §7 |
| 28 | IC-EXECUTION-CMD-002 | AssignPendingAction — EA: Catalog §7 | Assign responsibility for a pending action. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | operator responsibility — EA: Catalog §7 |
| 29 | IC-EXECUTION-CMD-003 | ResolvePendingAction — EA: Catalog §7 | Record the governed resolution, cancellation, or escalation of a pending action. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | complete, cancel, or escalate action — EA: Catalog §7 |
| 30 | IC-EXECUTION-QRY-001 | RetrievePendingActionStatus — EA: Catalog §7 | Provide the current status of a pending action. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | case and MC views — EA: Catalog §7 |
| 31 | IC-EXECUTION-EVT-001 | PendingActionStateChanged — EA: Catalog §7 | Record a change to a pending action's state. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | Netpay, MC — EA: Catalog §7 |
| 32 | IC-EXECUTION-EVT-002 | WorkActivityRecorded — EA: Catalog §7 | Record attributable work activity in case history. — PD1: explicit metadata proposal | Operational (O) — EA: Catalog §7 | case history — EA: Catalog §7 |
| 33 | IC-MISSION-CMD-001 | AcknowledgeAttentionItem — EA: Catalog §7 | Record a human acknowledgement of an attention item. — PD1: explicit metadata proposal | Operational (O) — EA: Catalog §7 | human acknowledgement — EA: Catalog §7 |
| 34 | IC-MISSION-QRY-001 | RetrieveCaseAttention — EA: Catalog §7 | Provide attention information for a case. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | operator work surface — EA: Catalog §7 |
| 35 | IC-MISSION-EVT-001 | AttentionPublished — EA: Catalog §7 | Record that an attention item was published for operator visibility. — PD1: explicit metadata proposal | Operational (O) — EA: Catalog §7 | operator surfaces — EA: Catalog §7 |
| 36 | IC-MISSION-NTF-001 | NotifyAttentionRecipient — EA: Catalog §7 | Inform the relevant actor about an attention item. — PD1: explicit metadata proposal | Informational (I) — EA: Catalog §7 | relevant actor — EA: Catalog §7 |
| 37 | IC-NETPAY-CMD-001 | IdentifyOrRegisterMerchantCandidate — EA: Catalog §7 | Identify or register a merchant candidate for case handling. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | inbox association — EA: Catalog §7 |
| 38 | IC-NETPAY-CMD-002 | OpenNetpayOnboardingOrServiceCase — EA: Catalog §7 | Open a Netpay onboarding or service case. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | TPV/e-commerce service case — EA: Catalog §7 |
| 39 | IC-NETPAY-CMD-003 | ClassifyNetpayChannel — EA: Catalog §7 | Classify a Netpay case as TPV, e-commerce, or mixed. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | TPV, e-commerce, or mixed — EA: Catalog §7 |
| 40 | IC-NETPAY-CMD-004 | EvaluateChecklistAndSetPendingAction — EA: Catalog §7 | Evaluate checklist completeness and establish required pending work. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | missing-document detection; invokes owner contracts — EA: Catalog §7 |
| 41 | IC-NETPAY-QRY-001 | RetrieveMerchantCase — EA: Catalog §7 | Provide a Netpay merchant case for governed case handling. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | case handling — EA: Catalog §7 |
| 42 | IC-NETPAY-QRY-002 | RetrieveChecklistAndPendingActions — EA: Catalog §7 | Provide checklist state and related pending actions. — PD1: explicit metadata proposal | Core (Co) — EA: Catalog §7 | operator view — EA: Catalog §7 |
| 43 | IC-NETPAY-EVT-001 | NetpayCaseOpened — EA: Catalog §7 | Record that a Netpay case has been opened. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | Execution, MC — EA: Catalog §7 |
| 44 | IC-NETPAY-EVT-002 | NetpayCaseStatusChanged — EA: Catalog §7 | Record a change in Netpay case status. — PD1: explicit metadata proposal | Critical (C) — EA: Catalog §7 | MC, notification — EA: Catalog §7 |
| 45 | IC-NETPAY-NTF-001 | NotifyCaseActor — EA: Catalog §7 | Inform the assigned or relevant actor about a Netpay case. — PD1: explicit metadata proposal | Operational (O) — EA: Catalog §7 | assigned/relevant actor — EA: Catalog §7 |
| 46 | IC-DOCUMENT-CMD-001 | CreateDocument — EA: IG-001 Contract allocation | Create a governed Document — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 47 | IC-DOCUMENT-CMD-002 | UpdateDocumentMetadata — EA: IG-001 Contract allocation | Update governed Document metadata — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 48 | IC-DOCUMENT-CMD-003 | AddDocumentVersion — EA: IG-001 Contract allocation | Append immutable Document Version metadata — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 49 | IC-DOCUMENT-CMD-004 | ArchiveDocument — EA: IG-001 Contract allocation | Archive a governed Document — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 50 | IC-DOCUMENT-CMD-005 | LinkDocumentAssociation — EA: IG-001 Contract allocation | Link a governed Document association — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 51 | IC-DOCUMENT-CMD-006 | UnlinkDocumentAssociation — EA: IG-001 Contract allocation | Historically unlink a Document association — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document command range | governed Document Registry — EA: Catalog §7 Document command range |
| 52 | IC-DOCUMENT-QRY-001 | RetrieveDocument — EA: IG-001 Contract allocation | Retrieve a tenant-safe Document — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document query range | tenant-safe Document Registry views — EA: Catalog §7 Document query range |
| 53 | IC-DOCUMENT-QRY-002 | ListDocumentVersions — EA: IG-001 Contract allocation | Retrieve immutable Document Versions — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document query range | tenant-safe Document Registry views — EA: Catalog §7 Document query range |
| 54 | IC-DOCUMENT-QRY-003 | ListDocumentAssociations — EA: IG-001 Contract allocation | Retrieve active Document associations — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document query range | tenant-safe Document Registry views — EA: Catalog §7 Document query range |
| 55 | IC-DOCUMENT-QRY-004 | ListDocumentsBySubject — EA: IG-001 Contract allocation | Retrieve Documents actively associated with a subject — PD1: canonical implementation evidence | Critical (C) — EA: Catalog §7 Document query range | tenant-safe Document Registry views — EA: Catalog §7 Document query range |

The matrix contains 220 cells: 174 Existing Authority values and 46 Proposed by
Decision 001 values. The 46 proposals are the 36 historical
`semantic_purpose` values and 10 Document Registry `semantic_purpose` values.

The four Document Registry query names remain `RetrieveDocument`,
`ListDocumentVersions`, `ListDocumentAssociations`, and
`ListDocumentsBySubject` under IG-001. Current implementation evidence uses
the distinct `GetDocument`, `GetDocumentVersions`, `GetDocumentAssociations`,
and `GetDocumentsBySubject` names. This decision records the divergence without
resolving it; no implementation metadata is changed here.

## 4. Workspace and Mission Boundary

`IC-WORKSPACE-QRY-001` remains an independent V1 identity. It is not an alias,
equivalent, replacement, or deprecation relation for
`IC-MISSION-QRY-007`. The latter remains among the 61 catalogued exclusions.
Nothing in this matrix changes that boundary, the approved composition, or the
semantic limits already stated in Baseline Reconciliation Amendment 001.

## 5. Immutable Snapshot and Future Change Control

This matrix is the immutable V1 metadata snapshot for
the 55 listed contracts. Future catalog modifications do not retroactively
alter this baseline metadata. The Catalog retains authority for Tier-1
classification and lifecycle/operational-status governance; the ratified V1
baseline retains authority for its composition and projection metadata.

Any composition or metadata change requires a new nominal baseline version,
independent review, and ratification. A future divergence between Catalog and
baseline must be recorded explicitly in that version; it must not be resolved
by implicit inheritance, a count change, a shared owner, or implementation
presence.

Baseline Reconciliation Amendment 001 incorporates this decision through its
immutable reference before that amendment's ratification. Neither document
authorizes runtime implementation, and `FOUNDATION-DEBT-001` remains open
until the separate technical remediation and validation are accepted.

## 6. Review Request

The completed independent review verified all 220 matrix values, the 174/46
provenance classification, the unchanged 55-member V1 inventory and 61
exclusions, the Workspace/Mission boundary, and the absence of implementation
authority.
