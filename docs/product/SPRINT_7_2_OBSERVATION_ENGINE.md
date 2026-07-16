# Sprint 7.2 Observation Engine

## Goal

Deliver the minimum reusable operational brain that converts evidence into traceable, reviewable, and actionable operational knowledge.

## Delivered Scope

- Observation pipeline persistence:
  - SourceRecord
  - DocumentRecord
  - Observation
  - ResolutionDecision
  - OperationalPolicy
  - PolicyEvaluation
  - AttentionItem
- Deterministic policy evaluator with explicit operator allow-list.
- NetPay adapter mapped extracted fields into observation records with provenance.
- Mission Control summary and attention extensions for observation/policy signals.

## Explicit Non-Scope

- Gmail integration activation.
- WhatsApp integration.
- Google Drive integration.
- Portal NetPay automation.
- Tax calculations.
- Production OCR.
- Graph database.
- Autonomous agents.

## API Highlights

- POST /observations/sources
- POST /observations/documents
- GET /observations/documents
- GET /observations/documents/{document_id}
- POST /observations
- GET /observations
- GET /observations/{observation_id}
- POST /observations/{observation_id}/confirm
- POST /observations/{observation_id}/reject
- POST /observations/{observation_id}/conflict
- POST /observations/{observation_id}/resolution-proposals
- POST /resolutions/{resolution_id}/confirm
- POST /resolutions/{resolution_id}/reject
- GET /operational-policies
- POST /operational-policies
- POST /operational-policies/evaluate
- GET /policy-evaluations

## NetPay Demonstration

NetPay import now emits observations for:
- folio
- tracking_number
- company_name
- branch_name
- store_id
- asset_serial
- recipient
- address

All with provenance metadata and candidate confirmation by default.
