# Current Sprint

## Identity

**Work package:** DI-003 C06 — Requirement Definition Catalog (completed)
**Authorization:** [IG-004](../engineering/IG-004_REQUIREMENT_DEFINITION_IMPLEMENTATION_AUTHORIZATION.md), under AR-005, DR-002, and EP-001.

## Goal

Deliver immutable, tenant-local, Published Dossier Template Version-bound Requirement Definitions with governed registration, authoritative retrieval, semantic dependencies, durable idempotency, and PostgreSQL-backed historical protection.

## Closure status

C06B2A, C06B2B-1, and C06B2B-2 are complete. C06 implementation and technical validation are closed by [C06 Requirement Definition Catalog Closure](../engineering/C06_REQUIREMENT_DEFINITION_CLOSURE.md).

## Completed scope

- Requirement Definition and same-version dependency persistence.
- Registration command and two authoritative retrieval queries.
- Exact authority, tenant concealment, Published Template eligibility, receipts, replay/conflict, rollback, and concurrency behavior.
- Immutable Definition and dependency protection, including late-insert prevention.
- Linear migration `20260804_29` with validated downgrade/re-upgrade.

## Validation evidence

- C06 focused suite: 18 passed.
- Affected regression: 38 passed.
- Migration round trip: `20260803_28 -> 20260804_29 -> 20260803_28 -> 20260804_29`.
- PostgreSQL verification: two tables, one index, 13 constraints, three triggers, and three protection functions.
- Docker compilation and `git diff --check` passed.

## Explicitly deferred

C07 Requirement Instance Bootstrap, C08 Requirement Dependency Readiness, C09 Artifact/Document Association Intake, Milestones, Evidence, Commercial behavior, Proposal generation, AI, OCR, integrations, listing/search, update/delete/purge, and Dossier rebinding remain unauthorized.

## Resolved Foundation debt

FOUNDATION-DEBT-001 is closed by the accepted F-006/F-013 reconciliation. The
canonical projection and conformance test now validate the ratified 55-member
Runtime Baseline V1. This was not a C06 regression. See the [Foundation Debt
001 Closure](../engineering/FOUNDATION_DEBT_001_CLOSURE.md).

## Next package

No implementation package is currently authorized. Amendment 003 is ratified
only as a dependency-graph correction; it does not authorize implementation.
F-016 may be considered only through an independent implementation
authorization, and every successor package requires its own authorization.
