# YARVIS
# Implementation Roadmap Amendment 010

## Status

**RATIFIED**

This is a ratified consolidated authority amendment. It supplements Amendments
004–009 only within the Economics, Operational Task, and Process authority
scope stated here and does not authorize implementation.

## 1. Demonstrated Contractual Gaps

The 511-nodeid F-011 regression audit established that the closed persisted
role matrix has no roles for the Economics correction/read, Operational Task,
or Process permissions listed below. The resulting denials are correct: the
inherited fixtures supply those authorities through request headers instead of
persisted PrincipalMembership roles. This proposal does not change the
ratified mappings in Amendments 004–009.

## 2. Economics

| Permission | Contract and operation | Category | Proposed role |
| --- | --- | --- | --- |
| `economics.fact.correct` | `IC-ECONOMICS-CMD-002` CorrectEconomicFact | append-only correction | `economics_fact_corrector` |
| `economics.read` | `IC-ECONOMICS-QRY-001` summary; `IC-ECONOMICS-QRY-002` fact history | read | `economics_viewer` |

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `economics_fact_corrector` | `economics.fact.correct` | `economics.fact.record`, `economics.read`, and all non-Economics permissions |
| `economics_viewer` | `economics.read` | record, correction, and all non-Economics permissions |

`economics_fact_recorder` remains exactly as ratified in Amendment 009 and
does not acquire correction or read authority. Correction does not imply
reading; a separately authorized implementation must preserve the existing
tenant-concealment contract.

Affected evidence: `tests/test_operational_economics.py` correction and
cross-tenant/history scenarios.

## 3. Operational Task

The current catalog contains no Operational Task query contract or
`task.read` permission. It contains exactly the following commands.

| Permission | Contract and operation | Category | Proposed role |
| --- | --- | --- | --- |
| `task.create` | `IC-TASK-CMD-001` CreateOperationalTask | creation | `task_planner` |
| `task.update` | `IC-TASK-CMD-002` UpdateOperationalTask | planning update | `task_planner` |
| `task.assign` | `IC-TASK-CMD-003` AssignOperationalTask | assignment | `task_assigner` |
| `task.transition` | `IC-TASK-CMD-004` TransitionOperationalTask | lifecycle | `task_lifecycle_operator` |
| `task.complete` | `IC-TASK-CMD-005` CompleteOperationalTask | lifecycle | `task_lifecycle_operator` |
| `task.cancel` | `IC-TASK-CMD-006` CancelOperationalTask | lifecycle | `task_lifecycle_operator` |
| `task.dependency.manage` | `IC-TASK-CMD-007` add or remove dependency | dependency administration | `task_dependency_manager` |

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `task_planner` | `task.create`, `task.update` | assignment, lifecycle, dependencies, and all non-Task permissions |
| `task_assigner` | `task.assign` | planning, lifecycle, dependencies, and all non-Task permissions |
| `task_lifecycle_operator` | `task.transition`, `task.complete`, `task.cancel` | planning, assignment, dependencies, and all non-Task permissions |
| `task_dependency_manager` | `task.dependency.manage` | planning, assignment, lifecycle, and all non-Task permissions |

No Mission Work, Workspace, Process, Economics, Radar, Document, Intake,
Operational Context, Mission Inbox, or Governance role gains a Task permission
incidentally. Internal Task-to-Mission-Work projection receives no public write
permission.

Affected evidence: all seven authority/replay/tenant scenarios in
`tests/test_operational_task.py`.

## 4. Process Definitions, Runtime, and Work Association

| Permission | Contracts and operations | Category | Proposed role |
| --- | --- | --- | --- |
| `process.definition.read` | `IC-PROCESS-QRY-001..002` list and retrieve definitions | read | `process_definition_viewer` |
| `process.definition.manage` | `IC-PROCESS-CMD-001..010` create/version/stages/transitions/publish/retire | definition administration | `process_definition_manager` |
| `process.instance.read` | `IC-PROCESS-QRY-003..008` instances, timelines, and work-link queries | read | `process_instance_viewer` |
| `process.instance.start` | `IC-PROCESS-CMD-011` StartProcessInstance | runtime operation | `process_instance_operator` |
| `process.instance.transition` | `IC-PROCESS-CMD-012` TransitionProcessInstance | runtime operation | `process_instance_operator` |
| `process.instance.cancel` | `IC-PROCESS-CMD-013` CancelProcessInstance | runtime operation | `process_instance_operator` |
| `process.instance.work.link` | `IC-PROCESS-CMD-014` LinkProcessInstanceToMissionWork | work association | `process_work_link_coordinator` |
| `process.instance.work.unlink` | `IC-PROCESS-CMD-015` UnlinkProcessInstanceFromMissionWork | work association | `process_work_link_coordinator` |

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `process_definition_viewer` | `process.definition.read` | all definition mutation, all instance, and all non-Process permissions |
| `process_definition_manager` | `process.definition.manage` | definition read, instance, work-link, and all non-Process permissions |
| `process_instance_viewer` | `process.instance.read` | all runtime mutation, work-link, and all non-Process permissions |
| `process_instance_operator` | `process.instance.start`, `process.instance.transition`, `process.instance.cancel` | definition management, reads, work-link, and all non-Process permissions |
| `process_work_link_coordinator` | `process.instance.work.link`, `process.instance.work.unlink` | definition management, runtime lifecycle, reads, and all non-Process permissions |

Definitions, runtime lifecycle, and work association remain distinct duties.
Task and Mission Work receive no Process authority incidentally. The existing
Mission Work workspace query remains governed by `mission.work.read`, not by a
new Process grant.

Affected evidence: `tests/test_process_definitions.py`,
`tests/test_process_runtime.py`, and `tests/test_process_work_association.py`.

## 5. Canonical Authority, Fixture Evidence, and Exclusions

For every proposed role, effective authority derives only from an active
persisted Principal, active Organization, active PrincipalMembership, the
closed server role-to-permission matrix, and AuthorityResolutionService. A
local/test token identifies a subject only. Headers, token claims, payloads,
and fixed organization identifiers must not grant permissions or select an
organization.

Any separately authorized compatibility adapter may accept only an
already-resolved IdentityAuthorityEnvelope. It must preserve subject and
organization, project only validated permissions, and must not read headers or
tokens, synthesize/elevate permissions, or replace AuthorityResolutionService.

Fixtures must persist the Principal, Organization, active Membership, and
minimal role for each scenario. Focused evidence must retain denial for missing
permission, revoked membership before replay, cross-organization access or
concealment, forged header/token authority, and replay after revocation.

This proposal authorizes no roles, adapters, routes, tests, fixtures,
migrations, historical-record changes, F2, G/H/I, push, or merge. It does not
modify Amendments 004–009 or `authentication.py`.

A separate bounded implementation mandate is required before adding these
roles, resolving authority canonically, migrating fixtures, adapting routes,
or resuming the affected regression evidence.
