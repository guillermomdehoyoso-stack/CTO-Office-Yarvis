# IG-010 — Netpay alta workflow and second restricted pilot batch

Status: **RATIFIED — H2-Q PASS; H2-I PASS; H2-D PASS; ATTACHMENT-CONTENT/P2 CLOSED**
Date: 2026-10-12

Ratified: 2026-10-12 against canonical pre-ratification SHA-256
`5f4249a47e0466ae0d4dd48dae7d3c8f5ca0ca6ae9fabbf02fdfb347c11c4893`.
H2-Q and H2-I passed their synthetic isolated conformance and local-runtime availability checks on
2026-10-13. H2-D requires the additional catalog approval defined here. Attachment content/OCR and
P2 remain closed.

The H2-D catalog v1.0.0 was approved for this pilot on 2026-10-14 by Guillermo De Hoyos as the
named operational owner. The exact pre-approval canonical SHA-256
`4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b` was verified before the
approval record was written. The scope is physical-location onboarding for persona física or
persona moral across TPV/e-commerce/mixed; e-commerce without a physical establishment remains
excluded. This is pilot operational authority, not corporate Netpay approval. H2-D implementation
is now evidenced as PASS; the criteria and bounded evidence remain recorded below.

## Gate H2-Q — local candidate qualification overlay

Entry requires ratification of Design/Amendment 022/IG-010 and fresh contract/Alembic collision
checks. It uses persisted local data only. PASS requires append-only, server-attributed,
tenant-scoped corrections for applicant kind, legal person, representative, brand, requested
products and distinct branches; replay/conflict behavior; stable reload; and byte-for-byte
preservation of source, H1 chronology and decisions. Message evidence and operator reports remain
visibly separate. Name matching establishes neither identity nor legal authority.

## Gate H2-I — reviewed Commercial Intake promotion

Entry requires H2-Q PASS. Preview must disclose each field, provenance, validation finding and
unresolved value before confirmation. PASS requires one idempotent delegation to CMD-020,
candidate-to-intake trace, double-click/retry readback, organization isolation and proof that no
Master client/company/branch or case was created. The candidate is not automatically accepted,
linked or disposed. Draft values and branch rows survive navigation/reload.

## Gate H2-D — pre-case onboarding dossier

Entry requires H2-I PASS and a documentary catalog approved by a named Netpay process owner. The
approval evidence includes semantic version, effective date, canonical hash,
applicant-kind/product applicability, client/branch scope and supersession policy. Before the
2026-10-14 approval, the zero-row template table kept H2-D closed. The separately approved exact
catalog snapshot now opens implementation; synthetic templates still cannot approve or replace
pilot catalog content.

H2-D PASS requires an immutable approved-version snapshot, all governed states (`pending`,
`attachment_detected`, `under_review`, `validated`, `observed`, `not_applicable`), append-only
history, tenant isolation and readback/reload. It must distinguish missing evidence from detected
or under-review evidence. Filename/MIME suggestions remain unverified until human review. Combined
H2 conformance includes a mixed TPV/e-commerce request with five separate branches and proves that
the Inbox-only operator invokes no Master mutation.

**Attachment-content subgate: CLOSED.** H2 does not authorize opening, downloading, OCR, parsing or
semantic inspection of attachment content. A later proposal must state allowed types and sizes,
malware controls, storage/retention, tenant isolation, audit events and human review, and must be
ratified before any such access. It cannot be opened by H2-Q, H2-I, H2-D or catalog approval.

## Gate P2 — proposed additional 20-message pilot

P2 remains closed until H2-Q, H2-I and H2-D PASS and a separate human approval of the exact opaque
manifest. If H2-D remains closed for lack of an approved catalog, P2 also remains closed.

- Window: messages received from **2026-09-12T00:00:00-06:00 through
  2026-10-12T23:59:59-06:00**.
- Selection: the operator manually applies the exact parent label to 20 messages useful for new
  merchant/branch/e-commerce onboarding or their follow-up. Exclude unrelated support, personal
  mail, bulk notifications and messages already represented by the first manifest.
- Discovery returns exactly 20 HMAC handles and timestamps, no subject/body/sender ingestion.
- Store a new immutable batch/manifest identity. The original ten-entry manifest, approval,
  runs and evidence remain unchanged and queryable.
- Approval is explicit for that exact 20-entry digest. Any count, handle, window or digest change
  invalidates approval.
- Synchronization reads only approved IDs in the explicit window, once manually triggered. No
  automation, sublabels, mailbox-wide scan, attachment download or Gmail mutation.
- Dedupe uses tenant + connection + Gmail message ID and immutable fingerprint. Retry/readback
  must produce no duplicate source, candidate, link, decision, follow-up or derived event.

P2 usefulness PASS requires at least: five clear onboarding candidates, five follow-up/reply
messages, representation of multiple branches where available, no false activation for support,
and a reviewed report of relevant/unclassified/duplicate outcomes. These are evaluation thresholds,
not permission to select unavailable or unsuitable messages.

The existing persistence shape holds only one current manifest. Preserving the first manifest
therefore needs a reviewed batch model and likely a migration. Contract IDs and schema for P2 are
**TO BE VERIFIED** after H2; this proposal intentionally does not reserve them.
