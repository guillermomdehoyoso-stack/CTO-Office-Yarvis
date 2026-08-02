# Current Sprint

## Identity

**Work package:** DI-002 - Document Registry Foundation (completed)
**Authorization:** [IG-001](../engineering/IG-001_DI002_IMPLEMENTATION_AUTHORIZATION.md), under AR-001 and ADR-001.

## Goal

Implemented and validated the production-ready Document Registry backend slice: canonical metadata, immutable version lineage, provenance, provider-neutral storage-reference metadata, governed subject associations, runtime registration, and API routes.

## Current gate

DI-002 implementation is complete. AC-002 remains completed historical documentation evidence. DI-003 is the next planned package and requires its own authorization before implementation.

## Scope

- Document aggregate and immutable Document Versions.
- Provider-neutral storage references without binary I/O.
- Historical tenant-safe associations to Organization, Site, Project, Mission Work Item, Operational Task, and Process Instance.
- Governed commands, queries, authority, idempotency, events, migration, tests, and documentation.

## Explicitly out of scope

Binary upload/download/streaming; storage adapters; Gmail/WhatsApp; OCR; malware scanning; sharing; retention automation; AI; frontend UI; Evidence creation; and automatic Task, Process, or Economics creation.

## Entry criteria

All IG-001 entry criteria are satisfied.

## Exit criteria

All IG-001 exit criteria are satisfied, with no deferred scope introduced.

## Next package

DI-003 is the next planned package. DI-002 does not authorize DI-003; a new ratified authorization is required before implementation proceeds.
