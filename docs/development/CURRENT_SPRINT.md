# Current Sprint

## Identity

**Work package:** WS-000 - Development Workspace Bootstrap

## Goal

Establish repository-resident engineering context so a new human or AI session
can determine the current gate, allowed action, relevant authority, and active
work without relying on chat history.

Complete the final planned governance refinement required to scope Gates without turning documentary review into a repository-wide implementation stop.

## Packages

- WS-000 Development Workspace bootstrap under ratified scoped gate controls.
- EOS Foundation Documentation gate enforcement for in-scope artifacts.
- Governance baseline freeze: `docs/engineering/GOVERNANCE_BASELINE_V1.md`.

## Dependencies

- Amendment 001 through Amendment 003 and their reviews.
- Amendment 004 ratified scoped Gate authority.
- EOS Constitution and EOS Glossary proposals.
- Technical Blueprint, review, Implementation Epics, and F-001 through F-009 baselines.
- Repository documentation as the authoritative context source.

## Current Gate

Ratified scoped EOS Foundation Documentation Gate (per `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_004.md`), with WS-000 authorized outside EOS Foundation Documentation scope.

## Entry Criteria

- Current documentary state is available in the repository.
- Governance Baseline V1 is recorded.
- Unknown facts are recorded as `UNKNOWN` or `TO BE VERIFIED`.

## Exit Criteria

- WS-000 bootstrap prompt is prepared and executed under the scoped EOS gate.
- The EOS Gate remains scoped to EOS Foundation Documentation.
- WS-000 implementation proceeds without modifying EOS Foundation artifacts.
- No governance redesign is introduced by WS-000 startup activities.

## Definition of Done

A new engineering session can reconstruct the project identity, authority chain,
current gate, active work, roadmap location, and next allowed action in under
five minutes.

## Open Risks

- Branch, HEAD, working-tree state, and runtime health must be verified at each
  new session start.
- EOS Constitution is proposed, not ratified.
- EOS Glossary is proposed, not ratified.
- Baseline creation must remain scope-conformant to ratified Amendment 004 and must not authorize EOS artifact modification outside declared gate controls.

## Next Package

Prepare and execute the WS-000 bootstrap implementation prompt.
