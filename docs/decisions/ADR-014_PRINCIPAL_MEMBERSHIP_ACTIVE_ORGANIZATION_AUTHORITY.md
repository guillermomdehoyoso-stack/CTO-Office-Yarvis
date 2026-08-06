# ADR-014 — Principal, Membership, Active Organization, and Authority Envelope

## Status

**ACCEPTED — RATIFIED ARCHITECTURAL DECISION — NO IMPLEMENTATION AUTHORITY**

**Date:** 2026-08-06
**Decision authority:** Guillermo, Architecture Authority
**Proposal:** [F-011 Identity and Authority Envelopes Architecture Amendment 001](../engineering/F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_001.md)
**Sources:** AR-001, Technical Blueprint, Roadmap Amendments 002/003, Contract
Registry baseline, ADR-013, and IG-005.

## Context

Existing Organizations are persistent, but the current development/test
authentication adapter accepts actor, organization, and authority claims from
headers after a deterministic token check.  Radar separately scopes itself by
`X-Yarvis-Workspace`.  Neither pattern establishes persistent Principal,
membership, server-derived permissions, active-organization selection, or
target ownership checks.

F-011 is the Foundation boundary required before F-016 and before the Netpay
document design may seek implementation authority.  It must improve trusted
context without turning Person into a credential or creating a generic identity
administration product.

## Decision

1. Identity owns persistent Principal, with immutable ID, `active`/`disabled`
   lifecycle, and optional Person reference; Person is never credential.
2. Governance owns persistent PrincipalMembership, unique per Principal and
   Organization, with role and `active`/terminal `revoked` lifecycle.
3. The server derives active Organization from active Membership.  A client
   selector is validated input only; multiple memberships require it.
4. Governance owns a closed server-versioned role-to-permission matrix.  A
   client cannot declare role, authority, or permissions.
5. The target receives only a trusted evaluated envelope and must verify both
   permission and resource ownership.  Cross-organization access is concealed
   as `not found`.
6. The deterministic provider remains local/test-only and re-resolves all
   authority-relevant values through persistence.
7. Radar is an obligatory F-011 consumer; `X-Yarvis-Workspace` may remain only
   as a validated transition selector, never authority.

## Consequences

- New persistent Principal and Membership semantics, a migration design, and
  contract amendment review are required before implementation.
- Disabled Principals, revoked Memberships, inactive Organizations, absent
  selectors under multiple memberships, and foreign selectors cannot produce an
  authority envelope.
- Revocation is effective on each later request; it does not rely on a stale
  client claim.
- DI-003/C09 remains blocked until actual F-011 closure, an Approved IG-005,
  and separate implementation authority.

## Explicit Non-Goals

No SSO/OAuth provider, password/token storage, password recovery, invitation,
generic user administration, delegation runtime, F-016/F-017/F-010/F-014/F-015,
document capability, upload/download/storage, DI-003/C09, worker, queue,
broker, cloud service, code, migration, test, configuration, or deployment is
authorized by this Accepted ADR.

## Ratification Record

Guillermo, as Architecture Authority, accepted the eight stated decisions on
2026-08-06 and ratified the associated closed role matrix, Governance contract
profiles, Radar migration requirement, cross-organization concealment, and
DI-003/C09 block.  This Accepted ADR still names no runtime work; a separate
implementation guide approval and mandate remain required.
