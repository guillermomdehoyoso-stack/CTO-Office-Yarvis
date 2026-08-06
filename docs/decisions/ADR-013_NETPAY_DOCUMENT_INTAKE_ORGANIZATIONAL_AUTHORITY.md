# ADR-013 — Netpay Document Intake Organizational Authority

## Status

**ACCEPTED — RATIFIED ARCHITECTURAL DECISION — NO IMPLEMENTATION AUTHORITY**

**Date:** 2026-08-06
**Decision authority:** Guillermo, Architecture Authority
**Proposal:** [Netpay DI-003 / C09 Document Intake Amendment 001](../engineering/NETPAY_DI003_C09_AMENDMENT_001.md)
**Governing sources:** [ADR-001 — DI-001 Document Architecture](ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md), [AR-005](../architecture/AR-005_REQUIREMENT_SEMANTIC_ARCHITECTURE_RATIFICATION.md), [IG-004](../engineering/IG-004_REQUIREMENT_DEFINITION_IMPLEMENTATION_AUTHORIZATION.md), and [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md).

## Context

The Netpay Radar identifies data with a client-supplied `X-Yarvis-Workspace`
header and stores a local `workspace_id`.  The canonical Document Registry
requires a persisted `organization_id` and exact authority evaluation.  The
header is therefore neither an authenticated principal nor a canonical
organization authority.

Manual document intake would store sensitive evidence and expose upload,
metadata, download, review, and validation actions.  Treating the workspace
header as sufficient would permit arbitrary tenant assertion and would violate
the tenant/authority boundary required by DI-001 and DI-002.

## Options Considered

### Option A — Wait for F-011

Do not implement Netpay DI-003/C09 until F-011 supplies authenticated
principal, canonical organization identity, and target authority enforcement.
The vertical then uses the established envelope without inventing parallel
identity or permission behavior.

### Option B — Provisional Local Development Exception (rejected)

This considered alternative would have introduced a tightly bounded,
non-production development adapter for one preconfigured, persisted canonical
organization.  It is rejected and creates no adapter, identity mechanism, or
exception.

## Decision

**Option A is accepted.**  Netpay DI-003/C09 implementation shall not start
until F-011 is implemented, validated, closed, and separately authorized for
the target environment.

**Option B is rejected.**  No local, provisional, or non-production identity
exception is authorized.  This ADR neither creates a development identity
mechanism nor permits a client to choose an organization.

## Consequences

- `X-Yarvis-Workspace` remains context only and cannot authorize document
  operations.
- Every document, version, association, review, and download is scoped to a
  canonical organization and an authorized actor.
- Cross-organization references are concealed as `not found`.
- The Document Registry retains ownership of canonical Document and
  DocumentVersion identity; Netpay owns its typed Radar association and
  requirement state.
- The ratified Foundation chain remains unchanged.  F-011 remains the next
  Foundation package; F-016, F-017, F-010, F-014, and F-015 are not started.

## Constraints and Non-Goals

This Accepted ADR ratifies the Amendment's bounded architectural design and
the decisions stated above.  It does not open DI-003/C09, allocate new
contracts, or authorize code, migrations, tests, UI, filesystem storage,
download, retention, cloud storage, Gmail, WhatsApp, OCR, AI, workers, queues,
brokers, or public URLs.  F-011 closure, an expressly Approved IG-005, and a
separate implementation mandate are all required before runtime work.

## Ratification Record

Architecture Authority confirmed conformance with ADR-001, DI-001, AR-005,
IG-004, and AR-001; selected Option A; rejected Option B; and ratified the
20 MiB limit, closed MIME allowlist, explicit `received` migration, typed
integrity, separate permissions, append-only safe audit, pilot retention, and
no-purge/no-physical-delete boundaries.

## Status Effect

The Architecture Index records this accepted decision and the ratified
Amendment.  Current State and Current Sprint remain unchanged because the
implementation gate is not open.  IG-005 remains Proposed and Not Authorized.
