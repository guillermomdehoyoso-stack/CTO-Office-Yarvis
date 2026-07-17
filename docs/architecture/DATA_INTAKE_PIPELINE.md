# Data Intake Pipeline

## Approved Flow

Manual Upload
-> SourceRecord
-> DocumentRecord
-> File Classification
-> Content Extraction
-> Candidate Observations
-> Preview
-> Human Confirmation
-> Resolution / Operational State
-> Mission Control

## Lifecycle

1. User uploads a file through controlled API.
2. File inspection validates name, size, extension, and detected media type.
3. SHA-256 is computed and duplicate detection is performed.
4. SourceRecord and DocumentRecord are persisted.
5. File content is parsed locally with deterministic parser selection.
6. Report type classification is evaluated from deterministic signals.
7. Candidate observations are generated with row/column provenance.
8. Preview is persisted for human review.
9. Reviewer confirms/rejects/reprocesses explicitly.
10. Events are emitted without logging sensitive file content.

## File Storage

- Repository abstraction: DocumentRepository.
- Default implementation: LocalDocumentRepository.
- Root path: DOCUMENT_STORAGE_ROOT (default /data/yarvis in container).
- Stored filename is internal/generated.
- Original filename is metadata only.
- API exposes storage_reference only, never host absolute paths.

## Hash Calculation

- SHA-256 on uploaded bytes.
- Stored in DocumentRecord.file_hash.
- Used for duplicate detection and traceability.

## Duplicate Handling

- Duplicate detection by file_hash.
- New DocumentRecord may reference duplicate_of_document_id.
- Duplicate ingestion is idempotent and does not duplicate observations.

## Classification

Deterministic report classifier returns:
- report_type
- confidence
- matched_signals
- missing_expected_fields

Unknown documents remain importable with report_type=unknown.

## Extraction

Parsers:
- CsvTableParser
- XlsxTableParser
- DigitalPdfParser
- TextParser
- JsonParser
- ImageRegistrationParser

Rules:
- Local-only extraction.
- No external AI provider file transfer.
- Image OCR remains optional and non-blocking.

## Preview

Preview includes:
- document metadata
- duplicate status
- report type + confidence
- parser and worksheets
- original columns + canonical mapping proposals
- sample rows + total rows
- candidate observation count
- strong identifiers + conflicts + warnings
- fields requiring review

## Confirmation

Actions:
- confirm document
- reject document
- reprocess document

Recorded:
- reviewer
- timestamp
- parser version

## Failure Handling

- Invalid extension or file size rejected early.
- Unsupported/invalid parser input sets review_status=failed.
- Processing error is recorded in DocumentRecord.processing_error.

## Reprocessing

- Explicit action only.
- Preserves historical observations/events.
- Reprocessing must keep parser/version provenance.

## Provenance

Each observation preserves:
- source_id
- document_id
- source_reference (worksheet/row/column)
- extraction method
- parser key/version
- confidence
- observed_at

## Retention

- Files remain in configured repository storage.
- Metadata, hashes, observations, and events remain auditable.

## Security

- Uploaded files are never committed to Git.
- Path traversal is rejected.
- Executables and archives are rejected.
- File contents are not logged in events.
- External AI provider transfer is disabled in this flow.

## NetPay Examples

- Weekly sales XLSX produces candidate observations for store_id, sales_volume, inactive_days.
- Unknown CSV enters preview review with report_type=unknown.
- Reuploading same file triggers duplicate detection.

## Future Accounting Examples

Future evidence:
- CFDI XML
- invoice PDF
- invoice photo
- payment complement
- bank statement
- issued/received invoice reports
- expense receipt

Evidentiary priority:
1. CFDI XML
2. authoritative SAT/accounting export
3. digital PDF
4. image/photo
5. manual data

No VAT/income-tax calculation is implemented in Sprint 7.3A.
