# YARVIS
# Implementation Roadmap Amendment 003

## Status

**RATIFIED**

This is a ratified append-only corrective amendment that supplements
`IMPLEMENTATION_ROADMAP_AMENDMENT_001.md` and
`IMPLEMENTATION_ROADMAP_AMENDMENT_002.md` only within the scope stated here.
It does not replace any higher-authority artifact and introduces no
implementation authority.

## 1. Purpose and Scope

This amendment addresses only the outstanding MAJOR finding from the
Engineering Review of Implementation Roadmap Amendment 002:

- `ROADMAP-REVIEW-002-001`: F-016 is disconnected from the mandatory
  Foundation completion path.

No additional planning corrections are introduced in this amendment. It does
not modify architecture, ownership, runtime scope, product scope, integration
scope, or implementation sequencing beyond the required completion-path
correction.

## 2. Corrective Dependency Path

The Foundation completion path is corrected to require both F-016 and F-017
before F-015. The mandatory completion dependency is:

```text
F-012 --> F-013 --> F-011 --> F-016 --> F-017 --> F-010 --> F-014 --> F-015
```

This path is normative for completion gating.

The path makes the following requirements explicit and unambiguous:

- F-011 precedes F-016.
- F-016 precedes F-017.
- F-016 and F-017 are both mandatory prerequisites of F-015.
- F-015 remains the final Foundation demonstration and E-001 exit gate.

Any permitted design overlap or CI preparation remains non-completion work and
must not weaken this completion dependency path.

## 3. Interpretation of Amendments 001-003

For roadmap interpretation pending a consolidated roadmap baseline:

- Amendment 001 provides the original post-F-009 planning correction and
  Foundation sequencing intent.
- Amendment 002 provides the reviewed corrective clarifications for
  dependencies, observability exit criteria, domain-extension controls, and
  consolidation governance that this narrow correction preserves. Amendment 003
  does not itself ratify any broader still-proposed statement in Amendment 002.
- Amendment 003 ratifies only the remaining F-016 completion-path correction
  identified by the Amendment 002 review.

These amendments are interpreted together as append-only planning lineage.
Where they overlap, the later corrective amendment applies only to the specific
defect it corrects; unchanged statements remain in force.

## 4. Authority and Ratification Constraint

Independent Engineering Review is recorded in
`IMPLEMENTATION_ROADMAP_AMENDMENT_003_REVIEW.md`. Its approval and the formal
ratification recorded here apply only to the dependency-path correction. This
document cannot authorize product implementation.

`FOUNDATION-DEBT-001` remains open and must be corrected and validated before
F-016 Query Dispatch is authorized or started. Ratification does not create a
roadmap baseline, authorize F-016, F-017, F-015, or any other feature, or alter
the requirement for a separate implementation authorization.

## 5. Closing Statement

This amendment provides the minimum documentary correction required to restore a
single mandatory Foundation completion path while preserving existing authority,
scope, and append-only roadmap governance.
