# ADR — Process Instance Ownership

**Status:** Proposed for Ratification
**Decision:** ADR-PROCESS-INSTANCE-OWNERSHIP
**Related design:** [Process Runtime Design](../PROCESS_RUNTIME_DESIGN.md)

## Context

WS-006A implements versioned, immutable-on-publication Process Definitions. Mission Work already owns operational task lifecycle and Timeline evidence. Process Runtime requires a canonical owner for execution state without making templates mutable or moving Mission Work authority into Process.

## Decision

`ProcessInstance` is a distinct aggregate owned by the Process context. It belongs to one Organization and references one published Process Definition version for its whole life. It owns current stage, lifecycle, aggregate version, Process-local event history, and command replay identity.

A Process Definition is a template, not an instance. Retirement prevents new instances but does not invalidate or alter existing instances. Multiple historical instances may use the same published definition version.

Process-to-Work association is owned by Process through a historical link. The initial
rule is one active primary link per Process Instance; a Mission Work Item may have
multiple active Process Instances. Historical associations are preserved.

## Consequences

- Published definitions remain immutable and usable as historical evidence.
- Mission Work can exist without Process, and Process can start before it is linked to Work.
- A Work Item does not acquire Process lifecycle ownership and a Process Instance does not acquire Work lifecycle ownership.
- Cross-context communication uses public contracts and source events, not foreign repository mutation.

## Rejected Alternatives

- Store runtime state in `ProcessDefinition`.
- Make `MissionWorkItem` own Process lifecycle state.
- Put a mutable Process foreign key directly into Mission Work as the canonical association.
