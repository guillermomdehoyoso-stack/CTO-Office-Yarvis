# Sprint 7.3 — NetPay Operational Consolidation MVP

## Objective

Implement the first end-to-end operational workflow where Yarvis transforms one real NetPay operational report into actionable operational knowledge.

This sprint prioritizes usable functionality over architecture. If a design decision does not produce visible operational value during this sprint, postpone it.

This sprint follows [ADR-011](../decisions/ADR-011-operational-evidence-consolidation-system.md) and [ADR-012](../decisions/ADR-012-operational-memory-first-class-domain.md), using the development cycle:

**Build -> Use -> Learn -> Improve**

## Primary User Story

Guillermo receives multiple NetPay reports every week. Instead of opening Excel files, searching stores, comparing reports, and reconstructing operational context from memory, he uploads one report into Yarvis.

Yarvis recognizes the report, extracts its operational information, consolidates it with Operational Memory, identifies relevant findings, and presents them for confirmation.

One uploaded Excel file is sufficient. No external integrations are required.

## Sprint Goal

By the end of the sprint, Guillermo can upload one real NetPay report and immediately receive a useful operational summary.

## In Scope

### 1. Evidence Intake

- XLSX upload;
- SHA-256 fingerprint and duplicate detection;
- upload metadata; and
- preview before confirmation.

### 2. Report Classification

Only these deterministic, rule-based classifications are supported:

- Weekly Sales Report;
- Inventory Report; and
- Unknown Report.

### 3. Configurable Parsing

Extract data through column mappings. Avoid hard-coded column indexes whenever possible.

### 4. Commercial Identity Resolution

Resolve the available hierarchy without inventing missing data:

`Client Account -> Company -> Branch -> Store -> Asset`

Missing identity remains unresolved. Operational Memory preserves that uncertainty.

### 5. Deterministic Observations

Generate observations with provenance, including:

- **Churn Candidate:** `inactive_days >= 60`;
- **Critical Store:** high sales volume combined with increasing inactivity;
- **Asset Without Store:** asset known, Store unresolved;
- **Missing Identity:** Client Account, Company, Branch, or Store unresolved; and
- **Recently Reactivated Store:** previously inactive and now active.

### 6. Mission Control

Display only:

- Pending Reports;
- Critical Stores;
- Churn Candidates;
- Assets Without Store; and
- Identity Conflicts.

### 7. Operational Memory

After human confirmation, append observations, provenance, timestamps, and confirmations to Operational Memory. Historical evidence is never overwritten.

## Explicit Non-Goals

Do not implement Gmail, WhatsApp, OCR, PDF, XML, Google Drive, SAT, Accounting, CFE, NetPay portal automation, OpenSolar, AI classification, graph visualization, folder watchers, or generic dashboard work.

## Engineering Rules

Prefer simple, deterministic, observable, and explainable behavior. Avoid generic frameworks, premature abstractions, and speculative architecture.

Before adding code, ask: **Does this produce operational value for Guillermo during this sprint?** If not, postpone it.

## Demonstration Required

The sprint is complete only when this flow works:

```text
Upload weekly_sales.xlsx
  -> Preview detected
  -> Classification: Weekly Sales Report
  -> Operational Summary:
       214 Stores
       18 Churn Candidates
       7 Assets Without Store
       3 Identity Conflicts
  -> Confirm
  -> Mission Control updated
  -> Operational Memory enriched
```

The exact counts are the acceptance demonstration for the supplied real report; they must be produced from its evidence, not seeded or fabricated.

## Acceptance Criteria

- A real XLSX operational report is accepted.
- Its parser extracts data correctly through mapped columns.
- Commercial hierarchy is resolved where evidence permits.
- Observations are generated deterministically.
- Mission Control updates after confirmation.
- Operational Memory is enriched by append-only, provenance-preserving records.
- No speculative entities are introduced.
- Human confirmation is required before operational state is updated.
