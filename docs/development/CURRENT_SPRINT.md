# Current Sprint

## Identity

**Work package:** AC-001B — Yarvis Architecture Checkpoint Documentation

## Goal

Turn the read-only architectural inventory at the WS-006A baseline into versioned,
evidence-based repository documentation and synchronize the live development context.

## Scope

- Record the current As-Is architecture and implementation status.
- Describe the target direction without ratifying new architecture.
- Record roadmap dependencies and known technical debt.
- Update the development state, sprint record, and repository entry point where their
  declared implementation phase was stale.

## Dependencies

- WS-006A Process Domain Foundation at `63740d8` /
  `ws006a-process-domain-complete`.
- Existing ratified architecture, interaction contracts, decision trace, engineering
  baselines, implementation evidence, and tests.

## Current Gate

Documentation checkpoint only. This sprint must not modify runtime code, contracts,
migrations, tests, or ratified architectural semantics.

## Entry Criteria

- Repository state and WS-006A baseline are verified.
- The inventory uses repository files rather than remembered chat context.

## Exit Criteria

- Checkpoint, As-Is, target, and roadmap/debt documents exist and cross-reference
  each other.
- The checkpoint distinguishes implemented, partial, Foundation, planned, and
  exploratory capabilities.
- Development state and sprint documents point to the correct checkpoint and next
  allowed action.

## Definition of Done

The repository can bootstrap a new engineering session with current architectural
evidence, known limitations, and an explicit next design step without recovering a
previous conversation.

## Open Risks

- Older operational documents may contain historical baseline values; the checkpoint
  records the implementation evidence without rewriting ratified history.
- Technical-debt items remain findings, not authorized runtime changes.

## Explicitly Out of Scope

- Process runtime implementation.
- Changes to application code, APIs, migrations, tests, or contracts.
- Architecture ratification or a new implementation baseline.

## Next Package

WS-006B — Process Runtime Design Review, subject to approval. Its scope must define
Process Instance ownership, published-version references, transition authority,
Mission Work association, and event semantics before implementation starts.
