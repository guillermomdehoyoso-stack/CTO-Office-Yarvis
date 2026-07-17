from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DataIntakeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    filename: str | None
    original_filename: str | None
    media_type: str
    file_hash: str
    byte_size: int | None
    storage_reference: str | None
    extraction_status: str
    detected_file_type: str | None
    detected_report_type: str | None
    classification_confidence: float | None
    parser_key: str | None
    parser_version: str | None
    processing_error: str | None
    row_count: int | None
    observation_count: int | None
    duplicate_of_document_id: UUID | None
    review_status: str
    confirmed_by: str | None
    confirmed_at: datetime | None
    created_at: datetime
    processed_at: datetime | None


class DataIntakeUploadResponse(BaseModel):
    document_id: UUID
    duplicate: bool
    duplicate_of_document_id: UUID | None = None
    processing_status: str


class DataIntakeProcessResponse(BaseModel):
    document_id: UUID
    status: str
    preview_ready: bool


class DataIntakeConfirmRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=255)


class DataIntakeRejectRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=255)
    reason: str | None = None


class DataIntakeReprocessRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=255)


class DataIntakePreviewResponse(BaseModel):
    document_metadata: dict
    duplicate_status: bool
    detected_report_type: str
    confidence: float
    parser_used: str
    worksheets: list[str]
    original_columns: list[str]
    proposed_canonical_mappings: list[dict]
    sample_rows: list[dict]
    total_rows: int
    candidate_observation_count: int
    detected_strong_identifiers: list[dict]
    conflicts: list[dict]
    warnings: list[str]
    fields_requiring_review: list[dict]
    proposed_changes_summary: dict
    operational_summary: dict
