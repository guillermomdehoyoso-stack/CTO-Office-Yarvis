# YARVIS
# F-011 Governance Contract Amendment 001

## Status

**RATIFIED — CONTRACT PROFILE ONLY — PLANNED RUNTIME**

**Date:** 2026-08-06
**Authority:** Guillermo, Architecture Authority
**Scope:** Compatible F-011 profiles for `IC-GOVERNANCE-QRY-001` and
`IC-GOVERNANCE-EVT-001` only.  No new stable contract ID, runtime handler,
persistence, migration, or implementation authorization is created.

## 1. Authority and Compatibility

The [Interaction Contract Catalog](../architecture/INTERACTION_CONTRACT_CATALOG.md)
defines `IC-GOVERNANCE-QRY-001 EvaluateAuthority` as Governance authority for
target-command authorization and `IC-GOVERNANCE-EVT-001 AuthorityChanged` as a
Governance authority event.  The F-011 profiles below specialize those existing
purposes without changing owner, type, stable ID, criticality, or primary
consumer.  They are compatible `1.1.0` profiles of the historical `1.0.0`
semantics; the immutable Runtime Baseline V1 snapshot remains `P/P` and is not
rewritten by this amendment.

This amendment is ratified under [F-011 Amendment 001](F-011_IDENTITY_AUTHORITY_ENVELOPES_ARCHITECTURE_AMENDMENT_001.md)
and [ADR-014](../decisions/ADR-014_PRINCIPAL_MEMBERSHIP_ACTIVE_ORGANIZATION_AUTHORITY.md).
It does not ratify `IC-GOVERNANCE-QRY-002` or any Identity resolution contract.

## 2. IC-GOVERNANCE-QRY-001 — EvaluateAuthority F-011 Profile 1.1.0

The Query evaluates whether a trusted resolved Principal holds the server-
validated permission required for a named governed target action in the active
canonical Organization.  The caller may provide a selector but never authority,
role, permission, Principal, or Organization truth.  Before returning an allow
decision, the target verifies resource ownership in the same Organization.

The profile requires: trusted Principal ID; server-resolved active Organization;
server-evaluated closed permissions; required permission; target-resource
ownership validation; correlation/trace metadata; no side effects; and
cross-organization or foreign-target concealment as `not found`.  Its primary
consumer remains target-command authorization.  Acceptance evidence must prove
disabled Principal denial, revoked Membership denial, inactive/foreign
Organization rejection, ambiguous selector rejection, no client-claimed
authority, target ownership enforcement, and no query mutation.

## 3. IC-GOVERNANCE-EVT-001 — AuthorityChanged F-011 Profile 1.1.0

The Event asserts that Governance activated or revoked a PrincipalMembership.
It carries only safe identifiers for the changed PrincipalMembership, canonical
Organization, accountable trusted actor, reason/classification where required,
recorded/occurred time, correlation, optional causation, and contract version.
It contains no credential, token, secret, document content, or unnecessary PII.

The asserted transition is idempotent for an equivalent command replay and
conflicting for incompatible reuse according to the future allocated Membership
command's idempotency rule.  A revocation must be visible to authorization of
all subsequent requests; Event consumption itself grants no mutation authority.
Acceptance evidence must prove attribution, replay/conflict behavior, safe
payload, and denial after revocation.

## 4. Explicit Exclusions

This amendment does not add generic user administration, invitations,
delegation, document permissions, DI-003/C09, SSO/OAuth, external identity
providers, workers, queues, brokers, F-016, F-017, F-010, F-014, or F-015.
`IC-GOVERNANCE-QRY-002 RetrieveApplicableDelegation` remains rejected for
F-011; `IC-IDENTITY-CMD-001`, `IC-IDENTITY-QRY-001`, and
`IC-IDENTITY-EVT-001` remain deferred.

## 5. Implementation Gate Effect

The two profiles are ratified but Planned.  A future approved IG-006 must still
allocate the required Principal-resolution and Membership-mutation identities,
approve a detailed implementation/migration design, open F-011 in current
state/sprint, and receive a separate implementation mandate.  This amendment
does not start, authorize, implement, or close F-011.
