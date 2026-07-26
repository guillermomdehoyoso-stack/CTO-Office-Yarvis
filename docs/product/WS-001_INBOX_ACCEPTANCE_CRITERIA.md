# WS-001 Inbox Acceptance Criteria

## Document Control

- Work Package: WS-001
- Title: Inbox First Operational Acceptance Criteria
- Status: Draft for execution
- Last Updated: 2026-07-24
- Owners: Product + Engineering

## Authority and Scope

This document is constrained by:

1. Governance Baseline V1.
2. Yarvis Constitution and ratified architectural decisions.
3. DM-001 ratified domain semantics.
4. AM-001 application model.
5. Current implementation evidence in apps/api and apps/web.

This document defines product acceptance for the first canonical Inbox execution slice.
It does not redefine architecture, ownership, or domain semantics.

## Objective

Deliver an operator-usable Inbox flow where operational inputs become traceable Intake -> Evidence -> Observation -> Attention with explicit human confirmation and append-only history.

## In Scope

- Intake registration from manual text, attachment metadata, and controlled document upload.
- Evidence linkage to case context.
- Observation candidate generation, confirmation, rejection, and supersession paths.
- Policy evaluation and Attention generation.
- Mission Control visibility of pending operational work.
- Workspace/UI surfaces required to execute Inbox flow in a deterministic way.
- End-to-end traceability through DomainEvent and related records.

## Out of Scope

- New external connectors (Gmail/WhatsApp/Drive) beyond existing manual/import paths.
- Autonomous action execution without explicit authority.
- Architecture redesign, microservice split, or cross-context transaction semantics changes.
- Domain expansion outside Inbox-first operational scope.

## Canonical End-to-End Scenario

1. Operator submits intake input.
2. System registers source/document/intake metadata and duplicate status.
3. System generates candidate observations from qualified evidence.
4. Operator confirms context and evidence promotion when required.
5. Operator confirms/rejects observations.
6. System evaluates policies and raises attention items when conditions match.
7. Mission Control and Inbox projections reflect updated pending work.
8. Timeline and event history allow full causal reconstruction.

## Acceptance Criteria

### AC-001 Intake Registration

- Requirement: System accepts valid intake payloads and rejects invalid payloads with explicit reasons.
- Verification: API tests for create/list/get intake and negative payload validation.
- Evidence: passing test group TG-01 and OpenAPI examples.

### AC-002 Intake Context Association

- Requirement: Intake can be linked to existing Organization/Person/Case only when references exist.
- Verification: positive/negative API tests on context confirmation and link endpoints.
- Evidence: TG-01 + TG-02.

### AC-003 Document Upload Controls

- Requirement: Controlled upload enforces size/type restrictions and emits deterministic metadata.
- Verification: API tests for allowed/rejected file types, size limit, and metadata integrity.
- Evidence: TG-03.

### AC-004 Duplicate Detection

- Requirement: Duplicate detection is deterministic and idempotent for repeated evidence inputs.
- Verification: repeated upload/import test with same content and stable duplicate status.
- Evidence: TG-03.

### AC-005 Evidence Promotion

- Requirement: Evidence can be created/linked from intake only under valid case ownership.
- Verification: API tests for evidence creation, cross-case rejection, and listing.
- Evidence: TG-02.

### AC-006 Observation Creation

- Requirement: Observations are created with provenance, confidence, and source references.
- Verification: API tests assert required observation fields and provenance payload presence.
- Evidence: TG-04.

### AC-007 Observation Lifecycle Control

- Requirement: Observation confirm/reject/conflict/supersede transitions are enforced with terminal-state protection.
- Verification: API tests for valid transitions and terminal-state rejection.
- Evidence: TG-04.

### AC-008 Resolution Lifecycle

- Requirement: Resolution proposals can be created and explicitly confirmed/rejected.
- Verification: API tests covering proposal and decision endpoints.
- Evidence: TG-04.

### AC-009 Policy Evaluation

- Requirement: Policy evaluation produces deterministic statuses matched/not_matched/insufficient_data/conflict.
- Verification: API tests across all supported operators and status outcomes.
- Evidence: TG-05.

### AC-010 Attention Generation

- Requirement: Matching/insufficient/conflict policy outcomes raise attention items with actionable context.
- Verification: API tests verifying attention creation and visibility in mission summaries.
- Evidence: TG-05.

### AC-011 Mission Control Inbox Visibility

- Requirement: Mission Control summary exposes pending work counters derived from confirmed/candidate states.
- Verification: API tests for summary/attention endpoints before and after confirmation actions.
- Evidence: TG-06.

### AC-012 Case and Checklist Handshake

- Requirement: Inbox outputs can drive checklist fulfillment and operational state evaluation without manual data patching.
- Verification: integration tests linking intake/evidence/checklist/alerts.
- Evidence: TG-02 + TG-06.

### AC-013 Event Trace Completeness

- Requirement: Every accepted mutating step emits append-only domain events with causal reconstructability.
- Verification: timeline/events assertions for canonical flow and event ordering.
- Evidence: TG-07.

### AC-014 Idempotent Mutations

- Requirement: Repeated equivalent mutating requests do not duplicate business effects.
- Verification: replay tests for intake/document/netpay imports and action endpoints.
- Evidence: TG-03 + TG-07.

### AC-015 Error Contract Stability

- Requirement: Functional rejections return stable status codes and machine-usable error details.
- Verification: contract tests for 404/409/422 paths.
- Evidence: TG-01..TG-07 negative-path cases.

### AC-016 Inbox Workspace Usability

- Requirement: UI supports queue navigation, detail inspection, preview/confirm decisions, and visible failure states.
- Verification: frontend tests and manual script over key workflows.
- Evidence: TG-08.

### AC-017 Human Authority Enforcement

- Requirement: Sensitive transitions (confirmation/rejection/decision) require explicit actor input.
- Verification: API tests ensure missing actor rejected where required and actor persisted.
- Evidence: TG-04 + TG-05.

### AC-018 Projection Non-Authority

- Requirement: Read-side workspace projections never mutate write-side truth directly.
- Verification: architectural tests and route-level inspection with no write actions in projection handlers.
- Evidence: TG-06 + code review checklist.

### AC-019 Performance Baseline

- Requirement: Inbox query surfaces respond within agreed local baseline under representative fixture load.
- Verification: repeatable local benchmark script and threshold report.
- Evidence: TG-09 report.

### AC-020 Operational Recoverability

- Requirement: Failures in ingestion/processing leave records in diagnosable states with retry/reprocess path.
- Verification: forced-failure tests and successful reprocess confirmation.
- Evidence: TG-03 + TG-07.

## Test Groups

- TG-01 Intake contract tests.
- TG-02 Case/evidence/checklist linkage tests.
- TG-03 Controlled data-intake and duplicate tests.
- TG-04 Observation/resolution lifecycle tests.
- TG-05 Policy and attention tests.
- TG-06 Mission control projection tests.
- TG-07 Event trace and idempotency tests.
- TG-08 Frontend workspace and UX behavior tests.
- TG-09 Performance and recoverability baseline tests.

## Traceability Matrix

| Acceptance Criterion | Primary Commands/Queries | Planned Engineering Increments | Primary Test Group |
| --- | --- | --- | --- |
| AC-001, AC-002 | ReceiveIntake, AssociateIntakeWithCase, GetInboxQueue | F-003, F-004, F-009 | TG-01 |
| AC-003, AC-004 | RegisterDocument, DetectDuplicateIntake | F-003, F-011 | TG-03 |
| AC-005 | CaptureEvidence | F-005, F-009 | TG-02 |
| AC-006, AC-007 | ExtractObservations, ConfirmObservation, RejectObservation, SupersedeObservation | F-006 | TG-04 |
| AC-008 | ResolveObservationSubject | F-007 | TG-04 |
| AC-009, AC-010 | EvaluatePolicies, RaiseAttentionItem | F-008 | TG-05 |
| AC-011, AC-018 | GetMissionControlSummary, GetAttentionQueue, GetInboxQueue | F-010, F-014 | TG-06, TG-08 |
| AC-012 | ApplyChecklist, FulfillRequirement, EvaluatePolicies | F-009, F-010 | TG-02, TG-06 |
| AC-013, AC-014 | mutating command set and DomainEvent read paths | F-011, F-013 | TG-07 |
| AC-015 | all endpoint error contracts | F-012 | TG-01..TG-07 |
| AC-016 | Inbox workspace flows | F-014, F-015 | TG-08 |
| AC-019 | Inbox and mission query surfaces | F-017 | TG-09 |
| AC-020 | Process/reprocess/recovery paths | F-011, F-017 | TG-03, TG-09 |

## Definition of Done

WS-001 is Done only if all are true:

1. AC-001 through AC-020 pass with recorded evidence.
2. TG-01 through TG-09 pass in CI-equivalent local execution.
3. No acceptance path bypasses explicit human authority constraints.
4. Traceability chain from intake to attention is reconstructable from stored records.
5. Product and Engineering jointly sign off acceptance report.

## Release Readiness Decision Rule

- READY: all criteria pass with no open critical defects.
- CONDITIONALLY READY: only non-critical documentation/usability deltas remain with approved mitigation.
- NOT READY: any failure in authority, traceability, idempotency, or data integrity criteria.
