# Observation Pipeline

## Approved Flow

Source
-> Document
-> Observation
-> Resolution
-> Operational State
-> Policy Result
-> Attention Item

## Lifecycle

1. Source registration records source_type, source_name, received_at and source metadata.
2. Document registration stores metadata, hash and optional storage reference.
3. Observation creation records claims with field-level provenance.
4. Resolution proposes identity/hierarchy mapping and requires confirmation for sensitive links.
5. Operational state is derived from confirmed observations and confirmed resolutions.
6. Policies evaluate resolved state with deterministic operators.
7. Attention items are generated for matched, conflict, or insufficient-data outcomes.

## Status Transitions

Observation confirmation_status:
- observed
- candidate
- confirmed
- rejected
- superseded
- conflicted

Resolution decision_status:
- proposed
- confirmed
- rejected
- conflicted

Policy evaluation result_status:
- matched
- not_matched
- insufficient_data
- conflict

## Immutability

- Observation rows are append-first memory.
- Only confirmation metadata/status transitions are mutable.
- Corrections produce superseding observations or explicit resolution decisions.

## Provenance

Each observation stores provenance including:
- source_type
- source_reference
- extraction_method
- confidence
- processor and processor version
- related evidence references

## Conflicts

Conflicting observations are retained with status `conflicted`.
No automatic deletion or silent overwrite is allowed.

## Reprocessing And Idempotency

- Duplicate documents are detected by file_hash.
- No duplicate observations are created from duplicate documents unless reprocessing is explicitly requested.
- Reprocessing records processor/version metadata in provenance.

## Human Confirmation

Human confirmation is mandatory before promoting identity/ownership-sensitive claims to confirmed operational state.

## Retention

Evidence metadata, observations, resolution decisions, and policy evaluations remain auditable.
Retention policy enforcement remains an explicit future hardening task.

## Cross-Domain Example

- A logistics email and a CSV report may both observe store ownership.
- Observations conflict on branch_name.
- Resolution is proposed with both candidates and confidence.
- Human confirms one candidate; policy evaluation proceeds using confirmed state.

## NetPay Example

- Source: imported NetPay email.
- Document: normalized email payload with hash.
- Observations: folio, tracking_number, store_id, asset_serial, recipient, address.
- Resolution: Store and Asset candidate link.
- Policy: churn or asset recovery review.
- Attention: review_churn / review_asset_recovery.

## Future Accounting Example

Future intake sources:
- invoice photo
- PDF invoice
- CFDI XML
- issued invoices
- received invoices
- payment complements
- bank movements
- expense receipts
- tax retentions
- manual adjustments

Future observations:
- issuer_rfc
- receiver_rfc
- uuid
- invoice_date
- payment_date
- subtotal
- vat_amount
- withheld_vat
- withheld_income_tax
- total
- currency
- payment_method
- payment_form
- invoice_status
- deductible_candidate
- accounting_period
- source_document_hash

Future outputs:
- invoice registry
- payable/receivable status
- monthly VAT working estimate
- income tax working estimate
- missing XML/PDF alert
- duplicate invoice alert
- reconciliation exceptions
- accountant review package

Mandatory disclaimer:
- Estimates are operational working projections.
- They do not replace official tax accounting.
- CFDI XML and authoritative accounting records have higher evidentiary weight than photographs.
- Tax policy must be versioned by effective date.
- Every filing/payment recommendation requires human/accountant approval.

Future Drive behavior:
- External document repository behind an adapter.
- No vendor-specific dependency in domain logic.
- Files organized by Company, fiscal period, document type and UUID.
- Yarvis stores metadata, hash, provenance and repository reference.

## Sprint 7.3A Addendum

Manual file intake is now the controlled first source and follows:

Manual Upload -> SourceRecord -> DocumentRecord -> Classification -> Extraction -> Candidate Observations -> Preview -> Human Confirmation.

This addendum keeps the same immutability and confirmation constraints from ADR-010.
