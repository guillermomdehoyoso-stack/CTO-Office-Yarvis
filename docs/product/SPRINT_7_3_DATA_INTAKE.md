# Sprint 7.3A — Controlled Data Intake Backend

## Objective

Implement the first controlled evidence intake pipeline for reusable multi-domain ingestion, starting with NetPay.

## Delivered Backend Scope

- Multipart file upload endpoint.
- Local document repository adapter with safe storage references.
- SHA-256 duplicate detection.
- Deterministic parser registry.
- Deterministic report classifier.
- NetPay canonical mapping proposals.
- Candidate observation generation from structured rows.
- Preview service before confirmation.
- Explicit confirm/reject/reprocess flow.
- Mission Control intake counts.

## Supported Types

- CSV
- XLSX
- PDF (digital extraction local)
- TXT
- JSON
- PNG/JPG/JPEG (registration, optional local OCR)

## Explicit Non-Scope

- Gmail/WhatsApp/Drive integrations.
- Folder watchers.
- NetPay portal automation.
- Real invoice OCR pipeline.
- Tax calculations.
- Graph database.
- Autonomous agents.

## API

- POST /data-intake/documents
- GET /data-intake/documents
- GET /data-intake/documents/{document_id}
- POST /data-intake/documents/{document_id}/process
- GET /data-intake/documents/{document_id}/preview
- POST /data-intake/documents/{document_id}/confirm
- POST /data-intake/documents/{document_id}/reject
- POST /data-intake/documents/{document_id}/reprocess
- GET /data-intake/report-types
- GET /data-intake/parsers
