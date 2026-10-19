# Implementation Roadmap Amendment 022 — Alta qualification and commercial-intake promotion

Status: **RATIFIED — H2-Q PASS; H2-I PASS; H2-D PASS**
Date: 2026-10-12

Ratified: 2026-10-12 against canonical pre-ratification SHA-256
`b511b2fa8341bf31a50d355b9c3b5acf16530629e7bee78b92f01b4d89613bd7`.
The ratification opens H2-Q implementation and evidence. H2-I remains conditional on H2-Q PASS.
H2-D was initially closed pending catalog approval. The approved v1.0.0 catalog now opens H2-D
implementation and conformance; attachment content/OCR and P2 remain closed as stated below.

H2-Q and H2-I subsequently passed. On 2026-10-14 Guillermo De Hoyos, as named operational owner
for this pilot, approved catalog v1.0.0 with verified canonical SHA-256
`4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b`. This opens H2-D
implementation under IG-010. It is not corporate Netpay approval and does not open attachment
content/OCR, Drive, P2 or e-commerce without a physical establishment.

This amendment proposes one bounded H2 package based on
`NETPAY_ALTA_CANDIDATE_TO_COMMERCIAL_INTAKE_DESIGN.md`. It does not change the PASS status or
scope of IG-008 Gates A/B/C or IG-009 H1.

## Proposed delivery phases

1. **H2-Q — local qualification overlay.** Persist append-only corrections for applicant kind,
   legal person, representative, brand, products and separate branches using only existing local
   source/H1 data. Ratification of this amendment, its design and IG-010 opens implementation;
   H2-Q evidence must pass before H2-I opens.
2. **H2-I — reviewed Commercial Intake promotion.** Preview and create exactly one owner-controlled
   intake without recapture, Master/case creation or automatic candidate acceptance. The ratified
   package authorizes implementation only after H2-Q PASS. Creation with real business data remains
   an explicit operator act, outside synthetic conformance.
3. **H2-D — pre-case dossier.** Implement versioned requirements and review history only after H2-I
   PASS and a named Netpay process owner supplies/approves the documentary catalog with canonical
   hash, version and applicability. Package ratification does not approve catalog content. Without
   that approval H2-D stays closed and H2-Q/H2-I remain independently reviewable.

All three phases use local persisted data only and perform no Gmail or attachment-content call.

If ratified, H2 may implement only the proposed qualification overlay (including product and
separate branch observations), reviewed commercial-intake preview/creation, multi-branch draft
preservation, candidate trace, linked-candidate acceptance and the minimum UI needed for that
journey. It may register CMD-038..040, QRY-021 and EVT-028..029 after a fresh collision check.
The dossier extension may register CMD-041..042, QRY-022 and EVT-030 after the same fresh check.

H2 may extend the Commercial Intake product catalog with `mixed` only for this reviewed intake
path. It does not grant `netpay.master.read/manage`, change the pilot membership or create Master
records automatically. Master creation/conversion remains a later explicit human action under its
own existing authority.

H2 may also implement the minimum pre-case onboarding dossier in the ratified design: an approved,
versioned requirement catalog by applicant kind and product; client- and branch-scoped document
items; the six governed states; provenance, human review and append-only history. The repository's
case checklist semantics may be reused, but the currently empty pilot catalog cannot be treated as
an approved checklist. Attachment metadata may be referenced; attachment content access remains a
separate, closed capability requiring explicit later authorization and limits.

Before any migration, implementation must run `alembic heads`, preserve the single actual head,
and prove upgrade/downgrade/upgrade on an isolated database. The pilot database may receive only
the forward migration after the isolated proof. No migration ID is reserved by this proposal.

Evidence must prove source immutability, provenance separation, idempotency, tenant isolation,
owner validation, readback/reload and absence of automatic business decisions. Ratification of
this amendment alone does not open implementation; IG-010 must also be ratified.

The proposed second pilot batch is deliberately a separate gate in IG-010. H2 does not discover,
approve or ingest any additional Gmail message.

Attachment download/content reading/OCR requires a later design, roadmap amendment and gate for
types/sizes, malware handling, encrypted storage, retention, redaction, tenant isolation and human
review. The twenty-message expansion requires its separate P2 approval. Neither is opened by this
amendment.
