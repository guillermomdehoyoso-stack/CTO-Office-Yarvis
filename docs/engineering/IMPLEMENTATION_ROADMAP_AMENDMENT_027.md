# Implementation Roadmap Amendment 027 — Bounded Portfolio Reader Authority

## Status

**RATIFIED — EXACT ROLE AND ONE TRANSITION ONLY**

**Date:** 2026-10-22
**Base:** `99709fc1dacc852d783dc45e09bd5d5a6b3a902f`
**Gate:** [IG-014](IG-014_NETPAY_PORTFOLIO_AUTHENTICATED_READER_AUTHORIZATION.md)

The requester ratifies the minimum authority needed to retain Netpay Inbox
operation while reading Master and Portfolio: a new closed role
`netpay_inbox_portfolio_reader` with exactly the four capabilities stated in
[Governance Contract Amendment 002](F-011_GOVERNANCE_CONTRACT_AMENDMENT_002.md),
plus the single canonical transition from `netpay_inbox_operator`.

No existing role changes. Governance continues to own Membership mutation.
The administrative actor must hold both existing Membership create and revoke
capabilities and cannot be the target. The operational transition remains a
separate checkpoint and is not authorized by implementation conformance alone.

Excluded: generic role editing, Membership creation/revival, Master mutation,
sensitive or reconciliation Portfolio data, global permissions, production
data changes, P3–P5, imports and Master record creation.
