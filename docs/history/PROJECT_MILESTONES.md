# Yarvis Project Milestones

**Record type:** Append-only historical log
**Purpose:** Preserve the major implemented milestones of Yarvis without replacing
their governing architecture, ADRs, baselines, or engineering evidence.

## Milestones

| Order | Identifier | Name | Objective and delivered capability | Architectural impact / key decisions | Related evidence |
| --- | --- | --- | --- | --- | --- |
| 01 | Foundation | Engineering Foundation | Normalized the repository and established runtime dependencies, configuration, application bootstrap, module and contract registries, persistence, Unit of Work, and command dispatch foundation. | Modular-monolith composition is explicit; registries do not become service locators; persistence and transactions have defined ownership. | `foundation-m1`; Engineering Foundation commits through `7d341bc`. |
| 02 | WS-004A | Mission Work Queue Backend | Added tenant-scoped `MissionWorkItem` creation, assignment, status, priority, stable source identity, and governed events. | Mission Work became the transactional operator aggregate; duplicate prevention uses stable source identity rather than rebuildable Inbox identity. | `c139f74`, `ws004a-backend-complete`; WS-004A engineering baseline. |
| 03 | WS-004B | Mission Work Queue Frontend | Made Mission Work list, detail, filtering, creation from Inbox, assignment, status, and priority operable from the frontend. | The UI remains a contract consumer and recovers duplicate Work through stable source identity. | `1b97b72`, `ws004b-frontend-complete`; WS-004B engineering baseline. |
| 04 | WS-005A | Mission Event Timeline Backend | Added append-only `MissionWorkEvent`, ordered Timeline reads, and accountable internal comments. | Work lifecycle evidence is separate from aggregate state and ordered by per-Work sequence. | `2754b3f`, `ws005a-backend-complete`; WS-005A engineering baseline. |
| 05 | WS-005B | Mission Event Timeline Frontend | Exposed Timeline evidence and append-only comments in Mission Work detail. | Operators consume evidence; the frontend does not rewrite timeline history. | `6be4bcd`, `ws005b-frontend-complete`; WS-005B engineering baseline. |
| 06 | WS-006A | Process Domain Foundation | Added organization-scoped, versioned Process Definitions, draft graph editing, publication, retirement, and validation. | Published definitions are immutable templates; Process runtime remains a distinct owner. | `63740d8`, `ws006a-process-domain-complete`; WS-006A engineering baseline. |
| 07 | AC-001 | Architecture Checkpoint 001 | Recorded the first evidence-based implementation inventory and identified Process Runtime as the next design boundary. | Distinguished implemented, partial, foundation, planned, and exploratory capabilities. | `21270a1`, `architecture-checkpoint-001`; AC-001 companion architecture views. |
| 08 | WS-006C | Process Runtime Backend | Added `ProcessInstance`, append-only Process events, governed graph transitions, terminal completion, cancellation, idempotency, and concurrency control. | Process owns its lifecycle; Work and Process lifecycles remain independent. | `288431e`, `ws006c-process-runtime-backend-complete`; `ADR-PROCESS-INSTANCE-OWNERSHIP`, `ADR-PROCESS-EVENT-MODEL`, `ADR-PROCESS-WORK-LIFECYCLE`. |
| 09 | WS-006D | Mission Work / Process Association | Added Process-owned, historical `ProcessInstanceWorkLink` and idempotent projection of Process source events into Work Timeline. | A Process Instance has at most one active primary link; a Work Item may have many active Process Instances. No lifecycle synchronization or direct Process write to Work Timeline. | `8bf5cd7`, `ws006d-mission-work-process-association-complete`; `ADR-PROCESS-WORK-ASSOCIATION-PROJECTION`. |
| 10 | OV-001 | Operational Economics Architecture | Defined the vertical-agnostic Operational Economics boundary, fact model, correction lineage, currency policy, and roll-up safety rules. | Economics is operational, provenance-bearing, and distinct from accounting/ERP truth; Process/Work association never implies economic roll-up. | `0e9b5b8`, `operational-economics-architecture-001`; Economics ADRs and metric/event documents. |
| 11 | OV-002 | Operational Economics Foundation | Implemented append-only `EconomicFact`, superseding correction lineage, direct subject summaries, tenant isolation, and fact/correction contracts. | Direct summaries are deterministic and currency-safe; roll-ups, snapshots, FX, and accounting adapters remain deferred. | `96d4caf`, `ov002-operational-economics-foundation-complete`; OV-002 baseline. |
| 12 | WS-006E | Operational Workspace Read Model | Added a tenant-safe read composition for one Mission Work Item, its linked Process Instances, unified Timeline, and direct economic summaries. | The Workspace is a bounded query/read model with no duplicate persistence, implicit roll-up, or lifecycle coordination. | `d0f7b3f`, `ws006e-operational-workspace-read-model-complete`; `IC-MISSION-QRY-007`. |
| 13 | WS-006F | Operational Workspace UI | Added the Mission Work operational workspace route and UI over the WS-006E read model. | The frontend formats supplied direct values only; it does not calculate economics or own domain state. | `9751d45`, `ws006f-operational-workspace-ui-complete`; WS-006F engineering baseline. |
| 14 | AC-002 | Architecture Checkpoint 002 | Consolidated the implemented Core boundaries, dependencies, event/read-model strategy, extension points, deprecated navigation concepts, and forward boundaries. | AC-002 is the current As-Is navigation checkpoint; AC-001 remains historical evidence for its earlier baseline. | `docs/architecture/YARVIS_ARCHITECTURE_CHECKPOINT_002.md` (documentation checkpoint; pending commit at record creation). |

## Current Platform State

Yarvis currently has a governed Core centered on Mission Work as the operator-facing
aggregate. Process Runtime governs procedure independently, Operational Economics
records append-only economic facts independently, and Operational Workspace composes
their existing read models for operators. Mission Inbox is rebuildable projection
input, not transactional truth. All implemented core paths preserve Organization
isolation, explicit authority, historical evidence, and owner-local transactions.

Deferred capabilities include explicit economic roll-ups/snapshots, Tasks, Waiting,
SLA, Work/Checklist associations, Documents in the workspace, production authority,
dispatch handlers, worker/scheduler runtime, automation, and AI.

## Phase II Vision

Phase II evolves the implemented Core into a broader governed operating system
without collapsing ownership boundaries. The approved direction is to complete the
technical execution foundations first, then add separately designed operational
extensions (Tasks, Waiting, Checklists, SLA, Documents) and explicit Economics
roll-ups. Automation and AI remain later consumers/proposers of attributable,
authority-governed evidence; they must not become alternate owners of Work, Process,
or Economics state.

Future entries append to this file. Historical entries are not silently rewritten;
later checkpoints may clarify their current navigation status while retaining their
original baseline evidence.
