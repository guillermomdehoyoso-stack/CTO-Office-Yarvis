# F-011 Governance Contract Amendment 002

## Status

**RATIFIED — BOUNDED MEMBERSHIP ROLE TRANSITION**

**Date:** 2026-10-22
**Authority:** requester mandate of 2026-10-22
**Implementation gate:** [IG-014](IG-014_NETPAY_PORTFOLIO_AUTHENTICATED_READER_AUTHORIZATION.md)

This amendment allocates `IC-GOVERNANCE-CMD-010
ChangeMembershipRoleForPortfolioRead` and the compatible `1.2.0` profile of
`IC-GOVERNANCE-EVT-001 AuthorityChanged`. The command permits exactly the
transition from `netpay_inbox_operator` to
`netpay_inbox_portfolio_reader` for one active Membership in its canonical
Organization. The target role has exactly `netpay.inbox.read`,
`netpay.inbox.manage`, `netpay.master.read` and `netpay.portfolio.read`.

The command requires an authenticated actor other than the target Principal
with both existing capabilities `governance.membership.create` and
`governance.membership.revoke`. It requires the target Membership ID,
Organization from the trusted envelope, expected role, fixed target role,
reason and idempotency key. It locks the Membership, rejects foreign or revoked
targets, expected-role mismatch, incompatible replay and self-escalation, and
invalidates all active sessions of the target in the same transaction.

Equivalent replay returns the same result without another event. Success writes
one durable command receipt and one attributed `AuthorityChanged` event. The
existing activation/revocation profile remains unchanged.

IDs `007` through `009` are avoided because a still-proposed temporary-role
design already uses them as candidate identifiers. That proposal grants no
authority, but avoiding the collision preserves unambiguous traceability.

This authority does not create generic role administration, modify an existing
role's capabilities, reactivate Memberships, grant `netpay.master.manage`,
sensitive or reconciliation access, or apply a transition to an operational
database.
