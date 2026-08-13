# YARVIS
# Implementation Roadmap Amendment 006

## Status

**PROPOSED — PENDING INDEPENDENT REVIEW AND RATIFICATION**

This proposal is not ratified and authorizes no implementation.

## 1. Demonstrated Contractual Gap

F-011 G3 regression evidence identified two existing governed contracts whose
required scopes are absent from the closed F-011 matrix and Amendment 005:

- `AssociateIntakeOperationalContext` (`IC-INBOX-CMD-002`) requires
  `inbound.context.associate`.
- `ListMissionInbox` (`IC-MISSION-QRY-002`) and
  `RetrieveMissionInboxItem` (`IC-MISSION-QRY-003`) require
  `mission.inbox.read`.

The G3 tests used organization and authority headers, while F-011 correctly
treats the deterministic token as subject identification only. That evidence
does not authorize restoration of header authority.

## 2. Proposed Canonical Capabilities and Minimal Roles

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `inbound_context_operator` | `inbound.context.associate` | `inbound.intake`, `inbound.read`, all Radar and Mission permissions |
| `mission_inbox_viewer` | `mission.inbox.read` | all Intake mutation, Operational Context, Radar and Mission Work permissions |

The roles are separate from `radar_*`, `inbound_viewer`, `inbound_operator`,
and `foundation_membership_operator`. A subject may receive more than one
persisted active membership only through existing governed membership rules;
this proposal grants no incidental permission through either role.

## 3. Exact Authorized Operations

`inbound.context.associate` authorizes only
`AssociateIntakeOperationalContext` through
`POST /intake/deterministic/{intake_id}/operational-context`
(`IC-INBOX-CMD-002`). It does not authorize retrieval of the association;
that remains governed by its existing `inbound.read` query contract.

`mission.inbox.read` authorizes only `ListMissionInbox` and
`RetrieveMissionInboxItem` through `IC-MISSION-QRY-002` and
`IC-MISSION-QRY-003`. It grants no Mission Inbox write capability. Mission
Inbox projection is an internal consequence of already-authorized domain
events, not a client-invocable write operation, so no additional permission is
proposed for projection.

## 4. Authority Source and Transitional Boundary

Effective authority may arise only from a persisted active `Principal`, active
`Organization`, active `PrincipalMembership`, the closed server role-to-
permission matrix, and `AuthorityResolutionService`. A deterministic token
identifies a subject only.

If an unchanged legacy contract still consumes `AuthenticatedPrincipal`, a
narrow transitional adapter may be implemented only after ratification. It
must accept an already-resolved `IdentityAuthorityEnvelope`, preserve its
principal and organization, and project exactly one required scope only when
that validated permission is present. It must not read headers or tokens,
synthesize permissions, elevate scopes, or replace
`AuthorityResolutionService`.

## 5. Required Denials and Test Fixtures

Missing permission, disabled Principal, absent or revoked Membership,
inactive Organization, cross-organization target, forged authority/organization
header, forged token claim, and replay after revocation must deny before a
mutation or replay result is returned. Cross-organization reads remain
concealed according to their existing contracts.

Focused fixtures must persist the `Principal`, `Organization`, active
`PrincipalMembership`, and role. The token may identify only that subject; it
must not encode a role, permission, organization, or privileged profile.

## 6. Exclusions and Next Mandate

This proposal changes no runtime code, migrations, fixtures, tests, routes,
F2C artifacts, Document Registry, Document Routes, G/H/I, backfill, or the 62
historical records. It creates no token profile, hard-coded organization,
header-derived authority, push, or merge.

Independent review and ratification are required before a separate, bounded
implementation mandate may address the two authority mappings and their
focused evidence.
