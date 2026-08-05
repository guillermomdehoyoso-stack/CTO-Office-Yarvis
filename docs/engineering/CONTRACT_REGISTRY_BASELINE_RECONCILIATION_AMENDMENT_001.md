# YARVIS
# Contract Registry Baseline Reconciliation Amendment 001

## Status

**Ratified**

This is a narrow F-006 Contract Registry / F-013 Test and Conformance
Foundation governance amendment. It records the ratified reconciliation
decision; it does not authorize implementation and does not close
`FOUNDATION-DEBT-001`.

## 1. Purpose and Authority

The F-006 canonical projection currently contains 55 explicit definitions,
while the historic F-006 baseline and one conformance test still state 37. The
Interaction Contract Catalog has 116 Tier-1 identities after the documented
addition of `IC-WORKSPACE-QRY-001`. This amendment establishes an explicit,
closed, nominal, versioned runtime baseline so that a later technical
remediation can be assessed against an authoritative membership record rather
than a count alone.

This amendment supplements, and does not rewrite, the ratified Contract Registry
design, its implemented baseline, C06 closure at
`0fc8d615c85f42645ea61a85881309c9311fb3e1`, or Amendment 003 ratification at
`b20a44f879533a412369e950ddcc425fd1519432`.

## 2. Ratified Normative Definitions

### 2.1 Tier-1 catalog classification

**Tier-1** is an architectural catalog classification and coverage dimension.
It does not by itself establish ratification, implementation, runtime
availability, or membership in a canonical runtime projection.

`lifecycle`, `operational_status`, and runtime-baseline membership are
independent dimensions. A contract is not added to the baseline by any state,
by its Tier-1 classification, or merely because it exists in code.

The Interaction Contract Catalog is the authoritative record for catalog
classification and contract-governance state. Its 116 identities remain
catalogued whether or not they belong to the runtime baseline.

### 2.2 Runtime baseline V1

**F-006/F-013 Canonical Runtime Baseline V1** is the authoritative,
versioned record for the composition and projection metadata of its explicitly
listed members. Its membership is closed: only an identity named in section 4
belongs to V1.

The baseline has 55 members: 37 historic definitions, 7 Task definitions, 10
Document Registry definitions, and 1 Workspace definition. It has 27 Commands,
15 Queries, 11 Events, and 2 Notifications.

Catalog-governance metadata remains independent. In particular, the Catalog
continues to record its own lifecycle and operational-status values. For the
runtime projection, the ten Document Registry entries retain their established
`Ratified` / `Verified` metadata; the historic 37, the seven Task entries, and
the Workspace entry retain `Proposed` / `Planned`. This does not elevate,
rewrite, or otherwise alter the Catalog governance state of Task or Document
Registry entries.

## 3. Source of Truth and Membership Rule

This amendment's section 4 is the source of truth for V1
membership, order, identity, type, owner module, capability, and projection
lifecycle/operational-status metadata. The Catalog remains authoritative for
Tier-1 classification and catalog governance metadata. Neither document causes
an automatic update to the other.

Membership is established only by a later, explicitly ratified baseline version
that names the contract identity and projection metadata. The version must show
the complete ordered inventory and a nominal added/removed/substituted diff.
Counts, catalog status, implementation evidence, and a matching identifier
prefix are insufficient.

### 3.1 Ratified Metadata Decision 001 incorporation

This amendment incorporates by immutable reference the ratified
**Contract Registry Baseline Metadata Decision 001**:
`CONTRACT_REGISTRY_BASELINE_METADATA_DECISION_001.md`, UTF-8 content SHA-256
`C8844252E7C0ECBAA199B131833269C18F2B8AC4229C6DCC11471A4C7CE6E2BB`.
The referenced, ratified matrix fixes the V1 `name`, `semantic_purpose`,
`criticality`, and `primary_consumer_or_use_case` values for all 55 identities:
174 Existing Authority values and 46 Proposed by Decision 001 values.

The incorporation is limited to that immutable metadata snapshot. It does not
alter the Tier-1 Catalog, the executable expectation of 37, the 55-member
projection, or any code, test, migration, or implementation authority. The
Document Registry `Retrieve`/`List` versus `Get` naming divergence remains
recorded by the referenced decision and is not resolved here.

Metadata Decision 001 and this Amendment 001 are ratified. This incorporation
does not close `FOUNDATION-DEBT-001`, authorize F-006/F-013 technical
remediation, or authorize F-016, F-017, F-015, or C07-C09.

## 4. Canonical Runtime Baseline V1 Inventory

All entries have version `1.0.0`. `P/P` means `Proposed` / `Planned`; `R/V`
means `Ratified` / `Verified`. The table is ordered exactly as the current
canonical projection and is the nominal inventory; no range abbreviation adds
an unstated identity.

| # | Contract ID | Type | Owner module / capability | Projection state |
| ---: | --- | --- | --- | --- |
| 1 | IC-WORKSPACE-QRY-001 | Query | `mission_control` / operational workspace overview | P/P |
| 2 | IC-TASK-CMD-001 | Command | `operational_execution` / task creation | P/P |
| 3 | IC-TASK-CMD-002 | Command | `operational_execution` / task planning | P/P |
| 4 | IC-TASK-CMD-003 | Command | `operational_execution` / task assignment | P/P |
| 5 | IC-TASK-CMD-004 | Command | `operational_execution` / task transition | P/P |
| 6 | IC-TASK-CMD-005 | Command | `operational_execution` / task completion | P/P |
| 7 | IC-TASK-CMD-006 | Command | `operational_execution` / task cancellation | P/P |
| 8 | IC-TASK-CMD-007 | Command | `operational_execution` / task dependencies | P/P |
| 9 | IC-IDENTITY-CMD-001 | Command | `identity` / resolution | P/P |
| 10 | IC-IDENTITY-QRY-001 | Query | `identity` / canonical reference | P/P |
| 11 | IC-IDENTITY-EVT-001 | Event | `identity` / resolution | P/P |
| 12 | IC-GOVERNANCE-QRY-001 | Query | `governance` / authority | P/P |
| 13 | IC-GOVERNANCE-QRY-002 | Query | `governance` / policy/delegation | P/P |
| 14 | IC-GOVERNANCE-EVT-001 | Event | `governance` / authority | P/P |
| 15 | IC-RELATIONSHIP-CMD-001 | Command | `relationship` / association | P/P |
| 16 | IC-RELATIONSHIP-QRY-001 | Query | `relationship` / association | P/P |
| 17 | IC-RELATIONSHIP-EVT-001 | Event | `relationship` / association | P/P |
| 18 | IC-EVIDENCE-CMD-001 | Command | `observation_evidence` / observation | P/P |
| 19 | IC-EVIDENCE-CMD-002 | Command | `observation_evidence` / artifact/evidence | P/P |
| 20 | IC-EVIDENCE-CMD-003 | Command | `observation_evidence` / validation | P/P |
| 21 | IC-EVIDENCE-QRY-001 | Query | `observation_evidence` / lineage | P/P |
| 22 | IC-EVIDENCE-EVT-001 | Event | `observation_evidence` / observation | P/P |
| 23 | IC-EVIDENCE-EVT-002 | Event | `observation_evidence` / evidence | P/P |
| 24 | IC-KNOWLEDGE-CMD-001 | Command | `knowledge` / promotion | P/P |
| 25 | IC-KNOWLEDGE-QRY-001 | Query | `knowledge` / assertion | P/P |
| 26 | IC-KNOWLEDGE-EVT-001 | Event | `knowledge` / assertion | P/P |
| 27 | IC-EXECUTION-CMD-001 | Command | `execution` / work | P/P |
| 28 | IC-EXECUTION-CMD-002 | Command | `execution` / assignment | P/P |
| 29 | IC-EXECUTION-CMD-003 | Command | `execution` / work state | P/P |
| 30 | IC-EXECUTION-QRY-001 | Query | `execution` / work state | P/P |
| 31 | IC-EXECUTION-EVT-001 | Event | `execution` / work | P/P |
| 32 | IC-EXECUTION-EVT-002 | Event | `execution` / activity | P/P |
| 33 | IC-MISSION-CMD-001 | Command | `mission_control` / acknowledgement | P/P |
| 34 | IC-MISSION-QRY-001 | Query | `mission_control` / attention projection | P/P |
| 35 | IC-MISSION-EVT-001 | Event | `mission_control` / projection | P/P |
| 36 | IC-MISSION-NTF-001 | Notification | `mission_control` / communication | P/P |
| 37 | IC-NETPAY-CMD-001 | Command | `netpay_merchant_operations` / merchant candidate | P/P |
| 38 | IC-NETPAY-CMD-002 | Command | `netpay_merchant_operations` / case | P/P |
| 39 | IC-NETPAY-CMD-003 | Command | `netpay_merchant_operations` / case classification | P/P |
| 40 | IC-NETPAY-CMD-004 | Command | `netpay_merchant_operations` / checklist | P/P |
| 41 | IC-NETPAY-QRY-001 | Query | `netpay_merchant_operations` / case view | P/P |
| 42 | IC-NETPAY-QRY-002 | Query | `netpay_merchant_operations` / checklist view | P/P |
| 43 | IC-NETPAY-EVT-001 | Event | `netpay_merchant_operations` / case | P/P |
| 44 | IC-NETPAY-EVT-002 | Event | `netpay_merchant_operations` / case | P/P |
| 45 | IC-NETPAY-NTF-001 | Notification | `netpay_merchant_operations` / communication | P/P |
| 46 | IC-DOCUMENT-CMD-001 | Command | `document_registry` / document creation | R/V |
| 47 | IC-DOCUMENT-CMD-002 | Command | `document_registry` / metadata update | R/V |
| 48 | IC-DOCUMENT-CMD-003 | Command | `document_registry` / version creation | R/V |
| 49 | IC-DOCUMENT-CMD-004 | Command | `document_registry` / document archival | R/V |
| 50 | IC-DOCUMENT-CMD-005 | Command | `document_registry` / association link | R/V |
| 51 | IC-DOCUMENT-CMD-006 | Command | `document_registry` / association unlink | R/V |
| 52 | IC-DOCUMENT-QRY-001 | Query | `document_registry` / document retrieval | R/V |
| 53 | IC-DOCUMENT-QRY-002 | Query | `document_registry` / version retrieval | R/V |
| 54 | IC-DOCUMENT-QRY-003 | Query | `document_registry` / association retrieval | R/V |
| 55 | IC-DOCUMENT-QRY-004 | Query | `document_registry` / subject retrieval | R/V |

The baseline metadata record additionally fixes the existing canonical `name`,
semantic purpose, criticality, and primary consumer/use-case values for these
55 identities. Those fields must match the corresponding catalog record for
the 54 catalogued identities, except that the projection lifecycle and
operational-status values for the ten Document Registry entries are the R/V
values stated above. No later implementation may infer or replace a metadata
field from membership alone.

### 4.1 Reconciliation

```text
37 historic contracts
 + 7 Task contracts
 + 10 Document Registry contracts
 + 1 Workspace contract
 = 55 Canonical Runtime Baseline V1 contracts

116 Tier-1 catalog identities
 - 55 Canonical Runtime Baseline V1 identities
 = 61 catalogued identities outside the baseline
```

## 5. Workspace and Mission Contract Boundaries

`IC-WORKSPACE-QRY-001` is a new catalog identity with the following complete
metadata:

| Field | Value |
| --- | --- |
| Version | `1.0.0` |
| Type | Query |
| Owner module / context | `mission_control` / Mission Control |
| Capability | operational workspace overview |
| Name | `RetrieveOperationalWorkspaceOverview` |
| Semantic purpose | Retrieve tenant-safe operational workspace composition |
| Primary consumer | Operational Workspace |
| Criticality | Core |
| Lifecycle / operational status | Proposed / Planned |

It is distinct from `IC-MISSION-QRY-007`. The latter remains a Mission Control
operational-workspace catalog query whose stated purpose is bounded,
tenant-safe composition of existing owner read models. The two identities are
not aliases, equivalents, replacements, or deprecation relations. V1 includes
only `IC-WORKSPACE-QRY-001`; `IC-MISSION-QRY-007` remains catalogued and outside
the baseline. No consumer, owner, or name similarity may create a substitution
relation without a separately ratified baseline version.

## 6. Catalogued Identities Outside Runtime Baseline V1

The following 61 identities are explicitly excluded from V1 membership while
remaining Tier-1 catalog entries. They are not removed, degraded, or
reinterpreted by this amendment:

- `IC-INBOX-CMD-001`, `IC-INBOX-QRY-001`, `IC-INBOX-CMD-003`,
  `IC-INBOX-QRY-002`, `IC-INBOX-EVT-001`.
- `IC-MISSION-QRY-002`, `IC-MISSION-QRY-003`, `IC-MISSION-CMD-002`,
  `IC-MISSION-CMD-003`, `IC-MISSION-CMD-004`, `IC-MISSION-CMD-005`,
  `IC-MISSION-CMD-006`, `IC-MISSION-QRY-004`, `IC-MISSION-QRY-005`,
  `IC-MISSION-QRY-006`, `IC-MISSION-EVT-002`, `IC-MISSION-EVT-003`,
  `IC-MISSION-EVT-004`, `IC-MISSION-EVT-005`, `IC-MISSION-EVT-006`,
  `IC-MISSION-EVT-007`, `IC-MISSION-QRY-007`.
- `IC-PROCESS-CMD-001`, `IC-PROCESS-CMD-002`, `IC-PROCESS-CMD-003`,
  `IC-PROCESS-CMD-004`, `IC-PROCESS-CMD-005`, `IC-PROCESS-CMD-006`,
  `IC-PROCESS-CMD-007`, `IC-PROCESS-CMD-008`, `IC-PROCESS-CMD-009`,
  `IC-PROCESS-CMD-010`, `IC-PROCESS-CMD-011`, `IC-PROCESS-CMD-012`,
  `IC-PROCESS-CMD-013`, `IC-PROCESS-CMD-014`, `IC-PROCESS-CMD-015`.
- `IC-PROCESS-QRY-001`, `IC-PROCESS-QRY-002`, `IC-PROCESS-QRY-003`,
  `IC-PROCESS-QRY-004`, `IC-PROCESS-QRY-005`, `IC-PROCESS-QRY-006`,
  `IC-PROCESS-QRY-007`, `IC-PROCESS-QRY-008`.
- `IC-PROCESS-EVT-001`, `IC-PROCESS-EVT-002`, `IC-PROCESS-EVT-003`,
  `IC-PROCESS-EVT-004`, `IC-PROCESS-EVT-005`, `IC-PROCESS-EVT-006`,
  `IC-PROCESS-EVT-007`, `IC-PROCESS-EVT-008`, `IC-PROCESS-EVT-009`,
  `IC-PROCESS-EVT-010`.
- `IC-ECONOMICS-CMD-001`, `IC-ECONOMICS-CMD-002`,
  `IC-ECONOMICS-QRY-001`, `IC-ECONOMICS-QRY-002`,
  `IC-ECONOMICS-EVT-001`, `IC-ECONOMICS-EVT-002`.

## 7. Baseline Versioning and Change Procedure

An addition, withdrawal, deprecation, or substitution requires a new baseline
version and independent review before ratification.

1. The proposal names every resulting baseline identity in order and the exact
   added, removed, retained, and substituted IDs.
2. It declares the full projection metadata for each changed identity and
   explicitly distinguishes catalog-governance state from runtime projection
   metadata.
3. A removal does not delete the catalog identity or historical implementation
   evidence. Deprecation is a catalog-governance decision, not an implied
   baseline deletion.
4. A substitution names both identities and its compatibility or non-
   compatibility semantics. Similar naming, owner, or consumer is never an
   implicit alias.
5. Only after ratification may a separately authorized technical remediation
   change code, tests, or runtime composition.

## 8. Future Technical Remediation Acceptance Criteria

No technical remediation is authorized by this amendment. A later, independent
F-006/F-013 implementation authorization must require evidence that:

- the projection contains exactly the 55 identities in section 4, in its
  declared order, with the stated type, owner module, capability, lifecycle,
  and operational status;
- the test expectation is replaced by this nominal inventory, not merely 55;
- all 54 catalogued baseline members match their catalog identity and type;
- `IC-WORKSPACE-QRY-001` is included only with its stated metadata;
- the 61 listed exclusions remain absent from V1 unless a later baseline version
  ratifies their inclusion;
- Task and Document Registry catalog states remain unchanged; and
- the focused Contract Registry and F-013 conformance evidence passes.

`FOUNDATION-DEBT-001` remains open until that remediation and validation are
completed and independently accepted. This proposal does not authorize or
start F-016, F-017, F-015, C07-C09, or any other implementation work.

## 9. Ratification Evidence

Independent review verified the 55 identities against the implementation
projection, 54 catalogued matches plus the one Workspace catalog entry, the 61
nominal exclusions, metadata separation, and the absence of automatic
membership rules. This ratification makes the baseline normative only as
composition and projection-metadata authority; it does not authorize runtime
implementation.
