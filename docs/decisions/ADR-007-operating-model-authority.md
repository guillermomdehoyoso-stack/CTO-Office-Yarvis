# ADR-007: Operating Model as Architectural Authority

- Status: Accepted
- Date: 2026-07-12

## Context
The project now has a stable Operating Model that defines the long-lived product and architecture intent for Yarvis. Several prior technical decisions remain valid, but the system needs a single top-level reference that resolves precedence when documents overlap or evolve at different speeds.

## Decision
The document [Yarvis Operating Model v1.0](../architecture/YARVIS_OPERATING_MODEL.md) is the highest-level architectural authority for Yarvis.

Specific ADRs remain binding when they do not contradict the Operating Model. If a conflict appears, the Operating Model takes precedence for product and architecture direction, and the specific ADR applies only within the bounds that remain compatible with it.

## Consequences
- Architectural decisions now have a clear precedence order.
- Future ADRs must align with the Operating Model or explicitly document the deviation.
- Existing ADRs remain valid and enforceable where they do not conflict with the Operating Model.
- The product can evolve without reopening settled architectural intent on every iteration.
