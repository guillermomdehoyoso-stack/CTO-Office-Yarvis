# Netpay MVP-2D1 — Principal and Membership Determination

**Date:** 2026-08-17

**Determination:** **Insufficient Evidence**

## Scope and non-authority

This separate, read-only determination evaluates whether this canonical chain can be proved without using a visible name or the Netpay mailbox as identity proof:

```text
Guillermo Mario De Hoyos Olivera → Principal → canonical external subject / identity → active PrincipalMembership → Distribución Netpay
```

It grants no authority. It does not assign a Principal, membership, role, or bootstrap; nor does it authorize contracts, implementation, OAuth, Google resources, credentials, Gmail, or mailbox access.

## Determination basis

**Insufficient Evidence.** Static sources establish the required model and authority-resolution process, but contain no canonical row or immutable record linking the named person to a Principal, identity subject, active membership, and Distribución Netpay. No safe database inspection was available under the constraints. This review therefore cannot prove one candidate, no candidate, or multiple plausible candidates in canonical persistence.

## Sources consulted (static, read-only)

| Source | Evidence | Limitation |
| --- | --- | --- |
| `apps/api/src/yarvis_api/models/principal.py` | Principal UUID, unique `external_subject`, active/disabled state, optional `person_id`; Membership UUID, Principal/Organization binding, role, active/revoked state, `revoked_at`. | Schema only; no issuer, Principal type, `valid_from`, or `valid_until` field. |
| `apps/api/src/yarvis_api/models/person.py` | Person UUID and optional name/email attributes. | No static Person-to-Principal join; email is not identity proof. |
| `apps/api/migrations/versions/20260806_32_principal_membership_foundation.py` | Unique subject and Principal/Organization membership constraints, lifecycle checks. | Migration structure is not row evidence. |
| `apps/api/src/yarvis_api/services/authority_resolution.py` | Requires persisted active Principal, active Membership, and active Organization; ambiguity fails closed. | No person-name lookup and no proof of any particular row. |
| `apps/api/src/yarvis_api/local_netpay_authority.py`, seeds, tests | Explicit local/test subjects and provisioning exist. | Fixtures/local provisioning are not proof for Guillermo; none was invoked. |
| IG-006, F-011 implementation design, ADR-014 | Server-side persisted identity and membership are required; Person is not credential. | Ratified authority/design, not persisted identity evidence. |
| Amendment 014 and Gmail design reviews | MVP-2D1 requires unequivocal Principal and active Distribución Netpay membership; it prohibits invented identifiers. | Design/review evidence, not runtime identity or membership record. |
| Repository search and relevant Git history | Guillermo appears only in narrative/authority references and historic Radar display-owner text; history records F-011 schema/local-provisioning work. | No committed canonical Person, Principal, external subject, membership, or binding record was found. |

No `.env`, secret, token, password, credential store, key, or sensitive configuration file was read. No Gmail, Google, OAuth, remote identity provider, or external service was contacted.

## Evidence chain

| Required link | Result | Evidence / absence |
| --- | --- | --- |
| Person → Person record | Not established | No canonical Person row was available. |
| Person → Principal | Not established | `person_id` is optional; no join evidence, Principal ID, or Person ID was found. |
| Principal → external subject / issuer | Not established | `external_subject` is unique, but no subject was inferred or disclosed; the model has no issuer field. |
| Principal → active membership | Not established | No membership ID, status, or `revoked_at` value was available. |
| Membership → target Organization | Not established as runtime fact | Amendment 014 names the organization for design scope only. |
| Existing roles | Not established | No role was inspected, inferred, or assigned. |
| Validity dates | Not established | The model lacks `valid_from` and `valid_until`. |
| No multiple plausible candidates | Not established | No canonical candidate set was available. |

## Facts, indications, absences, and contradictions

### Confirmed canonical facts

- Authority requires an active persisted Principal, active PrincipalMembership, and active Organization.
- `external_subject` is unique; membership is unique per Principal/Organization pair.
- MVP-2D1 requires this evidence before any future bootstrap.

### Non-sufficient indications

- Guillermo's documented authority name and historical Radar `owner="Guillermo"` text are narrative only.
- The Gmail mailbox is design configuration and may not infer a Principal or Organization.

### Material absences

- Principal UUID, person-linked Principal status/type, external subject, issuer, membership UUID/status, role, and effective dates.
- A canonical Organization row linked through membership, and evidence excluding competing candidates.

### Contradictions

None found. Absence of the chain does not establish non-existence.

## Database-access assessment

No local SQLite or other file-backed database artifact exists in the workspace. The PostgreSQL target is controlled by secret-valued process configuration. The effective configuration was not read, no credential was recovered or used, and no connection was attempted. A local target and an explicitly read-only transaction therefore could not be guaranteed without violating the restrictions.

No SQL was executed, so there are no results to redact and no transaction to roll back. If separately authorized evidence later makes a local canonical database safely available, the only permitted conceptual queries are Person → Principal → Membership → Organization joins, candidate-count/multiplicity checks, and existing-role observation. They must use `BEGIN READ ONLY`, only `SELECT`, minimum redacted output, and `ROLLBACK`.

## Next permitted action

Obtain separately authorized, read-only canonical identity evidence or a demonstrably local database session that can be opened as `BEGIN READ ONLY` without reading or exposing secrets. It must show one unambiguous persisted Principal and an active Distribución Netpay membership before any request for canonical contract assignment.

This is not permission to assign a membership or role, invoke bootstrap, modify data, create credentials, implement code, or access Gmail.

## Verification record

- Static inspection only; zero database, SQL, service, external-provider, or Gmail writes occurred.
- No tests, Docker commands, migrations, commit, or push were performed.
- `git diff --check` was run after creating this record.
