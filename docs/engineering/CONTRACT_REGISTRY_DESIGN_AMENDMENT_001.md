# YARVIS
# Contract Registry Design Amendment 001

## Status: Ratified Engineering-Design Alignment

## 1. Amendment Identity

**Amendment ID:** `CONTRACT-REGISTRY-AMENDMENT-001`  
**Affected work package:** F-006 — Contract Registry  
**Date:** 2026-07-21  
**Authority:** `CONTRACT_REGISTRY_DESIGN.md`, interpreted beneath the ratified
Interaction Contract Catalog and its review.

## 2. Reason for Amendment

F-006 implementation review established that three metadata requirements in
the original engineering design could not be projected from the ratified Tier
1 catalog without inventing values:

1. mandatory per-contract `architectural_steward`;
2. mandatory nonempty per-contract `traceability_references`; and
3. separate `permitted_consumers` and `use_case_references` collections.

The catalog establishes that those concepts exist architecturally, but its Tier
1 registry provides no per-contract steward or traceability mapping and uses
one combined “Primary consumer/use case” value.

## 3. Previous Requirements

The prior F-006 design required `architectural_steward`, nonempty
`traceability_references`, `permitted_consumers`, and `use_case_references` in
every projected definition. It therefore made the canonical Python projection
impossible without unsupported inference.

## 4. Amended Requirements

The F-006 `ContractDefinition` metadata model is now:

| Classification | Fields |
| --- | --- |
| Required | `interaction_contract_id`, `version`, `contract_type`, `owner_module_id`, `owning_context`, `owning_capability`, `name`, `semantic_purpose`, `lifecycle`, `operational_status`, `criticality`, `primary_consumer_or_use_case` |
| Optional | `architectural_steward`, `traceability_references` |

`architectural_steward` may be absent or `None`; when supplied it must be
nonblank and use ratified terminology. `traceability_references` defaults to
an empty immutable collection; every supplied reference must be nonblank.
Neither field may be invented or inferred.

`primary_consumer_or_use_case` preserves the catalog's supplied text exactly
as one nonblank governed field. It is not parsed into consumers or use-case
identifiers and has no authorization or access-control meaning.

## 5. Revised Validation

F-006 validates canonical contract ID, semantic version, required nonblank text
metadata, contract type, lifecycle, operational status, criticality, owner
module existence, duplicate ID rejection, lifecycle/operational-status
separation, optional steward nonblankness when present, nonblank supplied
traceability references, and mutation-after-sealing rejection.

It no longer requires a steward, nonempty traceability references,
`permitted_consumers`, or `use_case_references`.

## 6. Rationale and Scope Preserved

This is specification alignment, not an architecture redesign. Stable contract
identity, semantic versioning, four contract kinds, ownership, registry API,
sealing, per-application isolation, bootstrap semantics, typed error model,
and the exact 37 Tier 1 contracts remain unchanged.

The Contract Registry remains governed technical metadata. It does not
authorize, dispatch, transport, persist, execute, or create domain truth.

## 7. Deferred Governance and Implementation Impact

The following remain explicitly deferred: per-contract steward assignment,
detailed traceability mapping, separation of consumers from use cases,
authorization subjects, policy bindings, payloads, result types, handlers,
dispatch, buses, subscriptions, transport bindings, persistence, database
integration, Unit of Work, workers, scheduler, and dynamic discovery.

The amendment allows all 37 Tier 1 contracts to be projected using only
metadata actually present in the catalog. Future governance enrichment can add
optional stewardship or traceability metadata without changing a stable
contract identity.

## 8. Acceptance Criteria

This amendment is complete when the original three blockers are removed, no
Tier 1 metadata is invented, required and optional metadata are distinct, the
combined catalog field is preserved faithfully, authorization remains
deferred, and the F-006 implementation prompt can proceed without ambiguity.

## 9. Architecture Impact

No architecture amendment is required. The ratified catalog remains the
architectural authority; this amendment aligns the engineering projection with
the metadata that catalog actually provides.

## 10. Closing Statement

F-006 may now implement a faithful technical projection of the Tier 1 contract
baseline while preserving future governance enrichment as explicit, governed
work rather than inferred metadata.
