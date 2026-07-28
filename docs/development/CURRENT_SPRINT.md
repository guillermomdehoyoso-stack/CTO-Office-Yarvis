# Current Sprint

## Identity

**Work package:** WS-006C — Process Runtime Backend

## Goal

Implement the governed, tenant-owned Process Runtime designed in WS-006B without
introducing Mission Work association, frontend, automation, or scheduler behavior.

## Scope

- Start Process Instances only from published Process Definitions.
- Govern graph transitions, terminal completion, cancellation, idempotency,
  optimistic versioning, tenant isolation, and authorities.
- Persist Process-local append-only Timeline evidence and corresponding Domain Events
  in one Unit of Work.
- Deliver the linear migration, focused tests, and implementation documentation.

## Dependencies

- Architecture Checkpoint 001 at `21270a1` / `architecture-checkpoint-001`.
- `PROCESS_RUNTIME_DESIGN.md` and its Process Runtime ADRs.
- WS-006A Process Domain Foundation and existing persistence, Unit of Work,
  authorization, contract, and Domain Event patterns.

## Current Gate

Implementation validation. The Process Runtime design is authoritative; implementation
may specialize it but must not redefine Process ownership or lifecycle semantics.

## Entry Criteria

- Repository state and `21270a1` baseline are verified.
- WS-006B design and ADR decisions are read before implementation.
- No Process-to-Mission-Work association is introduced.

## Exit Criteria

- Process Instance lifecycle, graph transitions, cancellation, idempotency, Timeline,
  tenant isolation, and authority are implemented and tested.
- Migration is linear, round-trippable, and leaves a single Alembic head.
- Focused and complete backend validation, plus conformance review, are complete.

## Definition of Done

The repository can start, govern, and inspect a Process Instance without changing
Mission Work lifecycle or associating Process Instances to Work Items.

## Open Risks

- Concurrent writers require both the aggregate row lock and database sequence
  uniqueness to preserve Timeline order.
- Process remains absent from the historical canonical module baseline; that recorded
  checkpoint debt is not silently redefined by this increment.

## Explicitly Out of Scope

- Process Instance to Mission Work association and Work Timeline projection.
- Frontend, automation, scheduler, SLA, BPMN, and domain-specific process seeds.
- A Process lifecycle mutation that silently changes a Work lifecycle.

## Next Package

WS-006D — Process Instance to Mission Work Association, only after WS-006C is
validated, reviewed, and committed.
