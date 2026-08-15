# YARVIS
# Implementation Roadmap Amendment 013

## Status

**RATIFIED**

This ratification approves only the local Netpay operations role and bounded
local provisioning contract stated here. It does not implement or authorize by
itself any code, data change, bootstrap execution, or UI work.

## 1. Demonstrated operational gap

Amendments 011 and 012 ratify separate Master and Inbox roles. The current
`PrincipalMembership` model has one `role` and enforces one Membership per
`(principal_id, organization_id)`. `AuthorityResolutionService` resolves that
single persisted role through the closed `ROLE_PERMISSIONS` policy.

MVP-2C requires one real operator to find or create Netpay Master records and
then create and operate an Inbox case in the same Organization. No current role
contains both permission sets, and the durable local environment has no
approved bootstrap for such an operator. Headers, privileged tokens, fixed IDs,
or ungoverned database edits are not valid remedies.

## 2. Proposed combined role

| Proposed role | Exact permissions | Operational scope |
| --- | --- | --- |
| `netpay_operations_operator` | `netpay.master.read`, `netpay.master.manage`, `netpay.inbox.read`, `netpay.inbox.manage` | Maintain the Netpay master and manage the Netpay operational Inbox within the resolved Organization. |

This role represents the explicit job function of a Netpay operator. It
composes only permissions already ratified by Amendments 011 and 012; it does
not change their contracts or ownership boundaries.

The role grants no Radar, Mission, Intake, Document, Economics, Task, Process,
Governance, Workspace, Opportunity, Gmail, WhatsApp, file, OCR, or external
automation capability. It does not receive authority from headers or tokens,
does not select an Organization, does not replace or expand the existing
`netpay_master_viewer/operator` or `netpay_inbox_viewer/operator` roles, and
does not justify a combined viewer role.

## 3. Deferred membership model change

This proposal does not change `PrincipalMembership` or its one-role constraint.
A future many-to-many Membership-to-Role model may be evaluated only when real
dynamic role-combination needs justify its wider impact on schema, authority
resolution, revocation, fixtures, administration, and regression. That design
is outside this MVP.

## 4. Proposed local bootstrap contract

A future implementation may provide a non-public administrative command that
requires all of the following explicit inputs:

- canonical subject;
- stable persisted Organization selector, preferably an existing slug or key;
- requested role.

The command must:

1. run only in `local` or `test` and fail closed in `production`;
2. define no default subject, Organization ID, selector, or role;
3. treat tokens only as subject authentication evidence, never as permission;
4. resolve an existing active Organization from persistence and never create
   one;
5. create the Principal only when the explicit subject does not exist;
6. create an active Membership only when none exists for that
   Principal/Organization;
7. return an idempotent result when the same active Membership and role already
   exist;
8. stop without replacement or elevation when a Membership with another role
   exists, requiring a separate explicit governed administrative action;
9. report a safe operational result without secrets; and
10. avoid `authentication.py`, commercial records, historical records, and
    public endpoints.

The bootstrap exists only to enable an already configured local environment.
It is not a production user-administration system and cannot be invoked as an
application request path.

## 5. Authority, revocation, and replay invariants

- Persisted Principal, active Organization, active PrincipalMembership, the
  closed role policy, and `AuthorityResolutionService` remain the exclusive
  authority source.
- Revoking the combined Membership removes all four Master and Inbox
  permissions together.
- Every command revalidates Membership and authority before receipt lookup or
  replay.
- Assigning a case to a Principal never grants that Principal authority.
- Headers and tokens cannot grant permissions or choose an Organization.
- Cross-Organization concealment and the command idempotency, atomicity, event,
  receipt, and rollback invariants of Amendments 011 and 012 remain unchanged.

## 6. Compatibility and exclusions

The contracts `IC-NETPAY-CMD-005..015`, `IC-NETPAY-QRY-003..006`, and
`IC-NETPAY-EVT-003..006` remain unchanged. The existing four Netpay
viewer/operator roles remain unchanged. No migration is required for the role
proposal because `ROLE_PERMISSIONS` is the canonical code policy; this proposal
does not modify that policy or the persisted Membership schema.

The excluded historical sets `manual-close-validation` (11) and `netpay-demo`
(51) remain immutable, unlinked, and outside provisioning. This proposal does
not authorize code, `ROLE_PERMISSIONS`, an executable bootstrap, memberships,
UI, migrations, Gmail, WhatsApp, data writes, push, or merge.

## 7. Ratified scope and required next step

The combined role and local fail-closed bootstrap require a separate bounded
implementation mandate. MVP-2C remains blocked until that implementation has
been validated and a local operator has been provisioned explicitly.
