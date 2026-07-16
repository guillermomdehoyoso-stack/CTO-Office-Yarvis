# Incubator

## Purpose

Capture future capabilities as architecture-first candidates before implementation.

## Scope Boundaries

- This document is planning-only.
- Nothing here implies active implementation.
- Sensitive integrations remain disabled by default.

## Observation Hooks

Yarvis defines three integration modes for all future adapters:

1. Observation Mode
- Read-only observation of external signals.
- No state mutation in external systems.
- Human confirmation required before any promotion.

2. Demonstration Mode
- Reproducible scripted demonstrations with synthetic or approved data.
- No autonomous execution in external systems.

3. Automation Mode
- Explicitly approved automations with guardrails and rollback.
- Mandatory human confirmation for sensitive transitions.

## Candidate Integrations

- Gmail
- WhatsApp
- Google Drive
- Portal NetPay
- Hoymiles
- APsystems
- OpenSolar

## Future Domain Candidates

- ClientAccount model
- Company model
- Branch model
- Store model
- Asset model
- SalesSnapshot
- churn engine
- criticality engine
- OperationalNode projection
- document repository integration

## Activation Policy

- Default mode for new integration: Observation Mode.
- Promotion to Demonstration Mode requires documented controls.
- Promotion to Automation Mode requires domain owner approval and explicit risk review.
