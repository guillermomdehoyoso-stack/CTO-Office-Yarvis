# Current Sprint

## Identity

**Work package:** WS-006D — Mission Work / Process Association

## Goal

Connect Mission Work and Process Runtime through a governed, historical association
without merging ownership or lifecycle responsibility.

## Scope

- Process-owned `ProcessInstanceWorkLink` with one active primary link per Process
  Instance and no active-instance maximum per Mission Work Item.
- Tenant-safe link, unlink, list, primary-link, and history contracts.
- Idempotent link/unlink commands, source Domain Events, and Mission Work-owned
  idempotent Timeline projection.
- A linear Alembic migration and focused association/projection tests.

## Current Gate

Conformance review. Implementation validation passed: focused association, Process
Runtime, Mission Work Timeline, contract, and migration tests total **46 passed**;
the backend suite totals **289 passed**, 0 failed. The association ADR and Process
Runtime design remain authoritative.

## Exit Criteria

- Association history, primary-link constraint, idempotency, concurrency guards,
  tenant concealment, and source-event projection are verified.
- Migration is round-trippable and leaves a single Alembic head.
- Focused and full backend validation, followed by conformance review, are complete.

## Explicitly Out of Scope

- Frontend, dashboard, SLA, notifications, scheduler, automation, BPMN, and AI.
- Automatic Process or Mission Work lifecycle synchronization.
- Rigid process categories or domain-specific process seeds.

## Next Package

TO BE VERIFIED after WS-006D conformance review.
