# ADR-001 — Ratify DI-001 Document Architecture

**Status:** Accepted
**Date:** 2026-07-31
**Decision record:** AR-001-specific ADR-001 record; it does not renumber, replace, or supersede the legacy `ADR-001-case-as-operational-core.md`.

## Context

DI-001, [Data Intake and Document Architecture](../architecture/DATA_INTAKE_AND_DOCUMENT_ARCHITECTURE.md), defines a preservation-first, provider-neutral architecture for intake and documents. DI-002 correctly did not begin while DI-001 remained a proposal without explicit implementation authority.

AR-001 now supplies the governing lifecycle and decision process. This ADR applies that framework to the reviewed DI-001 scope.

## Decision

The Architecture Authority ratifies DI-001 as the governing architecture for the Document Registry boundary.

The ratified decision preserves these constraints:

- Document Registry owns canonical document metadata, version lineage, provenance, storage-reference metadata, visibility, archival state, and governed subject associations.
- Document Registry does not own Message, Intake, connector, Evidence, binary persistence, Task, Process, Project, or Mission Work lifecycle.
- Message, Intake Item, Document, Evidence, Binary Artifact, Source Artifact, External Reference, and Generated Document remain distinct concepts and ownership boundaries.
- Storage remains provider-neutral; absolute machine paths are not domain truth; a provider migration cannot change Document identity.
- Connector input is preserved before interpretation and cannot directly create authoritative business state without a governed owner contract.
- Tenant isolation, explicit authority, provenance, historical preservation, and non-authoritative projections remain mandatory.

## Implementation authority granted

This ADR explicitly authorizes **DI-002 — Document Registry Foundation** as the first runtime implementation under DI-001.

DI-002 is limited to canonical document metadata, immutable version records, provenance, storage-reference metadata, visibility/archive state, governed historical associations, owner contracts, tenant-safe queries, idempotency, events, migrations, and conformance validation.

This authorization does **not** authorize DI-003 or any upload/download/streaming, filesystem or object-storage adapter, Gmail, WhatsApp, OCR, malware scanning, external sharing, retention automation, AI classification, document generation, frontend UI, Evidence creation, or automatic Task/Process creation.

DI-002 remains subject to the active engineering gate, applicable contract allocation, reviewed implementation design/baseline, migration evidence, and validation requirements.

## Consequences

- DI-001 is effective architectural authority for DI-002 within this ADR's scope, even though its original proposal document is retained unchanged as historical proposal evidence.
- DI-002 may proceed only as the specifically scoped implementation package above.
- Future DI work requires its own explicit authorization; it is not implied by this decision.
- The Architecture Index and roadmap must distinguish DI-001's ratified authority from unapproved later DI work.

## Remaining approvals

Before DI-002 begins, the implementation package must confirm the active engineering gate, allocate/validate applicable interaction contracts, approve its implementation design and migration plan, and resolve any package-specific human decisions. Production storage provider, file/media policy, retention, external sharing, Gmail scope, WhatsApp inclusion, and routing policy remain deferred decisions.
