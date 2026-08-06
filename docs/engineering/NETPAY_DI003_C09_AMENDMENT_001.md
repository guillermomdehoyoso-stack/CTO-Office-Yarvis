# YARVIS
# Netpay DI-003 / C09 Document Intake Amendment 001

## Status

**RATIFIED — ARCHITECTURAL DESIGN ONLY — NOT IMPLEMENTATION AUTHORIZATION**

**Scope:** A decision package for a deliberately narrow Manual Document Intake
and typed Netpay document-association slice.  It is ratified by
[ADR-013](../decisions/ADR-013_NETPAY_DOCUMENT_INTAKE_ORGANIZATIONAL_AUTHORITY.md)
on 2026-08-06.  It does not alter the Foundation completion path, the active
engineering gate, or any pending F work package.

**Sources:** [ADR-001 — DI-001 Document Architecture](../decisions/ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md),
[Data Intake and Document Architecture](../architecture/DATA_INTAKE_AND_DOCUMENT_ARCHITECTURE.md),
[AR-005 — Requirement Semantic Architecture](../architecture/AR-005_REQUIREMENT_SEMANTIC_ARCHITECTURE_RATIFICATION.md),
[IG-004](IG-004_REQUIREMENT_DEFINITION_IMPLEMENTATION_AUTHORIZATION.md),
and [Implementation Roadmap Amendments 002](IMPLEMENTATION_ROADMAP_AMENDMENT_002.md)
and [003](IMPLEMENTATION_ROADMAP_AMENDMENT_003.md).

## 1. Purpose

The Netpay Operational Radar has a bounded, workspace-scoped checklist but no
governed document intake.  DI-002 deliberately excludes binary transfer,
storage adapters, download, UI, retention automation, and document validation.
C09 Artifact / Document Association Intake is also explicitly deferred.

This proposal submits the minimum vertical needed to accept one manual
document at a time from an existing Radar request while preserving the
Document Registry as the owner of Document identity and version lineage.  It
does not create a generic document platform, a generic association model, or
a substitute identity system.

## 2. Ratified DI-003 Manual Document Intake Boundary

If separately opened by an approved implementation gate after F-011 is
implemented, validated, and closed, the vertical may provide only:

- a synchronous manual upload initiated from an existing Netpay Radar request;
- exactly one `application/pdf`, `image/jpeg` (`.jpg` or `.jpeg`), or
  `image/png` file per operation;
- declared-type and magic-byte agreement, non-empty-file, maximum-size, and
  SHA-256 verification before registration;
- one canonical `Document` and one immutable `DocumentVersion`, using the
  existing Document Registry ownership and storage-reference semantics;
- a binary stored outside PostgreSQL through a provider-relative storage key;
- a filesystem provider **only** as a development adapter behind a Storage
  Provider boundary; and
- controlled, audited metadata read and binary download.

The ratified maximum is **20 MiB (20 * 1024 * 1024 bytes)** per file.  It must
be enforced before a binary is persisted or an effective DocumentVersion is
created.  Declared MIME type and filename extension are not authoritative:
effective type must be verified by magic bytes.  Rejection must not leave a
partial binary or inconsistent document record.

This proposal does not authorize Gmail, WhatsApp, API intake, OCR, AI,
classification or extraction, semantic or automatic documentary validation,
cloud storage, public URLs, workers, queues, brokers, retry services,
retention automation, physical deletion, or external sharing.

## 3. Ratified C09 — Typed Netpay Document Association

The association is a Netpay-owned, explicit record with referential integrity
to exactly one organization, one Netpay merchant, one Radar request, one Radar
checklist requirement, one Document, and the submitted DocumentVersion.  Each
reference must be in the same canonical organization and must be verified by a
foreign key or a named owner-contract validation.  The association records its
purpose, manual origin, actor, timestamps, and immutable historical lineage.

The implementation must prove transactionally that merchant belongs to the
organization, request belongs to merchant, checklist requirement belongs to
request, Document and DocumentVersion belong to the same organization, and
DocumentVersion belongs to Document.  No association may combine incompatible
organization, merchant, request, requirement, Document, or DocumentVersion.

The proposal expressly forbids an open `subject_type` / `subject_id` model,
unconstrained JSON references, or cross-workspace lookup.  It therefore does
not broaden the Document Registry's existing closed association subjects by
silently making Radar records generic subjects.

`workspace_id` remains Radar-local context only.  It is not an organization,
principal, permission, or authorization source.  A client must never choose an
arbitrary organization through a request header or body.

## 4. States, Checklist, and Historical Preservation

Two state dimensions remain distinct:

| Owner | States | Meaning |
| --- | --- | --- |
| Radar requirement association | `missing`, `received`, `in_review`, `valid`, `requires_replacement` | Current fulfillment condition of this specific Radar checklist requirement. |
| Immutable DocumentVersion review | `received`, `in_review`, `valid`, `rejected` | Attributable review outcome for one submitted version. |

Required transition rules are:

1. Upload creates `received`; it never satisfies the checklist.
2. A reviewer may move a submitted version to `in_review` and then to `valid`
   or `rejected` under distinct authority.
3. Rejection requires a non-empty reason and retains the file, checksum,
   decision, actor, and time.  The linked requirement becomes
   `requires_replacement`.
4. A replacement is a newly appended DocumentVersion with an explicit
   `supersedes` reference; it never overwrites an accepted version or decision.
5. Transition to version `valid` and the corresponding checklist fulfillment
   update occur in one transaction.
6. The existing Radar `received` boolean must be replaced or explicitly
   reinterpreted by the reviewed implementation design and migration.  It may
   not silently continue to mean both receipt and validated fulfillment.

No readiness engine, automatic closure, Evidence creation, workflow transition,
or requirement-instance semantics are introduced.

## 5. Ratified Organizational Authority Decision

**Option A is accepted.**  DI-003/C09 implementation must wait for F-011 to
supply authenticated principal, canonical organization, and exact authority
enforcement.  **Option B is rejected:** no local, provisional, or
non-production identity exception is authorized.

`X-Yarvis-Workspace` is Radar-local context only; it is never identity,
organization, permission, or authorization.  Upload, metadata read, download,
review submission, and validate/reject are distinct permissions.  A foreign or
unauthorized reference must be concealed as `not found`.

## 6. Idempotency, Duplicate Bytes, and Bitácora

Manual-upload idempotency is `(organization, caller idempotency key, request
fingerprint)`.  A matching retry returns the prior accepted result; a reused
key with a different fingerprint is a conflict.  SHA-256 equality is an alert
for the operator; it neither merges Documents nor changes source, association,
or replacement lineage.  Repeated close or replacement requests must not
duplicate a version or audit entry.

The Netpay-owned append-only activity record must contain only identifiers,
event type, actor, recorded time, correlation/idempotency metadata, and safe
decision metadata.  Minimum events are:

- `upload_received`;
- `checksum_recorded`;
- `document_associated`;
- `review_requested`;
- `document_validated`;
- `document_rejected`;
- `document_replaced`; and
- `document_downloaded`.

Binary data, document content, secrets, raw personal data, and credentials are
prohibited from activity and trace payloads.

## 7. Privacy, Retention, and Storage

Each submitted document is classified as sensitive by default.  Least-privilege
metadata display, controlled/audited download, and no external sharing by
default are mandatory.  The pilot retains accepted evidence; it introduces no
automated purge, physical deletion, legal-hold process, retention schedule, or
cross-organization sharing.  Those matters remain pending policy and must not
be simulated by deleting records or blobs.

The binary store is not PostgreSQL and its filesystem path is never a domain
identifier.  A provider-relative key, checksum, size, and storage metadata are
registered with the DocumentVersion.  The existing legacy direct upload route
is implementation evidence only and must not be generalized.

## 8. Foundation Dependencies and Non-Interference

The ratified Foundation completion path remains unchanged:

```text
F-012 -> F-013 -> F-011 -> F-016 -> F-017 -> F-010 -> F-014 -> F-015
```

DI-003/C09 is not inserted into this graph.  It neither starts nor completes
F-011, F-016, F-017, F-010, F-014, or F-015.  F-011 completion is the
prerequisite for any Netpay document implementation.  This ratification grants
no Foundation completion claim.

No new interaction-contract identifiers are allocated by this proposal.  A
future approved implementation gate must allocate any additional contract only
after contract-registry uniqueness and ownership review.

## 9. Ratified Decisions and Future Gate Criteria

Architecture Authority has ratified all of the following:

1. Option A; no authority exception before F-011.
2. 20 MiB maximum and the closed PDF/JPEG/PNG media allowlist.
3. Explicit migration of Radar `received`; no legacy received value is
   automatically valid, and only `valid` may satisfy a documentary requirement.
4. Typed association integrity using foreign keys, constraints, and
   transactional validations; no generic polymorphism.
5. Separate permissions; append-only safe audit; foreign references concealed
   as `not found`.
6. Sensitive-by-default pilot retention, no automated purge or physical
   deletion, and ratified retention/disposition policy required before
   production.

Any implementation gate still requires F-011 closure, an expressly Approved
IG-005, a separate implementation mandate, contract allocation, reviewed
implementation/migration design, and a current engineering gate.  Ratification
does not begin code.

## 10. Explicit Non-Authorization

This ratified architecture authorizes no runtime work.  Until F-011 is closed,
IG-005 is expressly Approved, and a separate implementation mandate exists, it
does not authorize code, tests, migrations, configuration, deployment, staging,
commit, or production use.
