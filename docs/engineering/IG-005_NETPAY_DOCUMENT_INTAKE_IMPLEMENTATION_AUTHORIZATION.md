# IG-005 — Netpay DI-003 / C09 Implementation Authorization

## Status

**PROPOSED — NOT AUTHORIZED — NOT AN ACTIVE ENGINEERING GATE**

**Candidate work package:** Netpay DI-003 Manual Document Intake and C09 typed
Radar Document Association Intake.
**Authority chain:** [ADR-001 — DI-001 Document Architecture](../decisions/ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md) -> [Netpay DI-003 / C09 Amendment 001](NETPAY_DI003_C09_AMENDMENT_001.md) -> [accepted ADR-013](../decisions/ADR-013_NETPAY_DOCUMENT_INTAKE_ORGANIZATIONAL_AUTHORITY.md) -> this proposed gate.

This document is a reviewable authorization template only.  Its status must be
changed to **Approved implementation gate** by the Architecture Authority only
after all entry criteria are proven.  Until then it grants no runtime work.

## 1. Candidate Scope

The eventual gate may authorize only the following bounded vertical:

- manual synchronous upload of one `application/pdf`, `image/jpeg` (`.jpg` or
  `.jpeg`), or `image/png` file from an existing Netpay Radar request;
- fixed ratified maximum size of 20 MiB;
- magic-byte, declared-type, non-empty-file, size, and SHA-256 checks;
- provider-relative binary persistence outside PostgreSQL through a local
  development Storage Provider adapter;
- Document Registry Document and immutable DocumentVersion registration;
- a typed, organization-safe association to exactly one Radar merchant,
  request, and checklist requirement;
- review transitions and an atomic `valid` decision plus checklist update;
- controlled/audited metadata read and download; and
- append-only Netpay document activity using only safe metadata.

## 2. Explicitly Unauthorized Scope

The eventual gate shall not authorize Gmail, WhatsApp, API intake, OCR, AI,
automatic classification, extraction, semantic document validation, automatic
checklist fulfillment, Evidence creation, generic associations, generic
document UI, cloud storage, public URLs, external sharing, workers, queues,
brokers, retry/scheduler infrastructure, retention automation, physical
deletion, F-011 implementation, or any F-016/F-017/F-010/F-014/F-015 work.

It shall not treat `X-Yarvis-Workspace` as a principal, organization, or
permission source.

## 3. Required Authorization Prerequisites

This gate cannot be approved until all of the following are true:

1. The Amendment is ratified through an Accepted ADR with no unresolved
   BLOCKER or MAJOR findings.
2. Accepted ADR-013's Option A is satisfied: F-011 is implemented, validated,
   and closed, and supplies the required organization/principal/authority
   boundary.  No local authority exception is permitted.
3. A reviewed implementation design defines the exact models, migrations,
   transaction boundary, Storage Provider interface, relative-key construction,
   typed foreign keys/owner-contract checks, download control, and failure
   cleanup.
4. Contract Registry review allocates every added command/query/event identity
   without collision and names its owning context.
5. The active Current State and Current Sprint explicitly open this work
   package without opening a Foundation successor.
6. The policy decision records the maximum size, closed media allowlist,
   sensitive classification, pilot retention rule, and no-delete boundary.

## 4. Required State and Integrity Rules

The implementation design must preserve separate requirement and version
states:

- requirement: `missing`, `received`, `in_review`, `valid`,
  `requires_replacement`;
- version review: `received`, `in_review`, `valid`, `rejected`.

Upload never satisfies a checklist item.  A rejection carries a reason and
actor and preserves its binary/version history.  Replacement appends a new
version with explicit `supersedes` lineage.  `valid` and the corresponding
checklist fulfillment must commit or roll back together.  The current Radar
`received` boolean requires an explicit migration or documented replacement;
silent semantic reuse is prohibited.

Idempotency is organization + caller key + request fingerprint.  SHA-256 byte
equality produces an alert, not merging, automatic versioning, or association
reuse.

## 5. Required Acceptance Evidence

Before closure, focused validation must prove:

- organization and exact authority enforcement for upload, metadata, download,
  review, validate, and reject, including foreign-reference concealment;
- media, signature, empty-file, size, checksum, idempotency, retry conflict,
  and duplicate-byte behavior;
- immutable version and `supersedes` history;
- rejection reason/actor preservation and replacement behavior;
- atomic valid-plus-checklist persistence and rollback;
- no duplicate version or audit history on repeated commands;
- controlled/audited downloads without content, secrets, or PII in activities;
- PostgreSQL migration upgrade, downgrade, and re-upgrade evidence;
- focused regression, compilation, and `git diff --check`; and
- a scope audit proving every excluded subsystem remains absent.

## 6. Production Block and Removal Rule

No deployment or production use is authorized by this proposed gate.  No local
identity adapter is permitted.  Any future production authorization must use
F-011's canonical authenticated authority envelope and preserve organization,
actor provenance, checksums, versions, and audit history.

## 7. Gate Non-Effect

This proposed document does not modify code, tests, migrations, configuration,
the Foundation dependency graph, CURRENT_STATE, CURRENT_SPRINT, Amendment 002
(which remains proposed), or ratified Amendment 003.  It creates no
implementation authority until the stated approval action occurs.
