# WS-002A — Intake Operational Context Association

**Status:** Implemented checkpoint — pending validation and review

## Scope

WS-002A establishes the immutable, tenant-owned association between a deterministic
Inbox Intake and the minimum operational-context reference hierarchy:

```text
Organization -> Site -> Project -> ConnectorMapping (optional)
```

It does not implement reference-entity public CRUD, Inbox projections, reassociation,
or full WS-002 processing.

## Ownership and Invariants

- `IntakeItem.organization_id` remains the authoritative tenant discriminator and is
  derived only from the authenticated principal.
- `IntakeItem.intake_mode` is the sole runtime eligibility invariant. Only the
  persisted value `deterministic` is eligible for association; organization,
  idempotency, trace, and source metadata do not imply eligibility.
- Operational Context owns canonical `Site`, `Project`, and `ConnectorMapping`
  references. Inbox owns `IntakeOperationalContextAssociation`.
- A Site belongs to one Organization. A Project belongs to one Site and one
  Organization. A ConnectorMapping belongs to one Project and one Organization.
- One immutable association is permitted for an Intake. Legacy Intake records without
  an organization are ineligible.
- Migration `20260726_12` backfills `intake_mode = deterministic` only for existing
  rows with a non-null organization, idempotency key, and idempotency fingerprint:
  the prior WS-001 deterministic persisted combination. All other historical rows
  remain `legacy`.
- Missing, cross-tenant, and hierarchy-inconsistent references are concealed as not
  found.
- The hierarchy is enforced both by governed application validation and PostgreSQL
  composite foreign keys. Site references are unique within an Organization, Project
  references within a Site, and connector references within a Project.

## Governed Contracts

- `IC-INBOX-CMD-003 AssociateIntakeOperationalContext`, authority
  `inbound.context.associate`.
- `IC-INBOX-QRY-002 RetrieveIntakeOperationalContext`, authority `inbound.read`.
- `IC-INBOX-EVT-001 IntakeOperationalContextAssociated`.

## Idempotency and Transactionality

The command namespace is `(organization_id, idempotency_key)`. Its fingerprint
contains the Intake and reference identifiers plus correlation. Equivalent retries
return the original association without a duplicate event. Reuse with different
command content and any already-associated Intake under an unrelated key returns a
conflict. The association and event commit in one Unit of Work.

## Deferred Work

No public reference administration, context reassociation, Inbox projection,
automation, or future WS-002 lifecycle behavior is included.

Production reference provisioning and import remain deferred. Test fixtures seed
the minimal reference records directly and do not define a production lifecycle.
