# IG-001 — DI-002 Implementation Authorization

**Status:** Approved implementation gate
**Authorized by:** [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md) and [ADR-001](../decisions/ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md)
**Authorized work package:** DI-002 — Document Registry Foundation only

## Gate status

**DI-002 runtime scope is OPEN.** This document satisfies the AR-001 and ADR-001 prerequisites for the named package. It is the active engineering-gate record; it does not authorize any adjacent DI, connector, UI, or storage package.

## Approved implementation baseline

DI-002 may implement the Document Registry as the owner of canonical Document identity, metadata, immutable Document Versions, version lineage, provenance, provider-neutral storage references, visibility/archive state, and governed historical associations.

The implementation must provide governed commands and queries; tenant isolation; exact existing authority enforcement; tenant-scoped idempotency and replay; local Unit-of-Work persistence with Document DomainEvents; and deterministic, concealed-absence reads. The Registry does not own Message, Intake, Evidence, connector, binary storage, Task, Process, Project, Mission Work, or subject lifecycle.

## Contract allocation

| Contract | Purpose | Required authority |
| --- | --- | --- |
| IC-DOCUMENT-CMD-001 | CreateDocument | document.create |
| IC-DOCUMENT-CMD-002 | UpdateDocumentMetadata | document.metadata.update |
| IC-DOCUMENT-CMD-003 | AddDocumentVersion | document.version.add |
| IC-DOCUMENT-CMD-004 | ArchiveDocument | document.archive |
| IC-DOCUMENT-CMD-005 | LinkDocumentAssociation | document.association.link |
| IC-DOCUMENT-CMD-006 | UnlinkDocumentAssociation | document.association.unlink |
| IC-DOCUMENT-QRY-001 | RetrieveDocument | document.read |
| IC-DOCUMENT-QRY-002 | ListDocumentVersions | document.read |
| IC-DOCUMENT-QRY-003 | ListDocumentAssociations | document.read |
| IC-DOCUMENT-QRY-004 | ListDocumentsBySubject | document.read |

These use the existing authenticated-principal, exact authority-scope, request-metadata, correlation/causation, and idempotency conventions. They do not introduce a new permission system.

## Migration baseline

DI-002 requires one linear Alembic migration after the current head, with no prior-migration rewrite. It must align exactly with its models; include tables, tenant/history/subject indexes, uniqueness and storage-reference constraints, applicable active-association indexes, and a downgrade. Migration tests, upgrade/downgrade validation, and one-head validation are required.

## Explicit non-goals

DI-002 does not authorize binary upload/download/streaming, local or S3 storage adapters, Gmail, WhatsApp, OCR, malware scanning, AI, sharing, frontend UI, retention automation, document generation, Evidence creation, or automatic creation of Tasks, Processes, or Economics facts.

## Entry criteria

- DI-001 is ratified.
- ADR-001 is Accepted.
- This approved implementation baseline and migration plan are present.
- The ten contracts above are allocated.
- Current State and Sprint declare DI-002 as the active runtime package.

## Exit criteria

- Focused DI-002 and relevant regression tests pass.
- Python compile validation passes.
- Alembic upgrade/downgrade and one-head validation pass.
- Tenant concealment, authority, replay, and concurrency are covered.
- git diff --check passes.
- No deferred scope is introduced.

## Deferred approvals

Production storage choice, file/media policy, retention, sharing, Gmail scope, WhatsApp inclusion, routing policy, and all DI-003+ work remain separately approved decisions.
