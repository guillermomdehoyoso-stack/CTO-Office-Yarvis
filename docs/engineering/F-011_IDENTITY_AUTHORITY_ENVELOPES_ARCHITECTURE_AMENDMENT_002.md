# YARVIS
# F-011 Identity and Authority Envelopes Architecture Amendment 002

## Status

**RATIFIED — IMPLEMENTATION-SCOPE CLARIFICATION — NO NEW PRODUCT CAPABILITY**

**Date:** 2026-08-06
**Authority:** Guillermo de Hoyos, Architecture Authority
**Scope:** resolves the F-011 E–I execution contradiction only.

## 1. Conflict Corrected

[Implementation Design](F-011_IDENTITY_AUTHORITY_ENVELOPES_IMPLEMENTATION_DESIGN.md)
defines E as Radar reads/lists under the Authority Envelope, F as Radar commands
and actor transition, G as Radar backfill/final constraints, H as legacy header
authority removal, and I as factual closure. IG-006 previously authorized only
A–D and prohibited Radar cutover/backfill. That combination made E–I impossible.

This Amendment preserves the ratified architecture and A–D. It authorizes E–I
only as the identity/authority migration of the existing Radar already required
by Amendment 001 and the Implementation Design.

## 2. Authorized E–I Scope

- **E:** migrate existing Radar reads and lists to the server-built Authority
  Envelope, persistent Principal/Membership/Organization selection, ownership,
  organization isolation, and concealed foreign `not found`.
- **F:** migrate existing Radar commands and historical actor transition to the
  canonical persisted actor; preserve existing behavior while adding ownership,
  correlation/causation, applicable idempotency/replay/conflict handling and
  safe events.
- **G:** perform only the explicit, auditable Radar authority backfill,
  reconciliation, final constraints/indexes, rollback, and cutover described in
  the Implementation Design.
- **H:** remove legacy header-derived authority only after E–G evidence proves
  no in-scope legacy consumer, reconciled backfill, active constraints and a
  tested rollback.
- **I:** close factually only after A–H, affected regression, compile, Docker,
  applicable migration validation, Markdown validation, diff review and scope
  audit are green.

## 3. Mandatory G Gates

Before backfill, produce and obtain approval for a mapping table containing the
legacy entity/record, target organization/principal/membership/canonical actor,
authoritative source, expected cardinality, unmapped and ambiguous records,
resolution strategy, and approval evidence. No default Organization, fabricated
authority, Membership created merely to pass migration, or mapping inferred from
historical headers, workspace strings, conversations, or non-authoritative data
is allowed.

Cutover requires zero unresolved ambiguity; origin/mapped/migrated/skipped/
conflicted counts; zero in-scope legacy authority consumers; A–G green; tested
rollback; and ready constraints. Backfill must be repeatable or protected from
double execution, preserve ownership, expose only safe counts, stop on conflict,
and not change non-authority Radar semantics.

## 4. Preserved Exclusions

This Amendment authorizes no new Radar screen, workflow, product capability,
Master Registry, requester contact, support routing, folio, logistics, activity,
engagement, scraping, integration, automation, Identity deferred contract,
Governance QRY-002, DI-003/C09, IG-005, F-016 or successor. `BACKLOG.md` is not
implementation authority. No historic identity, contact, Membership, authority,
folio, guide, date or status may be inferred.

## 5. Gate Effect

F-011 remains In Progress. IG-006 is active for A–I only under this Amendment;
E–G are bounded to the existing Radar authority migration. This Amendment does
not declare F-011 complete or authorize push/merge.
