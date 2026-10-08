"""API contracts for the read-only Netpay Gmail Intake D1 slice."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GmailConnectionCreate(BaseModel):
    provider_account_id: str = Field(min_length=1, max_length=255)
    label_id: str = Field(min_length=1, max_length=255)
    query: str = Field(default="", max_length=500)
    credential_secret_ref: str = Field(min_length=1, max_length=255)


class GmailConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    provider_account_id: str
    label_id: str
    query: str
    state: str
    cursor: str | None
    last_sync_at: datetime | None
    last_error_code: str | None
    created_at: datetime
    updated_at: datetime


class GmailSyncRequest(BaseModel):
    backfill_days: int = Field(default=30, ge=1, le=30)


class GmailSyncRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    connection_id: UUID
    status: str
    window_start: datetime
    window_end: datetime
    cursor_before: str | None
    cursor_after: str | None
    captured_count: int
    deduplicated_count: int
    conflict_count: int
    failed_count: int
    failure_code: str | None
    correlation_id: UUID
    started_at: datetime
    completed_at: datetime | None


class GmailSourceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    connection_id: UUID
    provider_account_id: str
    gmail_message_id: str
    gmail_thread_id: str
    provider_received_at: datetime
    synchronized_at: datetime
    sender: str | None
    recipient: str | None
    subject: str | None
    plain_excerpt: str
    source_fingerprint: str
    attachment_metadata: list[dict]
    provenance: dict
    conflict_detected_at: datetime | None
    conflict_fingerprint: str | None
    created_at: datetime
    updated_at: datetime


class GmailSourcePage(BaseModel):
    items: list[GmailSourceItemRead]
    offset: int
    limit: int
    total: int


class GmailSyncPage(BaseModel):
    items: list[GmailSyncRead]
    offset: int
    limit: int
    total: int
