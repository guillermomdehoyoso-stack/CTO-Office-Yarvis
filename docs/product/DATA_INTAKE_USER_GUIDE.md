# Data Intake User Guide (Backend Flow)

## Upload

Use POST /data-intake/documents (multipart/form-data) with:
- file
- source_type (optional)
- source_name (optional)
- classification (optional)

Response includes:
- document_id
- duplicate status
- processing status

## Process and Preview

1. POST /data-intake/documents/{document_id}/process
2. GET /data-intake/documents/{document_id}/preview

Preview shows parser/classification/mapping proposals and candidate observation summary.

## Confirm, Reject, Reprocess

- POST /data-intake/documents/{document_id}/confirm
- POST /data-intake/documents/{document_id}/reject
- POST /data-intake/documents/{document_id}/reprocess

All actions record reviewer and timeline events.

## Operational Rules

- Preview must happen before confirmation-sensitive state transitions.
- Candidate observations do not equal confirmed identity/ownership.
- Duplicate files are detected by SHA-256.
- Unknown report types remain reviewable and importable.
