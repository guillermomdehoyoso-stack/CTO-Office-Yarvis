# ADR-021 — Risk-Proportionate Assurance for Yarvis Modules

## Status

**ACCEPTED — ARCHITECTURE AND GOVERNANCE ONLY — NO IMPLEMENTATION AUTHORITY**

**Effective date:** 2026-10-19
**Decision authority:** Guillermo de Hoyos, Architecture Authority
**Roadmap record:** [Implementation Roadmap Amendment 023](../engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_023.md)

## Context

Yarvis needs assurance proportional to the risk of each change. The controls
used for regulated Energy Tracer evidence remain necessary in that domain, but
applying the same ceremony automatically to ordinary Netpay operations or user
interface behavior creates contracts and gates that do not correspond to a
distinct ownership, security or audit risk.

This decision specializes existing governance without weakening the
Constitution, ownership boundaries, security, privacy, organizational
isolation, transactional integrity or historical authority. A package may
combine profiles, and each part receives the strongest applicable controls.

## Decision

### A — Regulated evidence

Applies to Energy Tracer, energy measurement, financial evidence, I-RECs and
domains with equivalent obligations. As applicable, it requires strong
invariants, complete traceability, immutable evidence, hashes, events, verified
migrations, formal gates and durable evidence records.

### B — Security-sensitive work

Applies to OAuth, external providers, secrets, permissions, personally
identifiable information, communications and external effects. It requires
authentication and authorization, organizational isolation, consent,
encryption, replay protection, negative tests, and audit of sensitive access
and mutations.

### C — Business operations

Applies to merchants, contacts, profitability, dossiers, terminals, follow-up
and operational states. It requires transactional integrity, constraints,
provenance and freshness, idempotency when an operation is retryable, selective
history for material changes, and tests of critical journeys.

### D — Experience and analysis

Applies to filters, columns, colors, sorting, pagination, preferences,
navigation and visualizations. It requires functional tests, accessibility,
reasonable performance and a small set of representative end-to-end tests. It
does not require a Command, Query or Event for every interaction.

A package can combine profiles. Merchant contacts and PII are B/C; attention
rules are C; filters, columns and presentation are D. Classification is based
on actual risk and effect, not the package's highest-level label alone.

## Governance artifact rules

An **Amendment** is required for new regulated scope, a new external
integration, a new category of sensitive data, a new entity or material state
transition not already authorized, an isolation change, or an external or
irreversible effect.

An **Implementation Gate** is required for deployment or implementation of
profile A or B work, a material migration, or a profile C package with relevant
operational risk. A light profile D change does not require an IG.

An **ADR** is required for a change to ownership, a boundary, trust model,
persistence model or transversal pattern. Ordinary CRUD and UI changes do not
require an ADR when they preserve those decisions.

A **light change** is reversible and introduces no new entity, migration,
permission, sensitive-data category, external integration, material transition
or effect outside the existing owner. It requires explicit criteria, review and
affected tests, but no Amendment, IG or ADR.

When more than one rule applies, the stronger applicable artifact and evidence
requirements govern. Splitting a material change into smaller edits does not
make it light.

## Contract policy

- Do not create CMD/QRY/EVT contracts for filters, columns, sorting,
  pagination, navigation or purely visual preferences.
- Do not create events without a consumer or an audit requirement.
- Do not create a receipt when the entity and its idempotency key fully express
  the result.
- Retain commands for sensitive or retryable mutations and material effects.
- Reserve contractual queries for stable boundaries or external consumers,
  rather than every internal GET.
- Existing contracts remain unchanged. Deprecation or removal requires a
  separate compatibility analysis and explicit authority.

## Test and evidence strategy

Profile A uses invariant, lineage, immutability, migration, recovery and formal
evidence tests. Profile B uses authentication, authorization, isolation,
consent, secret-handling, replay, negative-path and audit tests. Profile C uses
constraints, transactions, provenance, freshness, idempotency where required,
history and critical-journey tests. Profile D uses focused functional,
accessibility, performance and representative browser tests.

The same invariant is not duplicated across gates unless a distinct risk or
boundary requires independent evidence. Combined-profile packages retain all
controls applicable to each affected surface.

This decision does not reduce security, privacy, isolation, secret protection,
OAuth controls, consent, atomicity, constraints, migration discipline,
recovery, or auditing of sensitive actions.

## First application: Netpay Commerce Attention Portfolio

The future Netpay Commerce Attention Portfolio is the first package to use this
policy. This ADR authorizes design only; it does not authorize implementation.

Its retained requirements include an integral merchant list; distinct owner,
legal representative, branch manager and operational contacts; latest
profitability; terminals and branches; operational state and next action;
green, yellow, orange, red and gray attention states with an explicit reason;
individual and combined filters; global search, sorting, pagination and saved
views; provenance, freshness and quality; organization isolation and PII
protection; and no outbound communications.

The future design shall classify contacts and PII as B/C, catalog,
profitability and attention rules as C, and filters, columns, colors and
navigation as D. It shall use few contracts centered on real boundaries and no
contract per table interaction.

Before implementation it still needs a canonical merchant-catalog source,
identity reconciliation across merchant, RFC, MID, branch, terminals,
candidates and intakes, authorization for Operational Data/D2-Lite or a
successor package, deterministic attention rules, and its own mandate and
contracts where actual boundaries require them.

## Compatibility, limits and consequences

The published D2, H1, H2-Q, H2-I and H2-D closure at commit
`8461818026d7a8de7c2571a8db6ea69294e35583` remains closed and unchanged. This
decision does not reinterpret its historical gates or evidence.

No code, model, schema, route, migration, data or existing contract changes are
authorized. D3, D2-Lite, P2, Gmail, OAuth, pilot access, attachment content,
Drive, automation and communications remain closed. The Commerce Attention
Portfolio remains unimplemented and unauthorized for implementation.

## Ratification review

The decision preserves singular ownership and existing trust boundaries;
introduces no canonical state transfer; allocates no contract; changes no
runtime, migration or compatibility surface; retains stronger controls for A/B
risks; and records explicit non-goals. There are zero unresolved BLOCKER or
MAJOR findings within this documentary scope. The Architecture Authority's
2026-10-19 instruction expressly ratifies the moderate compatible option and
authorizes preparation, validation, ratification and publication of these
architecture and governance documents only.
