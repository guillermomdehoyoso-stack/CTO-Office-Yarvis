# YARVIS
# Implementation Roadmap Amendment 002

## Status

**Proposed for Engineering Review**

This amendment is not yet ratified. It supplements
`IMPLEMENTATION_ROADMAP_AMENDMENT_001.md` only in the scope stated here and does
not replace the Engineering Roadmap or any higher-authority artifact until
ratification.

## 1. Purpose and Scope

This append-only planning amendment resolves ROADMAP-REVIEW-001 through
ROADMAP-REVIEW-005 from the Engineering Review of Implementation Roadmap
Amendment 001.

It corrects implementation sequencing, Foundation exit criteria, Domain
Extension Review controls, and documentary consolidation rules. It does not
change domain semantics, bounded-context ownership, canonical-state authority,
interaction-contract meaning, provenance, transaction ownership, human control,
or the modular-monolith strategy.

F-009 remains closed as synchronous owner Command Dispatch only. This amendment
does not introduce Query, Event, Notification, worker, scheduler, identity,
authorization, or observability implementation.

## 2. Authority and Documentary Control

The governing order remains:

```text
Ratified Architecture
        |
Technical Blueprint and Ratified Review
        |
Implementation Epics
        |
Ratified Roadmap Amendments
        |
Consolidated Roadmap Baseline
        |
Work-Package Designs and Baselines
        |
Implementation and Post-Implementation Evidence
```

Until a Consolidated Roadmap Baseline is ratified, each ratified roadmap
amendment supplements `IMPLEMENTATION_EPICS.md` only within its explicit scope.
It does not silently replace unrelated epic content.

A Consolidated Roadmap Baseline must identify its complete source set: the
applicable Technical Blueprint and ratified review, `IMPLEMENTATION_EPICS.md`,
and each ratified roadmap amendment being consolidated. If sources conflict, the
authority order above resolves the conflict; no lower-level document silently
supersedes a higher-level document. A baseline must state which planning
statements it consolidates and retain prior documents as historical evidence.

Future amendments must use sequential identifiers, cite their reviewed sources,
and state whether they supplement, clarify, or retire a prior planning statement.

## 3. F-016 Query Dispatch Dependency Correction

F-016 has the following required dependencies:

- F-006 Contract Registry;
- F-009 Command Dispatch composition patterns, reused without semantic coupling;
- F-011 Identity and Authority Envelopes;
- F-012 Errors, Traces, Logs, and Metrics; and
- F-013 Test and Conformance Foundation.

F-011 completion is a prerequisite for F-016 implementation. Query Dispatch
must enforce the target authorization and privacy constraints declared by each
Query contract. Authentication, a caller-supplied identifier, or a transport
credential alone is insufficient.

This requirement does not grant Query handlers mutation authority. Query
handlers remain side-effect free, may not acquire the Command Unit of Work by
default, and may not use cross-context repositories as a substitute for public
contracts.

## 4. Revised Foundation Completion Criteria

In addition to every E-001 exit criterion stated in Amendment 001, formal
Foundation completion requires:

- trace propagation across each relevant Foundation interaction;
- authorized inspection of critical traces, including correlation and causation
  where the Technical Blueprint requires them; and
- metrics where defined by the Technical Blueprint, including the applicable
  health, readiness, queue, handler, projection-freshness, and contract-
  conformance measures.

E-001 Core Kernel remains complete after F-009. E-001 Engineering Foundation
remains incomplete until F-015 proves the complete integrated Foundation
demonstration with all required observability evidence.

## 5. Domain Extension Review Control Additions

Before a new Operational Domain Context may be added, its Domain Extension Review
must additionally record:

1. namespace and interaction-contract-ID collision analysis;
2. data classification, privacy, retention, and historical-preservation impact;
3. named operational ownership, including accountable technical and domain
   stewards where required;
4. observability and traceability requirements, including relevant metrics;
5. failure-isolation expectations and cross-domain failure behavior; and
6. compatibility and migration effects on existing contracts, projections, and
   historical records.

These controls supplement, rather than replace, the existing questions about
canonical state, consumed and owned contracts, shared concepts, projections,
evidence, authority, migration, and independent vertical-slice proof.

Platform capabilities may be reused. Domain canonical models remain unshared by
default. Domain registration does not grant authority, direct cross-domain writes,
or persistence access.

## 6. F-010 and F-014 Completion Ordering Correction

F-014 Local Environment and CI may prepare quality automation after F-013,
including non-worker checks that are already defined. It may not be declared
complete until F-010 provides the worker and schedule-triggered execution
evidence that F-014 must validate in a repeatable local and CI environment.

The corrected completion dependency is:

```text
F-012 --> F-013 --> F-011 --> F-016
                    |
                    +--> F-017 --> F-010 --> F-014 --> F-015
```

The graph permits controlled preparation where stated; it does not permit
premature F-014 completion or an F-015 demonstration without worker, scheduler,
CI, and observability evidence.

## 7. Ratification Criteria

This amendment may be ratified only if review confirms:

- BLOCKER findings = 0;
- MAJOR findings = 0;
- F-016 declares and enforces the F-011 planning dependency;
- E-001 exit criteria retain trace propagation, trace inspection, and applicable
  metrics;
- Domain Extension Review controls preserve independent domain ownership;
- F-014 completion follows F-010 evidence;
- documentary consolidation and conflict-resolution rules are unambiguous; and
- no implementation code, test, migration, configuration, or ratified
  architecture artifact was modified.

## 8. Closing Statement

This amendment repairs the identified planning gaps while preserving the governed
path from the completed Command Dispatch kernel through Foundation closure and
Inbox First. It adds no implementation authority and introduces no shared domain
model.
