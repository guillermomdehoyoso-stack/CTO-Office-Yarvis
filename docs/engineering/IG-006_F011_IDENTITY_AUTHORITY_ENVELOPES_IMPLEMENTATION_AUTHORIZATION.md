# IG-006 — F-011 Identity and Authority Envelopes Implementation Authorization

## Status

**PROPOSED — NOT AUTHORIZED — NOT AN ACTIVE ENGINEERING GATE**

**Candidate work package:** F-011 Identity and Authority Envelopes.
**Authority chain:** Technical Blueprint -> Roadmap Amendments 002/003 ->
ratified F-011 Amendment 001 -> accepted ADR-014 -> ratified Governance
Contract Amendment 001 -> this proposed gate.

This document is an implementation-gate template only.  It neither opens F-011
nor authorizes runtime work until Architecture Authority changes it explicitly
to an Approved implementation gate after all criteria below are proven.

## 1. Candidate Scope

The eventual F-011 gate may authorize only:

- persistent Principal separate from Person, with active/disabled lifecycle;
- persistent PrincipalMembership and active/revoked lifecycle;
- canonical active-Organization resolution and server-owned role/permission
  evaluation;
- trusted Identity/Authority Envelope propagation to target handlers;
- exact target ownership checks and cross-organization `not found` behavior;
- local/test deterministic-provider adaptation that re-resolves persistence;
- required Radar migration from workspace authority to canonical organization;
- necessary linear migrations, narrowly allocated contracts, tests, and closure
  documentation.

## 2. Preconditions for Approval

This gate cannot be approved until:

1. **Satisfied:** F-011 Amendment 001 is ratified through accepted ADR-014.
2. **Satisfied:** Governance Contract Amendment 001 ratifies the F-011
   profiles of authority evaluation and authority change. Principal-resolution
   and Membership-mutation identities remain subject to the bounded allocation
   recorded in the approved implementation design.
3. **Satisfied:** the reviewed and approved
   [F-011 Implementation Design](F-011_IDENTITY_AUTHORITY_ENVELOPES_IMPLEMENTATION_DESIGN.md)
   fixes database constraints, role matrix,
   selector transport, envelope construction, transaction/idempotency behavior,
   error concealment, migration/backfill disposition, and Radar impact.
4. **Pending:** `CURRENT_STATE` and `CURRENT_SPRINT` must explicitly open F-011 without opening
   F-016, F-017, F-010, F-014, F-015, DI-003, or C09.
5. **Pending:** Architecture Authority must approve the bounded implementation
   of Slices A-I under this gate.
6. **Pending:** a separate implementation mandate must name the branch, scope, and validation
   responsibility.

## 3. Required Invariants and Evidence

Implementation must prove persistent Principal/Membership state; membership
uniqueness; immediate revocation; disabled-principal denial; active Organization
selection; server-derived permissions; target ownership checks; no authority
from arbitrary headers; tenant concealment; idempotency where allocated; and no
secrets or unnecessary PII in events/logs.

Radar acceptance requires preserved merchant/request/checklist/next-action/
close/reopen/activity behavior, canonical organization context, and focused
cross-organization command/query evidence.  Legacy `checklist.received` gains
no documentary meaning in F-011.

Closure additionally requires focused and affected regression tests, migration
upgrade/downgrade/re-upgrade, compile/Docker validation, `git diff --check`,
scope audit, and a factual closure record.

## 4. Explicit Exclusions

This proposed gate excludes external identity providers, SSO, OAuth, passwords,
credentials, tokens, invitations, generic identity administration, delegation
runtime, documents, Document Registry extensions, DI-003/C09, upload,
download, storage, Gmail, WhatsApp, OCR, AI, cloud services, workers, queues,
brokers, F-016, F-017, F-010, F-014, and F-015.

## 5. Gate Non-Effect

This guide changes no code, test, migration, configuration, or Foundation
dependency graph. F-011 remains Not Started and Not Authorized pending explicit
state/sprint opening, authorization of Slices A-I, and the separate mandate.
DI-003/C09 remains blocked until real F-011 closure plus an expressly Approved
IG-005 and separate mandate.
