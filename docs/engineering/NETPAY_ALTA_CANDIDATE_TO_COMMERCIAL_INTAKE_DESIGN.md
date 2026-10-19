# Netpay Alta Candidate to Commercial Intake — ratified design

Status: **RATIFIED — H2-D PASS RECORDED; H2-Q/H2-I SPECIFIC TRACEABILITY PENDING**
Prepared: 2026-10-12

Ratified: 2026-10-12 against canonical pre-ratification SHA-256
`cf3038b808f1fd0849ec1e5c46fcf9a768803fdae082438a150032181c615383`.
At initial ratification, H2-Q was authorized, H2-I depended on H2-Q PASS and
H2-D awaited catalog approval. Those entry conditions are preserved below as
historical design context; the dated reconciliation records later evidence.

## Documentary reconciliation — 2026-10-15

[Amendment 022](IMPLEMENTATION_ROADMAP_AMENDMENT_022.md) and
[IG-010](IG-010_NETPAY_ALTA_AND_SECOND_PILOT_BATCH_AUTHORIZATION.md) declare
historical H2-Q/H2-I PASS. Their specific closure traceability remains
**TO BE VERIFIED**. The combined H1/H2-Q/H2-D result is not a substitute for
separate H2-Q/H2-I evidence, and this reconciliation issues no new PASS.

The [catalog approval](NETPAY_H2D_DOCUMENT_CATALOG_V1_APPROVAL.md) records
pilot operational approval of v1.0.0 on 2026-10-14. The subsequent
[H2-D closure](evidence/netpay-h2d-conformance-20261014.txt) records PASS
within the approved physical-location scope. The approval's earlier
"not yet PASS" statement describes entry, not the later closure.

**H2-D PASS does not imply an operational dossier was created.** The closure
records zero dossiers, reviews and evidence references after the preview.
Current pilot counts and runtime are **TO BE VERIFIED**; no pilot read or
write, test or migration was performed for this reconciliation.

HEAD `b6bc5930ae8b608ff55aa9849e995cb7639966d7` closes D1 only.
This design, later authority/evidence and H2 implementation remain local and
uncommitted. Existing design-time observations below are historical, not a
fresh inspection of the current implementation or database.

The next existing operator journey is review of the preview and explicit
human dossier creation; it is not performed or newly authorized here.
D3, D2-Lite, P2, attachment content/OCR, Drive, Gmail access/mutation and
e-commerce without a physical establishment remain outside this execution.
No scope is ratified and no publication is authorized.

## Historical problem and design-time boundary

The restricted Gmail pilot can extract a candidate, record append-only operator follow-up,
search same-tenant cases and commercial-intake records, and accept or link only when a verified
destination already exists. It cannot record a human correction to observed commerce/branch
facts with separate provenance, create a commercial-intake record from the candidate with an
auditable source trace, or accept a candidate after it has been terminally linked.

Existing authority remains unchanged:

- `IC-NETPAY-CMD-018` edits candidate classification, priority, next action and follow-up;
- `IC-NETPAY-CMD-020` creates a standalone commercial-intake item;
- `IC-NETPAY-CMD-032` accepts a candidate against a verified same-tenant destination;
- `IC-NETPAY-CMD-035` links a candidate to an existing same-tenant destination; and
- `IC-NETPAY-CMD-037` appends operator-reported follow-up without changing source evidence.

## Minimum proposed capability

1. Append a human qualification overlay to a mutable candidate. The overlay may correct the
   request type, requested product and record observed merchant/branch labels as
   `operator_reported`; it never
   rewrites extracted facts, Gmail source content or H1 notes.
2. Preview a commercial-intake payload from source facts plus the overlay. Every copied value
   retains its provenance. The operator must review all fields.
3. Create exactly one `CommercialIntakeItem` through the existing CMD-020 owner and persist the
   candidate-to-intake trace atomically and idempotently. No Master, branch, case or ticket is
   created.
4. Allow an explicit acceptance of a previously linked candidate through a separately audited
   command. This is the only proposed exception to the current immutable `linked` disposition.
5. Keep owner validation tenant-scoped and fail closed for missing, foreign or changed targets.
6. Preserve a reviewed multi-branch draft when moving from candidate review to commercial intake.
   Each branch remains a separate proposed row; the UI must never flatten five branches into one
   branch string. `product_interest` must represent `mixed` when both TPV and e-commerce are
   supported by evidence.
7. Allow an operator to propose a cross-thread relationship using the qualification overlay while
   keeping it unverified until a governed identifier or explicit human confirmation is recorded.
8. Conform a pre-case onboarding dossier without creating Master records. The dossier records the
   applicant kind (`persona_moral`, `persona_fisica` or unresolved), requested product and a
   versioned requirement snapshot. Requirements belong either to the client or to one specific
   proposed branch; multiple branches are never collapsed into one item.
9. Track each requirement as `pending`, `attachment_detected`, `under_review`, `validated`,
   `observed` or `not_applicable`. `pending` means no matching evidence has been identified;
   `attachment_detected` and `under_review` explicitly mean that evidence exists but has not been
   validated. Filename-based document types are suggestions with `unverified` verification.
10. Preserve for every dossier item its origin, source-item/attachment metadata reference,
    operator review, timestamps and append-only status history. Operator statements use
    `operator_reported` and never rewrite Gmail facts.

## Minimum onboarding dossier and checklist reuse

The pilot database was inspected on 2026-10-12. `netpay_checklist_templates` contains **zero
rows**, so there is no active content or version that can be reused for this request. The existing
mechanism is case-bound and supports a versioned JSON requirement snapshot; H2 should reuse those
versioning semantics after an approved catalog is supplied, rather than inventing an unversioned
list.

The proposed catalog must define, and a human owner must approve, requirements by applicant kind
and product. At minimum it must distinguish client-level fiscal identity, representative identity
where applicable, banking evidence and client address from branch-level address/site evidence;
and distinguish TPV readiness from e-commerce onboarding information. These labels are proposed
catalog categories, not a claim that any detected attachment fulfills them. Requirements that do
not apply require an attributed human decision.

The current pilot stores attachment name, MIME type, byte size and source message. H2 may associate
those metadata references with dossier items and show an unverified type suggestion. Opening,
downloading, OCR, parsing, malware scanning or semantic reading of attachment content is a separate
capability: it requires explicit scope, size/type limits, safe storage and a separate authorization
gate. It is excluded from H2 unless that later authority is ratified.

No real destination is created or linked by preparing this proposal.

## Exact operator journey

The authorized surface remains **Netpay Inbox → Gmail candidate**. The proposed journey is:

1. **Review immutable evidence.** Select a candidate and inspect persisted source facts, attachment
   metadata and H1 chronology. The UI keeps `message_observed`, `operator_reported` and unresolved
   values visibly separate.
2. **Correct qualification.** Open `Revisar datos del alta`; compare extraction with the overlay and
   edit applicant kind, legal-person name, representative name, commercial brand, requested
   products and separate branch rows. An exact review screen precedes `Guardar corrección`, which
   appends one server-attributed revision and never rewrites Gmail evidence.
3. **Preview commercial intake.** Choose `Preparar ingreso comercial`. Yarvis pre-fills a draft from
   the latest overlay and source provenance. The operator reviews provisional company/contact,
   products, summary, priority, next action and branch rows. No business record exists yet.
4. **Create once.** `Confirmar creación` displays the exact payload and states that it creates no
   Master or case records. Confirmation invokes the Commercial Intake owner once, records the
   candidate-to-intake trace and reads it back. Retry returns the same intake; the candidate is not
   automatically accepted.
5. **Conform the pre-case dossier.** Open `Expediente de alta`, select an approved template version
   applicable to applicant kind/product, review client and per-branch requirements, then confirm an
   immutable snapshot.
6. **Review requirements.** Associate persisted attachment metadata as possible evidence, choose a
   governed state and confirm it. Chronology shows actor, server time, prior/new state, provenance
   and reference. The UI never opens the attachment and never calls Gmail.

Navigation/reload preserves qualification and intake drafts without creating a record. A banner
states whether the view is a draft, confirmed intake or approved-version dossier snapshot.

## Persisted fields and relations

### Qualification overlay revision

Each append-only, tenant-owned revision contains revision ID, organization/candidate IDs, sequence,
applicant kind (`persona_moral`, `persona_fisica`, `unresolved`), legal-person observed name,
representative observed name, commercial brand, requested products (`tpv`, `ecommerce` or both),
operator rationale, actor, server time, correlation ID and command receipt. Every corrected scalar
carries `value`, `provenance_kind=operator_reported`, verification state and the source fact it
supersedes for presentation without altering it.

Branches are child rows, never a delimited string. Each has a stable draft key, display name,
requested products, provenance/verification and optional source-fact reference. They are not Master
branches. Name similarity does not verify identity or a cross-thread relationship. A reported
legal-person/representative relationship does not establish legal authority.

### Candidate-to-commercial-intake promotion

The reviewed draft stores candidate and qualification-revision IDs, provisional company/contact,
product interest, summary, priority, next action, source received time, separate proposed branches,
per-field provenance and validation findings. Confirmation stores the resulting Commercial Intake
ID, actor, server time, correlation/causation IDs and an idempotent receipt. CMD-020 remains the
aggregate owner; no Master or case foreign key is required.

### Pre-case onboarding dossier

One dossier belongs to organization + candidate and may reference the Commercial Intake. It stores
applicant kind, products, template ID/version/approval record, snapshot hash, creator and server
time. Snapshot requirements contain stable key, label, scope (`client` or a branch draft key),
applicability rule/result, required flag and order. Append-only history contains prior/new state,
attachment-metadata reference, provenance, verification, safe operator comment, actor, server time
and correlation ID. A metadata reference never implies possession, validity or content inspection.

## Documentary template origin and approval

At the 2026-10-12 design inspection, the pilot database contained **zero**
`netpay_checklist_templates`; no approved template existed at that point.
Before H2-D opens, a named Netpay process owner must supply or approve a catalog artifact with owner,
semantic version, effective date, applicant-kind/product applicability, client/branch scope,
requirement keys/labels, required/optional rules and supersession policy. Its canonical hash and
approval record must be registered through a governed catalog operation.

Existing version/snapshot mechanics may be reused only after that approval. A new template never
mutates an existing snapshot. Until then, the UI may show attachment inventory and `Plantilla
documental pendiente de aprobación`, but cannot create a dossier or claim requirements missing or
complete.

## Documentary state semantics

| State | Exact meaning | Required evidence |
| --- | --- | --- |
| `pending` | Applicable requirement exists; no evidence reference is associated. | Approved snapshot. This is the only state meaning missing evidence. |
| `attachment_detected` | Metadata suggests possible evidence; nobody has reviewed content or validity. | Metadata reference; filename/MIME suggestion remains unverified. |
| `under_review` | A human explicitly began review; no validity decision exists. | Attributed operator action. It does not mean complete. |
| `validated` | An authorized human confirmed reviewed evidence satisfies the requirement. | Actor, server time, safe rationale/reference and prior-state history. Filename alone is insufficient. |
| `observed` | A human recorded a problem, mismatch or insufficiency requiring correction. | Attributed observation and safe rationale; remains unresolved. |
| `not_applicable` | An authorized human determined the requirement does not apply to this scope. | Attributed rationale; never inferred automatically. |

Completion derives only from the approved snapshot and human states, never filename, attachment
count or MIME type.

## Proposed contract allocation

The repository was searched on 2026-10-12. The following IDs were absent. They are candidates
only and must be checked again immediately before ratification and catalog registration.

| Candidate ID | Semantic name | Boundary |
| --- | --- | --- |
| `IC-NETPAY-CMD-038` | `CorrectNetpayCandidateQualification` | Append a traced human qualification overlay; source and extraction stay immutable. |
| `IC-NETPAY-CMD-039` | `CreateCommercialIntakeFromNetpayCandidate` | Human-confirmed, idempotent delegation to CMD-020 plus candidate trace. |
| `IC-NETPAY-CMD-040` | `AcceptLinkedNetpayIntakeCandidate` | Explicit `linked -> accepted` review with the same verified owner. |
| `IC-NETPAY-QRY-021` | `PreviewNetpayCandidateCommercialIntake` | Side-effect-free preview with provenance and validation findings. |
| `IC-NETPAY-EVT-028` | `NetpayCandidateQualificationCorrected` | Safe overlay metadata, actor and trace; no email or note text. |
| `IC-NETPAY-EVT-029` | `NetpayCandidatePromotedToCommercialIntake` | Candidate/intake IDs, actor and trace. |
| `IC-NETPAY-CMD-041` | `CreateNetpayCandidateOnboardingDossier` | Create one versioned, tenant-owned dossier snapshot after human confirmation. |
| `IC-NETPAY-CMD-042` | `ReviewNetpayCandidateDossierRequirement` | Append an attributed requirement state/review; original attachment metadata remains unchanged. |
| `IC-NETPAY-QRY-022` | `RetrieveNetpayCandidateOnboardingDossier` | Read the checklist, attachment references and stable status history. |
| `IC-NETPAY-EVT-030` | `NetpayCandidateDossierRequirementReviewed` | Safe requirement/state metadata, actor and trace; no attachment content. |

## Acceptance criteria

- Corrections are append-only, attributed to the authenticated operator, timestamped by the
  server, tenant-scoped and idempotent; conflicting replay fails closed.
- Email facts, H1 notes, prior decisions and source fingerprints are byte-for-byte unchanged.
- Preview clearly separates `message_observed`, `operator_reported` and unresolved values.
- Product and every proposed branch have their own provenance and verification state. Human
  correction of product/branches is append-only and never changes the original extraction.
- Creation requires confirmation, invokes the owner contract once, and readback exposes the
  candidate/intake trace. Double click and retry create no duplicate.
- A candidate needs no Master link to create a pre-Master commercial intake.
- Link and acceptance revalidate the same-tenant owner before receipt replay.
- The UI journey is: review evidence → correct qualification → preview intake → confirm creation
  → read back link → accept explicitly → set next action/follow-up in the owner surface.
- Draft transfer preserves entered values across the journey and browser reload without creating
  business records before confirmation.
- The dossier readback shows its template/version snapshot, applicant/product applicability,
  client-versus-branch ownership, current state and full provenance/status history.
- The UI never labels an attachment as valid from its filename and visibly separates a missing
  document from a detected but unreviewed attachment.
- Synthetic tests cover new merchant onboarding, multiple branches, replies and support messages,
  including tenant isolation, changed replay and browser reload.

## Explicit exclusions

No Gmail write, automatic case/Master creation, automatic acceptance, inferred ticket, attachment
download or content reading, D3, D2-Lite, mobile work or expansion of the current ten-message pilot.
