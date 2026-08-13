# YARVIS
# Implementation Roadmap Amendment 005

## Status

**RATIFIED**

This is a ratified narrow authority amendment. It supplements Amendment 004
only within the Intake authority scope stated here and does not authorize
implementation.

## 1. Purpose and Relationship to Amendment 004

This narrow amendment resolves the demonstrated F-011 compatibility gap between
the persistence-resolved authority model and the existing Intake contracts.
`ReceiveIntake` requires `inbound.intake`; `RetrieveDeterministicIntakeDetail`
requires `inbound.read`; neither capability is in the closed F-011 role matrix.

Amendment 004 remains ratified, effective, and frozen for its Radar command and
event scope. This amendment neither changes Amendment 004's Radar decisions nor
authorizes implementation.

## 2. Canonical Intake Authority Mapping

The following permissions are canonical, server-evaluated permissions. Their
identifiers retain compatibility with the existing Intake contracts; they are
not client authority claims.

| Role | Validated permissions | Authorized Intake capability |
| --- | --- | --- |
| `inbound_viewer` | `inbound.read` | `RetrieveDeterministicIntakeDetail` |
| `inbound_operator` | `inbound.read`, `inbound.intake` | `ReceiveIntake` and Intake detail retrieval |

`inbound.intake` authorizes only `ReceiveIntake`. `inbound.read` authorizes
only `RetrieveDeterministicIntakeDetail`. Neither permission is added to
`radar_viewer`, `radar_operator`, or `foundation_membership_operator`.

## 3. Authority Source and Transitional Adapter

Effective Intake authority is derived only from a persisted active `Principal`,
persisted active `Organization`, active `PrincipalMembership`, and the closed
server role-to-permission matrix, as resolved by `AuthorityResolutionService`.

A narrow transitional adapter from `IdentityAuthorityEnvelope` to
`AuthenticatedPrincipal` is authorized solely for the existing Intake
contracts. It accepts only an already-resolved envelope; preserves the resolved
subject and organization; and projects `inbound.intake` or `inbound.read` only
when that permission is present in the envelope. It does not read headers,
interpret tokens, add permissions, or replace `AuthorityResolutionService`.

## 4. Security Invariants and Acceptance Evidence

- A deterministic local/test token identifies a subject only; it grants no
  organization, role, permission, or authority.
- `X-Yarvis-Authority`, `X-Yarvis-Organization`, and all equivalent request
  headers cannot increase authority.
- Missing or disabled Principals, absent or revoked Memberships, inactive
  Organizations, and absent permissions deny before mutation or replay.
- Cross-organization Intake retrieval remains concealed as not found.
- Deterministic fixtures provision Principal, Organization, and active
  PrincipalMembership through persistence; no token profile or fixed tenant ID
  may bypass resolution.
- Tests must prove successful authorized Intake, missing-permission denial,
  revoked-membership denial before replay, forged-header denial, canonical
  organization ownership, cross-organization concealment, and no duplicate
  effects on success/replay.

## 5. Exclusions and Next Mandate

This amendment authorizes no runtime code, adapter implementation, migration,
Radar receipt change, backfill, fixture-global optimization, timeout change,
historical-record modification, F2 work, push, or merge.

A separate implementation mandate remains required to authorize the narrow
Intake adapter, focused fixtures, tests, and validation evidence.
