# ADR — Operational Task Ownership

**Status:** Accepted OE-001 Decision
**Decision:** ADR-OPERATIONAL-TASK-OWNERSHIP
**Related design:** [Operational Execution Architecture](../OPERATIONAL_EXECUTION_ARCHITECTURE.md)

## Context

Mission Work owns an operational matter; Process owns a procedure; Operational Economics owns economic facts. Yarvis needs assignable operational commitments without turning any of those contexts into a generic Task owner.

## Decision

Operational Execution owns `OperationalTask`. Every Task belongs to exactly one Mission Work Item in the same Organization, and its `mission_work_item_id` is immutable. A Task can optionally reference one Process Instance and stage as planning context; that association can change only while Task status is `planned`. These references never transfer lifecycle or mutation authority.

Tasks are neutral commitments. They do not encode business discipline. Their business meaning is supplied by owner context, participants, evidence, Timeline, and Economics references.

## Consequences

- Mission Work and Process remain independently evolvable.
- A Task can be read in an Operational Workspace without becoming Workspace state.
- Task-specific economics require an Economics fact; no relationship creates value.
- Reassociation to another Mission Work Item is not supported in the initial runtime.

## Rejected Alternatives

- Embed Task state directly in `MissionWorkItem`.
- Make Process stages implicitly create or complete Tasks.
- Classify Tasks by commercial, engineering, or vertical discipline.
