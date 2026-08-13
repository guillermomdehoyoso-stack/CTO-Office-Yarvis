# YARVIS
# Implementation Roadmap Amendment 007

## Status

**RATIFIED**

This is a ratified narrow authority amendment. It supplements Amendments 005
and 006 only within the Document Registry authority scope stated here and does
not authorize implementation.

## 1. Demonstrated Contractual Gap

Document Registry contracts require server-evaluated `document.*` permissions,
but the current closed F-011 role matrix has no persisted membership role that
grants them. Inherited Document Registry tests therefore cannot migrate to
persistence-resolved identity without inventing an authority assignment.

This proposal supplements the narrow Intake, Operational Context, and Mission
Inbox mappings in Amendments 005 and 006. It does not change Amendment 004's
Radar scope or any decision in Amendments 004–006.

## 2. Proposed Canonical Document Registry Roles

| Proposed role | Validated permissions | Deliberate non-grants |
| --- | --- | --- |
| `document_viewer` | `document.read` | all Document Registry mutations and all non-Document permissions |
| `document_contributor` | `document.read`, `document.create`, `document.metadata.update`, `document.version.add`, `document.association.link`, `document.association.unlink` | `document.archive` and all non-Document permissions |
| `document_archivist` | `document.read`, `document.archive` | creation, metadata update, versioning, association changes, and all non-Document permissions |

No Radar, Intake, Operational Context, Mission Inbox, or Governance role gains
Document Registry authority incidentally. Reading does not grant mutation;
contribution does not grant archive; archive does not grant contribution.

## 3. Operations Covered

| Permission | Existing contract and operation |
| --- | --- |
| `document.create` | `IC-DOCUMENT-CMD-001` CreateDocument |
| `document.metadata.update` | `IC-DOCUMENT-CMD-002` UpdateDocument |
| `document.version.add` | `IC-DOCUMENT-CMD-003` AddDocumentVersion |
| `document.archive` | `IC-DOCUMENT-CMD-004` ArchiveDocument |
| `document.association.link` | `IC-DOCUMENT-CMD-005` LinkDocumentAssociation |
| `document.association.unlink` | `IC-DOCUMENT-CMD-006` UnlinkDocumentAssociation |
| `document.read` | `IC-DOCUMENT-QRY-001..004` get document, versions, associations, and documents by subject |

No additional Document Registry operation or fourth role is proposed by the
current contract catalog.

## 4. Authority Source and Security Invariants

Effective authority derives only from a persisted active `Principal`, active
`Organization`, active `PrincipalMembership`, the closed server role-to-
permission matrix, and `AuthorityResolutionService`. Tokens identify a subject
only. Headers, tokens, request payloads, and fixed organization identifiers
must not grant or select authority.

An implementation, if separately authorized, may adapt only an already-resolved
`IdentityAuthorityEnvelope` for a legacy `AuthenticatedPrincipal` boundary. It
must preserve principal and organization, project only validated permissions,
and must not read headers or tokens, add permissions, or replace
`AuthorityResolutionService`.

Missing permission, disabled Principal, absent or revoked Membership, inactive
Organization, forged header/token claims, cross-organization access, and replay
after revocation must deny according to the existing command/query contract.

## 5. Required Fixture Evidence

Focused tests must persist each fixture `Principal`, `Organization`, active
`PrincipalMembership`, and role. They must prove allowed operations, separated
role denials, revoked-membership denial before replay, forged-header denial,
and cross-organization concealment. A deterministic token may identify only the
fixture subject and may not encode privilege or organization.

## 6. Exclusions and Next Mandate

This proposal authorizes no code, tests, fixtures, migrations, routes, F2,
F2C change, G/H/I, backfill, historical-record change, push, or merge. It does
not modify Document Registry behavior, only the proposed authority mapping.

A separate bounded implementation mandate is required before Document Registry
authority, any transitional adapter, fixtures, tests, or focused evidence may
be implemented.
