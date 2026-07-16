# ADR-010: Observation-Driven Operational Memory

- Status: Accepted
- Date: 2026-07-16

## Context

Yarvis needs a reusable operational brain that can ingest evidence from multiple sources without allowing raw extraction output to mutate confirmed operational state.

Phase II requires deterministic, explainable, and auditable transitions from evidence to action.

## Decision

Yarvis adopts an Observation Engine as the mandatory path from source evidence to operational action.

1. Evidence is not operational truth.
2. Observation is immutable domain memory, except explicit confirmation metadata transitions.
3. Knowledge is derived from observations and resolution decisions.
4. State changes require identity/hierarchy resolution or explicit human confirmation.
5. Policies run on resolved operational state, not raw extractions.
6. Every conclusion must be explainable back to evidence and observation provenance.
7. Sources cannot bypass the Observation Engine.
8. User corrections create new observations or decisions; history is not rewritten.

## Consequences

- Conflicts remain visible and queryable.
- Duplicate evidence is idempotent by hash unless explicitly reprocessed.
- Parser/OCR output remains candidate when identity or ownership is affected.
- Mission Control prioritizes exceptions and actions derived from deterministic policies.

## Out Of Scope

- No Gmail connector activation.
- No WhatsApp connector activation.
- No Google Drive integration.
- No production OCR pipeline.
- No graph database.
- No autonomous agents.
- No tax calculation automation.
