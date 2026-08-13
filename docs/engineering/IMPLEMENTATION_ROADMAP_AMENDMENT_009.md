# YARVIS
# Implementation Roadmap Amendment 009

## Status

**RATIFIED**

This is a ratified narrow authority amendment. It supplements Amendments 004–008
only within the Operational Economics authority scope stated here and does not
authorize implementation.

## 1. Demonstrated Contractual Gap

During the separately authorized implementation of Amendment 008, the focused
Workspace test
`tests/test_operational_workspace.py::test_workspace_composes_owner_read_models_without_economic_rollup`
reproduced `403 AUTHORIZATION_DENIED` when it invoked
`POST /operational-economics/facts`. The inherited fixture supplied
`economics.fact.record` in a request header. F-011 correctly ignores that
header as an authority source and resolves the persisted
`mission_work_viewer` membership instead. The current closed persisted role
matrix grants no `economics.*` permission.

The failing operation is the public Operational Economics command
`IC-ECONOMICS-CMD-001` (`RecordEconomicFact`), protected by
`economics.fact.record`. It is not an Operational Workspace permission and
does not establish an incidental Economics grant for Mission Work or Workspace.

## 2. Existing Operational Economics Capability Inventory

| Permission | Existing contract and operation | Category | Proposed by this amendment |
| --- | --- | --- | --- |
| `economics.fact.record` | `IC-ECONOMICS-CMD-001` — `POST /operational-economics/facts` — RecordEconomicFact | append-only fact recording | yes |
| `economics.fact.correct` | `IC-ECONOMICS-CMD-002` — `POST /operational-economics/facts/{id}/corrections` — CorrectEconomicFact | correction that creates a successor fact | no |
| `economics.read` | `IC-ECONOMICS-QRY-001` summary and `IC-ECONOMICS-QRY-002` fact history | read | no |

No other `economics.*` permission appears in the current application contract
catalog. This narrow proposal addresses only the demonstrated record command;
it does not infer an assignment for correction or read authority.

## 3. Proposed Minimal Persisted Role

| Proposed role | Validated permissions | Covered operation | Deliberate non-grants |
| --- | --- | --- | --- |
| `economics_fact_recorder` | `economics.fact.record` | `IC-ECONOMICS-CMD-001` RecordEconomicFact | `economics.fact.correct`, `economics.read`, all Mission Work, Workspace, Radar, Document, Intake, Operational Context, Mission Inbox, Governance, Task, and Process permissions |

Recording does not grant correction or read authority. No Mission Work,
Operational Workspace, Radar, Document Registry, Intake, Operational Context,
or Mission Inbox role receives an Economics permission incidentally. The
Workspace composes owner read models under its existing contract; it does not
become an Economics authority holder.

## 4. Canonical Authority and Transitional Boundary

Effective authority derives exclusively from an active persisted `Principal`,
active `Organization`, active `PrincipalMembership`, the closed server
role-to-permission matrix, and `AuthorityResolutionService`. A token may
identify a subject only. Headers, token claims, request payloads, and fixed
organization identifiers must not grant permissions or select an organization.

If a separately authorized implementation must preserve a legacy
`AuthenticatedPrincipal` boundary, its narrow adapter may receive only an
already-resolved `IdentityAuthorityEnvelope`. It must preserve subject and
organization, project only the validated Economics permission, and must not
read headers or tokens, synthesize or elevate permissions, or replace
`AuthorityResolutionService`.

## 5. Required Fixture and Denial Evidence

A separately authorized implementation must provision a `Principal`,
`Organization`, active `PrincipalMembership`, and the minimal persisted role
for a recording scenario. Its deterministic token may identify only that
subject.

Focused evidence must preserve denial for missing permission, revoked
membership before replay, cross-organization access or concealment according
to the command/query contract, and forged header or token authority or
organization. An otherwise valid replay after revocation must not disclose or
mutate data.

## 6. Relationship, Exclusions, and Next Step

This amendment supplements the persisted-authority invariants ratified in
Amendments 004–008. It does not change their mappings or authorize a role for
`economics.fact.correct` or `economics.read`.

It authorizes no implementation changes, routes, tests, fixtures, migrations,
contracts, F2, F2C, G/H/I, G5 execution, backfill, historical-record change,
push, or merge. It does not authorize correcting inherited header-authority
expectations until this amendment is independently ratified and a separate
implementation mandate is issued.

A separate bounded implementation mandate is required before adding the role,
resolve authority canonically, migrate fixtures, correct the affected
expectations, and resume the relevant regression evidence.
