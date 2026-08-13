# YARVIS
# Implementation Roadmap Amendment 008

## Status

**PROPOSED — PENDING INDEPENDENT REVIEW AND RATIFICATION**

This is a narrow F-011 authority proposal. It supplements Amendments 004–007
only for the existing Mission Work authority gap described here. It does not
authorize implementation.

## 1. Demonstrated Contractual Gap

G4 reproduced
`tests/test_mission_work.py::test_complete_status_transition_matrix_records_one_event[open-assigned]`
as `403 AUTHORIZATION_DENIED` with reason `principal_not_found`. The inherited
Mission Work fixtures persist only Organizations, then supply a subject,
organization, and `mission.work.*` claims in request headers. F-011 correctly
resolves authority from persisted Principal and active PrincipalMembership, so
those header-only scenarios are denied.

The resulting fixture debt propagates to Mission Work, its Timeline,
Operational Task scenarios that create or project Mission Work evidence, and
Operational Workspace scenarios that read it. The closed persisted role matrix
does not grant any existing `mission.work.*` capability.

## 2. Existing Mission Work Capability Inventory

| Permission | Protected existing contracts and operations | Category |
| --- | --- | --- |
| `mission.work.read` | `IC-MISSION-QRY-004` list work items; `IC-MISSION-QRY-005` retrieve work item; `IC-MISSION-QRY-006` retrieve timeline; `IC-MISSION-QRY-007` retrieve work-item workspace; `IC-WORKSPACE-QRY-001` retrieve organization operational-workspace overview | read |
| `mission.work.create` | `IC-MISSION-CMD-002` CreateMissionWorkItemFromInbox; `IC-MISSION-CMD-006` AddMissionWorkItemComment | operation |
| `mission.work.status.change` | `IC-MISSION-CMD-004` ChangeMissionWorkItemStatus | lifecycle operation |
| `mission.work.priority.change` | `IC-MISSION-CMD-005` ChangeMissionWorkItemPriority | lifecycle operation |
| `mission.work.assign` | `IC-MISSION-CMD-003` AssignMissionWorkItem, including governed unassignment | administration |

No other `mission.work.*` permission appears in the current application
contract catalog. Mission Work process-link history is `IC-PROCESS-QRY-006`
and requires `process.instance.read`; it is outside this proposal. Operational
Task uses its own `operational.task.*` contracts and permissions. The internal
Timeline and task/process projectors do not receive a new write permission:
their persistence is internal behavior, not a public authority grant.

## 3. Proposed Minimal Persisted Roles

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `mission_work_viewer` | `mission.work.read` | all Mission Work mutations and all non-Mission-Work permissions |
| `mission_work_operator` | `mission.work.read`, `mission.work.create`, `mission.work.status.change`, `mission.work.priority.change` | `mission.work.assign` and all non-Mission-Work permissions |
| `mission_work_coordinator` | `mission.work.read`, `mission.work.assign` | create, comment, status, priority, and all non-Mission-Work permissions |

Reading does not grant mutation. Operating the lifecycle or adding a comment
does not grant assignment. Coordinating assignment does not grant creation,
commenting, status, or priority changes. A Principal may hold multiple persisted
memberships only through the existing governed membership mechanism; this
proposal creates no global or composite role. No Radar, Intake, Operational
Context, Mission Inbox, Document Registry, Governance, Task, or Process role
receives Mission Work authority incidentally.

## 4. Canonical Authority and Transitional Boundary

Effective authority derives exclusively from an active persisted Principal,
active Organization, active PrincipalMembership, the closed server role-to-
permission matrix, and AuthorityResolutionService. A token may identify a
subject only. Headers, token claims, request payloads, and fixed organization
identifiers must not grant permissions or select an organization.

If a separately authorized implementation must preserve a legacy
AuthenticatedPrincipal boundary, a narrow adapter may receive only an already-
resolved IdentityAuthorityEnvelope. It must preserve principal and organization,
project only validated Mission Work permissions, and must not read headers or
tokens, synthesize/elevate permissions, or replace AuthorityResolutionService.

## 5. Required Fixture and Denial Evidence

An implementation mandate must migrate affected fixtures to persist Principal,
Organization, active PrincipalMembership, and the minimal role for every
scenario. Deterministic tokens identify only the fixture subject.

Focused evidence must preserve denials for missing permission, revoked
membership before replay, cross-organization access or concealment as specified
by each contract, and forged header/token authority or organization. An
otherwise valid replay after revocation must not disclose or mutate data.

## 6. Relationship, Exclusions, and Next Step

This proposal follows the persisted-authority invariants ratified in Amendments
004–007. It neither changes their mappings nor modifies F2, F2C, G/H/I, Radar,
Document Registry, migrations, routes, contracts, historical records, or
`authentication.py`. It authorizes no profiles encoded in tokens, header-based
authority, fixed organization identifiers, backfill, push, or merge.

The next step is independent review and ratification. Only a subsequent,
bounded implementation mandate may add roles, adapters, fixtures, tests, or
route changes and then resume G4/G5.
