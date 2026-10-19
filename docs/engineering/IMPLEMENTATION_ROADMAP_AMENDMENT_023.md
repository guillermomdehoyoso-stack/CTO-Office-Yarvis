# YARVIS
# Implementation Roadmap Amendment 023

## Risk-proportionate assurance and Netpay portfolio design sequencing

## Status

**RATIFIED — DOCUMENTARY GOVERNANCE ONLY — NO IMPLEMENTATION AUTHORITY**

**Effective date:** 2026-10-19
**Authority:** Guillermo de Hoyos, Architecture Authority
**Governing decision:** [ADR-021](../decisions/ADR-021_RISK_PROPORTIONATE_ASSURANCE_FOR_YARVIS_MODULES.md)

## Decision

The roadmap adopts the four risk profiles ratified by ADR-021:

| Profile | Scope | Proportional assurance |
| --- | --- | --- |
| A | Regulated evidence | Strong invariants, immutable traceability, verified migrations, formal gates and evidence. |
| B | Security-sensitive work | Authentication, authorization, isolation, consent, encryption, replay protection, negative tests and sensitive-action audit. |
| C | Business operations | Transactions, constraints, provenance, freshness, selective history, conditional idempotency and critical journeys. |
| D | Experience and analysis | Functional, accessibility, performance and representative E2E coverage without contracts per UI interaction. |

Packages may combine profiles. Amendment, IG and ADR requirements follow
ADR-021's material-risk rules. Reversible light changes that add no entity,
migration, permission, sensitive-data category, integration, material
transition or effect outside the existing owner require criteria, review and
affected tests, but no Amendment, IG or ADR.

No existing contract is removed or changed. Future contracts shall represent
real stable boundaries, sensitive or retryable mutations, material effects, or
queries with stable/external consumers. Pure table interaction does not create
a contract requirement.

## Roadmap effect

The accumulated Netpay D2, H1, H2-Q, H2-I, H2-D and navigation package remains
closed at commit `8461818026d7a8de7c2571a8db6ea69294e35583` under Amendments
020–022 and IG-008–IG-010. Historical authority and evidence are unchanged.

The next Netpay package is **design of the Netpay Commerce Attention
Portfolio**. Its future scope retains the complete merchant list, differentiated
contacts, profitability, terminals and branches, attention state and next
action, five explainable colors, compound filtering, search, sorting,
pagination, saved views, provenance, freshness, data quality, organization
isolation and PII protection. It authorizes no outbound communication.

The future design uses B/C for contacts and PII, C for merchant catalog,
profitability and attention rules, and D for filters, columns, colors and
navigation. It must resolve catalog authority, identity reconciliation,
Operational Data/D2-Lite or successor authorization, deterministic attention
rules and any necessary real-boundary contracts before implementation can be
considered.

## Gate decision

No IG is created by this amendment. There is no implementation, deployment,
migration, external integration or operational effect to gate. A later design
may require a new Amendment, ADR or IG according to its actual boundaries and
risk profiles; this amendment cannot be cited as implementation authority.

## Exclusions

No code, test, catalog contract, configuration, model, schema, route,
migration, data or pilot resource is changed or authorized. D3, D2-Lite, P2,
Gmail, OAuth, secrets, attachment content, Drive, automation, external
communications and the Commerce Attention Portfolio implementation remain
closed.
