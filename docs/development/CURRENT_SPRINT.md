# Current Sprint

## Identity

**Work package:** DI-002 — Document Registry Foundation
**Authorization:** [IG-001](../engineering/IG-001_DI002_IMPLEMENTATION_AUTHORIZATION.md), under AR-001 and ADR-001.

## Goal

Implement the smallest production-ready Document Registry backend slice: canonical metadata, immutable version lineage, provenance, provider-neutral storage-reference metadata, and governed subject associations.

## Current gate

DI-002 implementation is open. AC-002 is completed historical documentation evidence and is no longer the active gate.

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

TO BE VERIFIED after DI-002 validation and review.
