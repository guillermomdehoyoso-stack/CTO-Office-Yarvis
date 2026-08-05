# C06 — Requirement Definition Catalog Closure

**Status:** Complete — implementation and technical validation closed.
**Authority:** [IG-004](IG-004_REQUIREMENT_DEFINITION_IMPLEMENTATION_AUTHORIZATION.md), under [AR-005](../architecture/AR-005_REQUIREMENT_SEMANTIC_ARCHITECTURE_RATIFICATION.md), [DR-002](../design/DR-002_REQUIREMENT_DEFINITION_SEMANTIC_MODEL.md), and [EP-001](EP-001_ENGINEERING_GOVERNANCE_AND_DEVELOPMENT_PRACTICES.md).
**Scope:** DI-003 C06 Requirement Definition Catalog only.
**Non-authorizing:** This closure does not authorize C07–C09, F-012, F-016, or any other capability.

## 1. Closure Decision

C06 is complete. The validated C06B2A, C06B2B-1, and C06B2B-2 increments provide the authorized Requirement Definition Catalog: immutable, tenant-local, version-bound definitions with governed registration and authoritative retrieval.

This decision closes C06 implementation and technical validation. It does not declare global Contract Registry health, ratify a roadmap amendment, or create implementation authority for a successor capability.

## 2. Implemented Scope

- `IC-REQUIREMENT-DEFINITION-CMD-001` registers a Requirement Definition with `requirement.definition.register` authority.
- `IC-REQUIREMENT-DEFINITION-QRY-001` retrieves a tenant-local Definition by ID with `requirement.definition.read` authority.
- `IC-REQUIREMENT-DEFINITION-QRY-002` retrieves a tenant-local Definition by Published Dossier Template Version and semantic key with `requirement.definition.read` authority.
- Definitions retain tenant ownership, Published Template Version provenance, stable semantic key, title, purpose, semantic subject, fulfillment mode, required/optional classification, provenance, aggregate version, and same-version semantic dependencies.
- Receipt-first idempotency, replay, fingerprint conflict handling, concealed tenant lookup, events, and PostgreSQL concurrency recovery follow the repository command boundary.
- Migration `20260804_29_requirement_definition_catalog` introduces the Definition and dependency tables, constraints, index, and database immutability protections.

## 3. Validation Evidence

The technical checkpoint validated the following commands and results in Docker against PostgreSQL:

| Validation | Result |
| --- | --- |
| `pytest tests/test_requirement_definition_catalog.py -q -x` | 18 passed |
| `pytest tests/test_dossier_template_catalog.py tests/test_opportunity_dossier.py tests/test_opportunity_specialization.py tests/test_opportunity_aggregate.py tests/test_deterministic_inbound_migration.py -q` | 38 passed |
| `python -m compileall src` | passed |
| `git diff --check` | passed; LF-to-CRLF warnings only |

The C06 suite covers registration semantics, authority, Published Template eligibility and concealment, tenant-local idempotency, normalized dependencies, authoritative queries, Definition and dependency immutability, forced commit rollback and retry, matching and mismatched receipt races, different-key business-identity conflict, and late dependency-insert rejection.

## 4. Migration Evidence

The real migration round trip was validated:

```text
20260803_28
  -> 20260804_29
  -> 20260803_28
  -> 20260804_29
```

At `20260804_29`, PostgreSQL contained:

- `requirement_definitions` and `requirement_definition_dependencies`;
- `ix_requirement_definitions_template_key`;
- 13 named constraints across the two tables;
- three immutability triggers; and
- three corresponding protection functions.

The downgrade removed exactly these C06 tables, index, triggers, and functions. The re-upgrade recreated them, and Alembic head/current both reported `20260804_29`.

## 5. Scope Audit

The C06 implementation does not introduce Requirement Instances, satisfaction, readiness, Milestones, Evidence, Artifact or Document Association intake, workflow execution, rules, Commercial behavior, AI, OCR, integrations, update/delete/purge, listing/search, or Dossier rebinding.

C05 Published Dossier Template history remains unchanged by registration and rejection paths. Dependencies remain semantic relationships; they are not workflow ordering or automatic activation.

## 6. Deferred Work

The following remains deferred and unauthorized:

- C07 Requirement Instance Bootstrap;
- C08 Requirement Dependency Readiness;
- C09 Artifact/Document Association Intake;
- Milestones, Evidence, Commercial Decision and Proposal capabilities; and
- any successor feature without its own ratified design and implementation authorization.

## 7. Independent Technical Debt — Canonical Contract Projection

**Identifier:** FOUNDATION-DEBT-001
**Owner:** Engineering Foundation steward — F-006 Contract Registry / F-013 Test and Conformance Foundation.
**Status:** Open, independent of C06.

`tests/test_canonical_contracts.py::test_canonical_tier_one_projection_is_explicit_complete_and_deterministic` retains a rigid expectation of 37 Tier-1 contracts, while the current canonical projection returns 55. The difference includes earlier Document Registry contract work and is not a regression demonstrated by C06.

This debt does not block C06 closure and must not be resolved by reopening C06. Its resolution condition is to reconcile the canonical projection and its test expectations, then validate the Contract Registry before F-016 Query Dispatch is authorized or started. Until then, no document may claim global Contract Registry health.

## 8. Next Governance Decision

No implementation successor is opened by this closure. The next decision is to
reconcile the active engineering gate and, separately, obtain the required
implementation authorization before authorizing any Foundation increment.

Amendment 003 was subsequently ratified as a Foundation dependency-graph
correction only. That later documentary action does not reopen C06, which
remains closed at commit `0fc8d615c85f42645ea61a85881309c9311fb3e1`; it does
not authorize F-016 or another successor capability.
