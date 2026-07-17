# ADR-011: Operational Evidence Consolidation System

- Status: Accepted
- Date: 2026-07-16

## Context

Yarvis needs one controlled way to turn operational evidence into reviewable knowledge and follow-up work across sources, without treating source extracts as confirmed operational truth.

## Decision

Yarvis is an Operational Evidence Consolidation System whose primary purpose is to transform distributed operational evidence into actionable, explainable, and verifiable operational knowledge. It is not a data-capture system and it is not a CRM.

Every Yarvis decision must answer:

- What action does it recommend?
- Why?
- With what evidence?

It receives evidence from files, email, WhatsApp, and future connectors through a common intake contract. From that evidence it produces:

- Documents that preserve the source material and its provenance;
- Observations that record extracted or reported facts;
- resolution decisions that reconcile identity, ownership, or conflicting facts; and
- actions that require operational follow-up.

Provenance is retained from every Document, Observation, resolution, and action back to its source evidence. Conflicts remain visible; they are not silently overwritten or resolved by source order.

No connector, parser, or automated policy may make sensitive changes directly. Changes affecting identity, ownership, status, financial or tax interpretation, external communication, or irreversible operational action require explicit human confirmation.

## Operational Principle: Return on Investment

Yarvis must maximize operational value while minimizing software, infrastructure, and AI costs. Before introducing a new dependency, service, or paid integration, it evaluates:

1. Existing available capabilities.
2. Open-source alternatives.
3. Reuse of current infrastructure.
4. Human workflow simplification.

Additional cost is justified only when expected operational value clearly exceeds the incremental expense.

## Consequences

- A file upload is only one evidence source, not the product boundary.
- New connectors extend the common evidence flow instead of creating separate operational silos.
- Mission Control consumes resolved evidence, conflicts, and proposed actions rather than raw source output.
- Raw or automated results remain candidates until the required resolution and confirmation occur.

## Delivery Boundary

Architecture expansion stops with this decision. The development mantra is:

**Build -> Use -> Learn -> Improve**

Each sprint delivers one usable function in a new session, validates it, commits it, and stops. Improvement is informed by actual operation rather than speculative architecture.

The planned increments are:

1. Sprint 7.3A: NetPay XLSX consolidation for `client_id`, `store_id`, sales, last activity, and inactivity.
2. Sprint 7.3B: cross sales, non-use, and inventory reports to find discrepancies, churn candidates, and terminals to recover.
3. Sprint 7.3C: Mission Control for critical stores, churn candidates, recoverable assets, conflicts, and next actions.
4. Sprint 7.4: accounting evidence MVP for CFDI XML and digital PDF, consolidated issued/received invoices, and operational IVA/ISR projection for accounting review. Photos and OCR follow later.

## Out of Scope

- CRM capabilities or a new system of record for customer capture.
- Autonomous resolution, communication, or sensitive operational changes.
- Connector-specific architectures beyond the common evidence contract.
- OCR for photographs in the accounting MVP.

## Positioning

Yarvis does not seek to become the system where work is performed. Yarvis seeks to become the system that understands the work, connects the evidence, and helps humans make better operational decisions.
