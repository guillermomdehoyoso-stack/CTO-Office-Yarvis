# Current Sprint

## Identity

**Work package:** AC-002 — Core Architecture Checkpoint

## Goal

Record the implemented Core architecture after Process Runtime, Mission Work/Process
association, Operational Economics, and the Operational Workspace without changing
runtime behavior or architectural authority.

## Scope

- Core bounded contexts, dependency map, ownership boundaries, event flow, and read
  model strategy.
- Mission Work, Process Runtime, Operational Economics, and Operational Workspace
  implementation evidence.
- Explicit extension boundaries and non-goals for Tasks, Checklists, Waiting, SLA,
  Documents, and AI.
- Alignment of live architecture/navigation documentation and development context.

## Current Gate

Documentation consistency review. AC-002 makes no API, model, migration, contract,
or runtime change.

## Entry Criteria

- WS-006A, WS-006C, WS-006D, OV-001, OV-002, WS-006E, and WS-006F are committed.
- Repository evidence is inspected before making checkpoint claims.

## Exit Criteria

- The checkpoint identifies implemented, deferred, and deprecated/superseded
  navigation concepts.
- Relevant ADR and architecture views are consistent with implemented evidence.
- Documentation links and Mermaid diagrams are valid, and `git diff --check` passes.

## Explicitly Out of Scope

- Runtime code, migrations, APIs, frontend behavior, roll-ups, lifecycle sync,
  automation, scheduler, SLA, Tasks, Waiting, Documents, and AI.

## Next Package

TO BE VERIFIED after AC-002 ratification. Any follow-on must be explicitly scoped
against the extension boundaries recorded in the checkpoint.
